import asyncio
from google import genai
from google.genai import types
from loguru import logger
from app.core.config import get_settings

settings = get_settings()

# Sync client — runs inside dedicated pipeline thread, no event loop issues
_client = genai.Client(api_key=settings.GEMINI_API_KEY)


class EmbeddingService:

    def embed_documents_sync(self, texts: list[str]) -> list[list[float]]:
        """Called from dedicated pipeline thread — sync is safe here."""
        logger.info(f"Embedding {len(texts)} chunks via Gemini...")
        embeddings = []
        for i, text in enumerate(texts):
            result = _client.models.embed_content(
                model="gemini-embedding-001",
                contents=text,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=768,
                ),
            )
            embeddings.append(list(result.embeddings[0].values))
            if (i + 1) % 10 == 0:
                logger.info(f"  embedded {i + 1}/{len(texts)} chunks")
        logger.info(f"Embedding complete: {len(embeddings)} chunks")
        return embeddings

    def embed_query_sync(self, text: str) -> list[float]:
        result = _client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=768,
            ),
        )
        return list(result.embeddings[0].values)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return await asyncio.to_thread(self.embed_documents_sync, texts)

    # ── Called during chat (main event loop) — wrap in executor ──────────────
    async def embed_query(self, text: str) -> list[float]:
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(
            None, self.embed_query_sync, text
        )


embedding_service = EmbeddingService()