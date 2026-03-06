from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from app.models.quiz import QuizSession


class QuizSessionRepo:

    async def create(self, db: AsyncSession, data: dict) -> QuizSession:
        session = QuizSession(**data)
        db.add(session)
        await db.flush()
        await db.refresh(session)
        return session

    async def get_by_id(self, db: AsyncSession, session_id: str) -> QuizSession | None:
        result = await db.execute(
            select(QuizSession)
            .where(QuizSession.id == session_id)
            .options(selectinload(QuizSession.questions))
        )
        return result.scalar_one_or_none()

    async def get_by_pdf(self, db: AsyncSession, pdf_id: str) -> list[QuizSession]:
        result = await db.execute(
            select(QuizSession)
            .where(QuizSession.pdf_id == pdf_id)
            .order_by(QuizSession.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(self, db: AsyncSession, session_id: str, status: str) -> None:
        session = await self.get_by_id(db, session_id)
        if session:
            session.status = status
            await db.flush()

    async def increment_question_count(self, db: AsyncSession, session_id: str, count: int) -> None:
        session = await self.get_by_id(db, session_id)
        if session:
            session.question_count += count
            await db.flush()

    async def delete(self, db: AsyncSession, session_id: str) -> bool:
        result = await db.execute(
            delete(QuizSession).where(QuizSession.id == session_id)
        )
        return result.rowcount > 0


quiz_session_repo = QuizSessionRepo()