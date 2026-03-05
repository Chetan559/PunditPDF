import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime
from app.core.database import Base


class Citation(Base):
    __tablename__ = "citations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id: Mapped[str] = mapped_column(String, ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False)
    chunk_id: Mapped[str | None] = mapped_column(String, ForeignKey("pdf_chunks.id", ondelete="SET NULL"))
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox: Mapped[dict] = mapped_column(JSON, nullable=False)
    cited_text: Mapped[str] = mapped_column(Text, nullable=False)
    relevance_score: Mapped[float | None] = mapped_column(Float)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    message: Mapped["ChatMessage"] = relationship("ChatMessage", back_populates="citations")
    chunk: Mapped["Chunk | None"] = relationship("Chunk", back_populates="citations")