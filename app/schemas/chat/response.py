from pydantic import BaseModel
from datetime import datetime
from app.schemas.common import BBox


class CitationResponse(BaseModel):
    id: str
    chunk_id: str | None
    page_number: int
    bbox: BBox
    cited_text: str
    relevance_score: float | None
    is_primary: bool


class ChatMessageResponse(BaseModel):
    id: str
    role: str                           # user | assistant
    content: str
    mode: str | None                    # rag | continuation
    follow_up: str | None
    citations: list[CitationResponse]
    created_at: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    session_id: str
    message_id: str
    answer: str
    mode: str                           # rag | continuation
    citations: list[CitationResponse]
    follow_up: str | None


class ChatHistoryResponse(BaseModel):
    session_id: str
    pdf_id: str
    messages: list[ChatMessageResponse]