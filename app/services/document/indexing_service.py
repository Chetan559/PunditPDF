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
        """
        Embed chunks and store:
        - Vectors in ChromaDB
        - Metadata (text, page, bbox, vector_id) in Postgres

        Returns count of indexed chunks.
        """
        if not raw_chunks:
            return 0

        # Assign IDs
        chunks_with_ids = [
            {**chunk, "chunk_id": str(uuid.uuid4())}
            for chunk in raw_chunks
        ]

        # Store in ChromaDB
        vector_repo.add(pdf_id, chunks_with_ids)
        logger.info(f"Stored {len(chunks_with_ids)} vectors in ChromaDB for PDF {pdf_id}")

        # Store metadata in Postgres
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
        logger.info(f"Stored {len(pg_records)} chunk records in Postgres for PDF {pdf_id}")

        return len(chunks_with_ids)

    def delete_index(self, pdf_id: str):
        """Remove all vectors for a PDF from ChromaDB"""
        vector_repo.delete_collection(pdf_id)
        logger.info(f"Deleted ChromaDB collection for PDF {pdf_id}")


indexing_service = IndexingService()