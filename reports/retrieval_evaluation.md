# RAGAssist — Retrieval Evaluation Report

## Objective

Evaluate whether RAGAssist retrieves the correct supporting document passages for natural-language questions.

## Evaluation Dataset

- Document: Fictional remote-working policy
- Total questions: 12
- Answerable questions used for retrieval evaluation: 9
- Unanswerable questions reserved for answer-quality evaluation: 3

## Retrieval Configuration

- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- Vector index: FAISS `IndexFlatIP`
- Similarity: Inner product on normalized embeddings
- Chunk size: 500 characters
- Chunk overlap: 100 characters
- Retrieval limit: Top 3 chunks

## Results

| Metric | Actual result |
|---|---|
| Mean Recall@1 | 0.5556 |
| Mean Recall@3 | 1.0000 |
| MRR@3 | 0.8148 |
| Mean retrieval latency | 211.41 ms |


## Error Analysis

The initial retrieval evaluation covered nine answerable questions using the fictional remote-working policy.

**All nine questions achieved Recall@3 = 1.00**, meaning that every chunk labelled relevant through evidence-phrase matching was retrieved within the top three results. Therefore, no complete Top-3 retrieval failures were observed in this evaluation.

However, ranking performance varied across questions:

- **Q01, Q02, Q05 and Q09:** Achieved Recall@1 = 1.00 and reciprocal rank = 1.00. All labelled relevant evidence was present in the highest-ranked result.
- **Q03 and Q04:** Achieved Recall@1 = 0.50 and Recall@3 = 1.00, with reciprocal rank = 1.00. The highest-ranked result contained relevant evidence, but only half of the labelled relevant chunks appeared at rank 1. The remaining relevant evidence was recovered within the top three results. This illustrates the distinction between retrieving the first relevant passage and recovering all labelled relevant passages.
- **Q06 (remote-working eligibility):** Achieved Recall@1 = 0.00 and reciprocal rank = 0.50. The first relevant chunk appeared at rank 2, indicating that a different chunk was ranked above the expected eligibility evidence.
- **Q07 (line-manager approval):** Achieved Recall@1 = 0.00 and reciprocal rank = 0.50. The relevant approval evidence first appeared at rank 2.
- **Q08 (six-month policy review):** Achieved Recall@1 = 0.00 and reciprocal rank ≈ 0.33. The relevant evidence first appeared at rank 3, making this the weakest first-relevant-result ranking in the evaluation.

These results indicate **ranking weaknesses rather than missing-evidence failures within Top 3**.

Potential contributing factors include the short document collection, character-based chunk boundaries, overlapping chunks that share similar content, and semantic similarity between policy sections. These are hypotheses rather than confirmed causes; the actual higher-ranked passages should be inspected before attributing a failure to a specific factor.

Future experiments should examine the retrieved text for Q06–Q08, compare alternative chunk sizes and overlaps, and evaluate whether improved chunk boundaries or reranking move the relevant evidence higher.

## Observations

1. **Strong Top-3 evidence coverage:** Mean Recall@3 reached 1.0000 across all nine answerable questions. Under the current evidence-phrase-based relevance labels, the retriever recovered all labelled supporting chunks within three results.

2. **Moderate-to-strong first-result ranking:** Mean Recall@1 was 0.5556, while MRR@3 was 0.8148. The relatively high MRR indicates that relevant evidence generally appeared early, although the highest-ranked result was not consistently the relevant one.

3. **Ranking is uneven across policy topics:** Questions about working abroad, equipment and personal-device restrictions performed well at rank 1. Questions about eligibility, line-manager approval and policy-review frequency required deeper retrieval.

4. **Top-3 retrieval is justified for the current baseline:** Every evaluated answerable question recovered its labelled evidence within the three retrieved chunks. Keeping `top_k=3` is therefore a reasonable initial configuration, although larger document collections may behave differently.

5. **Retrieval latency was low in this test environment:** Mean retrieval latency was 211.41 ms per question. This measures the retrieval operation, including query embedding and FAISS search, but excludes hosted LLM generation and network latency. It should not be interpreted as end-to-end answer response time.

6. **The evaluation dataset is limited:** Results come from nine answerable questions about one fictional policy. The dataset is too small and homogeneous to establish general performance on larger, more complex document collections.

7. **Ground-truth labelling is approximate:** Relevant chunks were identified through exact evidence-phrase matching. This approach can miss semantically relevant passages and may identify multiple overlapping chunks as relevant, affecting Recall@1 and Recall@3.

8. **Retrieval quality and answer quality must be evaluated separately:** Recovering source evidence does not guarantee that the LLM will answer correctly or cite the relevant passage. The next evaluation stage will measure factual correctness, citation support, abstention behaviour and end-to-end latency.

**Overall conclusion:** RAGAssist demonstrates reliable Top-3 evidence retrieval on the initial test set, with opportunities to improve rank-1 precision and ranking consistency. The next priority is to establish whether this retrieval performance translates into correct, well-supported LLM-generated answers.


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




## Limitations

- Only one fictional document is evaluated.
- The evaluation set is small.
- Relevant chunks are labelled through evidence-phrase matching.
- Exact phrase matching may omit semantically relevant chunks.
- Chunk boundaries can separate related text.
- Retrieval scores do not directly measure generated-answer correctness.

