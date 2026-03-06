from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.citation import Citation


class CitationRepo:

    async def bulk_create(self, db: AsyncSession, records: list[dict]) -> list[Citation]:
        citations = [Citation(**r) for r in records]
        db.add_all(citations)
        await db.flush()
        return citations

    async def get_by_message(self, db: AsyncSession, message_id: str) -> list[Citation]:
        result = await db.execute(
            select(Citation)
            .where(Citation.message_id == message_id)
            .order_by(Citation.is_primary.desc(), Citation.relevance_score.desc())
        )
        return list(result.scalars().all())


citation_repo = CitationRepo()