from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from src.api.usage_limits import UsageLimitMiddleware


def create_test_app():
    app = FastAPI()

    app.add_middleware(
        UsageLimitMiddleware,
        max_answers_per_hour=2,
        max_index_actions_per_hour=1,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://example.pages.dev"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/ask")
    def ask():
        return {"answer": "Example answer"}

    @app.post("/workspaces/text")
    def index_text():
        return {"indexed": True}

    return app


def test_answer_limit():
    with TestClient(create_test_app()) as client:
        assert client.post("/ask").status_code == 200
        assert client.post("/ask").status_code == 200

        response = client.post("/ask")

        assert response.status_code == 429
        assert "Retry-After" in response.headers


def test_indexing_limit():
    with TestClient(create_test_app()) as client:
        assert (
            client.post("/workspaces/text").status_code
            == 200
        )

        assert (
            client.post("/workspaces/text").status_code
            == 429
        )


def test_health_is_not_rate_limited():
    with TestClient(create_test_app()) as client:
        for _ in range(5):
            assert client.get("/health").status_code == 200


def test_rate_limit_response_allows_cors():
    with TestClient(create_test_app()) as client:
        headers = {
            "Origin": "https://example.pages.dev"
        }

        client.post("/ask", headers=headers)
        client.post("/ask", headers=headers)

        response = client.post(
            "/ask",
            headers=headers,
        )

        assert response.status_code == 429

        assert (
            response.headers["access-control-allow-origin"]
            == "https://example.pages.dev"
        )