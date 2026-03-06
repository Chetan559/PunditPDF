from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.repos.document.vector_repo import vector_repo
from app.core.config import get_settings

settings = get_settings()

MIN_SCORE = 0.3   # below this score, results are likely noise


class Retriever:

    async def retrieve(
        self,
        db: AsyncSession,
        pdf_id: str,
        query: str,
        top_k: int | None = None,
    ) -> list[dict]:
        """
        Hybrid retrieval:
        1. Vector search via ChromaDB
        2. If confidence is low → supplement with keyword search from Postgres
        3. Deduplicate and return sorted by score
        """
        k = top_k or settings.TOP_K_RETRIEVAL

        vector_results = await vector_repo.query(pdf_id, query, top_k=k)
        logger.debug(f"Vector search: {len(vector_results)} results for '{query[:50]}'")

        high_conf = [r for r in vector_results if r["score"] >= MIN_SCORE]

        if len(high_conf) >= 2:
            return sorted(high_conf, key=lambda x: x["score"], reverse=True)

        # Low confidence — fall back to keyword search
        logger.info(f"Low confidence results for PDF {pdf_id}, running keyword fallback")
        keyword_results = await self._keyword_search(db, pdf_id, query, top_k=k)

        return self._merge(vector_results, keyword_results, top_k=k)

    async def _keyword_search(
        self,
        db: AsyncSession,
        pdf_id: str,
        query: str,
        top_k: int,
    ) -> list[dict]:
        from sqlalchemy import select, or_
        from app.models.chunk import Chunk

        keywords = [w.strip() for w in query.split() if len(w.strip()) > 3]
        if not keywords:
            return []

        conditions = [Chunk.text.ilike(f"%{kw}%") for kw in keywords[:5]]
        result = await db.execute(
            select(Chunk)
            .where(Chunk.pdf_id == pdf_id)
            .where(or_(*conditions))
            .limit(top_k)
        )
        chunks = result.scalars().all()

        return [
            {
                "chunk_id": c.id,
                "text": c.text,
                "page_number": c.page_number,
                "bbox": c.bbox or {"x0": 0, "y0": 0, "x1": 0, "y1": 0},
                "score": 0.2,
            }
            for c in chunks
        ]

    def _merge(
        self,
        vector: list[dict],
        keyword: list[dict],
        top_k: int,
    ) -> list[dict]:
        seen = set()
        merged = []

        for r in vector:
            if r["chunk_id"] not in seen:
                seen.add(r["chunk_id"])
                merged.append(r)

        for r in keyword:
            if r["chunk_id"] not in seen:
                seen.add(r["chunk_id"])
                merged.append(r)

        return sorted(merged, key=lambda x: x["score"], reverse=True)[:top_k]


retriever = Retriever()