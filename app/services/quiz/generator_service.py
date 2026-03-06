import json
import re
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.repos.document.vector_repo import vector_repo
from app.repos.quiz.quiz_question_repo import quiz_question_repo
from app.services.llm_service import llm_service
from app.services.prompts.quiz_prompts import build_quiz_prompt


def _clean_json(text: str) -> str:
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    return text.strip()


class GeneratorService:
    """
    Responsible for generating quiz questions from PDF chunks via LLM.
    Called by quiz_service during generate and append flows.
    """

    async def generate_questions(
        self,
        db: AsyncSession,
        pdf_id: str,
        session_id: str,
        count: int,
        question_type: str,
        difficulty: str,
        topic: str | None,
        start_index: int = 0,
        exclude_questions: list[str] | None = None,
    ) -> list:
        exclude_questions = exclude_questions or []

        # Pull chunks from Qdrant
        chunks = await vector_repo.get_all(pdf_id, limit=40)
        if not chunks:
            logger.warning(f"No chunks found for PDF {pdf_id} — cannot generate questions")
            return []

        context = "\n\n".join([
            f"[Page {c['page_number']}] {c['text']}"
            for c in chunks
        ])

        prompt = build_quiz_prompt(
            context=context,
            count=count,
            question_type=question_type,
            difficulty=difficulty,
            topic=topic,
            exclude_questions=exclude_questions,
        )

        logger.info(f"Generating {count} {question_type} ({difficulty}) questions for PDF {pdf_id}...")
        raw = await llm_service.generate_groq(
            prompt,
            system="You are a quiz generator. Return only valid JSON.",
        )

        try:
            data = json.loads(_clean_json(raw))
            raw_questions = data.get("questions", [])
        except json.JSONDecodeError:
            logger.error(f"Failed to parse quiz JSON: {raw[:300]}")
            return []

        if not raw_questions:
            logger.warning("LLM returned 0 questions")
            return []

        records = [
            {
                "session_id": session_id,
                "question_index": start_index + i,
                "question_text": q.get("question_text", ""),
                "question_type": q.get("question_type", question_type),
                "difficulty": q.get("difficulty", difficulty),
                "options": q.get("options"),
                "correct_answer": q.get("correct_answer", ""),
                "explanation": q.get("explanation"),
                "source_page": q.get("source_page"),
            }
            for i, q in enumerate(raw_questions)
        ]

        saved = await quiz_question_repo.create_many(db, records)
        logger.info(f"Saved {len(saved)} questions for session {session_id}")
        return saved


generator_service = GeneratorService()