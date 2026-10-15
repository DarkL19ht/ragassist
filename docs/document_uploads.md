# Document Workspace — Uploads and Pasted Text

## Purpose

RAGAssist can answer questions about documents supplied through the research
workbench. Users can upload UTF-8 `.txt` files, text-based `.pdf` files, or paste
text directly into the interface. The uploaded documents are embedded using
`all-MiniLM-L6-v2`, chunked with the existing 500/100 configuration, and
indexed in a separate in-memory FAISS index.

The document workspace is **separate from the bundled demonstration policy**.
When no documents are uploaded, the frontend searches the existing sample
index. After documents are indexed, only that browser session's uploaded
sources are searched. Deleting the workspace switches back to the demo index.

## Running Locally

Install the dependencies, including `python-multipart`:

```bash
python -m pip install -r requirements.txt
```

Start FastAPI:

```bash
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

Start Gradio in a separate terminal:

```bash
python -m src.frontend.app
```

In the **Add Your Source Material** section, choose PDF/TXT files or paste text,
then select **Index Source Material**. When indexing finishes, enter a question
and select **Run Research**. The browser moves to the answer, citation register
and evidence register once generation finishes.

Select **Remove uploaded sources / use demo** to delete the active workspace
and return to the sample policy.

## API

The API exposes the following additional endpoints:

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/workspaces` | Create a temporary workspace and receive a random token |
| `GET` | `/workspaces` | List indexed source names |
| `POST` | `/workspaces/documents` | Upload one PDF/TXT file as multipart form data |
| `POST` | `/workspaces/text` | Index pasted text supplied as JSON |
| `POST` | `/workspaces/retrieve` | Search only this workspace's indexed text |
| `POST` | `/workspaces/ask` | Generate an answer from only this workspace's passages |
| `DELETE` | `/workspaces` | Delete the workspace from server memory |

All workspace endpoints except creation require the
`X-Workspace-Token` HTTP header. The token is a capability secret, **not
user authentication**; do not publish or log it.

### Example: Create and add pasted text

```bash
# Create a workspace and inspect the response to obtain workspace_token.
curl -X POST http://127.0.0.1:8000/workspaces
```

Set `TOKEN` to the returned value, then:

```bash
curl -X POST http://127.0.0.1:8000/workspaces/text \
  -H "X-Workspace-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"meeting_notes","text":"The team meets every Tuesday."}'
```

Run a retrieval request:

```bash
curl -X POST http://127.0.0.1:8000/workspaces/retrieve \
  -H "X-Workspace-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question":"When does the team meet?","top_k":3}'
```

The `/workspaces/ask` endpoint takes the same JSON body but also calls the
configured Groq-hosted language model.

## Limits and Behavior

- Accepted types: PDF with selectable text, and UTF-8 TXT.
- Per-file limit: 5 MB.
- Maximum 40 PDF pages per file.
- Maximum 10 source entries per workspace, including pasted-text entries.
- Maximum pasted-text length: 50,000 characters per entry.
- Maximum total indexed text: 150,000 characters per workspace.
- Maximum 450 generated chunks per workspace.
- Up to 25 active workspaces in this local-demo server.
- Workspaces expire after 30 minutes of inactivity (activity renews the expiry).
- Indexed documents are held in a single FastAPI process's memory and are
  **not persisted** to the repository or the sample FAISS index.
- Restarting FastAPI loses all workspaces. This is designed for a single
  server process; do not run multiple Uvicorn workers without shared storage.
- No OCR is provided; image-only PDFs will not produce searchable text.
- File uploads are copied to Gradio's temporary upload cache before indexing;
  deleting an API workspace does not guarantee immediate deletion of all
  temporary upload copies.

## Security and Privacy

This is a development/portfolio implementation, **not** a hardened public
multi-user document service. Token isolation prevents ordinary session
cross-contamination, but it does not replace authentication, authorization,
audit logging, or quotas. An unauthenticated caller can currently create
workspaces and trigger resource consumption. Keep both Codespaces ports private
until proper access control and rate limiting are added.

When `/workspaces/ask` is called, **retrieved passages from uploaded documents
are sent to the configured external Groq language-model provider**. Do not
upload confidential, personal, regulated, or proprietary documents unless the
provider and deployment are approved for that use.

The frontend escapes filenames and retrieved text before rendering HTML.
File extensions, input sizes, PDF page counts and total indexed text are
validated on the backend.

## Testing

```bash
python -m pytest tests/test_workspace_routes.py tests/test_document_uploads.py -v
python -m pytest -q
```

Test cases use fake services and HTTP transports and make no live Groq calls.
