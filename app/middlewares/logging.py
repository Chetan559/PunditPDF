import sys
import os
import time
from fastapi import FastAPI, Request
from loguru import logger
from app.core.config import get_settings

settings = get_settings()


def setup_logger():
    """Configure loguru — call once at startup."""
    logger.remove()

    # Console
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> — <level>{message}</level>",
    )

    # File with rotation
    if settings.LOG_FILE:
        os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)
        logger.add(
            settings.LOG_FILE,
            level=settings.LOG_LEVEL,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{line} — {message}",
        )

    logger.info(f"Logger ready — level: {settings.LOG_LEVEL}")


def add_request_logging(app: FastAPI):
    """Log method, path, status and duration for every request."""

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 1)

        logger.info(
            f"{request.method} {request.url.path} → {response.status_code} ({duration_ms}ms)"
        )
        return response