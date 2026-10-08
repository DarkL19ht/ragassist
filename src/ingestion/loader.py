# The unified document loader

# The RAG pipeline should not have to worry about whether a document is PDF or TXT.
# One interface that handles both will be created

from pathlib import Path

from src.ingestion.pdf_loader import load_pdf
from src.ingestion.txt_loader import load_txt


SUPPORTED_EXTENSIONS = {".pdf", ".txt"}


def load_document(file_path):
    """
    Load a supported PDF or TXT document.
    """

    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"Document not found: {path}"
        )

    extension = path.suffix.lower()

    if extension == ".pdf":
        return load_pdf(path)

    if extension == ".txt":
        return load_txt(path)

    raise ValueError(
        f"Unsupported file type: {extension}"
    )


def load_directory(directory_path):
    """
    Load supported files from one directory.
    """

    directory = Path(directory_path)

    if not directory.is_dir():
        raise NotADirectoryError(
            f"Directory not found: {directory}"
        )

    records = []

    for file_path in sorted(directory.iterdir()):
        if (
            file_path.is_file()
            and file_path.suffix.lower()
            in SUPPORTED_EXTENSIONS
        ):
            records.extend(
                load_document(file_path)
            )

    return records