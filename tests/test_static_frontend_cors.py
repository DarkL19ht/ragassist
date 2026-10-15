"""Verify a deployed website can make cross-origin API requests."""
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.api.cors_config import configure_cors


def make_client():
    app = FastAPI()
    configure_cors(app, origins=['https://ragassist-demo.pages.dev'])

    @app.get('/health')
    def health():
        return {'status': 'ok'}

    return TestClient(app)


def test_known_origin_is_allowed():
    response = make_client().get('/health', headers={'Origin': 'https://ragassist-demo.pages.dev'})
    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == 'https://ragassist-demo.pages.dev'


def test_unknown_origin_is_not_allowed():
    response = make_client().get('/health', headers={'Origin': 'https://untrusted.example'})
    assert response.status_code == 200
    assert 'access-control-allow-origin' not in response.headers


def test_preflight_for_workspace_upload_headers():
    response = make_client().options('/health', headers={
        'Origin': 'https://ragassist-demo.pages.dev',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'content-type,x-workspace-token',
    })
    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == 'https://ragassist-demo.pages.dev'
    assert 'POST' in response.headers['access-control-allow-methods']
