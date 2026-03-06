from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.chat.request import ChatRequest
from app.schemas.chat.response import ChatResponse, ChatHistoryResponse
from app.schemas.common import SuccessResponse
from app.services.rag.rag_service import rag_service

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("/{pdf_id}", response_model=ChatResponse)
async def chat(
    pdf_id: str,
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message and get an answer with citations.

    - Pass `session_id` to continue an existing conversation.
    - Omit `session_id` to start a new session (returned in response).
    - Citations include `page_number` and `bbox` for frontend highlighting.
    """
    return await rag_service.chat(
        db=db,
        pdf_id=pdf_id,
        message=body.message,
        session_id=body.session_id,
        user_id=body.user_id,
    )


@router.get("/{pdf_id}/history/{session_id}", response_model=ChatHistoryResponse)
async def get_history(
    pdf_id: str,
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get full conversation history with citations for a session."""
    return await rag_service.get_history(db, session_id, pdf_id)


@router.delete("/{pdf_id}/history/{session_id}", response_model=SuccessResponse)
async def clear_history(
    pdf_id: str,
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Clear all messages in a session (keeps session alive)."""
    await rag_service.clear_history(db, session_id)
    return SuccessResponse(message="Chat history cleared")