import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime
from app.core.database import Base


class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    pdf_id: Mapped[str] = mapped_column(String, ForeignKey("pdfs.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    question_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    pdf: Mapped["PDF"] = relationship("PDF", back_populates="quiz_sessions")
    user: Mapped["User"] = relationship("User", back_populates="quiz_sessions")
    questions: Mapped[list["QuizQuestion"]] = relationship("QuizQuestion", back_populates="session", cascade="all, delete-orphan")
    answers: Mapped[list["QuizAnswer"]] = relationship("QuizAnswer", back_populates="session", cascade="all, delete-orphan")
    result: Mapped["QuizResult | None"] = relationship("QuizResult", back_populates="session", uselist=False, cascade="all, delete-orphan")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String, ForeignKey("quiz_sessions.id", ondelete="CASCADE"), nullable=False)
    question_index: Mapped[int] = mapped_column(Integer, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(30), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(10), nullable=False)
    options: Mapped[list | None] = mapped_column(JSON)
    correct_answer: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text)
    source_page: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["QuizSession"] = relationship("QuizSession", back_populates="questions")
    answer: Mapped["QuizAnswer | None"] = relationship("QuizAnswer", back_populates="question", uselist=False)


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String, ForeignKey("quiz_sessions.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[str] = mapped_column(String, ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False)
    user_answer: Mapped[str | None] = mapped_column(Text)
    is_correct: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["QuizSession"] = relationship("QuizSession", back_populates="answers")
    question: Mapped["QuizQuestion"] = relationship("QuizQuestion", back_populates="answer")


class QuizResult(Base):
    __tablename__ = "quiz_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String, ForeignKey("quiz_sessions.id", ondelete="CASCADE"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    percentage: Mapped[float] = mapped_column(Float, nullable=False)
    grade: Mapped[str | None] = mapped_column(String(5))
    weak_topics: Mapped[list | None] = mapped_column(JSON)
    recommendation: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["QuizSession"] = relationship("QuizSession", back_populates="result")