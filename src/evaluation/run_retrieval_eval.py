import csv
import json
import time

from pathlib import Path
from statistics import mean

from src.evaluation.metrics import (
    find_relevant_chunk_ids,
    recall_at_k,
    reciprocal_rank_at_k,
)
from src.retrieval.langchain_retriever import (
    SemanticRetriever,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

QUESTIONS_FILE = (
    PROJECT_ROOT
    / "data"
    / "evaluation"
    / "questions.json"
)

CHUNKS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chunks.json"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "retrieval_evaluation.csv"
)


def main():
    questions = json.loads(
        QUESTIONS_FILE.read_text(
            encoding="utf-8"
        )
    )

    chunks = json.loads(
        CHUNKS_FILE.read_text(
            encoding="utf-8"
        )
    )

    retriever = SemanticRetriever.from_local()

    # Ensure the saved FAISS index corresponds
    # to the chunks being evaluated.
    chunk_ids = {
        chunk["chunk_id"]
        for chunk in chunks
    }

    index_chunk_ids = {
        item["chunk_id"]
        for item in retriever.store.metadata
    }

    if chunk_ids != index_chunk_ids:
        raise ValueError(
            "FAISS index does not match chunks.json. "
            "Rebuild the vector index before evaluation."
        )

    results = []

    for item in questions:
        if not item["answerable"]:
            continue

        gold_ids = find_relevant_chunk_ids(
            chunks=chunks,
            evidence_phrase=item["evidence_phrase"],
        )

        if not gold_ids:
            raise ValueError(
                f"No matching evidence found for "
                f"{item['id']}. Check the evidence "
                f"phrase and chunks.json."
            )

        start_time = time.perf_counter()

        documents = retriever.retrieve(
            question=item["question"],
            top_k=3,
        )

        latency_ms = (
            time.perf_counter() - start_time
        ) * 1000

        retrieved_ids = [
            document.metadata["chunk_id"]
            for document in documents
        ]

        recall_1 = recall_at_k(
            retrieved_ids,
            gold_ids,
            k=1,
        )

        recall_3 = recall_at_k(
            retrieved_ids,
            gold_ids,
            k=3,
        )

        reciprocal_rank = reciprocal_rank_at_k(
            retrieved_ids,
            gold_ids,
            k=3,
        )

        results.append(
            {
                "question_id": item["id"],
                "question": item["question"],
                "gold_chunk_ids": "|".join(gold_ids),
                "retrieved_chunk_ids": "|".join(
                    retrieved_ids
                ),
                "recall_at_1": recall_1,
                "recall_at_3": recall_3,
                "reciprocal_rank_at_3": reciprocal_rank,
                "latency_ms": round(latency_ms, 2),
            }
        )

        print(
            f"{item['id']}: "
            f"Recall@1={recall_1:.2f}, "
            f"Recall@3={recall_3:.2f}, "
            f"RR@3={reciprocal_rank:.2f}"
        )

    if not results:
        raise ValueError(
            "No answerable questions found"
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(results[0].keys()),
        )

        writer.writeheader()
        writer.writerows(results)

    mean_recall_1 = mean(
        row["recall_at_1"]
        for row in results
    )

    mean_recall_3 = mean(
        row["recall_at_3"]
        for row in results
    )

    mrr_3 = mean(
        row["reciprocal_rank_at_3"]
        for row in results
    )

    mean_latency = mean(
        row["latency_ms"]
        for row in results
    )

    print("\n=== RETRIEVAL EVALUATION SUMMARY ===")

    print(
        "Questions evaluated:",
        len(results),
    )

    print(
        f"Mean Recall@1: {mean_recall_1:.4f}"
    )

    print(
        f"Mean Recall@3: {mean_recall_3:.4f}"
    )

    print(
        f"MRR@3: {mrr_3:.4f}"
    )

    print(
        f"Mean retrieval latency: "
        f"{mean_latency:.2f} ms"
    )

    print(
        f"\nResults saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()