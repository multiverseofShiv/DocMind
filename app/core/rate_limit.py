from __future__ import annotations

from slowapi import Limiter
from fastapi import Request
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

from app.core.config import get_settings


def _key_func(request: Request) -> str:
    api_key = request.headers.get("x-api-key")
    if api_key:
        return f"key: {api_key}"
    return f"ip:{get_remote_address(request)}"

settings = get_settings()
limiter = Limiter(
    key_func= _key_func,
    default_limits=[settings.rate_limit_default],
    storage_uri= settings.redis_url
)

def rate_limit_handler(request: Request, exc:RateLimitExceeded)-> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"}
    )