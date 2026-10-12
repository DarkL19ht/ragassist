import csv
from pathlib import Path
from statistics import mean, median


PROJECT_ROOT = Path(__file__).resolve().parents[2]

ANSWER_AUDIT_FILE = (
    PROJECT_ROOT / "reports" / "answer_audit.csv"
)

RETRIEVAL_RESULTS_FILE = (
    PROJECT_ROOT / "reports" / "retrieval_evaluation.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT / "reports" / "evaluation_summary.md"
)


def load_csv(file_path: Path) -> list[dict]:
    if not file_path.is_file():
        raise FileNotFoundError(
            f"Required evaluation file not found: {file_path}"
        )

    with file_path.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as file:
        return list(csv.DictReader(file))


def percentage(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "N/A"

    return f"{numerator / denominator:.1%}"


def validate_answer_reviews(rows: list[dict]) -> None:
    if not rows:
        raise ValueError("Answer evaluation results are empty.")

    ids = [row["question_id"] for row in rows]

    if len(ids) != len(set(ids)):
        raise ValueError(
            "Duplicate question IDs found in answer audit."
        )

    for row in rows:
        question_id = row["question_id"]

        correctness = row["answer_correct"].strip().lower()

        if correctness not in {"yes", "no", "partial"}:
            raise ValueError(
                f"{question_id}: answer correctness "
                "has not been reviewed."
            )

        if row["status"] == "answered":
            citation_review = (
                row["citation_supported"].strip().lower()
            )

            if citation_review not in {"yes", "no"}:
                raise ValueError(
                    f"{question_id}: citation support "
                    "has not been reviewed."
                )


def main():
    answers = load_csv(ANSWER_AUDIT_FILE)
    retrieval_results = load_csv(RETRIEVAL_RESULTS_FILE)

    validate_answer_reviews(answers)

    if not retrieval_results:
        raise ValueError(
            "Retrieval evaluation results are empty."
        )

    answerable = [
        row for row in answers
        if row["answerable"].strip().lower() == "true"
    ]

    unanswerable = [
        row for row in answers
        if row["answerable"].strip().lower() == "false"
    ]

    correct_answerable = sum(
        row["answer_correct"].strip().lower() == "yes"
        for row in answerable
    )

    partial_answerable = sum(
        row["answer_correct"].strip().lower() == "partial"
        for row in answerable
    )

    overall_correct = sum(
        row["answer_correct"].strip().lower() == "yes"
        for row in answers
    )

    correct_abstentions = sum(
        row["status"] == "insufficient_evidence"
        and row["answer_correct"].strip().lower() == "yes"
        for row in unanswerable
    )

    incorrect_abstentions = sum(
        row["status"] == "insufficient_evidence"
        for row in answerable
    )

    answered_results = [
        row for row in answers
        if row["status"] == "answered"
    ]

    supported_citations = sum(
        row["citation_supported"].strip().lower() == "yes"
        for row in answered_results
    )

    unsupported_responses = sum(
        row["status"] == "answered"
        for row in unanswerable
    )

    recall_at_1 = mean(
        float(row["recall_at_1"])
        for row in retrieval_results
    )

    recall_at_3 = mean(
        float(row["recall_at_3"])
        for row in retrieval_results
    )

    mrr_at_3 = mean(
        float(row["reciprocal_rank_at_3"])
        for row in retrieval_results
    )

    retrieval_latency = mean(
        float(row["latency_ms"])
        for row in retrieval_results
    )

    answer_latencies = [
        float(row["latency_seconds"])
        for row in answers
    ]

    report = f"""# RAGAssist — Evaluation Summary

## Executive Summary

This report evaluates the retrieval accuracy, answer quality,
citation reliability, abstention behaviour, and response
latency of RAGAssist.

The evaluation examines the ability of the system to retrieve
relevant document passages and generate answers grounded
in supporting evidence.

Results are based on a curated evaluation dataset using
a fictional remote-working policy.

## System Configuration

| Component | Configuration |
|---|---|
| Embedding model | all-MiniLM-L6-v2 |
| Vector database | FAISS IndexFlatIP |
| Retrieval framework | LangChain |
| Language model | openai/gpt-oss-20b |
| LLM provider | GroqCloud |
| Chunk size | 500 characters |
| Chunk overlap | 100 characters |
| Retrieved passages | Top 3 |
| Similarity measure | Cosine similarity |

## Evaluation Dataset

| Category | Count |
|---|---:|
| Total answer evaluation questions | {len(answers)} |
| Answerable questions | {len(answerable)} |
| Unanswerable questions | {len(unanswerable)} |
| Retrieval evaluation questions | {len(retrieval_results)} |

Answerable questions evaluate evidence retrieval and
factual answer generation.

Unanswerable questions assess whether the application
appropriately abstains when the source documents do
not contain sufficient information.

## Retrieval Performance

| Metric | Result |
|---|---:|
| Mean Recall@1 | {recall_at_1:.4f} |
| Mean Recall@3 | {recall_at_3:.4f} |
| MRR@3 | {mrr_at_3:.4f} |
| Mean retrieval latency | {retrieval_latency:.2f} ms |

Recall@K measures the fraction of labelled relevant
chunks recovered within the first K retrieved results.

MRR@3 measures how highly the first relevant passage
is ranked within the first three results.

Retrieval latency includes query embedding and vector
search but excludes LLM generation.

## Answer Quality

| Metric | Result |
|---|---:|
| Correct answers to answerable questions | {percentage(correct_answerable, len(answerable))} |
| Partially correct answerable responses | {partial_answerable} |
| Overall correctness including abstentions | {percentage(overall_correct, len(answers))} |
| Supported citations among answered responses | {percentage(supported_citations, len(answered_results))} |
| Correct abstention rate | {percentage(correct_abstentions, len(unanswerable))} |
| Incorrect abstentions | {incorrect_abstentions} |
| Responses to unanswerable questions | {unsupported_responses} |

Answer correctness and citation support were assessed
through manual review against the original source document.

A citation is considered supported only when the cited
passage provides evidence for the material claims in
the generated answer.

Responses to unanswerable questions are flagged for
review; they are not automatically classified as
hallucinations without examining their content.

## Response Latency

| Metric | Result |
|---|---:|
| Mean end-to-end latency | {mean(answer_latencies):.3f} seconds |
| Median end-to-end latency | {median(answer_latencies):.3f} seconds |

End-to-end latency includes retrieval, LLM API processing,
and answer generation.

These measurements reflect the development environment
and network conditions during evaluation.

## Key Findings

- Retrieval performance is measured independently of
  generated-answer correctness.
- Top-K retrieval metrics identify whether supporting
  passages are recovered and how effectively they rank.
- Manual answer evaluation identifies unsupported claims,
  unnecessary abstentions, and citation-grounding issues.
- End-to-end latency includes external LLM service
  overhead and is therefore higher than retrieval-only
  latency.
- Results provide an initial engineering baseline rather
  than a production reliability guarantee.

## Limitations

1. The evaluation uses a single fictional document.
2. The question set is relatively small.
3. Relevant chunks are labelled using evidence-phrase
   matching, which may omit semantically relevant text.
4. Answer correctness and citation support rely on
   manual assessment.
5. LLM responses may vary between repeated executions.
6. Citation-format validation does not independently
   verify factual support.
7. Runtime performance depends on hardware, network
   conditions, and external API availability.

## Recommended Improvements

1. Expand evaluation across multiple documents and
   document types.
2. Compare alternative chunk sizes and overlap settings.
3. Investigate queries where relevant evidence appears
   below the first retrieved result.
4. Evaluate retrieval reranking strategies.
5. Improve citation verification and unsupported-answer
   detection.
6. Repeat the evaluation to measure consistency across
   multiple LLM responses.
7. Monitor end-to-end latency and API reliability as
   the document collection grows.

## Conclusion

RAGAssist combines semantic retrieval, source-aware
context construction, and LLM-based answer generation
in a measurable document question-answering workflow.

The evaluation establishes a reproducible baseline
for retrieval quality, factual correctness, citation
support, abstention behaviour, and response latency.

The findings provide a foundation for further
experimentation and system optimisation.
"""

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        report,
        encoding="utf-8",
    )

    print(report)
    print(f"\nReport saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()