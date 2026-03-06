from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.repos.quiz.quiz_question_repo import quiz_question_repo
from app.repos.quiz.quiz_answer_repo import quiz_answer_repo
from app.utils.constants import calculate_grade


class GradingService:
    """
    Computes score and grade from per-question evaluation results.
    Works with the output of evaluation_service — pure calculation, no LLM calls.
    """

    async def compute_score(
        self,
        db: AsyncSession,
        quiz_id: str,
        answers: dict[str, str],
        per_q_results: list[dict],
    ) -> dict:
        """
        Save answers, mark correctness, compute score.

        per_q_results: [{ question_id, is_correct, explanation }]
        Returns: { score, total, percentage, grade, per_q_map }
        """
        # Save answers
        await quiz_answer_repo.upsert(db, quiz_id, answers)
        await db.flush()

        # Build lookup map
        per_q_map = {r["question_id"]: r for r in per_q_results}

        # Mark correctness on answer rows
        await quiz_answer_repo.mark_correctness(db, per_q_map)

        # Calculate score
        questions = await quiz_question_repo.get_by_session(db, quiz_id)
        total = len(questions)
        score = sum(
            1 for q in questions
            if per_q_map.get(q.id, {}).get("is_correct", False)
        )
        percentage = round((score / total) * 100, 1) if total > 0 else 0.0
        grade = calculate_grade(percentage)

        logger.info(f"Quiz {quiz_id} graded: {score}/{total} = {percentage}% ({grade})")

        return {
            "score": score,
            "total": total,
            "percentage": percentage,
            "grade": grade,
            "per_q_map": per_q_map,
        }

    def build_result_rows(
        self,
        questions: list,
        answers: dict[str, str],
        per_q_map: dict[str, dict],
    ) -> list[dict]:
        """Format per-question result for API response."""
        return [
            {
                "question_id": q.id,
                "question_text": q.question_text,
                "is_correct": per_q_map.get(q.id, {}).get("is_correct", False),
                "user_answer": answers.get(q.id),
                "correct_answer": q.correct_answer,
                "explanation": per_q_map.get(q.id, {}).get("explanation") or q.explanation,
            }
            for q in questions
        ]

    def fallback_grade(self, qa_pairs: list[dict]) -> list[dict]:
        """
        String-match fallback when LLM evaluation fails.
        Returns per_q_results in the same shape as LLM output.
        """
        results = []
        for qa in qa_pairs:
            user = (qa.get("user_answer") or "").strip().lower()
            correct = (qa.get("correct_answer") or "").strip().lower()
            results.append({
                "question_id": qa["question_id"],
                "is_correct": user == correct,
                "explanation": qa.get("explanation", ""),
            })
        return results


grading_service = GradingService()