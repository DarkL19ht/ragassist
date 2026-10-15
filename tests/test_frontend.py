import httpx
import pytest

from src.frontend.client import (
    BackendRequestError,
    query_backend,
)

from src.frontend.app import (
    format_evidence,
    handle_question,
)


SAMPLE_ANSWER = {
    "question": "Can employees work abroad?",
    "answer": "Written HR approval is required. [Source 1]",
    "status": "answered",
    "sources": [
        {
            "source_number": 1,
            "file_name": "remote_work_policy.txt",
            "page_number": None,
            "chunk_id": "chunk-001",
            "score": 0.9,
        }
    ],
    "retrieved_chunks": 1,
}


SAMPLE_RETRIEVAL = {
    "question": "Can employees work abroad?",
    "results": [
        {
            "text": "Written HR approval is required.",
            "file_name": "remote_work_policy.txt",
            "page_number": None,
            "chunk_id": "chunk-001",
            "score": 0.9,
        }
    ],
}


def mock_backend(request):
    if request.url.path == "/ask":
        return httpx.Response(
            200,
            json=SAMPLE_ANSWER,
        )

    if request.url.path == "/retrieve":
        return httpx.Response(
            200,
            json=SAMPLE_RETRIEVAL,
        )

    return httpx.Response(404)


def test_client_returns_answer_and_evidence():
    transport = httpx.MockTransport(mock_backend)

    answer, retrieval = query_backend(
        "Can employees work abroad?",
        top_k=3,
        base_url="http://testserver",
        transport=transport,
    )

    assert answer["status"] == "answered"
    assert len(answer["sources"]) == 1
    assert len(retrieval["results"]) == 1


def test_client_rejects_empty_question():
    with pytest.raises(ValueError):
        query_backend("   ")


def test_client_rejects_invalid_top_k():
    with pytest.raises(ValueError):
        query_backend(
            "What is the policy?",
            top_k=0,
        )


def test_client_rejects_long_question():
    with pytest.raises(ValueError):
        query_backend("A" * 2001)


def test_client_handles_server_errors():
    def error_backend(request):
        return httpx.Response(
            503,
            json={"detail": "Unavailable"},
        )

    transport = httpx.MockTransport(error_backend)

    with pytest.raises(
        BackendRequestError,
        match="HTTP 503",
    ):
        query_backend(
            "What is the policy?",
            base_url="http://testserver",
            transport=transport,
        )


def test_evidence_formatting():
    evidence = format_evidence(SAMPLE_RETRIEVAL)

    assert "remote_work_policy.txt" in evidence
    assert "chunk-001" in evidence
    assert "Written HR approval" in evidence


def test_frontend_handler(monkeypatch):
    import src.frontend.app as frontend_app

    monkeypatch.setattr(
        frontend_app,
        "query_backend",
        lambda question, top_k: (
            SAMPLE_ANSWER,
            SAMPLE_RETRIEVAL,
        ),
    )

    answer, status, sources, evidence = (
        handle_question(
            "Can employees work abroad?",
            3,
        )
    )

    assert status == "answered"
    assert "HR approval" in answer
    assert len(sources) == 1
    assert "remote_work_policy.txt" in evidence