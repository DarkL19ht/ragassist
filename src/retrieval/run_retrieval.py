# A Command-Line Retrieval Application

import argparse

from src.retrieval.langchain_pipeline import (
    build_retrieval_chain,
)
from src.retrieval.langchain_retriever import (
    SemanticRetriever,
)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Retrieve source-grounded context "
            "with LangChain and FAISS."
        )
    )

    parser.add_argument(
        "question",
        type=str,
        help="Question to search for.",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of passages to retrieve.",
    )

    args = parser.parse_args()

    retriever = SemanticRetriever.from_local()

    chain = build_retrieval_chain(
        retriever
    )

    result = chain.invoke(
        {
            "question": args.question,
            "top_k": args.top_k,
        }
    )

    print("\nQUESTION")
    print(result["question"])

    print("\nRETRIEVED DOCUMENTS")
    print(len(result["documents"]))

    print("\nFORMATTED CONTEXT")
    print(result["context"])


if __name__ == "__main__":
    main()