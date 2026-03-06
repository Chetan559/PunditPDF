import uuid
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.repos.document.chunk_repo import chunk_repo
from app.repos.document.vector_repo import vector_repo


class IndexingService:

    async def index_chunks(
        self,
        db: AsyncSession,
        pdf_id: str,
        raw_chunks: list[dict],
    ) -> int:
        if not raw_chunks:
            return 0

        chunks_with_ids = [
            {**chunk, "chunk_id": str(uuid.uuid4())}
            for chunk in raw_chunks
        ]

        # Store in ChromaDB
        logger.info(f"Storing {len(chunks_with_ids)} vectors in ChromaDB...")
        try:
            await vector_repo.add(pdf_id, chunks_with_ids)
            logger.info("ChromaDB storage complete")
        except Exception as e:
            logger.error(f"ChromaDB storage failed: {e}")
            raise

        # Store metadata in Postgres
        logger.info("Storing chunk metadata in Postgres...")
        try:
            pg_records = [
                {
                    "id": c["chunk_id"],
                    "pdf_id": pdf_id,
                    "chunk_index": i,
                    "text": c["text"],
                    "page_number": c["page_number"],
                    "bbox": c["bbox"],
                    "vector_id": c["chunk_id"],
                }
                for i, c in enumerate(chunks_with_ids)
            ]
            await chunk_repo.bulk_create(db, pg_records)
            logger.info(f"Postgres storage complete: {len(pg_records)} chunks")
        except Exception as e:
            logger.error(f"Postgres chunk storage failed: {e}")
            raise

        return len(chunks_with_ids)

    async def delete_index(self, pdf_id: str):
        await vector_repo.delete_collection(pdf_id)
        logger.info(f"Deleted ChromaDB collection for PDF {pdf_id}")


indexing_service = IndexingService()