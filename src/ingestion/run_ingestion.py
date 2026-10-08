# Export the Extracted Documents
# Saving the extracted text as JSON so that future stages can reuse it

import json
from pathlib import Path

from src.ingestion.loader import load_directory


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "sample_docs"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "documents.json"
)


def main():
    records = load_directory(INPUT_DIRECTORY)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_data = [
        record.to_dict()
        for record in records
    ]

    OUTPUT_FILE.write_text(
        json.dumps(
            output_data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(f"Extracted records: {len(records)}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()