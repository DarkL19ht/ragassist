# The embedding model wrapper
# Putting all embedding logic in one reusable module.

import numpy as np
from sentence_transformers import SentenceTransformer


DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class TextEmbedder:
    """
    Generate normalized sentence embeddings.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
    ):
        self.model_name = model_name

        self.model = SentenceTransformer(
            model_name
        )

    def encode(
        self,
        texts: list[str],
    ) -> np.ndarray:
        """
        Convert texts into normalized float32 vectors.
        """

        if not texts:
            raise ValueError(
                "At least one text is required."
            )

        if any(
            not isinstance(text, str)
            or not text.strip()
            for text in texts
        ):
            raise ValueError(
                "All texts must be non-empty strings."
            )

        vectors = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return np.asarray(
            vectors,
            dtype=np.float32,
        )