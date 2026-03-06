from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.quiz import QuizResult, QuizQuestion
from app.repos.quiz.quiz_question_repo import quiz_question_repo
from app.repos.quiz.quiz_answer_repo import quiz_answer_repo
from app.services.llm_service import llm_service
from app.services.prompts.evaluation_prompts import build_recommendation_prompt


class RecommendationService:
    """
    Generates personalized study recommendations after quiz evaluation.
    Identifies weak topics from wrong answers and produces actionable advice.
    """

    async def generate(
        self,
        db: AsyncSession,
        quiz_id: str,
        per_q_map: dict[str, dict],
        percentage: float,
        grade: str,
        pdf_name: str = "",
    ) -> tuple[list[str], str]:
        """
        Returns (weak_topics, recommendation_text).
        Called after evaluation_service — updates QuizResult in place.
        """
        questions = await quiz_question_repo.get_by_session(db, quiz_id)

        # Identify weak topics from wrong answers
        weak_topics = self._identify_weak_topics(questions, per_q_map)

        # Build a short context summary from source pages of wrong questions
        wrong_pages = sorted(set(
            q.source_page for q in questions
            if not per_q_map.get(q.id, {}).get("is_correct", True)
            and q.source_page is not None
        ))
        pdf_summary = (
            f"Document: {pdf_name or 'the uploaded PDF'}. "
            f"Incorrect answers were related to pages: {wrong_pages or 'unknown'}."
        )

        # Generate recommendation via LLM
        recommendation = await self._llm_recommend(
            weak_topics=weak_topics,
            pdf_summary=pdf_summary,
            percentage=percentage,
            grade=grade,
        )

        # Update QuizResult
        result = await db.execute(
            select(QuizResult).where(QuizResult.session_id == quiz_id)
        )
        result_obj = result.scalar_one_or_none()
        if result_obj:
            result_obj.weak_topics = weak_topics
            result_obj.recommendation = recommendation
            await db.flush()

        logger.info(f"Recommendations generated for quiz {quiz_id} — {len(weak_topics)} weak topics")
        return weak_topics, recommendation

    def _identify_weak_topics(
        self,
        questions: list,
        per_q_map: dict[str, dict],
    ) -> list[str]:
        """
        Group wrong answers by difficulty and question_type to surface weak areas.
        Returns a list of human-readable topic labels.
        """
        weak = []
        wrong_by_type: dict[str, int] = {}
        wrong_by_difficulty: dict[str, int] = {}

        for q in questions:
            if not per_q_map.get(q.id, {}).get("is_correct", True):
                wrong_by_type[q.question_type] = wrong_by_type.get(q.question_type, 0) + 1
                wrong_by_difficulty[q.difficulty] = wrong_by_difficulty.get(q.difficulty, 0) + 1

        # Flag question types with >50% wrong
        total_by_type: dict[str, int] = {}
        for q in questions:
            total_by_type[q.question_type] = total_by_type.get(q.question_type, 0) + 1

        for qtype, wrong_count in wrong_by_type.items():
            total = total_by_type.get(qtype, 1)
            if wrong_count / total >= 0.5:
                weak.append(f"{qtype.replace('_', ' ').title()} questions")

        # Flag difficulty levels with majority wrong
        total_by_diff: dict[str, int] = {}
        for q in questions:
            total_by_diff[q.difficulty] = total_by_diff.get(q.difficulty, 0) + 1

        for diff, wrong_count in wrong_by_difficulty.items():
            total = total_by_diff.get(diff, 1)
            if wrong_count / total >= 0.6:
                weak.append(f"{diff.title()} difficulty concepts")

        return weak or ["General comprehension"]

    async def _llm_recommend(
        self,
        weak_topics: list[str],
        pdf_summary: str,
        percentage: float,
        grade: str,
    ) -> str:
        prompt = build_recommendation_prompt(
            weak_topics=weak_topics,
            pdf_summary=pdf_summary,
            percentage=percentage,
            grade=grade,
        )
        try:
            return await llm_service.generate(prompt, lite=True)
        except Exception as e:
            logger.warning(f"Recommendation LLM failed: {e}")
            return (
                f"You scored {percentage}% ({grade}). "
                f"Focus on reviewing: {', '.join(weak_topics)}. "
                "Re-read the relevant sections and retry the quiz."
            )


recommendation_service = RecommendationService()