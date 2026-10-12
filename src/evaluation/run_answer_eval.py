# answer-evaluation runner

import argparse
import csv
import json
import time
from pathlib import Path

from dotenv import load_dotenv

from src.generation.answer_generator import GroundedAnswerGenerator
from src.generation.llm_provider import create_llm
from src.retrieval.langchain_retriever import SemanticRetriever


PROJECT_ROOT = Path(__file__).resolve().parents[2]

QUESTIONS_FILE = PROJECT_ROOT / "data/evaluation/questions.json"
CHUNKS_FILE = PROJECT_ROOT / "data/processed/chunks.json"
OUTPUT_FILE = PROJECT_ROOT / "reports/answer_audit.csv"

FIELDS = [
    "question_id",
    "question",
    "answerable",
    "expected_answer",
    "generated_answer",
    "status",
    "source_chunk_ids",
    "cited_passages",
    "latency_seconds",
    "answer_correct",
    "citation_supported",
    "review_notes",
]


def get_completed_ids():
    if not OUTPUT_FILE.exists() or OUTPUT_FILE.stat().st_size == 0:
        return set()

    with OUTPUT_FILE.open(
        "r", newline="", encoding="utf-8"
    ) as file:
        reader = csv.DictReader(file)

        if reader.fieldnames != FIELDS:
            raise ValueError(
                "answer_audit.csv has an unexpected structure. "
                "Back it up and check its column headings."
            )

        return {
            row["question_id"]
            for row in reader
        }


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help="Evaluate the first N questions (default: 3).",
    )

    args = parser.parse_args()

    if args.limit <= 0:
        raise ValueError("--limit must be positive")

    load_dotenv(PROJECT_ROOT / ".env")

    questions = json.loads(
        QUESTIONS_FILE.read_text(encoding="utf-8")
    )

    chunks = json.loads(
        CHUNKS_FILE.read_text(encoding="utf-8")
    )

    chunks_by_id = {
        chunk["chunk_id"]: chunk
        for chunk in chunks
    }

    completed_ids = get_completed_ids()

    selected = [
        item
        for item in questions[:args.limit]
        if item["id"] not in completed_ids
    ]

    if not selected:
        print("All selected questions are already evaluated.")
        return

    retriever = SemanticRetriever.from_local()

    generator = GroundedAnswerGenerator(
        retriever=retriever,
        llm=create_llm(),
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    needs_header = (
        not OUTPUT_FILE.exists()
        or OUTPUT_FILE.stat().st_size == 0
    )

    with OUTPUT_FILE.open(
        "a", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=FIELDS,
        )

        if needs_header:
            writer.writeheader()

        for item in selected:
            print(
                f"\nEvaluating {item['id']}: "
                f"{item['question']}"
            )

            start = time.perf_counter()

            result = generator.answer(
                question=item["question"],
                top_k=3,
            )

            latency = time.perf_counter() - start

            cited_passages = []

            for source in result["sources"]:
                chunk_id = source["chunk_id"]
                chunk = chunks_by_id.get(chunk_id)

                if chunk is None:
                    cited_passages.append(
                        f"{chunk_id}: MISSING CHUNK"
                    )
                else:
                    cited_passages.append(
                        f"{chunk_id}: {chunk['text']}"
                    )

            row = {
                "question_id": item["id"],
                "question": item["question"],
                "answerable": item["answerable"],
                "expected_answer": item["expected_answer"],
                "generated_answer": result["answer"],
                "status": result["status"],
                "source_chunk_ids": "|".join(
                    source["chunk_id"]
                    for source in result["sources"]
                ),
                "cited_passages": "\n\n---\n\n".join(
                    cited_passages
                ),
                "latency_seconds": round(latency, 3),
                "answer_correct": "",
                "citation_supported": "",
                "review_notes": "",
            }

            writer.writerow(row)
            file.flush()

            print("Status:", result["status"])
            print("Latency:", round(latency, 3), "seconds")
            print("Result saved.")

    print("\nOutput:", OUTPUT_FILE)


if __name__ == "__main__":
    main()