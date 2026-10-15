"""Session-scoped document indexing and Q&A HTTP endpoints."""

from functools import partial
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field, field_validator

from src.api.schemas import AnswerResponse, QuestionRequest, RetrievalResponse
from src.api.workspace_store import (
    MAX_FILE_BYTES,
    WorkspaceError,
    WorkspaceService,
    get_workspace_service,
)
from src.generation.answer_generator import GroundedAnswerGenerator
from src.generation.llm_provider import create_llm


router = APIRouter(prefix="/workspaces", tags=["Uploaded Documents"])
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class PastedTextRequest(BaseModel):
    title: str = Field(default="pasted_notes", max_length=100)
    text: str = Field(min_length=1, max_length=50_000)

    @field_validator("text")
    @classmethod
    def check_text(cls, value):
        if not value.strip():
            raise ValueError("Pasted text cannot be blank.")
        return value


def service_error(error: WorkspaceError):
    message = str(error)
    if "not found or expired" in message:
        return HTTPException(status_code=404, detail=message)
    if "Too many active" in message:
        return HTTPException(status_code=503, detail=message)
    if "Index a PDF" in message:
        return HTTPException(status_code=409, detail=message)
    return HTTPException(status_code=422, detail=message)


@router.post("")
def create_workspace(service: WorkspaceService = Depends(get_workspace_service)):
    try:
        return service.create()
    except WorkspaceError as error:
        raise service_error(error) from error


@router.get("")
def get_workspace(
    x_workspace_token: str = Header(...),
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        return service.describe(x_workspace_token)
    except WorkspaceError as error:
        raise service_error(error) from error


@router.delete("")
def clear_workspace(
    x_workspace_token: str = Header(...),
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        service.delete(x_workspace_token)
        return {"deleted": True}
    except WorkspaceError as error:
        raise service_error(error) from error


@router.post("/documents")
async def upload_document(
    file: UploadFile = File(...),
    x_workspace_token: str = Header(...),
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        # Bound memory usage; do not trust client Content-Length headers.
        content = await file.read(MAX_FILE_BYTES + 1)
        return service.add_file(x_workspace_token, file.filename or "", content)
    except WorkspaceError as error:
        raise service_error(error) from error
    finally:
        await file.close()


@router.post("/text")
def upload_text(
    body: PastedTextRequest,
    x_workspace_token: str = Header(...),
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        return service.add_text(x_workspace_token, body.title, body.text)
    except WorkspaceError as error:
        raise service_error(error) from error


@router.post("/retrieve", response_model=RetrievalResponse)
def retrieve_uploaded(
    body: QuestionRequest,
    x_workspace_token: str = Header(...),
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        retriever = service.retriever(x_workspace_token)
        documents = retriever.retrieve(question=body.question, top_k=body.top_k)
        return {
            "question": body.question,
            "results": [
                {
                    "text": document.page_content,
                    "file_name": document.metadata.get("file_name"),
                    "page_number": document.metadata.get("page_number"),
                    "chunk_id": document.metadata.get("chunk_id"),
                    "score": document.metadata.get("score"),
                }
                for document in documents
            ],
        }
    except WorkspaceError as error:
        raise service_error(error) from error
    except Exception as error:
        raise HTTPException(
            status_code=503, detail="Uploaded document retrieval failed."
        ) from error


@router.post("/ask", response_model=AnswerResponse)
def ask_uploaded(
    body: QuestionRequest,
    x_workspace_token: str = Header(...),
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        retriever = service.retriever(x_workspace_token)
    except WorkspaceError as error:
        raise service_error(error) from error

    load_dotenv(PROJECT_ROOT / ".env")
    try:
        generator = GroundedAnswerGenerator(
            retriever=retriever,
            llm=create_llm(),
        )
        return generator.answer(question=body.question, top_k=body.top_k)
    except Exception as error:
        raise HTTPException(
            status_code=502, detail="Uploaded document answer generation failed."
        ) from error
