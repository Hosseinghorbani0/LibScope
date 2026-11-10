"""API authentication and lightweight abuse protection."""
import hmac
import threading
import time
from collections import defaultdict, deque

from fastapi import Header, HTTPException, Request, status
from libscope.core.config import get_settings

_RATE_WINDOW_SECONDS = 60.0
_RATE_LIMIT_PER_WINDOW = 10
_request_times: dict[str, deque[float]] = defaultdict(deque)
_rate_lock = threading.Lock()


def require_api_key(authorization: str | None = Header(default=None)) -> None:
    settings = get_settings()
    expected = settings.api_key
    if not expected:
        if settings.environment.lower() == "production":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="API authentication is not configured",
            )
        return

    scheme, _, supplied = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not hmac.compare_digest(supplied, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )


def rate_limit_expensive_requests(request: Request) -> None:
    client_host = request.client.host if request.client else "unknown"
    key = f"{client_host}:{request.url.path}"
    now = time.monotonic()
    cutoff = now - _RATE_WINDOW_SECONDS

    with _rate_lock:
        timestamps = _request_times[key]
        while timestamps and timestamps[0] <= cutoff:
            timestamps.popleft()
        if len(timestamps) >= _RATE_LIMIT_PER_WINDOW:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Request limit exceeded; retry shortly",
                headers={"Retry-After": str(int(_RATE_WINDOW_SECONDS))},
            )
        timestamps.append(now)

        stale_keys = [entry for entry, values in _request_times.items() if not values or values[-1] <= cutoff]
        for stale_key in stale_keys:
            _request_times.pop(stale_key, None)
