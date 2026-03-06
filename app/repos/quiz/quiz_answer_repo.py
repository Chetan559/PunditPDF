from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.quiz import QuizAnswer


class QuizAnswerRepo:

    async def upsert(
        self, db: AsyncSession, session_id: str, answers: dict[str, str]
    ) -> list[QuizAnswer]:
        """Save user answers — overwrites any existing answers for the same question."""
        objs = []
        for question_id, user_answer in answers.items():
            # Delete existing before inserting fresh
            await db.execute(
                delete(QuizAnswer).where(
                    QuizAnswer.session_id == session_id,
                    QuizAnswer.question_id == question_id,
                )
            )
            obj = QuizAnswer(
                session_id=session_id,
                question_id=question_id,
                user_answer=user_answer,
            )
            db.add(obj)
            objs.append(obj)
        await db.flush()
        return objs

    async def mark_correctness(
        self, db: AsyncSession, per_q_map: dict[str, dict]
    ) -> None:
        """
        Set is_correct on each answer after LLM evaluation.
        per_q_map: { question_id: { "is_correct": bool, ... } }
        """
        for question_id, result in per_q_map.items():
            res = await db.execute(
                select(QuizAnswer).where(QuizAnswer.question_id == question_id)
            )
            answer = res.scalar_one_or_none()
            if answer:
                answer.is_correct = result.get("is_correct", False)
        await db.flush()

    async def get_by_session(
        self, db: AsyncSession, session_id: str
    ) -> list[QuizAnswer]:
        result = await db.execute(
            select(QuizAnswer).where(QuizAnswer.session_id == session_id)
        )
        return list(result.scalars().all())

    async def get_as_map(
        self, db: AsyncSession, session_id: str
    ) -> dict[str, "QuizAnswer"]:
        """Returns {question_id: QuizAnswer} for quick lookup."""
        answers = await self.get_by_session(db, session_id)
        return {a.question_id: a for a in answers}


quiz_answer_repo = QuizAnswerRepo()