import numpy as np
import pytest

from langchain_core.runnables import RunnableLambda

from src.generation.answer_generator import (
    FALLBACK_ANSWER,
    GroundedAnswerGenerator,
)
from src.retrieval.langchain_retriever import (
    SemanticRetriever,
)


SAMPLE_RESULT = {
    "chunk_id": "policy-chunk-001",
    "text": (
        "Employees must obtain written approval "
        "from HR before working from another country."
    ),
    "source": "data/sample_docs/policy.txt",
    "file_name": "policy.txt",
    "file_type": "txt",
    "page_number": None,
    "chunk_index": 0,
    "start_char": 0,
    "end_char": 94,
    "score": 0.89,
}


class FakeEmbedder:
    def encode(self, texts):
        return np.array(
            [[1.0, 0.0, 0.0]],
            dtype=np.float32,
        )


class FakeStore:
    def __init__(self, results=None):
        self.results = (
            [SAMPLE_RESULT]
            if results is None
            else results
        )

    def search(self, query_vector, top_k=3):
        return self.results[:top_k]


def make_generator(response, results=None):
    embedder = FakeEmbedder()
    store = FakeStore(results)

    retriever = SemanticRetriever(
        embedder=embedder,
        store=store,
    )

    fake_llm = RunnableLambda(
        lambda prompt: response
    )

    return GroundedAnswerGenerator(
        retriever=retriever,
        llm=fake_llm,
    )


def test_grounded_answer():
    generator = make_generator(
        "Written HR approval is required. [Source 1]"
    )

    result = generator.answer(
        "Can employees work abroad?"
    )

    assert result["status"] == "answered"
    assert "HR approval" in result["answer"]
    assert len(result["sources"]) == 1


def test_source_metadata_preserved():
    generator = make_generator(
        "HR approval is required. [Source 1]"
    )

    result = generator.answer(
        "What approval is required?"
    )

    source = result["sources"][0]

    assert source["file_name"] == "policy.txt"
    assert source["chunk_id"] == "policy-chunk-001"
    assert source["source_number"] == 1


def test_model_abstention():
    generator = make_generator(
        "NOT_FOUND"
    )

    result = generator.answer(
        "What is the furniture allowance?"
    )

    assert result["status"] == "insufficient_evidence"
    assert result["answer"] == FALLBACK_ANSWER
    assert result["sources"] == []


def test_answer_without_citation_rejected():
    generator = make_generator(
        "Employees can work abroad."
    )

    result = generator.answer(
        "Can employees work abroad?"
    )

    assert result["status"] == "insufficient_evidence"


def test_invented_source_rejected():
    generator = make_generator(
        "Employees can work abroad. [Source 99]"
    )

    result = generator.answer(
        "Can employees work abroad?"
    )

    assert result["status"] == "insufficient_evidence"


def test_no_documents_skips_llm():
    generator = make_generator(
        "This should never be returned.",
        results=[],
    )

    result = generator.answer(
        "What is the policy?"
    )

    assert result["status"] == "insufficient_evidence"
    assert result["retrieved_chunks"] == 0
    assert result["sources"] == []


def test_empty_question_rejected():
    generator = make_generator(
        "Answer [Source 1]"
    )

    with pytest.raises(
        ValueError,
        match="non-empty",
    ):
        generator.answer("  ")


def test_invalid_top_k_rejected():
    generator = make_generator(
        "Answer [Source 1]"
    )

    with pytest.raises(ValueError):
        generator.answer(
            "Policy question",
            top_k=0,
        )


def test_pdf_page_metadata_preserved():
    pdf_result = {
        **SAMPLE_RESULT,
        "file_name": "policy.pdf",
        "file_type": "pdf",
        "page_number": 3,
    }

    generator = make_generator(
        "Written approval is required. [Source 1]",
        results=[pdf_result],
    )

    result = generator.answer(
        "What approval is required?"
    )

    assert result["sources"][0]["page_number"] == 3