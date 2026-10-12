import os

from langchain_groq import ChatGroq


DEFAULT_LLM_MODEL = "openai/gpt-oss-20b"


def create_llm(
    model_name: str = DEFAULT_LLM_MODEL,
):
    """
    Create a Groq-hosted language model.
    """

    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError(
            "GROQ_API_KEY is missing. "
            "Add it to your .env file."
        )

    return ChatGroq(
        model=model_name,
        temperature=0,
        max_retries=2,
        timeout=30,
    )