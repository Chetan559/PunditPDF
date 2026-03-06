import asyncio
import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger
from app.core.config import get_settings

settings = get_settings()


class VectorRepo:
    def __init__(self):
        # Initialize the sync client eagerly on the main thread.
        # Lazy init inside a run_in_executor thread causes chromadb 1.x
        # to conflict with the running asyncio event loop during first-time
        # setup (SQLite WAL init, HNSW segment loading, etc.).
        self._client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    def _get_collection(self, pdf_id: str):
        return self._client.get_or_create_collection(
            name=f"pdf_{pdf_id}",
            metadata={"hnsw:space": "cosine"},
        )

    # ── Sync helpers — always call via asyncio.to_thread() ────────────────────

    def _add_sync(self, pdf_id: str, chunks: list[dict], embeddings: list[list[float]]):
        collection = self._get_collection(pdf_id)
        collection.add(
            ids=[c["chunk_id"] for c in chunks],
            embeddings=embeddings,
            documents=[c["text"] for c in chunks],
            metadatas=[
                {
                    "page_number": c["page_number"],
                    "x0": c["bbox"].get("x0", 0),
                    "y0": c["bbox"].get("y0", 0),
                    "x1": c["bbox"].get("x1", 0),
                    "y1": c["bbox"].get("y1", 0),
                }
                for c in chunks
            ],
        )
        logger.info(f"ChromaDB: stored {len(chunks)} vectors for PDF {pdf_id}")

    def _query_sync(self, pdf_id: str, embedding: list[float], top_k: int) -> dict | None:
        collection = self._get_collection(pdf_id)
        count = collection.count()
        if count == 0:
            return None
        return collection.query(
            query_embeddings=[embedding],
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"],
        )

    def _delete_sync(self, pdf_id: str):
        try:
            self._client.delete_collection(f"pdf_{pdf_id}")
        except Exception as e:
            logger.warning(f"Could not delete collection pdf_{pdf_id}: {e}")

    def _get_all_sync(self, pdf_id: str, limit: int) -> list[dict]:
        collection = self._get_collection(pdf_id)
        results = collection.get(limit=limit, include=["documents", "metadatas"])
        chunks = []
        for i, cid in enumerate(results["ids"]):
            meta = results["metadatas"][i]
            chunks.append({
                "chunk_id": cid,
                "text": results["documents"][i],
                "page_number": meta["page_number"],
            })
        return sorted(chunks, key=lambda x: x["page_number"])

    # ── Async API — used everywhere in the FastAPI app ────────────────────────

    async def add(self, pdf_id: str, chunks: list[dict]):
        from app.services.embedding_service import embedding_service

        texts = [c["text"] for c in chunks]
        embeddings = await embedding_service.embed_documents(texts)

        logger.info(f"Writing {len(chunks)} vectors to ChromaDB...")
        await asyncio.to_thread(self._add_sync, pdf_id, chunks, embeddings)

    async def query(self, pdf_id: str, query_text: str, top_k: int = 5) -> list[dict]:
        from app.services.embedding_service import embedding_service

        embedding = await embedding_service.embed_query(query_text)
        results = await asyncio.to_thread(self._query_sync, pdf_id, embedding, top_k)

        if not results:
            return []

        chunks = []
        for i, cid in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i]
            chunks.append({
                "chunk_id": cid,
                "text": results["documents"][0][i],
                "page_number": meta["page_number"],
                "bbox": {"x0": meta["x0"], "y0": meta["y0"], "x1": meta["x1"], "y1": meta["y1"]},
                "score": round(1 - results["distances"][0][i], 4),
            })
        return chunks

    async def get_all(self, pdf_id: str, limit: int = 50) -> list[dict]:
        return await asyncio.to_thread(self._get_all_sync, pdf_id, limit)

    async def delete_collection(self, pdf_id: str):
        await asyncio.to_thread(self._delete_sync, pdf_id)
        logger.info(f"Deleted ChromaDB collection for PDF {pdf_id}")


vector_repo = VectorRepo()