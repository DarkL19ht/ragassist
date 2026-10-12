# RAGAssist — Evaluation Summary

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
| Total answer evaluation questions | 12 |
| Answerable questions | 9 |
| Unanswerable questions | 3 |
| Retrieval evaluation questions | 9 |

Answerable questions evaluate evidence retrieval and
factual answer generation.

Unanswerable questions assess whether the application
appropriately abstains when the source documents do
not contain sufficient information.

## Retrieval Performance

| Metric | Result |
|---|---:|
| Mean Recall@1 | 0.5556 |
| Mean Recall@3 | 1.0000 |
| MRR@3 | 0.8148 |
| Mean retrieval latency | 211.41 ms |

Recall@K measures the fraction of labelled relevant
chunks recovered within the first K retrieved results.

MRR@3 measures how highly the first relevant passage
is ranked within the first three results.

Retrieval latency includes query embedding and vector
search but excludes LLM generation.

## Answer Quality

| Metric | Result |
|---|---:|
| Correct answers to answerable questions | 66.7% |
| Partially correct answerable responses | 0 |
| Overall correctness including abstentions | 75.0% |
| Supported citations among answered responses | 100.0% |
| Correct abstention rate | 100.0% |
| Incorrect abstentions | 3 |
| Responses to unanswerable questions | 0 |

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
| Mean end-to-end latency | 0.496 seconds |
| Median end-to-end latency | 0.474 seconds |

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
