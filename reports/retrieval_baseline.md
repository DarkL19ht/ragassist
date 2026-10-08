# RAGAssist — Initial Retrieval Baseline

## Configuration

- Embedding model: sentence-transformers/all-MiniLM-L6-v2
- Embedding dimensions: 384
- Vector index: FAISS IndexFlatIP
- Similarity: Cosine similarity using normalized embeddings
- Chunk size: 500 characters
- Chunk overlap: 100 characters
- Top K: 3

## Manual Retrieval Checks

| Question | Relevant chunk retrieved in Top 3? | Rank | Notes |
|---|---|---|---|
| What approval is needed to work overseas? | YES | 1 | Only 1 of the top 3 chunks contained the relevant evidence |
| What are the company's core working hours? | YES | 1,2 | Two of the top 3 chunks contained the relevant evidence |
| Who supplies equipment for remote work? | YES | 1 | Only 1 of the top 3 chunks contained the relevant evidence |

## Observations

1 or more relevant evidence was found in the top 3 chunks retrieved. The second test 'What are the company's core working hours?' had 2 of its top 3 chunks both containing the relevant evidence. 

## Limitations

- Very small fictional document collection.
- Character-based chunking may split sentences.
- Manual checks are not a substitute for systematic evaluation.
- Similarity scores do not represent calibrated probabilities.