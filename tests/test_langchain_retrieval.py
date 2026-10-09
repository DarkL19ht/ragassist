import numpy as np
import pytest

from langchain_core.documents import Document

from src.retrieval.context_formatter import (
    format_documents,
)
from src.retrieval.langchain_pipeline import (
    build_retrieval_chain,
)
from src.retrieval.langchain_retriever import (
    SemanticRetriever,
    result_to_document,
)


SAMPLE_RESULT = {
    "chunk_id": "chunk-001",
    "text": (
        "Employees must obtain written "
        "approval from HR."
    ),
    "source": "data/sample_docs/policy.pdf",
    "file_name": "policy.pdf",
    "file_type": "pdf",
    "page_number": 4,
    "chunk_index": 0,
    "start_char": 0,
    "end_char": 47,
    "score": 0.92,
}


class FakeEmbedder:
    def __init__(self):
        self.last_texts = None

    def encode(self, texts):
        self.last_texts = texts

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

        self.last_top_k = None

    def search(
        self,
        query_vector,
        top_k=3,
    ):
        self.last_top_k = top_k

        return self.results[:top_k]


def make_retriever(results=None):
    embedder = FakeEmbedder()

    store = FakeStore(results)

    return SemanticRetriever(
        embedder=embedder,
        store=store,
    )


def test_result_converts_to_langchain_document():
    document = result_to_document(
        SAMPLE_RESULT
    )

    assert isinstance(
        document,
        Document,
    )

    assert "approval from HR" in (
        document.page_content
    )

    assert document.id == "chunk-001"


def test_retriever_preserves_metadata():
    retriever = make_retriever()

    documents = retriever.retrieve(
        "Can I work abroad?"
    )

    assert len(documents) == 1

    metadata = documents[0].metadata

    assert metadata["file_name"] == "policy.pdf"
    assert metadata["page_number"] == 4
    assert metadata["chunk_id"] == "chunk-001"
    assert metadata["score"] == 0.92


def test_pdf_context_includes_page():
    document = result_to_document(
        SAMPLE_RESULT
    )

    context = format_documents(
        [document]
    )

    assert "[Source 1]" in context
    assert "policy.pdf" in context
    assert "Page 4" in context
    assert "chunk-001" in context


def test_txt_context_has_no_page():
    result = {
        **SAMPLE_RESULT,
        "file_name": "policy.txt",
        "file_type": "txt",
        "page_number": None,
    }

    context = format_documents(
        [result_to_document(result)]
    )

    assert "policy.txt" in context
    assert "Page" not in context


def test_retrieval_chain_returns_context():
    retriever = make_retriever()

    chain = build_retrieval_chain(
        retriever
    )

    output = chain.invoke(
        {
            "question": "Can I work abroad?",
            "top_k": 3,
        }
    )

    assert (
        output["question"]
        == "Can I work abroad?"
    )

    assert len(output["documents"]) == 1

    assert "approval from HR" in (
        output["context"]
    )


def test_retrieval_chain_preserves_top_k():
    retriever = make_retriever()

    chain = build_retrieval_chain(
        retriever
    )

    output = chain.invoke(
        {
            "question": "Remote work policy",
            "top_k": 1,
        }
    )

    assert output["top_k"] == 1
    assert retriever.store.last_top_k == 1


def test_empty_question_rejected():
    retriever = make_retriever()

    with pytest.raises(
        ValueError,
        match="non-empty",
    ):
        retriever.retrieve("   ")


def test_invalid_top_k_rejected():
    retriever = make_retriever()

    with pytest.raises(
        ValueError,
        match="positive integer",
    ):
        retriever.retrieve(
            "Policy question",
            top_k=0,
        )


def test_no_results_produce_safe_context():
    retriever = make_retriever(
        results=[]
    )

    chain = build_retrieval_chain(
        retriever
    )

    output = chain.invoke(
        {
            "question": "Unknown policy",
            "top_k": 3,
        }
    )

    assert output["documents"] == []

    assert (
        "No relevant document passages"
        in output["context"]
    )


def test_query_is_embedded_once():
    retriever = make_retriever()

    retriever.retrieve(
        "  Can employees work abroad?  "
    )

    assert retriever.embedder.last_texts == [
        "Can employees work abroad?"
    ]