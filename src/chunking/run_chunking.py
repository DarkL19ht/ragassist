# The chunking runner

import json
from pathlib import Path

from src.chunking.splitter import split_documents
from src.ingestion.schema import DocumentRecord


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "documents.json"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chunks.json"
)


def main():
    if not INPUT_FILE.is_file():
        raise FileNotFoundError(
            "documents.json not found. "
            "Run ingestion first."
        )

    documents_data = json.loads(
        INPUT_FILE.read_text(
            encoding="utf-8"
        )
    )

    records = [
        DocumentRecord(**item)
        for item in documents_data
    ]

    chunks = split_documents(
        records,
        chunk_size=500,
        chunk_overlap=100,
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            [
                chunk.to_dict()
                for chunk in chunks
            ],
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(f"Input documents: {len(records)}")
    print(f"Generated chunks: {len(chunks)}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()