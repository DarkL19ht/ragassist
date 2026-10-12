import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from src.generation.answer_generator import (
    GroundedAnswerGenerator,
)
from src.generation.llm_provider import (
    create_llm,
)
from src.retrieval.langchain_retriever import (
    SemanticRetriever,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def main():
    load_dotenv(
        PROJECT_ROOT / ".env"
    )

    parser = argparse.ArgumentParser(
        description=(
            "Ask questions about indexed documents."
        )
    )

    parser.add_argument(
        "question",
        type=str,
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
    )

    args = parser.parse_args()

    retriever = SemanticRetriever.from_local()

    llm = create_llm()

    generator = GroundedAnswerGenerator(
        retriever=retriever,
        llm=llm,
    )

    result = generator.answer(
        question=args.question,
        top_k=args.top_k,
    )

    print("\nQUESTION")
    print(result["question"])

    print("\nANSWER")
    print(result["answer"])

    print("\nSTATUS")
    print(result["status"])

    print("\nSOURCES")
    print(
        json.dumps(
            result["sources"],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()