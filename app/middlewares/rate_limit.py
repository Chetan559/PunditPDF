from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# ── Limiter instance (import this in routers to use @limiter.limit) ───────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


def add_rate_limiting(app: FastAPI):
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ── Per-route limit decorators (import and use in routers) ───────────────────
# Usage in a router:
#
#   from app.middlewares.rate_limit import limiter
#
#   @router.post("/upload")
#   @limiter.limit("10/minute")
#   async def upload(request: Request, ...):
#       ...
#
# Default limits:
UPLOAD_LIMIT    = "10/minute"
CHAT_LIMIT      = "30/minute"
QUIZ_LIMIT      = "20/minute"
GENERAL_LIMIT   = "60/minute"