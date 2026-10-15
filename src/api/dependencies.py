# Dependency functions

import logging

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, HTTPException

from src.generation.answer_generator import (
    GroundedAnswerGenerator,
)
from src.generation.llm_provider import create_llm
from src.retrieval.langchain_retriever import (
    SemanticRetriever,
)


logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def get_retriever() -> SemanticRetriever:
    """
    Load and cache the embedding model
    and FAISS index.
    """

    try:
        return SemanticRetriever.from_local()

    except Exception as error:
        logger.exception(
            "Failed to initialize document retriever."
        )

        raise HTTPException(
            status_code=503,
            detail="Retrieval service unavailable.",
        ) from error


def get_answer_generator(
    retriever: SemanticRetriever = Depends(
        get_retriever
    ),
) -> GroundedAnswerGenerator:
    """
    Create an answer generator using the
    existing retriever and Groq LLM.
    """

    load_dotenv(
        PROJECT_ROOT / ".env"
    )

    try:
        llm = create_llm()

        return GroundedAnswerGenerator(
            retriever=retriever,
            llm=llm,
        )

    except Exception as error:
        logger.exception(
            "Failed to initialize answer generator."
        )

        raise HTTPException(
            status_code=503,
            detail="Answer generation service unavailable.",
        ) from error