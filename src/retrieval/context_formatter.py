# Context formatter
# This function is deliberately separate from retrieval
# That means the source-citation format can be changed later without changing the embedding model or vector search logic

from langchain_core.documents import Document


def format_documents(
    documents: list[Document],
) -> str:
    """
    Format retrieved documents into source-labelled
    context suitable for a future LLM prompt.
    """

    if not documents:
        return (
            "No relevant document passages "
            "were retrieved."
        )

    formatted = []

    for number, document in enumerate(
        documents,
        start=1,
    ):
        metadata = document.metadata

        filename = metadata.get(
            "file_name",
            "Unknown document",
        )

        page_number = metadata.get(
            "page_number"
        )

        chunk_id = metadata.get(
            "chunk_id",
            "Unknown",
        )

        score = metadata.get("score")

        source_label = (
            f"[Source {number}] {filename}"
        )

        if page_number is not None:
            source_label += (
                f" | Page {page_number}"
            )

        header = [
            source_label,
            f"Chunk ID: {chunk_id}",
        ]

        if score is not None:
            header.append(
                f"Similarity score: {score:.4f}"
            )

        formatted.append(
            "\n".join(header)
            + "\n\n"
            + document.page_content
        )

    return "\n\n---\n\n".join(
        formatted
    )