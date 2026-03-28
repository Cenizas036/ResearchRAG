"""
Hybrid Search — Combines dense embeddings with BM25 sparse retrieval.
"""

import math
import logging
from collections import Counter
from dataclasses import dataclass

logger = logging.getLogger("ResearchRAG.HybridSearch")


@dataclass
class SearchResult:
    chunk_id: str
    content: str
    score: float
    metadata: dict
    source: str = "unknown"


class BM25:
    """BM25 sparse retrieval implementation."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus: list[list[str]] = []
        self.doc_freqs: dict[str, int] = {}
        self.avg_dl: float = 0
        self.doc_lengths: list[int] = []
        self.idf: dict[str, float] = {}
        self.n_docs: int = 0

    def fit(self, corpus: list[str]):
        """Index the corpus."""
        self.corpus = [doc.lower().split() for doc in corpus]
        self.n_docs = len(self.corpus)
        self.doc_lengths = [len(doc) for doc in self.corpus]
        self.avg_dl = sum(self.doc_lengths) / max(self.n_docs, 1)

        # Calculate document frequencies
        self.doc_freqs = {}
        for doc in self.corpus:
            unique_terms = set(doc)
            for term in unique_terms:
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

        # Calculate IDF
        self.idf = {}
        for term, df in self.doc_freqs.items():
            self.idf[term] = math.log((self.n_docs - df + 0.5) / (df + 0.5) + 1)

    def search(self, query: str, top_k: int = 10) -> list[tuple[int, float]]:
        """Search the corpus."""
        query_terms = query.lower().split()
        scores = []

        for idx, doc in enumerate(self.corpus):
            score = 0.0
            dl = self.doc_lengths[idx]
            tf_counter = Counter(doc)

            for term in query_terms:
                if term not in self.idf:
                    continue
                tf = tf_counter.get(term, 0)
                idf = self.idf[term]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * dl / self.avg_dl)
                score += idf * numerator / denominator

            scores.append((idx, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class HybridSearchEngine:
    """Combines dense vector search with BM25 sparse retrieval."""

    def __init__(self, dense_weight: float = 0.6, sparse_weight: float = 0.4):
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        self.bm25 = BM25()
        self.chunks: list = []

    def index(self, chunks: list, embeddings: list):
        """Index chunks for hybrid search."""
        self.chunks = chunks
        texts = [c.content for c in chunks]
        self.bm25.fit(texts)
        logger.info(f"Indexed {len(chunks)} chunks for hybrid search")

    def search(self, query: str, query_embedding: list, top_k: int = 10) -> list[SearchResult]:
        """Perform hybrid search combining dense and sparse signals."""
        # BM25 sparse search
        sparse_results = self.bm25.search(query, top_k=top_k * 2)
        sparse_scores = {idx: score for idx, score in sparse_results}

        # Normalize sparse scores
        max_sparse = max((s for _, s in sparse_results), default=1.0) or 1.0
        sparse_scores = {k: v / max_sparse for k, v in sparse_scores.items()}

        # Dense search (cosine similarity)
        dense_scores = {}
        for idx, chunk in enumerate(self.chunks):
            if chunk.embedding:
                sim = self._cosine_similarity(query_embedding, chunk.embedding)
                dense_scores[idx] = sim

        # Normalize dense scores
        max_dense = max(dense_scores.values(), default=1.0) or 1.0
        dense_scores = {k: v / max_dense for k, v in dense_scores.items()}

        # Combine scores
        all_indices = set(sparse_scores.keys()) | set(dense_scores.keys())
        combined = []
        for idx in all_indices:
            score = (self.dense_weight * dense_scores.get(idx, 0.0) +
                     self.sparse_weight * sparse_scores.get(idx, 0.0))
            chunk = self.chunks[idx]
            combined.append(SearchResult(
                chunk_id=chunk.chunk_id,
                content=chunk.content,
                score=score,
                metadata=chunk.metadata,
            ))

        combined.sort(key=lambda x: x.score, reverse=True)
        return combined[:top_k]

    @staticmethod
    def _cosine_similarity(a: list, b: list) -> float:
        """Calculate cosine similarity between two vectors."""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x ** 2 for x in a))
        norm_b = math.sqrt(sum(x ** 2 for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
