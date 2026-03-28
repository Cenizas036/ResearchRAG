"""
Embedding Engine — Multi-provider embedding generation.
"""

import logging
from typing import Optional

logger = logging.getLogger("ResearchRAG.Embeddings")


class EmbeddingEngine:
    """Generates embeddings using OpenAI, sentence-transformers, or local models."""

    def __init__(self, provider: str = "openai", model: str = "text-embedding-3-small"):
        self.provider = provider
        self.model = model
        self._client = None

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        if self.provider == "openai":
            return await self._openai_embed(text)
        elif self.provider == "local":
            return self._local_embed(text)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    async def embed_chunks(self, chunks: list) -> list[list[float]]:
        """Generate embeddings for multiple chunks."""
        texts = [c.content for c in chunks]

        if self.provider == "openai":
            return await self._openai_embed_batch(texts)
        else:
            return [self._local_embed(t) for t in texts]

    async def _openai_embed(self, text: str) -> list[float]:
        """Generate embedding using OpenAI."""
        try:
            from openai import AsyncOpenAI
            import os
            client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            response = await client.embeddings.create(model=self.model, input=text)
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            return []

    async def _openai_embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch embedding with OpenAI."""
        try:
            from openai import AsyncOpenAI
            import os
            client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            # Process in batches of 100
            all_embeddings = []
            for i in range(0, len(texts), 100):
                batch = texts[i:i+100]
                response = await client.embeddings.create(model=self.model, input=batch)
                all_embeddings.extend([d.embedding for d in response.data])
            return all_embeddings
        except Exception as e:
            logger.error(f"OpenAI batch embedding failed: {e}")
            return [[] for _ in texts]

    def _local_embed(self, text: str) -> list[float]:
        """Generate embedding using sentence-transformers."""
        try:
            from sentence_transformers import SentenceTransformer
            if not self._client:
                self._client = SentenceTransformer("all-MiniLM-L6-v2")
            return self._client.encode(text).tolist()
        except ImportError:
            logger.error("sentence-transformers not installed")
            return []
