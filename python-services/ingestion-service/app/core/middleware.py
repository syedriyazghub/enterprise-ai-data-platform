"""
Enterprise middleware:
- RequestIDMiddleware: attaches X-Request-ID to every request
- RateLimitMiddleware: Redis-backed sliding-window rate limiter (distributed-safe)
- TenantMiddleware: extracts tenant_id from JWT Bearer token
"""
from __future__ import annotations

import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import structlog

from app.core.config import settings

logger = structlog.get_logger()

_SKIP_PATHS = {"/health", "/metrics", "/docs", "/redoc", "/openapi.json"}


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique X-Request-ID to every request and bind it to log context."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        structlog.contextvars.clear_contextvars()
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Redis-backed sliding-window rate limiter.
    Falls back to in-memory if Redis is unavailable (dev mode).
    """

    def __init__(self, app):
        super().__init__(app)
        self._redis = None
        self._fallback: dict[str, list[float]] = {}

    def _get_redis(self):
        if self._redis is None:
            try:
                import redis as redis_lib
                self._redis = redis_lib.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=1)
                self._redis.ping()
            except Exception:
                self._redis = None
        return self._redis

    async def dispatch(self, request: Request, call_next):
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        client_ip = (request.headers.get("X-Forwarded-For") or "").split(",")[0].strip() \
                    or (request.client.host if request.client else "unknown")

        allowed = self._check_rate_limit(client_ip)
        if not allowed:
            logger.warning("rate_limit_exceeded", client_ip=client_ip)
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please retry after a moment.", "code": "RATE_LIMITED"},
                headers={"Retry-After": str(settings.RATE_LIMIT_WINDOW)},
            )
        return await call_next(request)

    def _check_rate_limit(self, client_ip: str) -> bool:
        r = self._get_redis()
        if r:
            return self._redis_check(r, client_ip)
        return self._memory_check(client_ip)

    def _redis_check(self, r, client_ip: str) -> bool:
        key = f"rl:{client_ip}"
        now = time.time()
        window_start = now - settings.RATE_LIMIT_WINDOW
        pipe = r.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, settings.RATE_LIMIT_WINDOW)
        results = pipe.execute()
        return results[2] <= settings.RATE_LIMIT_REQUESTS

    def _memory_check(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - settings.RATE_LIMIT_WINDOW
        self._fallback[client_ip] = [t for t in self._fallback.get(client_ip, []) if t > window_start]
        if len(self._fallback[client_ip]) >= settings.RATE_LIMIT_REQUESTS:
            return False
        self._fallback[client_ip].append(now)
        return True
