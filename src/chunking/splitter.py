# Implement the chunking algorithm

import hashlib

from src.chunking.schema import ChunkRecord
from src.ingestion.schema import DocumentRecord


def create_chunk_id(
    record: DocumentRecord,
    chunk_index: int,
    start_char: int,
    end_char: int,
    text: str,
) -> str:
    """
    Create a deterministic chunk ID.

    Identical inputs produce identical IDs.
    """
    identity = (
        f"{record.source}|"
        f"{record.page_number}|"
        f"{chunk_index}|"
        f"{start_char}|"
        f"{end_char}|"
        f"{text}"
    )

    return hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()[:16]


def split_document(
    record: DocumentRecord,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
) -> list[ChunkRecord]:
    """
    Split a document record into overlapping
    character-based chunks.
    """

    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be greater than zero"
        )

    if chunk_overlap < 0:
        raise ValueError(
            "chunk_overlap cannot be negative"
        )

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size"
        )

    text = record.text

    if not text or not text.strip():
        return []

    chunks = []
    start = 0
    chunk_index = 0

    while start < len(text):
        end = min(
            start + chunk_size,
            len(text),
        )

        chunk_text = text[start:end]

        if chunk_text.strip():
            chunk_id = create_chunk_id(
                record=record,
                chunk_index=chunk_index,
                start_char=start,
                end_char=end,
                text=chunk_text,
            )

            chunks.append(
                ChunkRecord(
                    chunk_id=chunk_id,
                    text=chunk_text,
                    source=record.source,
                    file_name=record.file_name,
                    file_type=record.file_type,
                    page_number=record.page_number,
                    chunk_index=chunk_index,
                    start_char=start,
                    end_char=end,
                )
            )

        if end == len(text):
            break

        start = end - chunk_overlap
        chunk_index += 1

    return chunks


def split_documents(
    records: list[DocumentRecord],
    chunk_size: int = 500,
    chunk_overlap: int = 100,
) -> list[ChunkRecord]:
    """
    Chunk multiple document records.
    """

    all_chunks = []

    for record in records:
        all_chunks.extend(
            split_document(
                record=record,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        )

    return all_chunks