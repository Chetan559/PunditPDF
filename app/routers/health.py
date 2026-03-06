from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime

from app.core.database import get_db
from app.core.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/health", tags=["Health"])


@router.get("/")
async def health(db: AsyncSession = Depends(get_db)):
    """Full health check — DB connectivity + app status."""
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    return {
        "status": "ok" if db_ok else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "env": settings.APP_ENV,
        "services": {
            "database": "ok" if db_ok else "error",
            "vector_store": "qdrant",
            "llm": "groq/llama-3.3-70b",
            "embeddings": "gemini-embedding-001",
        },
    }


@router.get("/ping")
async def ping():
    """Lightweight liveness check — no DB call."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}