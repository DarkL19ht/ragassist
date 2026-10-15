"""Short-lived, session-isolated document indexes for the research workbench.

These indexes live in ONE backend process, not on disk. This is deliberately a
local-demo implementation, not a production multi-tenant storage service.
"""

from __future__ import annotations

import io
import secrets
import threading
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from pypdf import PdfReader


MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_PDF_PAGES = 40
MAX_TEXT_CHARS = 50_000
MAX_TOTAL_CHARS = 150_000
MAX_SOURCES = 10
MAX_CHUNKS = 450
MAX_WORKSPACES = 25
WORKSPACE_TTL_SECONDS = 30 * 60
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


class WorkspaceError(ValueError):
    """An invalid, unavailable or expired workspace operation."""


@dataclass
class Workspace:
    token: str
    expires_at: float
    documents: list = field(default_factory=list)
    names: list[str] = field(default_factory=list)
    retriever: object | None = None
    chunk_count: int = 0


@lru_cache(maxsize=1)
def load_embedder():
    # Import lazily: health checks and mocked API tests do not load ML models.
    from src.embeddings.embedder import TextEmbedder
    return TextEmbedder()


class WorkspaceService:
    def __init__(self, *, embedder_factory=load_embedder, clock=time.monotonic):
        self._workspaces: dict[str, Workspace] = {}
        self._lock = threading.RLock()
        self._clock = clock
        self._embedder_factory = embedder_factory

    def _cleanup_expired(self):
        now = self._clock()
        for token in list(self._workspaces):
            if self._workspaces[token].expires_at <= now:
                del self._workspaces[token]

    def create(self) -> dict:
        with self._lock:
            self._cleanup_expired()
            if len(self._workspaces) >= MAX_WORKSPACES:
                raise WorkspaceError("Too many active workspaces. Please retry later.")
            token = secrets.token_urlsafe(32)
            workspace = Workspace(
                token=token,
                expires_at=self._clock() + WORKSPACE_TTL_SECONDS,
            )
            self._workspaces[token] = workspace
            return {
                "workspace_token": token,
                "expires_in_minutes": WORKSPACE_TTL_SECONDS // 60,
                "documents": [],
            }

    def _get(self, token: str) -> Workspace:
        self._cleanup_expired()
        workspace = self._workspaces.get(token)
        if workspace is None:
            raise WorkspaceError(
                "Document workspace not found or expired. "
                "Please index your documents again."
            )
        workspace.expires_at = self._clock() + WORKSPACE_TTL_SECONDS
        return workspace

    def describe(self, token: str) -> dict:
        with self._lock:
            workspace = self._get(token)
            return {
                "documents": list(workspace.names),
                "document_count": len(workspace.names),
                "chunk_count": workspace.chunk_count,
                "expires_in_minutes": WORKSPACE_TTL_SECONDS // 60,
            }

    def delete(self, token: str) -> None:
        with self._lock:
            if token not in self._workspaces:
                raise WorkspaceError("Document workspace not found or expired.")
            del self._workspaces[token]

    @staticmethod
    def _safe_name(name: str) -> str:
        base = Path((name or "document.txt").replace("\\", "/")).name
        base = "".join(c for c in base if c.isprintable() and c not in "/\\")
        return base[:100] or "document.txt"

    def add_text(self, token: str, title: str, text: str) -> dict:
        from src.ingestion.schema import DocumentRecord

        if not text or not text.strip():
            raise WorkspaceError("Paste some non-empty text before indexing.")
        if len(text) > MAX_TEXT_CHARS:
            raise WorkspaceError("Pasted text is limited to 50,000 characters.")
        name = self._safe_name(title.strip() or "pasted_notes.txt")
        if not name.lower().endswith(".txt"):
            name += ".txt"
        record = DocumentRecord(
            text=text.strip(),
            source=f"workspace/{uuid4().hex}/{name}",
            file_name=name,
            file_type="txt",
            page_number=None,
        )
        return self._add_records(token, [record], name)

    def add_file(self, token: str, filename: str, content: bytes) -> dict:
        name = self._safe_name(filename)
        extension = Path(name).suffix.lower()
        if extension not in {".pdf", ".txt"}:
            raise WorkspaceError("Only PDF and TXT files are supported.")
        if not content:
            raise WorkspaceError("The selected file is empty.")
        if len(content) > MAX_FILE_BYTES:
            raise WorkspaceError("Each uploaded file must be 5 MB or smaller.")

        prefix = f"workspace/{uuid4().hex}/{name}"
        if extension == ".txt":
            try:
                text = content.decode("utf-8-sig")
            except UnicodeDecodeError as error:
                raise WorkspaceError("TXT documents must use UTF-8 encoding.") from error
            if "\x00" in text or not text.strip():
                raise WorkspaceError("TXT file has no readable plain text.")
            if len(text) > MAX_TOTAL_CHARS:
                raise WorkspaceError("Document text exceeds the workspace limit.")
            from src.ingestion.schema import DocumentRecord
            records = [DocumentRecord(
                text=text,
                source=prefix,
                file_name=name,
                file_type="txt",
                page_number=None,
            )]
        else:
            if not content.startswith(b"%PDF-"):
                raise WorkspaceError("The selected PDF is not a valid PDF file.")
            try:
                reader = PdfReader(io.BytesIO(content), strict=False)
                if reader.is_encrypted or len(reader.pages) > MAX_PDF_PAGES:
                    raise WorkspaceError(
                        "Encrypted PDFs and PDFs over 40 pages are not supported."
                    )
                from src.ingestion.schema import DocumentRecord
                records = []
                char_count = 0
                for page_number, page in enumerate(reader.pages, start=1):
                    text = page.extract_text() or ""
                    if text.strip():
                        char_count += len(text)
                        if char_count > MAX_TOTAL_CHARS:
                            raise WorkspaceError("Extracted PDF text is too long.")
                        records.append(DocumentRecord(
                            text=text,
                            source=prefix,
                            file_name=name,
                            file_type="pdf",
                            page_number=page_number,
                        ))
            except WorkspaceError:
                raise
            except Exception as error:
                raise WorkspaceError("PDF could not be parsed.") from error
            if not records:
                raise WorkspaceError(
                    "No selectable text was found. Scanned PDFs need OCR, "
                    "which is not supported yet."
                )

        return self._add_records(token, records, name)

    def _add_records(self, token: str, new_records: list, source_name: str) -> dict:
        from src.chunking.splitter import split_document
        from src.retrieval.langchain_retriever import SemanticRetriever
        from src.retrieval.vector_store import FAISSVectorStore

        with self._lock:
            workspace = self._get(token)
            if len(workspace.names) >= MAX_SOURCES:
                raise WorkspaceError("A workspace supports up to 10 sources.")

            records = workspace.documents + new_records
            if sum(len(record.text) for record in records) > MAX_TOTAL_CHARS:
                raise WorkspaceError(
                    "Workspace text limit exceeded (150,000 characters)."
                )

            chunks = []
            for record in records:
                chunks.extend(split_document(
                    record,
                    chunk_size=CHUNK_SIZE,
                    chunk_overlap=CHUNK_OVERLAP,
                ))
            if not chunks:
                raise WorkspaceError("No indexable text was found.")
            if len(chunks) > MAX_CHUNKS:
                raise WorkspaceError("Too many document chunks for this demo.")

            # Construct the replacement index before changing workspace state.
            embedder = self._embedder_factory()
            vectors = embedder.encode([chunk.text for chunk in chunks])
            store = FAISSVectorStore()
            store.build(
                vectors=vectors,
                metadata=[chunk.to_dict() for chunk in chunks],
            )
            retriever = SemanticRetriever(embedder, store)
            workspace.documents = records
            workspace.names.append(source_name)
            workspace.retriever = retriever
            workspace.chunk_count = len(chunks)
            return self.describe(token)

    def retriever(self, token: str):
        with self._lock:
            workspace = self._get(token)
            if workspace.retriever is None:
                raise WorkspaceError("Index a PDF, TXT file or pasted text first.")
            return workspace.retriever


@lru_cache(maxsize=1)
def get_workspace_service() -> WorkspaceService:
    return WorkspaceService()
