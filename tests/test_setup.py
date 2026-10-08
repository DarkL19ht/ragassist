from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SAMPLE_DOCUMENT = (
    PROJECT_ROOT
    / "data"
    / "sample_docs"
    / "remote_work_policy.txt"
)


def test_sample_document_exists():
    assert SAMPLE_DOCUMENT.is_file()


def test_sample_document_not_empty():
    text = SAMPLE_DOCUMENT.read_text(
        encoding="utf-8"
    )

    assert len(text.strip()) > 0


def test_sample_document_contains_policy():
    text = SAMPLE_DOCUMENT.read_text(
        encoding="utf-8"
    )

    assert "Working From Abroad" in text


def test_sample_document_contains_hr_approval():
    text = SAMPLE_DOCUMENT.read_text(
        encoding="utf-8"
    )

    assert "written approval from HR" in text