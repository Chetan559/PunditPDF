from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger

from app.core.config import get_settings
from app.core.database import create_tables, AsyncSessionLocal
from app.middlewares.cors import add_cors
from app.middlewares.logging import setup_logger, add_request_logging
from app.middlewares.rate_limit import add_rate_limiting
from app.routers.document.routes import router as document_router
from app.routers.chat.routes import router as chat_router

# ── Models in dependency order ────────────────────────────────────────────────
import app.models.user      # noqa: F401
import app.models.pdf       # noqa: F401
import app.models.chunk     # noqa: F401
import app.models.chat      # noqa: F401
import app.models.citation  # noqa: F401
import app.models.quiz      # noqa: F401

settings = get_settings()


async def seed_default_user():
    from sqlalchemy import select
    from app.models.user import User
    async with AsyncSessionLocal() as db:
        exists = await db.execute(select(User).where(User.id == "default_user"))
        if not exists.scalar_one_or_none():
            db.add(User(id="default_user", email="default@local.dev", name="Default User"))
            await db.commit()
            logger.info("Default user seeded")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger()
    logger.info(f"Starting PDF Chat API — env: {settings.APP_ENV}")
    await create_tables()
    await seed_default_user()
    logger.info("Database ready")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="PDF Chat API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

add_cors(app)
add_rate_limiting(app)
add_request_logging(app)

app.include_router(document_router)
app.include_router(chat_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)