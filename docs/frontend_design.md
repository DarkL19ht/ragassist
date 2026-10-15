# RAGAssist — Interface Design

## Product Direction

RAGAssist uses a document-analysis workbench rather than a conversational support-assistant interface. An editorial layout, restrained typography, dark forest-green navigation, warm paper backgrounds, and lime evidence highlights differentiate the application from chatbot-style experiences.

## Information Architecture

1. **Research desk:** question input, configurable evidence depth, and example policy inquiries.
2. **Research brief:** the generated answer is presented as a reading document, not a chat bubble.
3. **Cited references:** cited source metadata is displayed separately from the text of the answer.
4. **Evidence register:** retrieved source passages are visible and individually indexed without opening another tab.
5. **Status banner:** distinguishes generated answers, unsupported answers, and API errors.

## Technical Integration

The interface is implemented in Gradio and connects through the existing `src/frontend/client.py` to the FastAPI `/ask` and `/retrieve` endpoints. Retrieval and generation remain on the backend. The previous `format_evidence()` and `handle_question()` signatures are preserved for compatibility with the existing test suite.

Custom CSS lives in `src/frontend/styles.css`. Gradio 6 applies application-level CSS through `Blocks.launch(css=...)`.

## Trust and Safety

All LLM answer text, retrieved passage text, filenames, and source IDs are HTML-escaped before being inserted into custom HTML components. Similarity scores are described as ranking signals rather than probabilities or proof of factual support. The product warns users to verify generated claims against retrieved evidence.

## Development Limitations

- The frontend makes separate `/ask` and `/retrieve` requests, which duplicates retrieval work; a combined endpoint is a future optimisation.
- The current index is pre-built; uploads and document-management features are not supported.
- The backend is not authenticated or rate-limited. Keep development ports private.
- The interface renders cited source metadata and retrieved passages but does not independently verify whether cited passages support all generated claims.
