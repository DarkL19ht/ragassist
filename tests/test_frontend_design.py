"""Unit tests for safe HTML rendering and the research-workbench UI."""

from src.frontend.app import (
    build_demo,
    format_answer_text,
    render_citations,
    render_evidence,
    render_status,
    run_research,
)


def test_answer_text_escapes_untrusted_markup():
    output = format_answer_text('<script>alert("x")</script> [Source 1]')
    assert "<script>" not in output
    assert "&lt;script&gt;" in output
    assert 'class="ra-inline-cite"' in output


def test_passages_escape_untrusted_markup():
    output = render_evidence({"results": [{
        "text": "<img src=x onerror=alert(1)>",
        "file_name": "policy.txt",
        "chunk_id": "abc123",
        "score": 0.75,
    }]})
    assert "<img" not in output
    assert "&lt;img" in output
    assert "0.7500" in output


def test_citations_escape_filename():
    output = render_citations([{
        "source_number": 1,
        "file_name": '<svg onload="alert(1)">',
        "chunk_id": "c1",
    }])
    assert "<svg" not in output
    assert "&lt;svg" in output


def test_status_indicates_insufficient_evidence():
    output = render_status("insufficient_evidence", 2)
    assert "NO SUPPORTED ANSWER" in output
    assert "2 PASSAGES" in output


def test_research_error_falls_back_to_safe_card(monkeypatch):
    import src.frontend.app as app_module
    from src.frontend.client import BackendRequestError

    def failing_backend(question, top_k):
        raise BackendRequestError("API unavailable")

    monkeypatch.setattr(app_module, "query_backend", failing_backend)
    status, answer, citations, evidence = run_research("Question", 3)
    assert "REQUEST FAILED" in status
    assert "API unavailable" in answer
    assert "0 REFERENCES" in citations
    assert "0 PASSAGES" in evidence


def test_gradio_demo_builds_without_api_calls():
    demo = build_demo()
    assert demo is not None


def test_research_completion_scrolls_to_answer():
    from src.frontend.app import SCROLL_TO_RESULTS_JS
    assert "ra-answer-panel" in SCROLL_TO_RESULTS_JS
    assert "scrollIntoView" in SCROLL_TO_RESULTS_JS
    assert "prefers-reduced-motion" in SCROLL_TO_RESULTS_JS
    assert "focus({ preventScroll: true })" in SCROLL_TO_RESULTS_JS


def test_inquiry_heading_has_explicit_contrast():
    from src.frontend.app import STYLES_FILE
    css = STYLES_FILE.read_text(encoding="utf-8")
    assert ".ra-panel-intro h2" in css
    assert "color: var(--ra-ink) !important" in css
    assert "--ra-orange: #a24b32" in css


def test_scroll_chain_registered_on_submit():
    from src.frontend.app import build_demo
    demo = build_demo()
    dependencies = demo.config.get("dependencies", [])
    assert any(
        "scrollIntoView" in (event.get("js") or "")
        and event.get("trigger_after") is not None
        for event in dependencies
    )


def test_upload_action_is_legible_without_hover():
    from src.frontend.app import STYLES_FILE
    css = STYLES_FILE.read_text(encoding="utf-8")
    assert "#ra-upload-accordion #ra-index," in css
    assert "#ra-upload-accordion #ra-index :is(span, p, strong)" in css
    assert "-webkit-text-fill-color: #e9ffab !important" in css
    # Avoid reintroducing the less-specific broad override.
    assert "#ra-upload-accordion summary, #ra-upload-accordion button," not in css


def test_file_drop_area_is_readable():
    from src.frontend.app import STYLES_FILE
    css = STYLES_FILE.read_text(encoding="utf-8")
    assert "#ra-upload-accordion #ra-files" in css
    assert "#ra-upload-accordion #ra-files button" in css
    assert "-webkit-text-fill-color: #142d2d !important" in css


def test_upload_instructions_are_one_compact_paragraph():
    import inspect
    from src.frontend.app import build_demo, STYLES_FILE
    code = inspect.getsource(build_demo)
    css = STYLES_FILE.read_text(encoding="utf-8")
    assert "ra-upload-guidance" in code
    assert "scanned PDFs require OCR and are not supported." in code
    assert "Retrieved passages are sent to Groq" in code
    assert ".ra-upload-guidance p" in css
    assert "margin: 0 !important" in css
