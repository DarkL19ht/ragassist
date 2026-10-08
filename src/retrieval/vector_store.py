# The vector-store 

# build() creates a FAISS index from document vectors.
# search() finds the most similar vectors and returns the associated document metadata.
# save() stores the index and metadata on disk.
# load() restores the index without recalculating document embeddings.

import json
from pathlib import Path

import faiss
import numpy as np


class FAISSVectorStore:
    """
    Store and search normalized document embeddings.
    """

    def __init__(self):
        self.index = None
        self.metadata = []

    def build(
        self,
        vectors: np.ndarray,
        metadata: list[dict],
    ):
        vectors = np.asarray(
            vectors,
            dtype=np.float32,
        )

        if vectors.ndim != 2:
            raise ValueError(
                "Vectors must be a 2D array."
            )

        if len(vectors) == 0:
            raise ValueError(
                "Cannot build an empty FAISS index."
            )

        if len(vectors) != len(metadata):
            raise ValueError(
                "Vector count and metadata count must match."
            )

        dimension = vectors.shape[1]

        self.index = faiss.IndexFlatIP(
            dimension
        )

        self.index.add(
            np.ascontiguousarray(vectors)
        )

        self.metadata = metadata

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 3,
    ) -> list[dict]:
        if self.index is None:
            raise RuntimeError(
                "FAISS index has not been built."
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )

        query_vector = np.asarray(
            query_vector,
            dtype=np.float32,
        )

        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(
                1,
                -1,
            )

        if (
            query_vector.ndim != 2
            or query_vector.shape[0] != 1
        ):
            raise ValueError(
                "Expected one query vector."
            )

        if (
            query_vector.shape[1]
            != self.index.d
        ):
            raise ValueError(
                "Query vector dimension does not match the index."
            )

        actual_k = min(
            top_k,
            self.index.ntotal,
        )

        scores, indices = self.index.search(
            np.ascontiguousarray(query_vector),
            actual_k,
        )

        results = []

        for score, index in zip(
            scores[0],
            indices[0],
        ):
            if index < 0:
                continue

            result = dict(
                self.metadata[int(index)]
            )

            result["score"] = float(score)

            results.append(result)

        return results

    def save(
        self,
        directory: str | Path,
    ):
        if self.index is None:
            raise RuntimeError(
                "Cannot save an unbuilt index."
            )

        directory = Path(directory)

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        faiss.write_index(
            self.index,
            str(directory / "index.faiss"),
        )

        (directory / "metadata.json").write_text(
            json.dumps(
                self.metadata,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def load(
        self,
        directory: str | Path,
    ):
        directory = Path(directory)

        self.index = faiss.read_index(
            str(directory / "index.faiss")
        )

        self.metadata = json.loads(
            (directory / "metadata.json").read_text(
                encoding="utf-8"
            )
        )

        if self.index.ntotal != len(self.metadata):
            raise ValueError(
                "Saved index and metadata are inconsistent."
            )