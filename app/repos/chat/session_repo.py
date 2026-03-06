from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.chat import ChatSession


class SessionRepo:

    async def get_by_id(self, db: AsyncSession, session_id: str) -> ChatSession | None:
        result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        db: AsyncSession,
        pdf_id: str,
        user_id: str,
        session_id: str | None,
    ) -> ChatSession:
        # Try existing session first
        if session_id:
            session = await self.get_by_id(db, session_id)
            if session:
                return session

        # Create new session
        session = ChatSession(pdf_id=pdf_id, user_id=user_id)
        db.add(session)
        await db.flush()
        await db.refresh(session)
        return session

    async def delete(self, db: AsyncSession, session_id: str) -> bool:
        session = await self.get_by_id(db, session_id)
        if not session:
            return False
        await db.delete(session)
        return True


session_repo = SessionRepo()