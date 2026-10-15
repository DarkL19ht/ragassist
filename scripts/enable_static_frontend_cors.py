"""Idempotently install static-site CORS support into the existing API."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
api_file = root / 'src' / 'api' / 'main.py'
import_line = 'from src.api.cors_config import configure_cors'
setup_line = 'configure_cors(app)'

if not api_file.exists():
    raise SystemExit(f'Cannot find {api_file}; run from the RAGAssist repository root.')

source = api_file.read_text(encoding='utf-8')
if 'app = FastAPI(' not in source and 'app=FastAPI(' not in source:
    raise SystemExit('Expected app = FastAPI(...) in src/api/main.py; install CORS manually.')
if setup_line not in source:
    source += ('\n\n# Accept browser requests from the separate static frontend.\n'
               + (import_line + '\n' if import_line not in source else '')
               + setup_line + '\n')
    api_file.write_text(source, encoding='utf-8')
    print('Added static-frontend CORS configuration to src/api/main.py')
else:
    print('CORS configuration is already present.')
