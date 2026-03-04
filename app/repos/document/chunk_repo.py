from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.chunk import Chunk


class ChunkRepo:

    async def bulk_create(self, db: AsyncSession, chunks: list[dict]) -> list[Chunk]:
        objects = [Chunk(**c) for c in chunks]
        db.add_all(objects)
        await db.flush()
        return objects

    async def get_by_pdf(self, db: AsyncSession, pdf_id: str) -> list[Chunk]:
        result = await db.execute(
            select(Chunk)
            .where(Chunk.pdf_id == pdf_id)
            .order_by(Chunk.chunk_index)
        )
        return list(result.scalars().all())

    async def get_by_vector_id(self, db: AsyncSession, vector_id: str) -> Chunk | None:
        result = await db.execute(select(Chunk).where(Chunk.vector_id == vector_id))
        return result.scalar_one_or_none()

    async def delete_by_pdf(self, db: AsyncSession, pdf_id: str):
        await db.execute(delete(Chunk).where(Chunk.pdf_id == pdf_id))


chunk_repo = ChunkRepo()