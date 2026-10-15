import pytest

from fastapi import HTTPException
from fastapi.testclient import TestClient
from langchain_core.documents import Document

from src.api.dependencies import (
    get_answer_generator,
    get_retriever,
)
from src.api.main import app


class FakeRetriever:
    def retrieve(self, question, top_k=3):
        documents = [
            Document(
                page_content=(
                    "Employees must obtain written "
                    "approval from HR before working "
                    "from another country."
                ),
                metadata={
                    "file_name": "remote_work_policy.txt",
                    "page_number": None,
                    "chunk_id": "chunk-001",
                    "score": 0.92,
                },
            ),
            Document(
                page_content=(
                    "Remote-working arrangements "
                    "are reviewed every six months."
                ),
                metadata={
                    "file_name": "remote_work_policy.txt",
                    "page_number": None,
                    "chunk_id": "chunk-002",
                    "score": 0.70,
                },
            ),
        ]

        return documents[:top_k]


class FakeAnswerGenerator:
    def __init__(self, insufficient=False):
        self.insufficient = insufficient

    def answer(self, question, top_k=3):
        if self.insufficient:
            return {
                "question": question,
                "answer": (
                    "I couldn't find enough reliable "
                    "evidence in the provided documents "
                    "to answer that question."
                ),
                "status": "insufficient_evidence",
                "sources": [],
                "retrieved_chunks": 2,
            }

        return {
            "question": question,
            "answer": (
                "Written HR approval is required. "
                "[Source 1]"
            ),
            "status": "answered",
            "sources": [
                {
                    "source_number": 1,
                    "file_name": "remote_work_policy.txt",
                    "page_number": None,
                    "chunk_id": "chunk-001",
                    "score": 0.92,
                }
            ],
            "retrieved_chunks": 2,
        }


@pytest.fixture(autouse=True)
def reset_dependency_overrides():
    app.dependency_overrides.clear()

    yield

    app.dependency_overrides.clear()


@pytest.fixture
def client():
    app.dependency_overrides[get_retriever] = (
        lambda: FakeRetriever()
    )

    app.dependency_overrides[get_answer_generator] = (
        lambda: FakeAnswerGenerator()
    )

    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "RAGAssist API",
    }


def test_retrieve_endpoint(client):
    response = client.post(
        "/retrieve",
        json={
            "question": "Can I work abroad?",
            "top_k": 3,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["results"]) == 2

    assert (
        data["results"][0]["file_name"]
        == "remote_work_policy.txt"
    )

    assert (
        data["results"][0]["chunk_id"]
        == "chunk-001"
    )


def test_retrieve_top_k(client):
    response = client.post(
        "/retrieve",
        json={
            "question": "What is the policy?",
            "top_k": 1,
        },
    )

    assert response.status_code == 200
    assert len(response.json()["results"]) == 1


def test_ask_endpoint(client):
    response = client.post(
        "/ask",
        json={
            "question": "Can I work abroad?",
            "top_k": 3,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "answered"
    assert "HR approval" in data["answer"]
    assert len(data["sources"]) == 1


def test_ask_insufficient_evidence(client):
    app.dependency_overrides[get_answer_generator] = (
        lambda: FakeAnswerGenerator(
            insufficient=True
        )
    )

    response = client.post(
        "/ask",
        json={
            "question": "What is the furniture allowance?",
            "top_k": 3,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "insufficient_evidence"
    assert data["sources"] == []


def test_empty_question_rejected(client):
    response = client.post(
        "/ask",
        json={
            "question": "   ",
            "top_k": 3,
        },
    )

    assert response.status_code == 422


def test_zero_top_k_rejected(client):
    response = client.post(
        "/retrieve",
        json={
            "question": "Policy question",
            "top_k": 0,
        },
    )

    assert response.status_code == 422


def test_large_top_k_rejected(client):
    response = client.post(
        "/retrieve",
        json={
            "question": "Policy question",
            "top_k": 100,
        },
    )

    assert response.status_code == 422


def test_long_question_rejected(client):
    response = client.post(
        "/ask",
        json={
            "question": "A" * 2001,
            "top_k": 3,
        },
    )

    assert response.status_code == 422


def test_generator_failure(client):
    class BrokenGenerator:
        def answer(self, question, top_k=3):
            raise RuntimeError(
                "Simulated provider failure"
            )

    app.dependency_overrides[get_answer_generator] = (
        lambda: BrokenGenerator()
    )

    response = client.post(
        "/ask",
        json={
            "question": "Policy question",
            "top_k": 3,
        },
    )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "Answer generation failed."
    )


def test_unavailable_retriever(client):
    def unavailable():
        raise HTTPException(
            status_code=503,
            detail="Retrieval service unavailable.",
        )

    app.dependency_overrides[get_retriever] = unavailable

    response = client.post(
        "/retrieve",
        json={
            "question": "Policy question",
            "top_k": 3,
        },
    )

    assert response.status_code == 503