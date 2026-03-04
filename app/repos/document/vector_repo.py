import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger
from app.core.config import get_settings
from app.services.embedding_service import embedding_service

settings = get_settings()


class VectorRepo:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIR,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._client

    def _collection(self, pdf_id: str):
        return self.client.get_or_create_collection(
            name=f"pdf_{pdf_id}",
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, pdf_id: str, chunks: list[dict]):
        """
        chunks: [{chunk_id, text, page_number, bbox: {x0,y0,x1,y1}}]
        """
        collection = self._collection(pdf_id)
        texts = [c["text"] for c in chunks]
        embeddings = embedding_service.embed_documents(texts)

        collection.add(
            ids=[c["chunk_id"] for c in chunks],
            embeddings=embeddings,
            documents=texts,
            metadatas=[
                {
                    "page_number": c["page_number"],
                    "x0": c["bbox"]["x0"],
                    "y0": c["bbox"]["y0"],
                    "x1": c["bbox"]["x1"],
                    "y1": c["bbox"]["y1"],
                }
                for c in chunks
            ],
        )

    def query(self, pdf_id: str, query_text: str, top_k: int = 5) -> list[dict]:
        """Returns [{chunk_id, text, page_number, bbox, score}]"""
        collection = self._collection(pdf_id)
        count = collection.count()
        if count == 0:
            return []

        embedding = embedding_service.embed_query(query_text)
        results = collection.query(
            query_embeddings=[embedding],
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"],
        )

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

    def get_all(self, pdf_id: str, limit: int = 50) -> list[dict]:
        """Fetch chunks without query — used for quiz generation"""
        collection = self._collection(pdf_id)
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

    def delete_collection(self, pdf_id: str):
        try:
            self.client.delete_collection(f"pdf_{pdf_id}")
        except Exception as e:
            logger.warning(f"Could not delete collection pdf_{pdf_id}: {e}")


vector_repo = VectorRepo()