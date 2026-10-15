"""Allow the dedicated public website to call the FastAPI backend.

CORS is a browser policy, not an authentication or abuse-prevention feature.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def configure_cors(app: FastAPI, *, origins: list[str] | None = None) -> None:
    if origins is None:
        origins = [
            origin.strip().rstrip('/')
            for origin in os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
            if origin.strip()
        ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=['GET', 'POST', 'DELETE', 'OPTIONS'],
        allow_headers=['Content-Type', 'X-Workspace-Token'],
        max_age=600,
    )
