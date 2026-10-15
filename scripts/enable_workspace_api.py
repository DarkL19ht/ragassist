"""Idempotently register the uploaded-document API in the existing FastAPI app."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "src/api/main.py"
REQUIREMENTS = ROOT / "requirements.txt"
ROUTE_IMPORT = "from src.api.workspace_routes import router as workspace_router"
ROUTE_SETUP = "app.include_router(workspace_router)"


def main():
    if not APP.exists():
        raise FileNotFoundError(f"Existing FastAPI application not found: {APP}")

    source = APP.read_text(encoding="utf-8")
    if "app = FastAPI(" not in source and "app=FastAPI(" not in source:
        raise ValueError(
            "Expected FastAPI app instance named 'app' in src/api/main.py. "
            "Register workspace_router manually if your setup differs."
        )

    if ROUTE_IMPORT not in source or ROUTE_SETUP not in source:
        source += (
            "\n\n# Session-scoped document uploads and question answering.\n"
            + (ROUTE_IMPORT + "\n" if ROUTE_IMPORT not in source else "")
            + (ROUTE_SETUP + "\n" if ROUTE_SETUP not in source else "")
        )
        APP.write_text(source, encoding="utf-8")
        print("Registered document workspace endpoints in src/api/main.py")
    else:
        print("Workspace endpoints are already registered.")

    if REQUIREMENTS.exists():
        requirements = REQUIREMENTS.read_text(encoding="utf-8")
        if not any(
            line.lower().startswith("python-multipart")
            for line in requirements.splitlines()
        ):
            with REQUIREMENTS.open("a", encoding="utf-8") as file:
                if requirements and not requirements.endswith("\n"):
                    file.write("\n")
                file.write("python-multipart\n")
            print("Added python-multipart to requirements.txt")


if __name__ == "__main__":
    main()
