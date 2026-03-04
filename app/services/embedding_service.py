from huggingface_hub import InferenceClient
from loguru import logger
from app.core.config import get_settings

settings = get_settings()

MODEL_NAME = "nomic-ai/nomic-embed-text-v1.5"


class EmbeddingService:
    def __init__(self):
        self._client: InferenceClient | None = None

    def _get_client(self) -> InferenceClient:
        if self._client is None:
            if not settings.HUGGINGFACE_API_KEY:
                raise RuntimeError("HUGGINGFACE_API_KEY is required for embeddings")
            self._client = InferenceClient(token=settings.HUGGINGFACE_API_KEY)
            logger.info(f"HuggingFace InferenceClient ready — model: {MODEL_NAME}")
        return self._client

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Embed document chunks via HF Inference API.
        Nomic requires 'passage:' prefix for documents.
        """
        client = self._get_client()
        prefixed = [f"passage: {t}" for t in texts]
        try:
            result = client.feature_extraction(prefixed, model=MODEL_NAME)
            # result is a nested list: [[emb1], [emb2], ...]
            return [r if isinstance(r[0], float) else r[0] for r in result]
        except Exception as e:
            logger.error(f"Embedding documents failed: {e}")
            raise

    def embed_query(self, text: str) -> list[float]:
        """
        Embed a single query via HF Inference API.
        Nomic requires 'query:' prefix for queries.
        """
        client = self._get_client()
        try:
            result = client.feature_extraction(f"query: {text}", model=MODEL_NAME)
            # result is a single embedding list
            return result[0] if isinstance(result[0], list) else result
        except Exception as e:
            logger.error(f"Embedding query failed: {e}")
            raise


embedding_service = EmbeddingService()