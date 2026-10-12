import pytest

from src.evaluation.metrics import (
    recall_at_k,
    reciprocal_rank_at_k,
    find_relevant_chunk_ids,
)


def test_recall_at_one_success():
    result = recall_at_k(
        retrieved_ids=["a", "b", "c"],
        relevant_ids=["a"],
        k=1,
    )

    assert result == 1.0


def test_recall_at_one_failure():
    result = recall_at_k(
        retrieved_ids=["a", "b", "c"],
        relevant_ids=["b"],
        k=1,
    )

    assert result == 0.0


def test_recall_at_three():
    result = recall_at_k(
        retrieved_ids=["a", "b", "c"],
        relevant_ids=["c"],
        k=3,
    )

    assert result == 1.0


def test_partial_recall():
    result = recall_at_k(
        retrieved_ids=["a", "x", "y"],
        relevant_ids=["a", "b"],
        k=3,
    )

    assert result == 0.5


def test_reciprocal_rank_first():
    result = reciprocal_rank_at_k(
        retrieved_ids=["a", "b", "c"],
        relevant_ids=["a"],
        k=3,
    )

    assert result == 1.0


def test_reciprocal_rank_second():
    result = reciprocal_rank_at_k(
        retrieved_ids=["a", "b", "c"],
        relevant_ids=["b"],
        k=3,
    )

    assert result == 0.5


def test_reciprocal_rank_missing():
    result = reciprocal_rank_at_k(
        retrieved_ids=["a", "b", "c"],
        relevant_ids=["z"],
        k=3,
    )

    assert result == 0.0


def test_empty_relevant_ids_rejected():
    with pytest.raises(ValueError):
        recall_at_k(
            retrieved_ids=["a"],
            relevant_ids=[],
            k=3,
        )


def test_invalid_k_rejected():
    with pytest.raises(ValueError):
        reciprocal_rank_at_k(
            retrieved_ids=["a"],
            relevant_ids=["a"],
            k=0,
        )


def test_find_relevant_chunk_ids():
    chunks = [
        {
            "chunk_id": "chunk-1",
            "file_name": "remote_work_policy.txt",
            "text": "Written approval from HR is required.",
        },
        {
            "chunk_id": "chunk-2",
            "file_name": "remote_work_policy.txt",
            "text": "The company provides laptops.",
        },
    ]

    matches = find_relevant_chunk_ids(
        chunks,
        evidence_phrase="written approval from HR",
    )

    assert matches == ["chunk-1"]