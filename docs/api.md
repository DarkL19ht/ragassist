# RAGAssist API Reference

## Overview

RAGAssist exposes a REST API for document retrieval and evidence-grounded question answering.

The backend uses FastAPI and Pydantic for endpoint definition, request validation and response schemas.

Semantic retrieval is implemented with Sentence Transformers and FAISS. Answer generation uses LangChain and a Groq-hosted LLM.

## Development Setup

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Build the local document index if necessary:

```bash
python -m src.ingestion.run_ingestion
python -m src.chunking.run_chunking
python -m src.embeddings.build_index
```

Run the API:

```bash
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation is available at `/docs`.

## Endpoints

### GET /health

Returns the current API liveness status.

Example response:

```json
{
  "status": "ok",
  "service": "RAGAssist API"
}
```

This endpoint confirms that the API process is responding. It does not verify readiness of the embedding model, FAISS index or hosted LLM.

### POST /retrieve

Retrieves document passages ranked by semantic similarity.

Example request:

```json
{
  "question": "Can employees work from another country?",
  "top_k": 3
}
```

The response includes the original question and a list of retrieved passages containing text, filenames, page numbers, chunk identifiers and similarity scores.

This endpoint does not perform LLM generation.

### POST /ask

Generates an answer grounded in retrieved document passages.

Example request:

```json
{
  "question": "Can employees work from another country?",
  "top_k": 3
}
```

Example response:

```json
{
  "question": "Can employees work from another country?",
  "answer": "Written HR approval is required. [Source 1]",
  "status": "answered",
  "sources": [
    {
      "source_number": 1,
      "file_name": "remote_work_policy.txt",
      "page_number": null,
      "chunk_id": "example-chunk-id",
      "score": 0.92
    }
  ],
  "retrieved_chunks": 3
}
```

The response is illustrative and does not represent a guaranteed model output.

If sufficient evidence is unavailable or citation validation fails, the service returns `insufficient_evidence`.

## Input Validation

- Question: non-empty string, maximum 2,000 characters.
- Retrieval limit: integer between 1 and 10.
- Default retrieval limit: 3.
- Invalid request bodies return HTTP 422.

## Error Handling

- HTTP 422: Request validation failed.
- HTTP 502: Answer generation failed.
- HTTP 503: Retrieval or model initialization unavailable.

Internal exception details are logged server-side rather than returned to API clients.

## Automated Testing

```bash
python -m pytest tests/test_api.py -v
```

API tests use dependency overrides and fake components. They do not require live model inference or external LLM requests.

## Security and Operational Limitations

The current API is intended for local development and portfolio demonstration.

It does not yet implement authentication, per-client rate limiting, request quotas or production monitoring.

The API should not be exposed publicly with unrestricted access to the hosted LLM.

Only public or non-sensitive documents should be used during development, since retrieved passages are sent to an external LLM provider.