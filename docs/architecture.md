
flowchart TD
    U[Portfolio visitor] --> CF[Cloudflare Pages]
    CF --> UI[Evidence Workbench]
    UI --> API[FastAPI backend on Render]

    API --> ING[Document ingestion]
    ING --> CH[Text chunking]
    CH --> EMB[Sentence Transformer embeddings]
    EMB --> FAISS[FAISS vector index]

    API --> RET[Semantic retrieval]
    FAISS --> RET
    RET --> LLM[Groq hosted LLM]
    LLM --> OUT[Grounded answer and citations]

    OUT --> API
    API --> UI

Frontend: A static HTML/CSS/JavaScript interface served through Cloudflare Pages. It handles user interactions, displays backend status, and renders answers and retrieved evidence.
Backend: FastAPI handles request validation, document-workspace operations, retrieval, and answer generation.
Retrieval: Sentence Transformers convert document chunks and questions into embeddings. FAISS ranks passages using similarity search.
Generation: The LLM receives retrieved document context and generates a response using the existing grounding instructions and citation-validation logic.
Deployment: Cloudflare serves the frontend independently of Render. This improves page-loading experience but does not eliminate backend cold starts.