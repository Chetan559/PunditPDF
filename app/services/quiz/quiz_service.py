from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.quiz.session_service import session_service
from app.services.quiz.evaluation_service import evaluation_service
from app.services.quiz.recommendation_service import recommendation_service
from app.repos.quiz.quiz_question_repo import quiz_question_repo
from app.repos.quiz.quiz_answer_repo import quiz_answer_repo
from app.repos.quiz.quiz_session_repo import quiz_session_repo
from app.core.exceptions import QuizNotFoundError
from app.utils.constants import QuizStatus
from sqlalchemy import select
from app.models.quiz import QuizResult


class QuizService:
    """
    Top-level orchestrator — delegates to:
    - session_service   → create / append / get / list / delete
    - evaluation_service → LLM grading + score computation
    - recommendation_service → weak topics + study advice
    """

    async def generate_quiz(
        self,
        db: AsyncSession,
        pdf_id: str,
        user_id: str,
        count: int,
        question_type: str,
        difficulty: str,
        topic: str | None,
    ) -> dict:
        return await session_service.create(
            db=db,
            pdf_id=pdf_id,
            user_id=user_id,
            count=count,
            question_type=question_type,
            difficulty=difficulty,
            topic=topic,
        )

    async def append_questions(
        self,
        db: AsyncSession,
        quiz_id: str,
        count: int,
        question_type: str | None,
        difficulty: str | None,
    ) -> dict:
        return await session_service.append(
            db=db,
            quiz_id=quiz_id,
            count=count,
            question_type=question_type,
            difficulty=difficulty,
        )

    async def submit_and_evaluate(
        self,
        db: AsyncSession,
        quiz_id: str,
        answers: dict[str, str],
    ) -> dict:
        # 1. Evaluate + grade
        result = await evaluation_service.evaluate(db, quiz_id, answers)

        # 2. Get PDF name for recommendation context
        session = await quiz_session_repo.get_by_id(db, quiz_id)
        pdf_name = session.pdf.name if session and hasattr(session, "pdf") and session.pdf else ""

        # 3. Generate recommendations + update QuizResult
        weak_topics, recommendation = await recommendation_service.generate(
            db=db,
            quiz_id=quiz_id,
            per_q_map=result.pop("_per_q_map"),
            percentage=result["percentage"],
            grade=result["grade"],
            pdf_name=pdf_name,
        )
        result.pop("_result_id", None)

        # 4. Mark session as evaluated
        session = await quiz_session_repo.get_by_id(db, quiz_id)
        if session:
            session.status = QuizStatus.EVALUATED

        await db.commit()

        result["weak_topics"] = weak_topics
        result["recommendation"] = recommendation
        return result

    async def get_quiz(self, db: AsyncSession, quiz_id: str) -> dict:
        return await session_service.get(db, quiz_id)

    async def list_by_pdf(self, db: AsyncSession, pdf_id: str) -> list[dict]:
        return await session_service.list_by_pdf(db, pdf_id)

    async def get_result(self, db: AsyncSession, quiz_id: str) -> dict:
        result = await db.execute(
            select(QuizResult).where(QuizResult.session_id == quiz_id)
        )
        result_obj = result.scalar_one_or_none()
        if not result_obj:
            raise QuizNotFoundError(quiz_id)

        questions = await quiz_question_repo.get_by_session(db, quiz_id)
        answer_map = await quiz_answer_repo.get_as_map(db, quiz_id)

        return {
            "session_id": quiz_id,
            "score": result_obj.score,
            "total": result_obj.total,
            "percentage": result_obj.percentage,
            "grade": result_obj.grade,
            "per_question": [
                {
                    "question_id": q.id,
                    "question_text": q.question_text,
                    "is_correct": answer_map[q.id].is_correct if q.id in answer_map else False,
                    "user_answer": answer_map[q.id].user_answer if q.id in answer_map else None,
                    "correct_answer": q.correct_answer,
                    "explanation": q.explanation,
                }
                for q in questions
            ],
            "weak_topics": result_obj.weak_topics or [],
            "recommendation": result_obj.recommendation or "",
        }

    async def delete_quiz(self, db: AsyncSession, quiz_id: str) -> None:
        await session_service.delete(db, quiz_id)


quiz_service = QuizService()