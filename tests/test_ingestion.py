# Automated Ingestion Tests

import pytest

from src.ingestion.loader import (
    load_directory,
    load_document,
)
from src.ingestion.schema import DocumentRecord
from src.ingestion.txt_loader import load_txt
from reportlab.pdfgen import canvas
from src.ingestion.pdf_loader import load_pdf


def test_load_sample_txt():
    records = load_document(
        "data/sample_docs/remote_work_policy.txt"
    )

    assert len(records) == 1
    assert isinstance(records[0], DocumentRecord)
    assert records[0].file_type == "txt"
    assert records[0].file_name == "remote_work_policy.txt"


def test_sample_text_contains_policy():
    records = load_document(
        "data/sample_docs/remote_work_policy.txt"
    )

    assert "Working From Abroad" in records[0].text


def test_txt_has_no_page_number():
    records = load_document(
        "data/sample_docs/remote_work_policy.txt"
    )

    assert records[0].page_number is None


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        load_document(
            "data/sample_docs/does_not_exist.txt"
        )


def test_unsupported_file_type(tmp_path):
    file_path = tmp_path / "example.csv"
    file_path.write_text(
        "sample",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported file type",
    ):
        load_document(file_path)


def test_empty_txt_file(tmp_path):
    file_path = tmp_path / "empty.txt"
    file_path.write_text(
        "",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="empty",
    ):
        load_txt(file_path)


def test_load_directory():
    records = load_directory(
        "data/sample_docs"
    )

    assert len(records) >= 1


def test_document_record_to_dict():
    record = DocumentRecord(
        text="Example content",
        source="example.txt",
        file_name="example.txt",
        file_type="txt",
    )

    result = record.to_dict()

    assert result["text"] == "Example content"
    assert result["page_number"] is None

def test_pdf_extraction(tmp_path):
    pdf_path = tmp_path / "example.pdf"

    pdf = canvas.Canvas(str(pdf_path))

    pdf.drawString(
        72,
        750,
        "Employees need HR approval to work abroad.",
    )

    pdf.showPage()
    pdf.save()

    records = load_pdf(pdf_path)

    assert len(records) == 1
    assert records[0].file_type == "pdf"
    assert records[0].page_number == 1
    assert "HR approval" in records[0].text