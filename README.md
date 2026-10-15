# RAGAssist — Evaluated, Citation-Aware Document Question Answering

RAGAssist is an AI engineering portfolio project focused on building a reliable retrieval-augmented generation (RAG) system.

The application will allow users to upload documents, ask natural-language questions, and receive answers grounded in retrieved document passages.

## Project Objectives

- Ingest PDF and TXT documents.
- Extract and chunk text while preserving source metadata.
- Generate embeddings and build a FAISS vector index.
- Implement semantic retrieval using LangChain.
- Generate answers using an LLM with source citations.
- Evaluate retrieval using Recall@K and Mean Reciprocal Rank (MRR).
- Assess answer quality, hallucinations and unsupported responses.
- Expose the application through FastAPI.
- Build an interactive frontend and deploy the application online.

## Planned Technology Stack

Python, LangChain, FAISS, embedding models, LLM APIs or local models, FastAPI, pytest and GitHub Actions.

## Project Structure

- `data/sample_docs/` — Fictional sample documents for development and evaluation
- `src/ingestion/` — PDF and TXT document loading
- `src/chunking/` — Text splitting and metadata preservation
- `src/embeddings/` — Text embedding generation
- `src/retrieval/` — Vector search and retrieval logic
- `src/generation/` — LLM prompts and answer generation
- `src/evaluation/` — Retrieval and answer-quality evaluation
- `src/api/` — FastAPI backend
- `tests/` — Automated tests
- `docs/` — Architecture and technical documentation

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -v
```

## Document Ingestion

RAGAssist supports text extraction from UTF-8 TXT files and text-based PDF documents.

The ingestion pipeline:

- Validates supported file types.
- Extracts document text.
- Preserves source filenames, file types and PDF page numbers.
- Skips PDF pages without extractable text.
- Exports structured document records as JSON.

Run the pipeline:

```bash
python -m src.ingestion.run_ingestion
```

The extracted records are saved to `data/processed/documents.json`.

**Current limitation:** Scanned PDFs, OCR and password-protected documents are not supported.


## Text Chunking

RAGAssist uses deterministic, overlapping character-based chunking to prepare extracted documents for semantic search.

**Current configuration:**

- Chunk size: 500 characters
- Chunk overlap: 100 characters
- Stable chunk IDs generated using SHA-256
- Preserved source filenames, file types and PDF page numbers
- Character offsets for traceability

Run the pipeline:

```bash
python -m src.ingestion.run_ingestion
python -m src.chunking.run_chunking
```

The resulting chunks are stored in `data/processed/chunks.json`.

Character-based chunking is the initial baseline. Alternative chunking strategies will be evaluated in later phases.

## Semantic Search

RAGAssist uses `sentence-transformers/all-MiniLM-L6-v2` to generate 384-dimensional document embeddings.

Embeddings are normalized and indexed using FAISS `IndexFlatIP` for cosine-similarity search.

### Build the search index

```bash
python -m src.ingestion.run_ingestion
python -m src.chunking.run_chunking
python -m src.embeddings.build_index
```

### Search documents

```bash
python -m src.retrieval.search "Can employees work abroad?" --top-k 3
```

Search results include similarity scores, source filenames, page numbers, chunk IDs and retrieved text.

The initial retrieval baseline is documented in `reports/retrieval_baseline.md`.


## LangChain Retrieval Pipeline

RAGAssist uses LangChain Core to orchestrate semantic retrieval over the existing FAISS vector index.

The retrieval pipeline:

- Embeds a natural-language question using Sentence Transformers.
- Retrieves matching document chunks from FAISS.
- Converts the results into LangChain `Document` objects.
- Preserves source filenames, page numbers, chunk IDs and similarity scores.
- Produces formatted, source-labelled context for a future LLM.

### Run Retrieval

First, build the index if necessary:

```bash
python -m src.ingestion.run_ingestion
python -m src.chunking.run_chunking
python -m src.embeddings.build_index
```

Then retrieve document passages:

```bash
python -m src.retrieval.run_retrieval \
    "Can employees work abroad?" \
    --top-k 3
```

### Automated Testing

```bash
python -m pytest -q
```

The retrieval components are tested using dependency injection and fake embedding/vector-search implementations, avoiding external model downloads during unit tests.




## Sample Data

The repository includes a fictional remote-working policy document for development and testing.

No real employee or confidential company data is required.

## Retrieval Evaluation

RAGAssist includes a reproducible evaluation pipeline
for measuring semantic-retrieval quality.

The evaluation uses curated questions and labelled
source evidence to calculate:

- Mean Recall@1
- Mean Recall@3
- Mean Reciprocal Rank at 3 (MRR@3)
- Retrieval latency

Run the evaluation:

    python -m src.evaluation.run_retrieval_eval

Results are saved to:

- `reports/retrieval_evaluation.csv`
- `reports/retrieval_evaluation.md`

The current evaluation dataset is small and based on a
fictional policy document. Results are an initial
engineering baseline, not production benchmarks.


## Answer Quality Evaluation

RAGAssist evaluates its generated answers using 12
curated questions, including unsupported questions
designed to test hallucination and abstention behaviour.

Run answer evaluation:

    python -m src.evaluation.run_answer_eval --limit 12

Manually review generated answers and their citations:

    python -m src.evaluation.review_answer_eval

Generate the evaluation summary:

    python -m src.evaluation.summarize_answer_eval

The evaluation records:

- Answer correctness
- Citation support
- Correct and incorrect abstentions
- Unsupported-answer events
- End-to-end response latency

See `reports/evaluation_summary.md` for results.

The current dataset is small and fictional. These results
are an initial engineering baseline, not a production
reliability guarantee.


## Retrieval Optimisation

RAGAssist includes controlled experiments comparing character-based text chunking configurations.

The experiments measure:

- Recall@1 and Recall@3
- Mean Reciprocal Rank at 3 (MRR@3)
- Availability of labelled supporting evidence
- Query retrieval latency
- Number of indexed document chunks

Run the comparison:

```bash
python -m src.evaluation.compare_retrieval
```

Results are saved in `reports/retrieval_comparison.csv` and `reports/retrieval_comparison_details.csv`.

The experimental findings and configuration trade-offs are documented in `reports/retrieval_optimisation.md`.

The comparison uses the same source documents and evaluation questions for each configuration and does not modify the application's saved FAISS index.




