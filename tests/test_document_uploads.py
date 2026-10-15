"""Upload workspace tests; no real embedding model or Groq calls."""

from pathlib import Path

import httpx
import pytest

from src.frontend.app import (
    build_demo,
    index_sources,
    render_library,
    run_active_research,
)
from src.frontend.client import (
    create_workspace,
    delete_workspace,
    query_workspace,
    upload_workspace_file,
    upload_workspace_text,
)
from src.api.workspace_store import (
    WORKSPACE_TTL_SECONDS,
    WorkspaceError,
    WorkspaceService,
)


def test_workspace_tokens_are_separate_and_expire():
    now = [0.0]
    svc = WorkspaceService(clock=lambda: now[0])
    alice = svc.create()["workspace_token"]
    bob = svc.create()["workspace_token"]
    assert alice != bob
    assert svc.describe(alice)["documents"] == []
    assert svc.describe(bob)["documents"] == []
    now[0] = WORKSPACE_TTL_SECONDS + 1
    with pytest.raises(WorkspaceError, match="expired"):
        svc.describe(alice)


def test_workspace_delete_invalidates_token():
    svc = WorkspaceService()
    token = svc.create()["workspace_token"]
    svc.delete(token)
    with pytest.raises(WorkspaceError):
        svc.describe(token)


def test_file_upload_rejects_unsupported_extension():
    svc = WorkspaceService()
    token = svc.create()["workspace_token"]
    with pytest.raises(WorkspaceError, match="Only PDF and TXT"):
        svc.add_file(token, "payload.exe", b"some content")


def test_upload_rejects_invalid_utf8():
    svc = WorkspaceService()
    token = svc.create()["workspace_token"]
    with pytest.raises(WorkspaceError, match="UTF-8"):
        svc.add_file(token, "policy.txt", b"\xff\xfe\xff")


def test_gradio_layout_builds_with_document_upload():
    assert build_demo() is not None


def test_uploaded_filename_is_escaped():
    markup = render_library(['<script>alert(1)</script>.txt'])
    assert "<script>" not in markup
    assert "&lt;script&gt;" in markup


def test_frontend_routes_uploaded_questions_to_uploaded_index(monkeypatch):
    import src.frontend.app as module
    calls = []

    def fake_uploaded(question, top_k, token):
        calls.append((question, top_k, token))
        return (
            {"answer": "From uploaded source.", "sources": [], "status": "answered"},
            {"results": []},
        )

    def fail_demo(*args):
        raise AssertionError("Demo documents must not be searched")

    monkeypatch.setattr(module, "query_workspace", fake_uploaded)
    monkeypatch.setattr(module, "query_backend", fail_demo)
    panels = run_active_research("Where is the policy?", 3, "secret-token")
    assert "From uploaded source" in panels[1]
    assert calls == [("Where is the policy?", 3, "secret-token")]


def test_frontend_uses_demo_only_before_upload(monkeypatch):
    import src.frontend.app as module
    monkeypatch.setattr(module, "query_backend", lambda question, top_k: (
        {"answer": "Bundled sample", "sources": [], "status": "answered"},
        {"results": []},
    ))
    assert "Bundled sample" in run_active_research("Demo?", 3, None)[1]


def test_paste_text_is_sent_to_backend(monkeypatch):
    import src.frontend.app as module
    monkeypatch.setattr(module, "create_workspace", lambda: "secret-token")
    monkeypatch.setattr(module, "upload_workspace_text", lambda token, title, text: {
        "documents": ["meeting_notes.txt"],
        "document_count": 1,
        "chunk_count": 1,
    })
    result = index_sources([], "A written policy is required.",
                           "meeting_notes", None, [])
    assert result[0] == "secret-token"
    assert result[1] == ["meeting_notes.txt"]
    assert "YOUR SOURCE LIBRARY" in result[2]


def test_client_upload_and_query_uses_header_token():
    requests = []

    def mock_api(request):
        requests.append(request)
        if request.url.path == "/workspaces" and request.method == "POST":
            return httpx.Response(200, json={"workspace_token": "top-secret"})
        assert request.headers["X-Workspace-Token"] == "top-secret"
        if request.url.path.endswith("/ask"):
            return httpx.Response(200, json={
                "status": "answered", "answer": "A", "sources": []
            })
        if request.url.path.endswith("/retrieve"):
            return httpx.Response(200, json={"results": []})
        return httpx.Response(200, json={"documents": ["uploaded.txt"]})

    transport = httpx.MockTransport(mock_api)
    token = create_workspace(base_url="http://local", transport=transport)
    upload_workspace_file(token, "uploaded.txt", b"Policy", base_url="http://local",
                          transport=transport)
    upload_workspace_text(token, "notes", "Policy", base_url="http://local",
                          transport=transport)
    answer, retrieved = query_workspace("What?", 2, token, base_url="http://local",
                                        transport=transport)
    assert answer["status"] == "answered"
    assert retrieved["results"] == []
    assert len(requests) == 5
    assert all("top-secret" not in str(request.url) for request in requests)


def test_valid_utf8_txt_is_indexed_without_model_download():
    import numpy as np

    class FakeEmbedder:
        def encode(self, texts):
            vectors = np.zeros((len(texts), 384), dtype="float32")
            vectors[:, 0] = 1.0
            return vectors

    service = WorkspaceService(embedder_factory=lambda: FakeEmbedder())
    token = service.create()["workspace_token"]
    info = service.add_file(token, "uploaded.txt", b"A policy requires written approval.")
    assert info["documents"] == ["uploaded.txt"]
    results = service.retriever(token).retrieve("What is required?", top_k=3)
    assert "written approval" in results[0].page_content
    assert results[0].metadata["file_name"] == "uploaded.txt"


def test_pdf_upload_extracts_text_and_page_metadata():
    import io

    import numpy as np
    from reportlab.pdfgen import canvas

    class FakeEmbedder:
        def encode(self, texts):
            vectors = np.zeros((len(texts), 384), dtype="float32")
            vectors[:, 0] = 1.0
            return vectors

    pdf_buffer = io.BytesIO()
    pdf = canvas.Canvas(pdf_buffer)
    pdf.drawString(72, 720, "Travel expenses require prior approval.")
    pdf.showPage()
    pdf.save()

    service = WorkspaceService(embedder_factory=lambda: FakeEmbedder())
    token = service.create()["workspace_token"]
    info = service.add_file(token, "travel_policy.pdf", pdf_buffer.getvalue())
    assert info["documents"] == ["travel_policy.pdf"]
    results = service.retriever(token).retrieve("What requires approval?", top_k=3)
    assert results[0].metadata["page_number"] == 1
    assert "Travel expenses" in results[0].page_content
