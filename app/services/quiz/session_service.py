from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.repos.quiz.quiz_session_repo import quiz_session_repo
from app.repos.quiz.quiz_question_repo import quiz_question_repo
from app.repos.document.document_repo import document_repo
from app.services.quiz.generator_service import generator_service
from app.core.exceptions import PDFNotFoundError, PDFNotReadyError, QuizNotFoundError
from app.utils.constants import QuizStatus


class SessionService:
    """
    Manages quiz session lifecycle: create, retrieve, append, delete.
    Delegates question generation to generator_service.
    """

    async def create(
        self,
        db: AsyncSession,
        pdf_id: str,
        user_id: str,
        count: int,
        question_type: str,
        difficulty: str,
        topic: str | None,
    ) -> dict:
        pdf = await document_repo.get_by_id(db, pdf_id)
        if not pdf:
            raise PDFNotFoundError(pdf_id)
        if pdf.status != "ready":
            raise PDFNotReadyError(pdf_id, pdf.status)

        session = await quiz_session_repo.create(db, {
            "pdf_id": pdf_id,
            "user_id": user_id,
            "status": QuizStatus.ACTIVE,
            "question_count": 0,
        })
        await db.flush()
        logger.info(f"Quiz session {session.id} created for PDF {pdf_id}")

        questions = await generator_service.generate_questions(
            db=db,
            pdf_id=pdf_id,
            session_id=session.id,
            count=count,
            question_type=question_type,
            difficulty=difficulty,
            topic=topic,
            start_index=0,
            exclude_questions=[],
        )

        session.question_count = len(questions)
        await db.commit()
        return self._format(session, questions)

    async def append(
        self,
        db: AsyncSession,
        quiz_id: str,
        count: int,
        question_type: str | None,
        difficulty: str | None,
    ) -> dict:
        session = await quiz_session_repo.get_by_id(db, quiz_id)
        if not session:
            raise QuizNotFoundError(quiz_id)

        existing = await quiz_question_repo.get_by_session(db, quiz_id)
        exclude = [q.question_text for q in existing]
        first = existing[0] if existing else None
        q_type = question_type or (first.question_type if first else "mcq")
        q_diff = difficulty or (first.difficulty if first else "medium")

        new_questions = await generator_service.generate_questions(
            db=db,
            pdf_id=session.pdf_id,
            session_id=quiz_id,
            count=count,
            question_type=q_type,
            difficulty=q_diff,
            topic=None,
            start_index=len(existing),
            exclude_questions=exclude,
        )

        session.question_count += len(new_questions)
        await db.commit()

        all_questions = await quiz_question_repo.get_by_session(db, quiz_id)
        return {
            "id": quiz_id,
            "question_count": len(all_questions),
            "new_questions_added": len(new_questions),
            "questions": self._format_questions(all_questions),
        }

    async def get(self, db: AsyncSession, quiz_id: str) -> dict:
        session = await quiz_session_repo.get_by_id(db, quiz_id)
        if not session:
            raise QuizNotFoundError(quiz_id)
        questions = await quiz_question_repo.get_by_session(db, quiz_id)
        return self._format(session, questions)

    async def list_by_pdf(self, db: AsyncSession, pdf_id: str) -> list[dict]:
        sessions = await quiz_session_repo.get_by_pdf(db, pdf_id)
        result = []
        for s in sessions:
            questions = await quiz_question_repo.get_by_session(db, s.id)
            result.append(self._format(s, questions))
        return result

    async def delete(self, db: AsyncSession, quiz_id: str) -> None:
        deleted = await quiz_session_repo.delete(db, quiz_id)
        if not deleted:
            raise QuizNotFoundError(quiz_id)
        await db.commit()
        logger.info(f"Quiz session {quiz_id} deleted")

    def _format_questions(self, questions: list) -> list[dict]:
        return [
            {
                "id": q.id,
                "question_index": q.question_index,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "difficulty": q.difficulty,
                "options": q.options,
                "source_page": q.source_page,
            }
            for q in questions
        ]

    def _format(self, session, questions: list) -> dict:
        return {
            "id": session.id,
            "pdf_id": session.pdf_id,
            "status": session.status,
            "question_count": session.question_count,
            "questions": self._format_questions(questions),
            "created_at": session.created_at,
        }


session_service = SessionService()