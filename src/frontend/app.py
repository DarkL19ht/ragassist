"""RAGAssist document research workbench (Gradio frontend)."""

import html
import os
import re
from pathlib import Path

import gradio as gr

from src.frontend.client import (
    BackendRequestError, query_backend, query_workspace,
    create_workspace, upload_workspace_file, upload_workspace_text,
    delete_workspace,
)


STYLES_FILE = Path(__file__).with_name("styles.css")

SUGGESTED_QUESTIONS = (
    "Can employees work from another country?",
    "What are the company's core working hours?",
    "Who approves ordinary remote-working requests?",
    "How often are remote-working arrangements reviewed?",
)

INITIAL_STATUS = """
<div class="ra-status ra-status-idle" role="status" aria-live="polite">
  <span class="ra-led"></span>
  <span>AWAITING RESEARCH QUERY</span>
  <span class="ra-status-meta">NO SEARCH EXECUTED</span>
</div>
"""

INITIAL_ANSWER = """
<section class="ra-answer ra-empty">
  <div class="ra-section-line"><span>01 / RESEARCH BRIEF</span><span>NOT GENERATED</span></div>
  <div class="ra-empty-symbol">↗</div>
  <h2>Answers backed<br>by evidence.</h2>
  <p>Choose a suggested question or write your own. The answer and its supporting
  passages will appear in this workspace.</p>
</section>
"""

INITIAL_CITATIONS = """
<section class="ra-citations">
  <div class="ra-section-line"><span>02 / CITED REFERENCES</span><span>0 REFERENCES</span></div>
  <p class="ra-placeholder-small">Source references will appear here when the model cites a passage.</p>
</section>
"""

INITIAL_EVIDENCE = """
<section class="ra-evidence">
  <div class="ra-section-line"><span>03 / EVIDENCE REGISTER</span><span>0 PASSAGES</span></div>
  <p class="ra-placeholder-small">Retrieved document excerpts will be displayed here for independent review.</p>
</section>
"""


def safe(value) -> str:
    """Escape any value before inserting it into generated HTML."""
    return html.escape(str(value if value is not None else ""), quote=True)


def format_evidence(retrieval_response: dict) -> str:
    """Legacy text representation retained for compatibility with existing tests."""
    results = retrieval_response.get("results", [])
    if not results:
        return "No document passages were retrieved."

    sections = []
    for rank, passage in enumerate(results, start=1):
        info = [
            f"Result {rank}",
            f"File: {passage.get('file_name') or 'Unknown document'}",
            f"Chunk ID: {passage.get('chunk_id') or 'Unknown'}",
        ]
        if passage.get("page_number") is not None:
            info.append(f"Page: {passage['page_number']}")
        if passage.get("score") is not None:
            info.append(f"Similarity: {float(passage['score']):.4f}")
        info.extend(["", str(passage.get("text", ""))])
        sections.append("\n".join(info))

    return "\n\n" + ("\n" + "-" * 55 + "\n\n").join(sections)


def handle_question(question: str, top_k: int):
    """Preserve the tested four-field handler from the original frontend."""
    try:
        answer, retrieval = query_backend(question, int(top_k))
        return (
            answer.get("answer", ""),
            answer.get("status", "unknown"),
            answer.get("sources", []),
            format_evidence(retrieval),
        )
    except (ValueError, BackendRequestError) as error:
        return str(error), "error", [], ""


def format_answer_text(answer: str) -> str:
    """Escape generated text, then visually highlight source markers."""
    escaped = safe(answer)
    cited = re.sub(
        r"\[\s*Source\s+(\d+)\s*\]",
        lambda match: (
            f'<span class="ra-inline-cite">[Source {match.group(1)}]</span>'
        ),
        escaped,
        flags=re.IGNORECASE,
    )
    return cited.replace("\n", "<br>")


def render_status(status: str, result_count: int) -> str:
    options = {
        "answered": ("complete", "ANSWER GENERATED", "Review supporting evidence"),
        "insufficient_evidence": (
            "caution",
            "NO SUPPORTED ANSWER",
            "Supporting text may still be available below",
        ),
        "error": ("error", "REQUEST FAILED", "Check the API connection"),
    }
    kind, label, explanation = options.get(
        status,
        ("idle", "RESPONSE RECEIVED", "Review the output below"),
    )
    return (
        f'<div class="ra-status ra-status-{kind}" role="status" aria-live="polite">'
        f'<span class="ra-led"></span><span>{label}</span>'
        f'<span class="ra-status-meta">'
        f'{int(result_count)} PASSAGES · {explanation}'
        f'</span></div>'
    )


def render_answer(answer: str, *, error: bool = False) -> str:
    heading = "Request interrupted" if error else "Research findings"
    message = format_answer_text(answer) if answer else "No answer was returned."
    return f"""
<section class="ra-answer">
  <div class="ra-section-line"><span>01 / RESEARCH BRIEF</span><span>GENERATED OUTPUT</span></div>
  <h2>{heading}</h2>
  <div class="ra-answer-body">{message}</div>
  <div class="ra-note">AI-generated content. Verify claims against the evidence register below.</div>
</section>
"""


def render_citations(sources: list[dict]) -> str:
    if not sources:
        return """
<section class="ra-citations">
  <div class="ra-section-line"><span>02 / CITED REFERENCES</span><span>0 REFERENCES</span></div>
  <p class="ra-placeholder-small">No source references were included in the final answer.</p>
</section>
"""

    cards = []
    for source in sources:
        number = safe(source.get("source_number", "?"))
        filename = safe(source.get("file_name") or "Unknown document")
        chunk_id = safe(source.get("chunk_id") or "Not available")
        page = source.get("page_number")
        page_label = f" · page {safe(page)}" if page is not None else ""
        cards.append(
            '<div class="ra-reference">'
            f'<span class="ra-reference-num">[{number}]</span>'
            '<div class="ra-reference-detail">'
            f'<strong>{filename}</strong>'
            f'<small>CHUNK {chunk_id}{page_label}</small>'
            '</div></div>'
        )

    return (
        '<section class="ra-citations">'
        '<div class="ra-section-line"><span>02 / CITED REFERENCES</span>'
        f'<span>{len(sources)} REFERENCES</span></div>'
        f'<div class="ra-reference-list">{"".join(cards)}</div>'
        '</section>'
    )


def render_evidence(retrieval: dict) -> str:
    passages = retrieval.get("results", [])
    if not passages:
        return INITIAL_EVIDENCE

    cards = []
    for rank, passage in enumerate(passages, start=1):
        filename = safe(passage.get("file_name") or "Unknown document")
        chunk_id = safe(passage.get("chunk_id") or "Not available")
        page = passage.get("page_number")
        page_label = f" · PAGE {safe(page)}" if page is not None else ""
        score = passage.get("score")
        score_label = "N/A" if score is None else f"{float(score):.4f}"
        excerpt = safe(passage.get("text") or "No text available.")
        cards.append(f"""
<article class="ra-passage">
  <div class="ra-passage-head">
    <span class="ra-passage-rank">{rank:02d}</span>
    <span class="ra-passage-file">{filename}</span>
    <span class="ra-passage-score">SCORE {score_label}</span>
  </div>
  <p class="ra-passage-body">{excerpt}</p>
  <div class="ra-passage-foot">CHUNK {chunk_id}{page_label}</div>
</article>
""")

    return (
        '<section class="ra-evidence">'
        '<div class="ra-section-line"><span>03 / EVIDENCE REGISTER</span>'
        f'<span>{len(passages)} PASSAGES RETRIEVED</span></div>'
        f'<div class="ra-passage-list">{"".join(cards)}</div>'
        '<p class="ra-evidence-footnote">Similarity scores are ranking signals, not probabilities or proof of factual correctness.</p>'
        '</section>'
    )


def run_research(question: str, top_k: int):
    """Generate the four HTML panels shown in the new workspace."""
    try:
        answer, retrieval = query_backend(question, int(top_k))
    except (ValueError, BackendRequestError) as error:
        return (
            render_status("error", 0),
            render_answer(str(error), error=True),
            render_citations([]),
            INITIAL_EVIDENCE,
        )

    status = answer.get("status", "unknown")
    results = retrieval.get("results", [])
    return (
        render_status(status, len(results)),
        render_answer(answer.get("answer", "")),
        render_citations(answer.get("sources", [])),
        render_evidence(retrieval),
    )


def clear_workspace():
    return (
        "", 3, INITIAL_STATUS, INITIAL_ANSWER,
        INITIAL_CITATIONS, INITIAL_EVIDENCE,
    )


# Runs in the browser only after run_research has returned and the panels
# have been updated. The answer panel is the target, rather than the bottom
# of the page, so users can immediately see their research findings.
SCROLL_TO_RESULTS_JS = """() => {
  const target = document.getElementById('ra-answer-panel');
  if (!target) return;
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  target.scrollIntoView({
    behavior: reduceMotion ? 'instant' : 'smooth',
    block: 'start'
  });
  target.setAttribute('tabindex', '-1');
  target.focus({ preventScroll: true });
}"""



INITIAL_LIBRARY = """
<section class="ra-library-status" role="status" aria-live="polite">
 <strong>SOURCE LIBRARY · DEMO MODE</strong>
 <p>Searching the bundled example policy. Upload files or paste text below
 to switch to your own documents.</p>
</section>
"""


def render_library(names, *, message="", error=False):
    """Display active sources; never render unescaped uploaded filenames."""
    if not names:
        heading = "SOURCE LIBRARY · DEMO MODE"
        detail = "Searching the bundled sample policy. Add documents to switch sources."
    else:
        heading = f"YOUR SOURCE LIBRARY · {len(names)} SOURCE(S)"
        detail = "Only your temporarily indexed documents are searched."
    items = "".join(f"<li>{safe(name)}</li>" for name in names)
    notification = (
        f'<p class="ra-library-{ "error" if error else "notice" }">{safe(message)}</p>'
        if message else ""
    )
    return (
        '<section class="ra-library-status" role="status" aria-live="polite">'
        f'<strong>{heading}</strong><p>{detail}</p>'
        f'{"<ul>" + items + "</ul>" if items else ""}'
        f'{notification}</section>'
    )


def index_sources(files, pasted_text, text_title, token, source_names):
    """Build/rebuild a session-specific index using the backend HTTP API."""
    files = files or []
    if isinstance(files, str):
        files = [files]
    pasted_text = pasted_text or ""
    source_names = list(source_names or [])
    if not files and not pasted_text.strip():
        return (token, source_names, render_library(
            source_names, message="Select a PDF/TXT file or paste text first.", error=True
        ), gr.update(), gr.update(),
            INITIAL_STATUS, INITIAL_ANSWER, INITIAL_CITATIONS, INITIAL_EVIDENCE)

    try:
        if token is None:
            token = create_workspace()
        response = None
        for item in files:
            filepath = Path(str(item))
            if not filepath.is_file():
                raise ValueError("Selected upload could not be read. Select the file again.")
            if filepath.stat().st_size > 5 * 1024 * 1024:
                raise ValueError("Each file must be 5 MB or smaller.")
            name = getattr(item, "orig_name", None) or filepath.name
            response = upload_workspace_file(token, name, filepath.read_bytes())
            source_names = list(response.get("documents", source_names))
        if pasted_text.strip():
            response = upload_workspace_text(
                token, text_title.strip() or "pasted_notes", pasted_text.strip()
            )
            source_names = list(response.get("documents", source_names))
        message = f"Indexed {len(source_names)} source(s). Enter a question to research them."
        return (token, source_names, render_library(source_names, message=message),
                gr.update(value=None), gr.update(value=""),
                INITIAL_STATUS, INITIAL_ANSWER, INITIAL_CITATIONS, INITIAL_EVIDENCE)
    except (BackendRequestError, ValueError, OSError) as error:
        return (token, source_names, render_library(
            source_names, message=str(error), error=True
        ), gr.update(), gr.update(),
            INITIAL_STATUS, INITIAL_ANSWER, INITIAL_CITATIONS, INITIAL_EVIDENCE)


def remove_sources(token):
    """Discard the current index and switch back to the sample-policy demo."""
    if token:
        try:
            delete_workspace(token)
        except BackendRequestError as error:
            # If the backend has restarted or expired the index, local state
            # should still be reset so the browser can recover.
            return (None, [], render_library([], message=str(error), error=True),
                    INITIAL_STATUS, INITIAL_ANSWER, INITIAL_CITATIONS, INITIAL_EVIDENCE)
    return (None, [], INITIAL_LIBRARY,
            INITIAL_STATUS, INITIAL_ANSWER, INITIAL_CITATIONS, INITIAL_EVIDENCE)


def run_active_research(question, top_k, workspace_token):
    """Choose ONLY uploaded sources when a workspace is active."""
    try:
        if workspace_token:
            answer, retrieval = query_workspace(question, int(top_k), workspace_token)
        else:
            answer, retrieval = query_backend(question, int(top_k))
    except (BackendRequestError, ValueError) as error:
        return (render_status("error", 0), render_answer(str(error), error=True),
                render_citations([]), INITIAL_EVIDENCE)
    passages = retrieval.get("results", [])
    return (
        render_status(answer.get("status", "unknown"), len(passages)),
        render_answer(answer.get("answer", "")),
        render_citations(answer.get("sources", [])),
        render_evidence(retrieval),
    )

def build_demo():
    with gr.Blocks(
        title="RAGAssist | Evidence Workbench",
    ) as demo:
        gr.HTML("""
<header class="ra-topbar">
  <div class="ra-wordmark"><span class="ra-mark">R<span>✳</span></span><span>RAG<span class="ra-wordmark-light">ASSIST</span></span></div>
  <div class="ra-topbar-right"><span>DOCUMENT INTELLIGENCE</span><span class="ra-topbar-dot"></span><span>RESEARCH WORKBENCH / 01</span></div>
</header>
<div class="ra-masthead">
  <div><span class="ra-eyebrow">RESEARCH SYSTEM / SOURCE-GROUNDED AI</span>
  <h1>Read between<br><em>the documents.</em></h1></div>
  <div class="ra-masthead-side"><span class="ra-masthead-index">01 — 03</span><p>Turn indexed documents into answers you can inspect, trace, and verify.</p></div>
</div>
""")

        with gr.Row(equal_height=False, elem_id="ra-workspace"):
            with gr.Column(scale=4, min_width=310, elem_id="ra-sidebar"):
                gr.HTML("""
<div class="ra-panel-intro"><span class="ra-eyebrow">THE RESEARCH DESK</span>
<h2>Start an inquiry.</h2><p>Ask about a policy, procedure, or detail in the indexed documents.</p></div>
""")
                question = gr.Textbox(
                    label="YOUR RESEARCH QUESTION",
                    placeholder="e.g. Who approves working from abroad?",
                    lines=4,
                    max_length=2000,
                    elem_id="ra-question",
                )
                top_k = gr.Slider(
                    minimum=1,
                    maximum=10,
                    value=3,
                    step=1,
                    label="Evidence depth · passages",
                    elem_id="ra-depth",
                )
                with gr.Row():
                    ask_button = gr.Button(
                        "RUN RESEARCH  ↗",
                        variant="primary",
                        elem_id="ra-run",
                    )
                    clear_button = gr.Button(
                        "Clear",
                        variant="secondary",
                        elem_id="ra-clear",
                    )

                gr.HTML('<div class="ra-sidebar-divider"></div>')
                with gr.Accordion("ADD YOUR SOURCE MATERIAL", open=True, elem_id="ra-upload-accordion"):
                    gr.HTML(
                        '<div class="ra-upload-guidance">'
                        '<p><strong>PDF / TXT documents or pasted text.</strong> '
                        'Up to 10 sources, 5 MB per file. Text must be selectable; '
                        'scanned PDFs require OCR and are not supported. '
                        'Retrieved passages are sent to Groq when generating answers, '
                        'so use non-sensitive documents.</p>'
                        '</div>'
                    )
                    uploaded_files = gr.File(
                        label="DOCUMENT FILES",
                        file_types=[".pdf", ".txt"],
                        file_count="multiple",
                        type="filepath",
                        elem_id="ra-files",
                    )
                    pasted_title = gr.Textbox(
                        label="TITLE FOR PASTED TEXT",
                        value="pasted_notes",
                        max_length=100,
                        elem_id="ra-paste-title",
                    )
                    pasted_text = gr.Textbox(
                        label="PASTE SOURCE TEXT (OPTIONAL)",
                        placeholder="Paste document content here to include it in your research...",
                        lines=5,
                        max_length=50000,
                        elem_id="ra-paste-text",
                    )
                    index_button = gr.Button(
                        "INDEX SOURCE MATERIAL  +",
                        variant="primary",
                        elem_id="ra-index",
                    )
                    reset_button = gr.Button(
                        "Remove uploaded sources / use demo",
                        variant="secondary",
                        elem_id="ra-reset-sources",
                    )
                workspace_token = gr.State(None)
                indexed_names = gr.State([])
                library_panel = gr.HTML(INITIAL_LIBRARY, elem_id="ra-library-panel")

                gr.HTML('<div class="ra-sidebar-divider"></div><div class="ra-eyebrow ra-suggest-label">DEMO POLICY · EXAMPLE QUESTIONS</div>')
                preset_buttons = [
                    gr.Button("01   Work from another country  ↗", elem_classes="ra-preset"),
                    gr.Button("02   Core working hours  ↗", elem_classes="ra-preset"),
                    gr.Button("03   Approval authority  ↗", elem_classes="ra-preset"),
                    gr.Button("04   Policy review cycle  ↗", elem_classes="ra-preset"),
                ]
                for button, prompt in zip(preset_buttons, SUGGESTED_QUESTIONS):
                    button.click(
                        fn=lambda text=prompt: text,
                        inputs=None,
                        outputs=question,
                        queue=False,
                    )


                gr.HTML("""
<div class="ra-source-note">
  <span class="ra-source-icon">▤</span>
  <div><strong>INDEXED DOCUMENTS</strong>
  <p>The example policy is available initially. Uploading documents switches your research to a session-scoped document collection.</p></div>
</div>
""")

            with gr.Column(scale=7, min_width=380, elem_id="ra-results"):
                status_panel = gr.HTML(INITIAL_STATUS, elem_id="ra-status-panel")
                answer_panel = gr.HTML(INITIAL_ANSWER, elem_id="ra-answer-panel")
                citation_panel = gr.HTML(INITIAL_CITATIONS, elem_id="ra-citation-panel")
                evidence_panel = gr.HTML(INITIAL_EVIDENCE, elem_id="ra-evidence-panel")

        gr.HTML("""
<footer class="ra-footer"><span>RAGASSIST / DOCUMENT INTELLIGENCE WORKBENCH</span>
<span>TRACE EVERY CLAIM TO ITS SOURCE · VERIFY BEFORE USE</span></footer>
""")

        # Make the results visible immediately after Gradio updates all panels.
        # Built-in eager scrolling can happen before the model finishes, so the
        # chained client-side callback runs AFTER the answer has been rendered.
        research_event = ask_button.click(
            fn=run_active_research,
            inputs=[question, top_k, workspace_token],
            outputs=[status_panel, answer_panel, citation_panel, evidence_panel],
        )
        research_event.then(
            fn=None,
            inputs=None,
            outputs=None,
            js=SCROLL_TO_RESULTS_JS,
            queue=False,
            show_progress="hidden",
        )
        index_button.click(
            fn=index_sources,
            inputs=[uploaded_files, pasted_text, pasted_title,
                    workspace_token, indexed_names],
            outputs=[workspace_token, indexed_names, library_panel,
                     uploaded_files, pasted_text,
                     status_panel, answer_panel, citation_panel, evidence_panel],
        )
        reset_button.click(
            fn=remove_sources,
            inputs=[workspace_token],
            outputs=[workspace_token, indexed_names, library_panel,
                     status_panel, answer_panel, citation_panel, evidence_panel],
        )
        clear_button.click(
            fn=clear_workspace,
            inputs=None,
            outputs=[question, top_k, status_panel, answer_panel, citation_panel, evidence_panel],
            queue=False,
        )

    return demo


if __name__ == "__main__":
    build_demo().launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", "7860")),
        share=False,
        theme=gr.themes.Base(),
        css=STYLES_FILE.read_text(encoding="utf-8"),
    )
