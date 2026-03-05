import uuid
from datetime import datetime
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    pdfs: Mapped[list["PDF"]] = relationship("PDF", back_populates="user", cascade="all, delete-orphan")
    chat_sessions: Mapped[list["ChatSession"]] = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    quiz_sessions: Mapped[list["QuizSession"]] = relationship("QuizSession", back_populates="user", cascade="all, delete-orphan")