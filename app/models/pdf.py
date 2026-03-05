import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime
from app.core.database import Base


class PDF(Base):
    __tablename__ = "pdfs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer)
    total_pages: Mapped[int | None] = mapped_column(Integer)
    pdf_type: Mapped[str | None] = mapped_column(String(50))
    ocr_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(50), default="queued")
    status_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="pdfs")
    chunks: Mapped[list["Chunk"]] = relationship("Chunk", back_populates="pdf", cascade="all, delete-orphan")
    chat_sessions: Mapped[list["ChatSession"]] = relationship("ChatSession", back_populates="pdf", cascade="all, delete-orphan")
    quiz_sessions: Mapped[list["QuizSession"]] = relationship("QuizSession", back_populates="pdf", cascade="all, delete-orphan")