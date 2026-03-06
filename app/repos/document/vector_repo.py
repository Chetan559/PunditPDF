import uuid
from loguru import logger
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models


class VectorRepo:
    def __init__(self):
        self.client = AsyncQdrantClient(path="./qdrant_db")

    async def _ensure_collection(self, collection_name: str):
        exists = await self.client.collection_exists(collection_name)
        if not exists:
            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=768,
                    distance=models.Distance.COSINE,
                ),
            )

    async def add(self, pdf_id: str, chunks: list[dict]):
        from app.services.embedding_service import embedding_service

        collection_name = f"pdf_{pdf_id}"
        await self._ensure_collection(collection_name)

        texts = [c["text"] for c in chunks]
        embeddings = await embedding_service.embed_documents(texts)

        points = []
        for i, c in enumerate(chunks):
            point_id = c.get("chunk_id") or str(uuid.uuid4())
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=embeddings[i],
                    payload={
                        "text": c["text"],
                        "page_number": int(c.get("page_number", 1)),
                        "bbox": c.get("bbox") or {"x0": 0.0, "y0": 0.0, "x1": 0.0, "y1": 0.0},
                    },
                )
            )

        logger.info(f"Writing {len(points)} vectors to Qdrant...")
        await self.client.upsert(collection_name=collection_name, points=points)
        logger.info(f"Qdrant: stored {len(points)} vectors for PDF {pdf_id}")

    async def query(self, pdf_id: str, query_text: str, top_k: int = 5) -> list[dict]:
        from app.services.embedding_service import embedding_service

        collection_name = f"pdf_{pdf_id}"
        if not await self.client.collection_exists(collection_name):
            return []

        embedding = await embedding_service.embed_query(query_text)

        # query_points replaced search() in qdrant-client >= 1.7
        results = await self.client.query_points(
            collection_name=collection_name,
            query=embedding,
            limit=top_k,
            with_payload=True,
        )

        chunks = []
        for hit in results.points:
            chunks.append({
                "chunk_id": str(hit.id),
                "text": hit.payload.get("text", ""),
                "page_number": hit.payload.get("page_number", 1),
                "bbox": hit.payload.get("bbox", {"x0": 0.0, "y0": 0.0, "x1": 0.0, "y1": 0.0}),
                "score": round(hit.score, 4),
            })
        return chunks

    async def get_all(self, pdf_id: str, limit: int = 50) -> list[dict]:
        collection_name = f"pdf_{pdf_id}"
        if not await self.client.collection_exists(collection_name):
            return []

        results, _ = await self.client.scroll(
            collection_name=collection_name,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )
        return sorted([
            {
                "chunk_id": str(hit.id),
                "text": hit.payload.get("text", ""),
                "page_number": hit.payload.get("page_number", 1),
            }
            for hit in results
        ], key=lambda x: x["page_number"])

    async def delete_collection(self, pdf_id: str):
        collection_name = f"pdf_{pdf_id}"
        if await self.client.collection_exists(collection_name):
            await self.client.delete_collection(collection_name=collection_name)
            logger.info(f"Deleted Qdrant collection for PDF {pdf_id}")


vector_repo = VectorRepo()