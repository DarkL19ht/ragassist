# The LangChain Retriever

# Dependency injection here 'making SemanticRetriever accept an embedder and store in its constructor'
# It allows testing of retrieval logic using fake embedding and search components rather than downloading a model or building a real FAISS index for every test


from pathlib import Path

from langchain_core.documents import Document

from src.embeddings.embedder import TextEmbedder
from src.retrieval.vector_store import FAISSVectorStore


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_INDEX_DIRECTORY = (
    PROJECT_ROOT / "vector_store"
)


def result_to_document(result: dict) -> Document:
    """
    Convert a FAISS search result into a LangChain Document.
    """

    text = result["text"]

    metadata = {
        key: value
        for key, value in result.items()
        if key != "text"
    }

    return Document(
        page_content=text,
        metadata=metadata,
        id=result.get("chunk_id"),
    )


class SemanticRetriever:
    """
    Retrieve document chunks using an existing
    embedding model and FAISS vector store.
    """

    def __init__(
        self,
        embedder,
        store,
    ):
        self.embedder = embedder
        self.store = store

    @classmethod
    def from_local(
        cls,
        index_directory=DEFAULT_INDEX_DIRECTORY,
    ):
        """
        Load a saved FAISS index and embedding model.
        """

        store = FAISSVectorStore()
        store.load(index_directory)

        embedder = TextEmbedder()

        return cls(
            embedder=embedder,
            store=store,
        )

    def retrieve(
        self,
        question: str,
        top_k: int = 3,
    ) -> list[Document]:
        """
        Retrieve the most relevant document chunks.
        """

        if (
            not isinstance(question, str)
            or not question.strip()
        ):
            raise ValueError(
                "Question must be a non-empty string."
            )

        if (
            not isinstance(top_k, int)
            or isinstance(top_k, bool)
            or top_k <= 0
        ):
            raise ValueError(
                "top_k must be a positive integer."
            )

        query_vector = self.embedder.encode(
            [question.strip()]
        )

        results = self.store.search(
            query_vector=query_vector,
            top_k=top_k,
        )

        return [
            result_to_document(result)
            for result in results
        ]