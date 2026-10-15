# The comparison script

import csv
import json
import time
from pathlib import Path
from statistics import mean

from src.chunking.splitter import split_documents
from src.embeddings.embedder import TextEmbedder
from src.evaluation.metrics import (
    find_relevant_chunk_ids,
    recall_at_k,
    reciprocal_rank_at_k,
)
from src.ingestion.schema import DocumentRecord
from src.retrieval.vector_store import FAISSVectorStore


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DOCUMENTS_FILE = (
    PROJECT_ROOT / "data/processed/documents.json"
)

QUESTIONS_FILE = (
    PROJECT_ROOT / "data/evaluation/questions.json"
)

SUMMARY_FILE = (
    PROJECT_ROOT / "reports/retrieval_comparison.csv"
)

DETAILS_FILE = (
    PROJECT_ROOT / "reports/retrieval_comparison_details.csv"
)


CONFIGURATIONS = [
    {
        "name": "baseline",
        "chunk_size": 500,
        "chunk_overlap": 100,
    },
    {
        "name": "smaller_chunks",
        "chunk_size": 300,
        "chunk_overlap": 50,
    },
    {
        "name": "larger_chunks",
        "chunk_size": 800,
        "chunk_overlap": 150,
    },
]


def load_json(path):
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def evaluate_configuration(
    config,
    documents,
    questions,
    embedder,
):
    chunks = split_documents(
        documents,
        chunk_size=config["chunk_size"],
        chunk_overlap=config["chunk_overlap"],
    )

    if not chunks:
        raise ValueError(
            f"No chunks generated for {config['name']}"
        )

    chunk_metadata = [
        chunk.to_dict()
        for chunk in chunks
    ]

    # Create a separate in-memory FAISS index.
    # This does not overwrite the existing index.
    vectors = embedder.encode(
        [chunk.text for chunk in chunks]
    )

    store = FAISSVectorStore()

    store.build(
        vectors=vectors,
        metadata=chunk_metadata,
    )

    details = []

    for item in questions:
        if not item["answerable"]:
            continue

        gold_ids = find_relevant_chunk_ids(
            chunks=chunk_metadata,
            evidence_phrase=item["evidence_phrase"],
        )

        start = time.perf_counter()

        query_vector = embedder.encode(
            [item["question"]]
        )

        results = store.search(
            query_vector=query_vector,
            top_k=3,
        )

        latency_ms = (
            time.perf_counter() - start
        ) * 1000

        retrieved_ids = [
            result["chunk_id"]
            for result in results
        ]

        # An evidence phrase can cross chunk boundaries.
        # Record this explicitly rather than pretending
        # that a missing gold label is a retrieval miss.
        evidence_available = bool(gold_ids)

        if evidence_available:
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

            rr_3 = reciprocal_rank_at_k(
                retrieved_ids,
                gold_ids,
                k=3,
            )
        else:
            recall_1 = None
            recall_3 = None
            rr_3 = None

        details.append(
            {
                "configuration": config["name"],
                "question_id": item["id"],
                "question": item["question"],
                "evidence_available": evidence_available,
                "gold_chunk_count": len(gold_ids),
                "retrieved_chunk_ids": "|".join(
                    retrieved_ids
                ),
                "recall_at_1": recall_1,
                "recall_at_3": recall_3,
                "reciprocal_rank_at_3": rr_3,
                "latency_ms": round(latency_ms, 2),
            }
        )

    valid = [
        row
        for row in details
        if row["evidence_available"]
    ]

    def metric_average(key):
        if not valid:
            return None

        return round(
            mean(row[key] for row in valid),
            4,
        )

    summary = {
        "configuration": config["name"],
        "chunk_size": config["chunk_size"],
        "chunk_overlap": config["chunk_overlap"],
        "chunk_count": len(chunks),
        "questions_evaluated": len(details),
        "questions_with_labelled_evidence": len(valid),
        "questions_without_labelled_evidence": (
            len(details) - len(valid)
        ),
        "mean_recall_at_1": metric_average("recall_at_1"),
        "mean_recall_at_3": metric_average("recall_at_3"),
        "mrr_at_3": metric_average(
            "reciprocal_rank_at_3"
        ),
        "mean_latency_ms": round(
            mean(row["latency_ms"] for row in details),
            2,
        ),
    }

    return summary, details


def save_csv(path, rows):
    if not rows:
        raise ValueError(
            f"No results available for {path.name}"
        )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(rows[0].keys()),
        )

        writer.writeheader()
        writer.writerows(rows)


def main():
    document_data = load_json(DOCUMENTS_FILE)
    question_data = load_json(QUESTIONS_FILE)

    documents = [
        DocumentRecord(**item)
        for item in document_data
    ]

    print("Loading embedding model...")
    embedder = TextEmbedder()

    summaries = []
    all_details = []

    for config in CONFIGURATIONS:
        print(
            f"\nEvaluating {config['name']} "
            f"({config['chunk_size']}/"
            f"{config['chunk_overlap']})"
        )

        summary, details = evaluate_configuration(
            config=config,
            documents=documents,
            questions=question_data,
            embedder=embedder,
        )

        summaries.append(summary)
        all_details.extend(details)

        print(
            "Chunks:",
            summary["chunk_count"],
        )

        print(
            "Evidence available for:",
            summary["questions_with_labelled_evidence"],
            "questions",
        )

        print(
            "Mean Recall@1:",
            summary["mean_recall_at_1"],
        )

        print(
            "Mean Recall@3:",
            summary["mean_recall_at_3"],
        )

        print(
            "MRR@3:",
            summary["mrr_at_3"],
        )

    save_csv(
        SUMMARY_FILE,
        summaries,
    )

    save_csv(
        DETAILS_FILE,
        all_details,
    )

    print("\nComparison complete.")
    print("Summary:", SUMMARY_FILE)
    print("Details:", DETAILS_FILE)


if __name__ == "__main__":
    main()