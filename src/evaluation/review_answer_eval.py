import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

AUDIT_FILE = PROJECT_ROOT / "reports/answer_audit.csv"


def save_rows(rows, fieldnames):
    temporary_file = AUDIT_FILE.with_suffix(".csv.tmp")

    with temporary_file.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)

    temporary_file.replace(AUDIT_FILE)


def ask_choice(prompt, allowed):
    while True:
        value = input(prompt).strip().lower()

        if value in allowed:
            return value

        print(
            "Please enter one of:",
            ", ".join(sorted(allowed)),
        )


def main():
    if not AUDIT_FILE.exists():
        raise FileNotFoundError(
            "Run answer evaluation first."
        )

    with AUDIT_FILE.open(
        "r", newline="", encoding="utf-8"
    ) as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
        rows = list(reader)

    for row in rows:
        if row["answer_correct"].strip():
            continue

        print("\n" + "=" * 65)
        print("QUESTION:", row["question_id"])
        print(row["question"])

        print("\nEXPECTED:")
        print(row["expected_answer"])

        print("\nGENERATED:")
        print(row["generated_answer"])

        print("\nSTATUS:")
        print(row["status"])

        print("\nCITED PASSAGES:")
        print(row["cited_passages"] or "None")

        print("\nMANUAL REVIEW")

        is_answerable = (
            row["answerable"].lower() == "true"
        )

        correctness_options = (
            {"yes", "no", "partial"}
            if is_answerable
            else {"yes", "no"}
        )

        row["answer_correct"] = ask_choice(
            "Answer correct? "
            f"({'/'.join(sorted(correctness_options))}): ",
            correctness_options,
        )

        if row["status"] == "answered":
            row["citation_supported"] = ask_choice(
                "Do the cited passages support all "
                "material claims? (yes/no): ",
                {"yes", "no"},
            )
        else:
            row["citation_supported"] = "na"

        row["review_notes"] = input(
            "Review notes (optional): "
        ).strip()

        # Save after every reviewed question.
        save_rows(rows, fieldnames)

        print("Review saved.")

    print("\nReview complete.")
    print("Updated:", AUDIT_FILE)


if __name__ == "__main__":
    main()