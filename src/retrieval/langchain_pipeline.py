# The LangChain Pipeline
# Connecting retrieval and formatting with LangChain

from langchain_core.runnables import (
    RunnableLambda,
    RunnablePassthrough,
)

from src.retrieval.context_formatter import (
    format_documents,
)


def build_retrieval_chain(retriever):
    """
    Build a LangChain retrieval pipeline.

    Input:
        {
            "question": str,
            "top_k": int
        }

    Output:
        {
            "question": str,
            "top_k": int,
            "documents": list[Document],
            "context": str
        }
    """

    retrieve_documents = RunnableLambda(
        lambda inputs: retriever.retrieve(
            question=inputs["question"],
            top_k=inputs.get("top_k", 3),
        )
    )

    chain = (
        RunnablePassthrough.assign(
            documents=retrieve_documents
        )
        |
        RunnablePassthrough.assign(
            context=lambda inputs: format_documents(
                inputs["documents"]
            )
        )
    )

    return chain