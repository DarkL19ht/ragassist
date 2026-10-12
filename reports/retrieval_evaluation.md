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





## Limitations

- Only one fictional document is evaluated.
- The evaluation set is small.
- Relevant chunks are labelled through evidence-phrase matching.
- Exact phrase matching may omit semantically relevant chunks.
- Chunk boundaries can separate related text.
- Retrieval scores do not directly measure generated-answer correctness.

## Next Steps

Evaluate generated answers, citation correctness, abstention behaviour and end-to-end latency.