# TXT loader

# This function:
# - Checks that the file exists.
# - Confirms that it is a TXT file.
# - Extracts its contents.
# - Rejects empty files.
# - Returns a structured document record.

from pathlib import Path

from src.ingestion.schema import DocumentRecord


def load_txt(file_path: str | Path) -> list[DocumentRecord]:
    """
    Load a UTF-8 TXT file into one document record.
    """

    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"Text file not found: {path}"
        )

    if path.suffix.lower() != ".txt":
        raise ValueError(
            f"Expected a TXT file, received: {path.suffix}"
        )

    text = path.read_text(
        encoding="utf-8"
    ).strip()

    if not text:
        raise ValueError(
            f"Text file is empty: {path}"
        )

    return [
        DocumentRecord(
            text=text,
            source=str(path),
            file_name=path.name,
            file_type="txt",
            page_number=None,
        )
    ]