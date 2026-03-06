import json
import re
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.repos.quiz.quiz_question_repo import quiz_question_repo
from app.repos.quiz.quiz_answer_repo import quiz_answer_repo
from app.models.quiz import QuizResult
from app.services.llm_service import llm_service
from app.services.prompts.evaluation_prompts import build_evaluation_prompt
from app.services.quiz.grading_service import grading_service
from app.core.database import AsyncSessionLocal


def _clean_json(text: str) -> str:
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    return text.strip()


class EvaluationService:
    """
    Orchestrates answer evaluation:
    1. Sends answers to LLM for intelligent grading
    2. Falls back to string match if LLM fails
    3. Delegates score computation to grading_service
    4. Persists QuizResult
    """

    async def evaluate(
        self,
        db: AsyncSession,
        quiz_id: str,
        answers: dict[str, str],
    ) -> dict:
        questions = await quiz_question_repo.get_by_session(db, quiz_id)

        qa_pairs = [
            {
                "question_id": q.id,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "correct_answer": q.correct_answer,
                "user_answer": answers.get(q.id),
                "explanation": q.explanation,
            }
            for q in questions
        ]

        # LLM evaluation
        per_q_results = await self._llm_evaluate(qa_pairs)

        # Compute score via grading_service
        grading = await grading_service.compute_score(
            db=db,
            quiz_id=quiz_id,
            answers=answers,
            per_q_results=per_q_results,
        )

        # Persist result
        result_obj = QuizResult(
            session_id=quiz_id,
            score=grading["score"],
            total=grading["total"],
            percentage=grading["percentage"],
            grade=grading["grade"],
            weak_topics=per_q_results[0].get("weak_topics", []) if per_q_results else [],
            recommendation="",
        )

        # Extract weak_topics and recommendation from LLM meta if present
        per_q_map = grading["per_q_map"]

        db.add(result_obj)
        await db.flush()

        result_rows = grading_service.build_result_rows(questions, answers, per_q_map)

        return {
            "session_id": quiz_id,
            "score": grading["score"],
            "total": grading["total"],
            "percentage": grading["percentage"],
            "grade": grading["grade"],
            "per_question": result_rows,
            "weak_topics": [],        # populated by recommendation_service after commit
            "recommendation": "",     # same
            "_per_q_map": per_q_map,  # passed to recommendation_service
            "_result_id": result_obj.id,
        }

    async def _llm_evaluate(self, qa_pairs: list[dict]) -> list[dict]:
        prompt = build_evaluation_prompt(qa_pairs)
        try:
            raw = await llm_service.generate_groq(
                prompt,
                system="You are a quiz evaluator. Return only valid JSON.",
            )
            data = json.loads(_clean_json(raw))
            return data.get("per_question", [])
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"LLM evaluation failed, using fallback: {e}")
            return grading_service.fallback_grade(qa_pairs)


evaluation_service = EvaluationService()