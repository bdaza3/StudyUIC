"""Lightweight abuse controls for the public course assistant API."""

import asyncio
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request


class InProcessRateLimiter:
    """Per-process sliding-window limiter; use shared storage behind multiple workers."""

    def __init__(self) -> None:
        self._hits: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check(self, request: Request, *, limit: int, window_seconds: int = 60) -> None:
        # Use the socket peer address. Do not trust X-Forwarded-For unless a
        # known reverse proxy is configured to overwrite it.
        client_ip = request.client.host if request.client else "unknown"
        key = (request.url.path, client_ip)
        now = time.monotonic()
        async with self._lock:
            hits = self._hits[key]
            while hits and hits[0] <= now - window_seconds:
                hits.popleft()
            if len(hits) >= limit:
                retry_after = max(1, int(window_seconds - (now - hits[0])))
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please wait before trying again.",
                    headers={"Retry-After": str(retry_after)},
                )
            hits.append(now)

            # Bound memory if many distinct clients send requests.
            if len(self._hits) > 10_000:
                expired_before = now - window_seconds
                self._hits = defaultdict(
                    deque,
                    {
                        stored_key: stored_hits
                        for stored_key, stored_hits in self._hits.items()
                        if stored_hits and stored_hits[-1] > expired_before
                    },
                )


chatbot_rate_limiter = InProcessRateLimiter()


async def limit_chatbot_requests(request: Request, *, limit: int) -> None:
    await chatbot_rate_limiter.check(request, limit=limit)


async def limit_answer_requests(request: Request) -> None:
    await limit_chatbot_requests(request, limit=10)


async def limit_search_requests(request: Request) -> None:
    await limit_chatbot_requests(request, limit=30)
