import os
import httpx
DEFAULT_API_URL = "http://127.0.0.1:8000"
class BackendRequestError(RuntimeError):
    pass

def query_backend(question: str, top_k: int = 3, *, base_url: str | None = None, transport=None) -> tuple[dict, dict]:
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Please enter a question.")
    question = question.strip()
    if len(question) > 2000:
        raise ValueError("Questions cannot exceed 2,000 characters.")
    if type(top_k) is not int or not 1 <= top_k <= 10:
        raise ValueError("The retrieval limit must be between 1 and 10.")
    api_url = (base_url or os.environ.get("RAGASSIST_API_URL", DEFAULT_API_URL)).rstrip("/")
    payload = {"question": question, "top_k": top_k}
    try:
        with httpx.Client(base_url=api_url,timeout=httpx.Timeout(90.0,connect=5.0),transport=transport) as client:
            a=client.post("/ask",json=payload); a.raise_for_status()
            r=client.post("/retrieve",json=payload); r.raise_for_status()
            return a.json(),r.json()
    except httpx.HTTPStatusError as error:
        raise BackendRequestError(f"RAGAssist API returned HTTP {error.response.status_code}. Check the FastAPI server logs.") from error
    except httpx.RequestError as error:
        raise BackendRequestError("Unable to connect to the RAGAssist API. Check that FastAPI is running.") from error


def _workspace_request(method, endpoint, *, token=None, json=None, files=None,
                       base_url=None, transport=None):
    """Send a workspace request without exposing the token in the URL."""
    api_url = (base_url or os.environ.get("RAGASSIST_API_URL", DEFAULT_API_URL)).rstrip("/")
    headers = {"X-Workspace-Token": token} if token else {}
    try:
        with httpx.Client(
            base_url=api_url,
            timeout=httpx.Timeout(120.0, connect=5.0),
            transport=transport,
        ) as client:
            response = client.request(
                method, endpoint, headers=headers, json=json, files=files,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as error:
        try:
            detail = error.response.json().get("detail", "Request failed")
            if not isinstance(detail, str):
                detail = "Request rejected"
        except (ValueError, AttributeError):
            detail = "Request failed"
        raise BackendRequestError(
            f"Upload workspace error (HTTP {error.response.status_code}): {detail}"
        ) from error
    except httpx.RequestError as error:
        raise BackendRequestError(
            "Could not contact the RAGAssist API. Make sure FastAPI is running."
        ) from error


def create_workspace(*, base_url=None, transport=None):
    return _workspace_request("POST", "/workspaces", base_url=base_url,
                              transport=transport)["workspace_token"]


def upload_workspace_file(token, filename, data, *, base_url=None, transport=None):
    return _workspace_request(
        "POST", "/workspaces/documents", token=token,
        files={"file": (filename, data, "application/octet-stream")},
        base_url=base_url, transport=transport,
    )


def upload_workspace_text(token, title, text, *, base_url=None, transport=None):
    return _workspace_request(
        "POST", "/workspaces/text", token=token,
        json={"title": title, "text": text},
        base_url=base_url, transport=transport,
    )


def delete_workspace(token, *, base_url=None, transport=None):
    if not token:
        return {"deleted": True}
    return _workspace_request("DELETE", "/workspaces", token=token,
                              base_url=base_url, transport=transport)


def query_workspace(question, top_k, token, *, base_url=None, transport=None):
    if not token:
        raise ValueError("Upload documents or paste text to start a document workspace.")
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Please enter a question.")
    if len(question) > 2000:
        raise ValueError("Questions cannot exceed 2,000 characters.")
    if type(top_k) is not int or not 1 <= top_k <= 10:
        raise ValueError("The retrieval limit must be between 1 and 10.")

    payload = {"question": question.strip(), "top_k": top_k}
    answer = _workspace_request("POST", "/workspaces/ask", token=token,
                                json=payload, base_url=base_url, transport=transport)
    retrieval = _workspace_request("POST", "/workspaces/retrieve", token=token,
                                   json=payload, base_url=base_url, transport=transport)
    return answer, retrieval
