def recall_at_k(
    retrieved_ids: list[str],
    relevant_ids: list[str],
    k: int,
) -> float:
    """
    Calculate Recall@K for a single query.
    """

    if k <= 0:
        raise ValueError(
            "k must be a positive integer"
        )

    relevant = set(relevant_ids)

    if not relevant:
        raise ValueError(
            "At least one relevant chunk is required"
        )

    retrieved = set(retrieved_ids[:k])

    relevant_found = relevant.intersection(
        retrieved
    )

    return len(relevant_found) / len(relevant)


def reciprocal_rank_at_k(
    retrieved_ids: list[str],
    relevant_ids: list[str],
    k: int,
) -> float:
    """
    Calculate reciprocal rank of the first
    relevant result within the top K.
    """

    if k <= 0:
        raise ValueError(
            "k must be a positive integer"
        )

    relevant = set(relevant_ids)

    if not relevant:
        raise ValueError(
            "At least one relevant chunk is required"
        )

    for rank, chunk_id in enumerate(
        retrieved_ids[:k],
        start=1,
    ):
        if chunk_id in relevant:
            return 1.0 / rank

    return 0.0


def find_relevant_chunk_ids(
    chunks: list[dict],
    evidence_phrase: str,
    file_name: str = "remote_work_policy.txt",
) -> list[str]:
    """
    Find chunks containing a labelled
    evidence phrase.
    """

    if (
        not isinstance(evidence_phrase, str)
        or not evidence_phrase.strip()
    ):
        raise ValueError(
            "Evidence phrase must be non-empty"
        )

    matches = []

    for chunk in chunks:
        if chunk["file_name"] != file_name:
            continue

        if (
            evidence_phrase.casefold()
            in chunk["text"].casefold()
        ):
            matches.append(
                chunk["chunk_id"]
            )

    return matches