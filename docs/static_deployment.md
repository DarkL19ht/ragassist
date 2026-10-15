# RAGAssist — Static Frontend and Free Backend Deployment

## Deployment architecture

- `web/`: standalone, static HTML/CSS/JavaScript Evidence Workbench on Cloudflare Pages.
- `src/api/main.py`: existing FastAPI application on a separate Python service.
- `/health`, `/ask`, `/retrieve`: built-in sample policy endpoints.
- `/workspaces`, `/workspaces/documents`, `/workspaces/text`, `/workspaces/ask`, `/workspaces/retrieve`: temporary per-session document endpoints.
- Groq API key is used **only on the backend** and never included in `web/config.js`.
- The old Gradio frontend remains available for Codespaces development; the public frontend does **not** run Gradio.

## What this solves and what it does not

Cloudflare Pages serves the public interface from static CDN assets without waiting for the backend. While the backend sleeps, the page remains usable and displays a connection banner, a non-LLM early `/health` wake-up request, and an honest progress panel during research and document uploads. One sample `/retrieve` request warms up the embedding model after `/health` responds.

**This does not make the free backend wake faster.** The first actual LLM answer may still be delayed or fail if the backend is out of RAM. The loader is visual feedback, not an acceleration mechanism. No indefinite keep-alive or fake progress percentage is used.

## 1. Copy files into your existing RAGAssist repository

Extract the archive in the repository root. New files include:

- `web/index.html`, `web/styles.css`, `web/config.js`, `web/app.mjs`, `web/utils.mjs`, `web/_headers`
- `src/api/cors_config.py`
- `scripts/enable_static_frontend_cors.py`
- `requirements-api.txt`
- `render.yaml`
- `tests/test_static_frontend_cors.py`
- `static_tests/static_utils.test.mjs`

The archive does **not** replace your existing `src/api/main.py`, `src/frontend/` Gradio application, existing API routes, ingestion, FAISS, or evaluation files.

Run from `/workspaces/ragassist`:

```bash
source .venv/bin/activate
python scripts/enable_static_frontend_cors.py
python -m pytest tests/test_static_frontend_cors.py -v
node --test static_tests/static_utils.test.mjs
python -m pytest -q
```

The Python installer appends `configure_cors(app)` to the existing `src/api/main.py` if needed. Inspect the resulting diff before committing.

## 2. Create the free static website first

1. Push the new files to your GitHub repository.
2. Open **https://dash.cloudflare.com/**, select **Workers & Pages**, then **Create** and **Pages**. Choose **Connect to Git** (UI wording may vary).
3. Authorize GitHub access to your `ragassist` repository.
4. Configure:

   | Setting | Value |
   |---|---|
   | Project name | `ragassist-workbench` (or another available name) |
   | Production branch | `main` |
   | Framework preset | `None` / no framework |
   | Repository root directory | `/` (repository root) |
   | Build command | `exit 0` |
   | Build output directory | `web` |

5. Deploy. The site will have a `https://<PROJECT>.pages.dev` address.
6. With the default `web/config.js` placeholder, the **website loads but displays 'Backend URL not configured'.** That is intentional until the backend has a public URL.
7. Record the exact `https://...pages.dev` origin **without a trailing slash**.

If Pages offers a different setup flow, consult Cloudflare's Git-integration and Static HTML documentation. Connecting via Git makes the site automatically redeploy when you push commits to `main`.

## 3. Deploy FastAPI on a free Python host

This guide uses Render Free as an example. **Render Free has 512 MB RAM and 0.1 CPU** (see Render documentation). The local Sentence Transformers/PyTorch stack may exceed this limit. If the API crashes with an out-of-memory error, UI loaders cannot solve it. The backend will need either a lighter embedding implementation, more memory on another host, or a different embedding/inference service.

In Render, create **New > Web Service** and connect the same GitHub repository.

| Setting | Value |
|---|---|
| Runtime | Python 3 |
| Plan | Free |
| Branch | `main` |
| Build Command | See command below |
| Start Command | See command below |
| Health Check Path | `/health` |

Build command (one line when pasting in Render):

```bash
python -m pip install --upgrade pip && python -m pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && python -m pip install --no-cache-dir -r requirements-api.txt && python -m src.ingestion.run_ingestion && python -m src.chunking.run_chunking && python -m src.embeddings.build_index
```

Start command:

```bash
python -m uvicorn src.api.main:app --host 0.0.0.0 --port $PORT --workers 1
```

Environment variables (Render dashboard, **not GitHub**):

| Variable | Value |
|---|---|
| `GROQ_API_KEY` | Your secret API key |
| `PYTHON_VERSION` | `3.12.11` |
| `CORS_ALLOWED_ORIGINS` | Exact Cloudflare Pages origin, e.g. `https://ragassist-workbench.pages.dev` |
| `HF_HOME` | `/opt/render/project/src/.hf_cache` (cache build-time embedding model assets in project workspace) |

Note: `HF_HOME` may be set in the environment for both build and runtime; Render's working directory may differ, so verify this path if the model re-downloads at runtime. The embedding model is downloaded as part of index building.

You can optionally use `render.yaml` via Render Blueprints instead of entering settings manually.

The configured CORS allowlist enables the hosted Pages site to call FastAPI across origins. It is **not** a security boundary against direct API usage.

**Verify the deployment URL** in a browser at `https://<YOUR-BACKEND>.onrender.com/health`; expect JSON with `status: ok`. For correctness, also test `/retrieve` from the site's actual UI: an HTTP 200 health check alone does not prove the embedding model loaded successfully.

The backend should already include the workspace upload routes you installed earlier. Confirm `/docs` contains `/workspaces` endpoints before testing uploads.

## 4. Connect the live API URL to Pages

Open `web/config.js` in Codespaces and change:

```js
window.RAGASSIST_CONFIG = {
  apiBaseUrl: 'https://YOUR-ACTUAL-SERVICE.onrender.com'
};
```

Do **not** add `/ask`, a trailing path, Groq secrets, or a private IP address.

Commit and push; Cloudflare Pages rebuilds your site automatically.

Open the Pages site, refresh, and verify the backend status banner eventually changes from **Connecting** to **Ready**, or displays a recoverable error with a retry control.

## 5. Test the whole user journey

- Landing page must display immediately even when Render is asleep.
- Loading indicator is visible while `/health` waits; it must never claim a precise percentage or promise an exact wake-up time.
- Ask `Can employees work from another country?` and confirm source citations and evidence (the exact wording of the answer may vary).
- Expand **ADD YOUR SOURCE MATERIAL**, paste a fictional travel policy, and click **INDEX SOURCE MATERIAL**.
- Ask about the pasted policy; verify that it uses the temporary workspace and shows evidence from your own source.
- Upload an ordinary non-scanned PDF or TXT document; verify supported extension, max size, and correct labels.
- Click **REMOVE MY SOURCES** and verify the built-in sample policy mode resumes.
- Test on a narrow mobile-sized browser window.
- Leave the backend idle long enough to sleep, then reopen the Pages URL. The page should still render promptly and show a reconnecting state.

## 6. Operational and privacy limitations

- A Render Free backend spins down after 15 minutes without incoming traffic and can take around a minute to restart. The website is available immediately; actual answers still depend on backend availability.
- The temporary `WorkspaceService` keeps uploaded documents and FAISS indexes **in memory**. They disappear after its 30-minute inactivity TTL or when the backend spins down/restarts. On an expired workspace, the static frontend asks users to re-index; files are not persisted in the browser.
- File sizes: up to 5 MB each, PDF up to 40 pages, max 10 sources per workspace, max 50,000 characters per pasted entry (limits are enforced by the existing API).
- No OCR for scanned PDFs.
- Uploaded excerpts are sent to Groq when generating an answer. Only use non-sensitive test documents.
- The public API currently has no strong authentication or per-user quota enforcement. Restrict public use, add backend-side rate limits/quotas before broadly advertising it, and monitor Groq usage. **CORS by itself does not stop bots or curl callers.**
- Do not add periodic keep-alive pings intended to bypass the free host's idle shutdown; the site issues a single wake-up request and a single non-LLM prewarm request when a visitor opens it.
- If the backend doesn't fit Render Free's memory budget, deployment work must address the backend size/architecture. A spinner only improves perceived UX, not reliability.

## 7. Verify tests and commit

```bash
python -m pytest tests/test_static_frontend_cors.py -v
node --test static_tests/static_utils.test.mjs
python -m pytest -q
git status
git add web src/api/cors_config.py scripts/enable_static_frontend_cors.py tests/test_static_frontend_cors.py static_tests requirements-api.txt render.yaml docs/static_deployment.md src/api/main.py
git diff --cached --stat
git commit -m "Deploy static Evidence Workbench with backend warmup states"
git push
```

## Official resources

- Cloudflare Pages static HTML: https://developers.cloudflare.com/pages/framework-guides/deploy-anything/
- Cloudflare Pages Git integration: https://developers.cloudflare.com/pages/configuration/git-integration/
- Render FastAPI: https://render.com/docs/deploy-fastapi
- Render Free limitations: https://render.com/docs/free
- FastAPI CORS: https://fastapi.tiangolo.com/tutorial/cors/
