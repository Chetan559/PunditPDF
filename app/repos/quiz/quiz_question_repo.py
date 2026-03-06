from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.quiz import QuizQuestion


class QuizQuestionRepo:

    async def create_many(self, db: AsyncSession, records: list[dict]) -> list[QuizQuestion]:
        objs = [QuizQuestion(**r) for r in records]
        db.add_all(objs)
        await db.flush()
        for obj in objs:
            await db.refresh(obj)
        return objs

    async def get_by_session(self, db: AsyncSession, session_id: str) -> list[QuizQuestion]:
        result = await db.execute(
            select(QuizQuestion)
            .where(QuizQuestion.session_id == session_id)
            .order_by(QuizQuestion.question_index)
        )
        return list(result.scalars().all())

    async def get_by_id(self, db: AsyncSession, question_id: str) -> QuizQuestion | None:
        result = await db.execute(
            select(QuizQuestion).where(QuizQuestion.id == question_id)
        )
        return result.scalar_one_or_none()

    async def get_texts_by_session(self, db: AsyncSession, session_id: str) -> list[str]:
        """Return just question texts — used to build exclude list for append."""
        questions = await self.get_by_session(db, session_id)
        return [q.question_text for q in questions]


quiz_question_repo = QuizQuestionRepo()