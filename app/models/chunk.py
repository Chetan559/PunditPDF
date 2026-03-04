import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Chunk(Base):
    __tablename__ = "pdf_chunks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    pdf_id: Mapped[str] = mapped_column(String, ForeignKey("pdfs.id", ondelete="CASCADE"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox: Mapped[dict | None] = mapped_column(JSON)           # {x0, y0, x1, y1}
    vector_id: Mapped[str | None] = mapped_column(String(255))  # ChromaDB reference
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    pdf: Mapped["PDF"] = relationship("PDF", back_populates="chunks")