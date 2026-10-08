# Vector-store tests

import numpy as np
import pytest

from src.retrieval.vector_store import FAISSVectorStore


def sample_data():
    vectors = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float32,
    )

    metadata = [
        {"chunk_id": "chunk-1", "text": "Cards"},
        {"chunk_id": "chunk-2", "text": "Loans"},
        {"chunk_id": "chunk-3", "text": "Payments"},
    ]

    return vectors, metadata


def test_build_index():
    vectors, metadata = sample_data()

    store = FAISSVectorStore()
    store.build(vectors, metadata)

    assert store.index.ntotal == 3
    assert store.index.d == 3


def test_search_returns_best_match():
    vectors, metadata = sample_data()

    store = FAISSVectorStore()
    store.build(vectors, metadata)

    results = store.search(
        np.array([0.0, 1.0, 0.0], dtype=np.float32),
        top_k=1,
    )

    assert len(results) == 1
    assert results[0]["chunk_id"] == "chunk-2"


def test_top_k_larger_than_index():
    vectors, metadata = sample_data()

    store = FAISSVectorStore()
    store.build(vectors, metadata)

    results = store.search(
        np.array([1.0, 0.0, 0.0], dtype=np.float32),
        top_k=10,
    )

    assert len(results) == 3


def test_empty_index_rejected():
    store = FAISSVectorStore()

    with pytest.raises(ValueError):
        store.build(
            np.empty((0, 3), dtype=np.float32),
            [],
        )


def test_metadata_count_mismatch():
    vectors, _ = sample_data()

    store = FAISSVectorStore()

    with pytest.raises(ValueError):
        store.build(
            vectors,
            [{"chunk_id": "only-one"}],
        )


def test_search_before_build():
    store = FAISSVectorStore()

    with pytest.raises(RuntimeError):
        store.search(
            np.array([1.0, 0.0, 0.0], dtype=np.float32)
        )


def test_invalid_top_k():
    vectors, metadata = sample_data()

    store = FAISSVectorStore()
    store.build(vectors, metadata)

    with pytest.raises(ValueError):
        store.search(
            np.array([1.0, 0.0, 0.0], dtype=np.float32),
            top_k=0,
        )


def test_save_and_load(tmp_path):
    vectors, metadata = sample_data()

    store = FAISSVectorStore()
    store.build(vectors, metadata)
    store.save(tmp_path)

    restored = FAISSVectorStore()
    restored.load(tmp_path)

    assert restored.index.ntotal == 3
    assert restored.metadata == metadata

    results = restored.search(
        np.array([1.0, 0.0, 0.0], dtype=np.float32),
        top_k=1,
    )

    assert results[0]["chunk_id"] == "chunk-1"