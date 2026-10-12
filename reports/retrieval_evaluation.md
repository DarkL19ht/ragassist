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



## Observations



## Limitations

- Only one fictional document is evaluated.
- The evaluation set is small.
- Relevant chunks are labelled through evidence-phrase matching.
- Exact phrase matching may omit semantically relevant chunks.
- Chunk boundaries can separate related text.
- Retrieval scores do not directly measure generated-answer correctness.

## Next Steps

Evaluate generated answers, citation correctness, abstention behaviour and end-to-end latency.