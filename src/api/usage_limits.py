import time
from collections import deque
from threading import Lock

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class UsageLimitMiddleware(BaseHTTPMiddleware):
    """
    Basic process-wide request limits for a
    small public demonstration application.

    Limits reset after one hour.
    """

    def __init__(
        self,
        app,
        max_answers_per_hour=20,
        max_index_actions_per_hour=12,
    ):
        super().__init__(app)

        self.limits = {
            "answer": max_answers_per_hour,
            "index": max_index_actions_per_hour,
        }

        self.requests = {
            "answer": deque(),
            "index": deque(),
        }

        self.lock = Lock()

    async def dispatch(self, request: Request, call_next):
        if request.method != "POST":
            return await call_next(request)

        path = request.url.path.rstrip("/")

        if path in {"/ask", "/workspaces/ask"}:
            category = "answer"

        elif path in {
            "/workspaces",
            "/workspaces/documents",
            "/workspaces/text",
        }:
            category = "index"

        else:
            return await call_next(request)

        now = time.monotonic()
        window = 3600

        with self.lock:
            timestamps = self.requests[category]

            while (
                timestamps
                and now - timestamps[0] >= window
            ):
                timestamps.popleft()

            if len(timestamps) >= self.limits[category]:
                retry_after = max(
                    1,
                    int(window - (now - timestamps[0])) + 1,
                )

                return JSONResponse(
                    status_code=429,
                    headers={
                        "Retry-After": str(retry_after),
                    },
                    content={
                        "detail": (
                            "The demonstration has reached "
                            "its temporary usage limit. "
                            "Please try again later."
                        )
                    },
                )

            timestamps.append(now)

        return await call_next(request)