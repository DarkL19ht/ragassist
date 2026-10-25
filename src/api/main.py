# API endpoints

import logging

from fastapi import Depends, FastAPI, HTTPException

from src.api.dependencies import (
    get_answer_generator,
    get_retriever,
)
from src.api.schemas import (
    AnswerResponse,
    HealthResponse,
    QuestionRequest,
    RetrievalResponse,
)
from src.generation.answer_generator import (
    GroundedAnswerGenerator,
)
from src.retrieval.langchain_retriever import (
    SemanticRetriever,
)


logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAGAssist API",
    description=(
        "Evidence-grounded document question answering "
        "using sentence embeddings, FAISS, "
        "LangChain and an LLM."
    ),
    version="1.0.0",
)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
)
def health_check():
    """
    Check whether the API server is responding.

    This is a liveness check, not a full
    embedding-model or LLM readiness check.
    """

    return {
        "status": "ok",
        "service": "RAGAssist API",
    }


@app.post(
    "/retrieve",
    response_model=RetrievalResponse,
    tags=["Retrieval"],
)
def retrieve_documents(
    request: QuestionRequest,
    retriever: SemanticRetriever = Depends(
        get_retriever
    ),
):
    """
    Return relevant source passages
    without generating an LLM answer.
    """

    try:
        documents = retriever.retrieve(
            question=request.question,
            top_k=request.top_k,
        )

    except Exception as error:
        logger.exception(
            "Document retrieval request failed."
        )

        raise HTTPException(
            status_code=503,
            detail="Document retrieval failed.",
        ) from error

    results = []

    for document in documents:
        metadata = document.metadata

        results.append(
            {
                "text": document.page_content,
                "file_name": metadata.get(
                    "file_name"
                ),
                "page_number": metadata.get(
                    "page_number"
                ),
                "chunk_id": metadata.get(
                    "chunk_id"
                ),
                "score": metadata.get(
                    "score"
                ),
            }
        )

    return {
        "question": request.question,
        "results": results,
    }


@app.post(
    "/ask",
    response_model=AnswerResponse,
    tags=["Question Answering"],
)
def ask_question(
    request: QuestionRequest,
    generator: GroundedAnswerGenerator = Depends(
        get_answer_generator
    ),
):
    """
    Retrieve evidence and generate
    a source-grounded answer.
    """

    try:
        return generator.answer(
            question=request.question,
            top_k=request.top_k,
        )

    except Exception as error:
        logger.exception(
            "Answer generation request failed."
        )

        raise HTTPException(
            status_code=502,
            detail="Answer generation failed.",
        ) from error

# Session-scoped document uploads and question answering.
from src.api.workspace_routes import router as workspace_router
app.include_router(workspace_router)


# Accept browser requests from the separate static frontend.
from src.api.cors_config import configure_cors

#Register the middleware
import os

from src.api.usage_limits import UsageLimitMiddleware

app.add_middleware(
    UsageLimitMiddleware,
    max_answers_per_hour=int(
        os.getenv("MAX_ANSWERS_PER_HOUR", "20")
    ),
    max_index_actions_per_hour=int(
        os.getenv("MAX_INDEX_ACTIONS_PER_HOUR", "12")
    ),
)
configure_cors(app)
