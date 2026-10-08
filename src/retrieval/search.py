# The search script

import argparse
from pathlib import Path

from src.embeddings.embedder import TextEmbedder
from src.retrieval.vector_store import FAISSVectorStore


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INDEX_DIRECTORY = (
    PROJECT_ROOT
    / "vector_store"
)


def search_documents(
    question: str,
    top_k: int = 3,
) -> list[dict]:
    if not isinstance(question, str) or not question.strip():
        raise ValueError(
            "Question must be a non-empty string."
        )

    embedder = TextEmbedder()

    store = FAISSVectorStore()
    store.load(INDEX_DIRECTORY)

    query_vector = embedder.encode(
        [question]
    )

    return store.search(
        query_vector,
        top_k=top_k,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Search indexed documents."
    )

    parser.add_argument(
        "question",
        type=str,
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
    )

    args = parser.parse_args()

    results = search_documents(
        args.question,
        top_k=args.top_k,
    )

    for rank, result in enumerate(
        results,
        start=1,
    ):
        print(f"\nResult {rank}")
        print(f"Score: {result['score']:.4f}")
        print(f"Source: {result['file_name']}")
        print(f"Page: {result['page_number']}")
        print(f"Chunk ID: {result['chunk_id']}")
        print(f"Text: {result['text'][:500]}")


if __name__ == "__main__":
    main()