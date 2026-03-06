from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.quiz.quiz_service import quiz_service
from app.schemas.quiz.request import QuizGenerateRequest, QuizAppendRequest, QuizSubmitRequest
from app.schemas.quiz.response import QuizSessionResponse, QuizResultResponse
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/api/quiz", tags=["Quiz"])


@router.post("/{pdf_id}/generate", response_model=QuizSessionResponse, status_code=201)
async def generate_quiz(
    pdf_id: str,
    body: QuizGenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a quiz for a PDF.
    - question_type: mcq | true_false | fill_in_the_blank
    - difficulty: easy | medium | hard
    - count: 5–20 questions
    - topic: optional focus area (e.g. "sorting algorithms")
    """
    return await quiz_service.generate_quiz(
        db=db,
        pdf_id=pdf_id,
        user_id=body.user_id,
        count=body.count,
        question_type=body.question_type.value,
        difficulty=body.difficulty.value,
        topic=body.topic,
    )


@router.get("/{pdf_id}/list", response_model=list[QuizSessionResponse])
async def list_quizzes(
    pdf_id: str,
    db: AsyncSession = Depends(get_db),
):
    """List all quiz sessions for a PDF."""
    return await quiz_service.list_by_pdf(db, pdf_id)


@router.get("/{quiz_id}", response_model=QuizSessionResponse)
async def get_quiz(
    quiz_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get quiz questions (without correct answers — for active quiz UI)."""
    return await quiz_service.get_quiz(db, quiz_id)


@router.post("/{quiz_id}/append")
async def append_questions(
    quiz_id: str,
    body: QuizAppendRequest,
    db: AsyncSession = Depends(get_db),
):
    """Add more questions to an existing quiz session."""
    return await quiz_service.append_questions(
        db=db,
        quiz_id=quiz_id,
        count=body.count,
        question_type=body.question_type.value if body.question_type else None,
        difficulty=body.difficulty.value if body.difficulty else None,
    )


@router.post("/{quiz_id}/submit", response_model=QuizResultResponse)
async def submit_quiz(
    quiz_id: str,
    body: QuizSubmitRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit answers and get evaluated results.
    Body: { "answers": { "question_id": "user_answer", ... } }
    """
    return await quiz_service.submit_and_evaluate(db, quiz_id, body.answers)


@router.get("/{quiz_id}/result", response_model=QuizResultResponse)
async def get_result(
    quiz_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get the evaluated result for a submitted quiz."""
    return await quiz_service.get_result(db, quiz_id)


@router.delete("/{quiz_id}", response_model=SuccessResponse)
async def delete_quiz(
    quiz_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a quiz session and all its questions/answers."""
    await quiz_service.delete_quiz(db, quiz_id)
    return SuccessResponse(message="Quiz deleted")