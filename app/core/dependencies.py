from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.config import get_settings, Settings


def get_settings_dep() -> Settings:
    return get_settings()


# ── DB session shorthand ──────────────────────────────────────────────────────

DBSession = Depends(get_db)


# ── User ID ───────────────────────────────────────────────────────────────────
# Placeholder — replace with real JWT auth later.
# Frontend should pass X-User-ID header.

async def get_current_user_id(
    x_user_id: str = Header(default="default_user"),
) -> str:
    """
    Extracts user ID from X-User-ID header.
    Replace this with JWT token parsing when auth is added.
    """
    return x_user_id


CurrentUser = Depends(get_current_user_id)