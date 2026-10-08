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


## Current Status

**Phase 1 — Repository and development environment setup.**

The RAG, LLM, API and deployment features listed above are planned and will be implemented incrementally.

## Sample Data

The repository includes a fictional remote-working policy document for development and testing.

No real employee or confidential company data is required.