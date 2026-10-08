# The indexing script

import json
from pathlib import Path

from src.embeddings.embedder import TextEmbedder
from src.retrieval.vector_store import FAISSVectorStore


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CHUNKS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chunks.json"
)

INDEX_DIRECTORY = (
    PROJECT_ROOT
    / "vector_store"
)


def main():
    if not CHUNKS_FILE.is_file():
        raise FileNotFoundError(
            "chunks.json not found. "
            "Run ingestion and chunking first."
        )

    chunks = json.loads(
        CHUNKS_FILE.read_text(
            encoding="utf-8"
        )
    )

    if not chunks:
        raise ValueError(
            "No chunks found to index."
        )

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    print(
        f"Generating embeddings for {len(texts)} chunks..."
    )

    embedder = TextEmbedder()

    vectors = embedder.encode(texts)

    store = FAISSVectorStore()

    store.build(
        vectors=vectors,
        metadata=chunks,
    )

    store.save(INDEX_DIRECTORY)

    print(
        f"FAISS vectors: {store.index.ntotal}"
    )

    print(
        f"Embedding dimensions: {store.index.d}"
    )

    print(
        f"Index saved to: {INDEX_DIRECTORY}"
    )


if __name__ == "__main__":
    main()