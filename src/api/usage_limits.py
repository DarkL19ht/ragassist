import time
from collections import deque
from threading import Lock

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class UsageLimitMiddleware(BaseHTTPMiddleware):
    """Basic process-wide API usage limits."""

    def __init__(
        self,
        app,
        max_answers_per_hour: int = 20,
        max_index_actions_per_hour: int = 12,
        max_retrievals_per_hour: int = 120,
    ):
        super().__init__(app)

        self.limits = {
            "answer": max_answers_per_hour,
            "index": max_index_actions_per_hour,
            "retrieval": max_retrievals_per_hour,
        }

        if any(limit < 1 for limit in self.limits.values()):
            raise ValueError(
                "Usage limits must be positive integers."
            )

        self.requests = {
            category: deque()
            for category in self.limits
        }

        self.lock = Lock()
        self.window_seconds = 3600

    async def dispatch(self, request: Request, call_next):
        if request.method != "POST":
            return await call_next(request)

        path = request.url.path.rstrip("/") or "/"

        if path in {"/ask", "/workspaces/ask"}:
            category = "answer"

        elif path in {"/retrieve", "/workspaces/retrieve"}:
            category = "retrieval"

        elif path in {
            "/workspaces",
            "/workspaces/documents",
            "/workspaces/text",
        }:
            category = "index"

        else:
            return await call_next(request)

        now = time.monotonic()

        with self.lock:
            timestamps = self.requests[category]

            while (
                timestamps
                and now - timestamps[0] >= self.window_seconds
            ):
                timestamps.popleft()

            if len(timestamps) >= self.limits[category]:
                retry_after = max(
                    1,
                    int(
                        self.window_seconds
                        - (now - timestamps[0])
                    ) + 1,
                )

                return JSONResponse(
                    status_code=429,
                    headers={
                        "Retry-After": str(retry_after),
                        "Cache-Control": "no-store",
                    },
                    content={
                        "detail": (
                            "The public demo is temporarily "
                            "at capacity. Please try again later."
                        )
                    },
                )

            timestamps.append(now)

        return await call_next(request)
