from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class QuestionRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000,
    )

    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        strict=True,
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, value):
        if not value.strip():
            raise ValueError(
                "Question cannot be empty or whitespace."
            )

        return value.strip()


class RetrievedPassage(BaseModel):
    text: str
    file_name: str | None = None
    page_number: int | None = None
    chunk_id: str | None = None
    score: float | None = None


class RetrievalResponse(BaseModel):
    question: str
    results: list[RetrievedPassage]


class SourceReference(BaseModel):
    source_number: int
    file_name: str | None = None
    page_number: int | None = None
    chunk_id: str | None = None
    score: float | None = None


class AnswerResponse(BaseModel):
    question: str
    answer: str
    status: Literal[
        "answered",
        "insufficient_evidence",
    ]
    sources: list[SourceReference]
    retrieved_chunks: int


class HealthResponse(BaseModel):
    status: str
    service: str