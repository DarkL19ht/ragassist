import { escapeHtml, readableError, validateQuestion, formatElapsed, safeApiUrl } from './utils.mjs';

const $ = id => document.getElementById(id);
const rawApiUrl = window.RAGASSIST_CONFIG?.apiBaseUrl;
const apiBase = safeApiUrl(rawApiUrl);

let backendReadyPromise = null;
let backendOnline = false;
let warmSearchPromise = Promise.resolve();
let workspaceToken = null; // Deliberately stays in memory; never in URLs or browser storage.
let workspaceNames = [];
let sourceMode = 'sample';
let busy = false;
let taskTimer = null;

const MAX_FILE_BYTES = 5 * 1024 * 1024;

function setConnection(phase, heading, description) {
  $('service-heading').textContent = heading;
  $('service-description').textContent = description;
  $('service-dot').className = `dot ${phase}`;
  $('retry-connection').hidden = phase !== 'failed';
}

async function fetchJSON(path, { method='GET', payload, form, token, timeout=135_000 } = {}) {
  if (!apiBase) throw Error('Set the deployed FastAPI URL in web/config.js before using RAGAssist.');
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  const headers = {};
  if (token) headers['X-Workspace-Token'] = token;
  if (payload !== undefined) headers['Content-Type'] = 'application/json';
  try {
    const response = await fetch(`${apiBase}${path}`, {
      method, headers,
      body: form ?? (payload === undefined ? undefined : JSON.stringify(payload)),
      signal: controller.signal,
      cache: 'no-store',
      mode: 'cors',
    });
    let data;
    try { data = await response.json(); } catch { data = {}; }
    if (!response.ok) {
      const detail = typeof data.detail === 'string' ? data.detail : '';
      const err = Error(readableError(response.status, detail));
      err.status = response.status;
      throw err;
    }
    return data;
  } catch (error) {
    if (error.name === 'AbortError') {
      throw Error('The document engine did not respond in time. It may be starting up or overloaded. Please retry.');
    }
    if (error instanceof TypeError) {
      throw Error('Could not reach the document engine. Check that the backend is deployed and that its CORS settings allow this website.');
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

function connectBackend() {
  backendOnline = false;
  setConnection('preparing', 'Connecting to research engine', 'The website is ready. The document engine is waking in the background.');
  backendReadyPromise = (async () => {
    try {
      const health = await fetchJSON('/health', { timeout: 110_000 });
      if (health.status !== 'ok') throw Error('The backend did not return a valid health response.');
      backendOnline = true;
      setConnection('ready', 'Research engine connected', 'The API is responding. Preparing document retrieval in the background.');
      // Background warm-up: one non-LLM retrieval, not a repeating keep-alive.
      // The first real query may still take time if the model is not loaded.
      warmSearchPromise = fetchJSON('/retrieve', {
        method: 'POST',
        payload: { question: 'What is the remote working policy?', top_k: 1 },
        timeout: 110_000,
      }).then(() => {
        setConnection('ready', 'Research engine ready', 'The document search index is ready for new inquiries.');
      }).catch(() => {
        setConnection('ready', 'API connected', 'The server is responding. Document retrieval will be checked when you submit a question.');
      });
    } catch (error) {
      warmSearchPromise = Promise.resolve();
      backendOnline = false;
      setConnection('failed', 'Research engine unavailable', error.message);
      throw error;
    }
  })();
  // Handle background rejection even when nobody presses a button.
  void backendReadyPromise.catch(() => {});
  return backendReadyPromise;
}

function startProgress(kind) {
  const isIndex = kind === 'index';
  $('progress-title').textContent = isIndex ? 'Indexing your source material.' : 'Preparing your research brief.';
  $('progress-description').textContent = isIndex
    ? 'Reading documents, creating embeddings and building a temporary search index. On a free backend this may include startup time.'
    : 'The document engine may need to wake up after inactivity. Your inquiry will continue automatically; there is no need to refresh.';
  $('progress-panel').hidden = false;
  const start = Date.now();
  $('elapsed').textContent = '00:00 ELAPSED';
  clearInterval(taskTimer);
  taskTimer = setInterval(() => {
    $('elapsed').textContent = `${formatElapsed((Date.now() - start) / 1000)} ELAPSED`;
  }, 1000);
  $('research-results').scrollIntoView({ behavior: prefersReducedMotion() ? 'auto' : 'smooth', block: 'start' });
}

function endProgress() {
  clearInterval(taskTimer);
  taskTimer = null;
  $('progress-panel').hidden = true;
}

function prefersReducedMotion() {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
}

function setBusy(value) {
  busy = value;
  for (const id of ['research-submit', 'index-submit', 'sample-mode', 'clear-workspace']) $(id).disabled = value;
  $('uploaded-mode').disabled = value || !workspaceToken;
  $('research-submit').textContent = value ? 'PROCESSING REQUEST…' : 'RUN RESEARCH ↗';
  $('index-submit').textContent = value ? 'INDEXING…' : 'INDEX SOURCE MATERIAL ＋';
}

function setAnswerStatus(kind, label, context) {
  const status = $('research-status');
  status.className = `status-banner ${kind}`;
  status.innerHTML = `<span class="dot" aria-hidden="true"></span><span>${escapeHtml(label)}</span><small>${escapeHtml(context)}</small>`;
}

function setError(message) {
  $('run-indicator').textContent = 'REQUEST INTERRUPTED';
  $('answer-tag').textContent = 'NOT GENERATED';
  $('answer-content').innerHTML = `<h2 id="answer-heading">Request interrupted</h2><div class="error-inline" role="alert">${escapeHtml(message)}</div>`;
  $('citation-count').textContent = '0 REFERENCES';
  $('citation-list').innerHTML = '<p class="placeholder">No citations returned.</p>';
  $('evidence-count').textContent = '0 PASSAGES';
  $('evidence-list').innerHTML = '<p class="placeholder">No supporting passages returned.</p>';
  setAnswerStatus('error', 'REQUEST FAILED', 'Check the backend status and try again');
  jumpToResults();
}

function jumpToResults() {
  $('research-results').scrollIntoView({ behavior: prefersReducedMotion() ? 'auto' : 'smooth', block: 'start' });
  $('research-results').focus({ preventScroll: true });
}

function renderAnswer(data, retrieval) {
  const status = data.status === 'answered' ? 'answered' : 'insufficient_evidence';
  const context = status === 'answered' ? 'Review cited references and evidence below' : 'Source evidence may not support an answer';
  setAnswerStatus(status === 'answered' ? '' : 'warning', status === 'answered' ? 'ANSWER GENERATED' : 'NO SUPPORTED ANSWER', context);
  $('run-indicator').textContent = `SEARCH COMPLETED / ${sourceMode === 'sample' ? 'SAMPLE POLICY' : 'MY SOURCES'}`;
  $('answer-tag').textContent = status === 'answered' ? 'GENERATED OUTPUT' : 'EVIDENCE INSUFFICIENT';
  const answer = escapeHtml(data.answer || 'No answer was returned.').replace(/\[\s*Source\s+(\d+)\s*\]/gi,
    '<mark style="background:#d8fb75;color:#142d2d;padding:2px 4px;border-radius:4px">[Source $1]</mark>');
  $('answer-content').innerHTML = `<h2 id="answer-heading">Research findings</h2><div class="answer-body">${answer}</div>`;

  const citations = Array.isArray(data.sources) ? data.sources : [];
  $('citation-count').textContent = `${citations.length} REFERENCES`;
  $('citation-list').innerHTML = citations.length ? citations.map(source => {
    const page = source.page_number != null ? ` · PAGE ${escapeHtml(source.page_number)}` : '';
    return `<article class="citation"><span class="citation-number">[${escapeHtml(source.source_number)}]</span><div><strong>${escapeHtml(source.file_name || 'Unknown document')}</strong><small>CHUNK ${escapeHtml(source.chunk_id || 'Unavailable')}${page}</small></div></article>`;
  }).join('') : '<p class="placeholder">No sources cited in the final answer.</p>';

  const passages = Array.isArray(retrieval.results) ? retrieval.results : [];
  $('evidence-count').textContent = `${passages.length} PASSAGES`;
  $('evidence-list').innerHTML = passages.length ? passages.map((result, index) => {
    const score = Number.isFinite(result.score) ? `SCORE ${Number(result.score).toFixed(4)}` : 'SCORE N/A';
    const page = result.page_number != null ? ` · PAGE ${escapeHtml(result.page_number)}` : '';
    return `<article class="passage"><header class="passage-header"><b>${String(index + 1).padStart(2,'0')}</b><strong>${escapeHtml(result.file_name || 'Unknown document')}</strong><small>${score}</small></header><p>${escapeHtml(result.text || '')}</p><footer>CHUNK ${escapeHtml(result.chunk_id || 'Unavailable')}${page}</footer></article>`;
  }).join('') : '<p class="placeholder">No passages retrieved.</p>';
  jumpToResults();
}

async function onResearch(event) {
  event.preventDefault();
  if (busy) return;
  let payload;
  try { payload = validateQuestion($('question').value, Number($('top-k').value)); }
  catch (error) { setError(error.message); return; }
  setBusy(true);
  startProgress('research');
  setAnswerStatus('', 'PROCESSING YOUR INQUIRY', 'Waiting for document engine');
  try {
    if (!backendOnline) await (backendReadyPromise ?? connectBackend());
    if (sourceMode === 'uploaded' && !workspaceToken) throw Error('Please upload or paste source material before searching your documents.');
    if (sourceMode === 'sample') await warmSearchPromise;
    const endpoint = sourceMode === 'uploaded' ? '/workspaces' : '';
    const options = {
      method:'POST', payload,
      ...(sourceMode === 'uploaded' ? { token: workspaceToken } : {}),
      timeout: 135_000,
    };
    const answer = await fetchJSON(`${endpoint}/ask`, options);
    $('progress-description').textContent = 'Answer received. Collecting the retrieved evidence for review…';
    let retrieval = { results: [] };
    let retrievalFailed = false;
    try { retrieval = await fetchJSON(`${endpoint}/retrieve`, { ...options, timeout: 100_000 }); }
    catch (error) {
      // Preserve the generated answer if the second, optional evidence request fails.
      retrieval = { results: [] };
      retrievalFailed = true;
      $('progress-description').textContent = 'Answer received. Supporting passage retrieval could not be completed.';
    }
    renderAnswer(answer, retrieval);
    if (retrievalFailed) setAnswerStatus('warning', 'ANSWER GENERATED; EVIDENCE UNAVAILABLE', 'Source passages could not be loaded for independent review');
  } catch (error) {
    if (error.status === 404 && sourceMode === 'uploaded') {
      workspaceToken = null;
      workspaceNames = [];
      updateWorkspaceUI();
    }
    setError(error.message);
  } finally {
    endProgress();
    setBusy(false);
  }
}

function setMode(mode) {
  if (mode === 'uploaded' && !workspaceToken) return;
  sourceMode = mode;
  $('sample-mode').classList.toggle('selected', mode === 'sample');
  $('uploaded-mode').classList.toggle('selected', mode === 'uploaded');
  $('sample-mode').setAttribute('aria-pressed', String(mode === 'sample'));
  $('uploaded-mode').setAttribute('aria-pressed', String(mode === 'uploaded'));
  $('collection-note').textContent = mode === 'sample'
    ? 'Searching the built-in fictional remote-work policy.'
    : `Searching your private temporary collection (${workspaceNames.length} source${workspaceNames.length === 1 ? '' : 's'}).`;
}

function updateWorkspaceUI() {
  $('uploaded-mode').disabled = busy || !workspaceToken;
  $('clear-workspace').disabled = busy || !workspaceToken;
  $('document-list').innerHTML = workspaceNames.length
    ? `<strong>${workspaceNames.length} INDEXED SOURCE${workspaceNames.length === 1 ? '' : 'S'}</strong><ul>${workspaceNames.map(name => `<li>${escapeHtml(name)}</li>`).join('')}</ul>`
    : 'Your sources will appear here after indexing.';
  if (!workspaceToken) setMode('sample');
  else setMode(sourceMode);
}

async function onUpload(event) {
  event.preventDefault();
  if (busy) return;
  const files = Array.from($('document-files').files ?? []);
  const pasted = $('paste-text').value.trim();
  const title = $('paste-title').value.trim() || 'Pasted notes';
  if (!files.length && !pasted) { setError('Select a PDF/TXT file or paste some document text first.'); return; }
  if (files.some(f => !/\.(pdf|txt)$/i.test(f.name) || f.size > MAX_FILE_BYTES || !f.size)) {
    setError('Each file must be a non-empty PDF or TXT document no larger than 5 MB.'); return;
  }
  if (files.length + workspaceNames.length + (pasted ? 1 : 0) > 10) {
    setError('A document workspace supports up to 10 sources.'); return;
  }
  setBusy(true); startProgress('index');
  setAnswerStatus('', 'INDEXING SOURCE MATERIAL', 'Creating your temporary search index');
  try {
    if (!backendOnline) await (backendReadyPromise ?? connectBackend());
    if (!workspaceToken) {
      const workspace = await fetchJSON('/workspaces', {method:'POST'});
      workspaceToken = workspace.workspace_token;
    }
    let indexed = null;
    for (const file of files) {
      $('progress-description').textContent = `Indexing ${file.name}…`;
      const form = new FormData(); form.append('file', file, file.name);
      indexed = await fetchJSON('/workspaces/documents', {method:'POST',form,token:workspaceToken,timeout:150_000});
      workspaceNames = indexed.documents ?? [];
      updateWorkspaceUI();
    }
    if (pasted) {
      $('progress-description').textContent = 'Indexing pasted document text…';
      indexed = await fetchJSON('/workspaces/text', {method:'POST',token:workspaceToken,payload:{title,text:pasted},timeout:150_000});
      workspaceNames = indexed.documents ?? [];
      updateWorkspaceUI();
    }
    setMode('uploaded');
    $('document-files').value = '';
    $('file-selection').textContent = 'No files selected';
    $('paste-text').value = '';
    $('progress-description').textContent = 'Your document collection is ready.';
    setAnswerStatus('', 'SOURCES INDEXED', `${workspaceNames.length} sources · ${indexed?.chunk_count ?? '—'} searchable passages`);
    $('run-indicator').textContent = 'SOURCE COLLECTION READY';
    $('answer-tag').textContent = 'READY TO RESEARCH';
    $('answer-content').innerHTML = '<h2 id="answer-heading">Your documents are ready.</h2><p class="empty-copy">Ask a question about your indexed material using the Research Desk.</p>';
    $('citation-list').innerHTML = '<p class="placeholder">Citations will appear after your next inquiry.</p>';
    $('evidence-list').innerHTML = '<p class="placeholder">Your retrieved source passages will appear after your next inquiry.</p>';
    jumpToResults();
  } catch (error) {
    if (error.status === 404) { workspaceToken = null; workspaceNames = []; }
    else if (workspaceToken && workspaceNames.length) setMode('uploaded');
    updateWorkspaceUI();
    setError(error.message);
  } finally {
    endProgress(); setBusy(false);
  }
}

async function clearSources() {
  if (busy || !workspaceToken) return;
  setBusy(true);
  const token = workspaceToken;
  try {
    if (backendOnline) await fetchJSON('/workspaces', { method:'DELETE',token,timeout:30_000 });
  } catch (error) { console.warn('Workspace may already have expired:', error.message); }
  finally {
    workspaceToken = null; workspaceNames = []; sourceMode = 'sample';
    updateWorkspaceUI(); setBusy(false);
    $('document-files').value = ''; $('paste-text').value = '';
    $('file-selection').textContent = 'No files selected';
    setAnswerStatus('', 'SOURCE COLLECTION CLEARED', 'Sample policy is now active');
  }
}

function main() {
  $('top-k').addEventListener('input', () => {
    $('top-k-value').textContent = `${$('top-k').value} PASSAGE${$('top-k').value === '1' ? '' : 'S'}`;
  });
  $('document-files').addEventListener('change', () => {
    const files = Array.from($('document-files').files ?? []);
    $('file-selection').textContent = files.length ? files.map(f => f.name).join(', ') : 'No files selected';
  });
  $('research-form').addEventListener('submit', onResearch);
  $('upload-form').addEventListener('submit', onUpload);
  $('sample-mode').addEventListener('click', () => setMode('sample'));
  $('uploaded-mode').addEventListener('click', () => setMode('uploaded'));
  $('clear-workspace').addEventListener('click', clearSources);
  $('retry-connection').addEventListener('click', () => { void connectBackend().catch(() => {}); });
  for (const button of document.querySelectorAll('[data-question]')) {
    button.addEventListener('click', () => {
      $('question').value = button.dataset.question;
      $('research-form').requestSubmit();
    });
  }
  if (!apiBase || rawApiUrl?.includes('REPLACE-WITH')) {
    setConnection('failed', 'Backend URL not configured', 'Edit web/config.js and specify your deployed FastAPI URL.');
  } else {
    void connectBackend().catch(() => {});
  }
}

main();
