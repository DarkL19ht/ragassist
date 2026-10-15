"""API smoke tests with a fake indexing service and fake LLM."""

import pytest
from fastapi.testclient import TestClient
from langchain_core.documents import Document

from src.api.main import app
from src.api.workspace_store import get_workspace_service


class FakeRetriever:
    def retrieve(self, question, top_k=3):
        return [Document(page_content="Employees need written approval.", metadata={
            "file_name": "uploaded.txt", "page_number": None,
            "chunk_id": "chunk-a", "score": 0.9,
        })][:top_k]


class FakeService:
    def __init__(self):
        self.tokens = set()
        self.data = {}

    def create(self):
        self.tokens.add("secret-token")
        self.data["secret-token"] = []
        return {"workspace_token": "secret-token", "expires_in_minutes": 30,
                "documents": []}

    def _checked(self, token):
        from src.api.workspace_store import WorkspaceError
        if token not in self.tokens:
            raise WorkspaceError("Document workspace not found or expired.")

    def describe(self, token):
        self._checked(token)
        return {"documents": self.data[token], "document_count": len(self.data[token]),
                "chunk_count": 1, "expires_in_minutes": 30}

    def add_text(self, token, title, text):
        self._checked(token)
        self.data[token].append(title + ".txt")
        return self.describe(token)

    def add_file(self, token, filename, content):
        self._checked(token)
        self.data[token].append(filename)
        return self.describe(token)

    def retriever(self, token):
        self._checked(token)
        return FakeRetriever()

    def delete(self, token):
        self._checked(token)
        self.tokens.remove(token)


@pytest.fixture
def client():
    service = FakeService()
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_create_and_index_pasted_text(client):
    token = client.post("/workspaces").json()["workspace_token"]
    response = client.post("/workspaces/text", headers={"X-Workspace-Token": token},
                           json={"title": "notes", "text": "Core hours are 10 to 3."})
    assert response.status_code == 200
    assert response.json()["documents"] == ["notes.txt"]


def test_pdf_txt_file_upload_endpoint(client):
    token = client.post("/workspaces").json()["workspace_token"]
    response = client.post("/workspaces/documents", headers={"X-Workspace-Token": token},
                           files={"file": ("policy.txt", b"Hello", "text/plain")})
    assert response.status_code == 200
    assert response.json()["document_count"] == 1


def test_uploaded_retrieval_returns_source_metadata(client):
    token = client.post("/workspaces").json()["workspace_token"]
    response = client.post("/workspaces/retrieve",
                           headers={"X-Workspace-Token": token},
                           json={"question": "What is required?", "top_k": 3})
    assert response.status_code == 200
    assert response.json()["results"][0]["file_name"] == "uploaded.txt"


def test_missing_token_is_rejected(client):
    response = client.post("/workspaces/retrieve",
                           json={"question": "What is required?", "top_k": 3})
    assert response.status_code == 422


def test_unknown_token_cannot_access_documents(client):
    response = client.get("/workspaces", headers={"X-Workspace-Token": "wrong"})
    assert response.status_code == 404


def test_ask_uses_uploaded_retriever_without_network(client, monkeypatch):
    import src.api.workspace_routes as routes

    class FakeGenerator:
        def __init__(self, retriever, llm):
            assert isinstance(retriever, FakeRetriever)

        def answer(self, question, top_k):
            return {"question": question, "answer": "Approval is required. [Source 1]",
                    "status": "answered", "retrieved_chunks": 1, "sources": [{
                        "source_number": 1, "file_name": "uploaded.txt",
                        "page_number": None, "chunk_id": "chunk-a", "score": 0.9,
                    }]}

    monkeypatch.setattr(routes, "GroundedAnswerGenerator", FakeGenerator)
    monkeypatch.setattr(routes, "create_llm", lambda: object())
    token = client.post("/workspaces").json()["workspace_token"]
    response = client.post("/workspaces/ask",
                           headers={"X-Workspace-Token": token},
                           json={"question": "What is required?", "top_k": 3})
    assert response.status_code == 200
    assert response.json()["status"] == "answered"
