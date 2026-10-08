# The PDF loader

from pathlib import Path

from pypdf import PdfReader

from src.ingestion.schema import DocumentRecord


def load_pdf(file_path: str | Path) -> list[DocumentRecord]:
    """
    Extract text from a PDF, preserving page numbers.
    """

    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"PDF file not found: {path}"
        )

    if path.suffix.lower() != ".pdf":
        raise ValueError(
            f"Expected a PDF file, received: {path.suffix}"
        )

    try:
        reader = PdfReader(str(path))

        if reader.is_encrypted:
            raise ValueError(
                f"Encrypted PDFs are not supported: {path}"
            )

        records = []

        for page_number, page in enumerate(
            reader.pages,
            start=1,
        ):
            text = (page.extract_text() or "").strip()

            if not text:
                continue

            records.append(
                DocumentRecord(
                    text=text,
                    source=str(path),
                    file_name=path.name,
                    file_type="pdf",
                    page_number=page_number,
                )
            )

    except ValueError:
        raise
    except Exception as error:
        raise ValueError(
            f"Unable to extract text from PDF: {path}"
        ) from error

    if not records:
        raise ValueError(
            f"No extractable text found in PDF: {path}"
        )

    return records