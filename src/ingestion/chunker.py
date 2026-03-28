"""
Semantic Chunker — Intelligent text chunking with semantic boundary detection.
"""

import re
import logging
from dataclasses import dataclass, field

logger = logging.getLogger("ResearchRAG.Chunker")


@dataclass
class Chunk:
    content: str
    metadata: dict = field(default_factory=dict)
    chunk_id: str = ""
    token_count: int = 0
    embedding: list = field(default_factory=list)


class SemanticChunker:
    """Chunks documents using semantic boundaries rather than fixed windows."""

    def __init__(self, chunk_size: int = 512, overlap: int = 50, respect_paragraphs: bool = True):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.respect_paragraphs = respect_paragraphs

    def chunk(self, documents: list) -> list[Chunk]:
        """Chunk documents into semantically coherent pieces."""
        all_chunks = []
        for doc in documents:
            doc_chunks = self._semantic_split(doc.content, doc.metadata, doc.source)
            all_chunks.extend(doc_chunks)
        return all_chunks

    def _semantic_split(self, text: str, metadata: dict, source: str) -> list[Chunk]:
        """Split text respecting semantic boundaries."""
        # First split by sections/paragraphs
        sections = self._find_sections(text)

        chunks = []
        chunk_idx = 0

        for section in sections:
            if self._estimate_tokens(section) <= self.chunk_size:
                chunks.append(Chunk(
                    content=section.strip(),
                    metadata={**metadata, "chunk_index": chunk_idx},
                    chunk_id=f"{source}:chunk_{chunk_idx}",
                    token_count=self._estimate_tokens(section),
                ))
                chunk_idx += 1
            else:
                # Split large sections with overlap
                sub_chunks = self._split_with_overlap(section, metadata, source, chunk_idx)
                chunks.extend(sub_chunks)
                chunk_idx += len(sub_chunks)

        return chunks

    def _find_sections(self, text: str) -> list[str]:
        """Find natural section boundaries."""
        # Split by headers, double newlines, or other structural markers
        section_patterns = [
            r'\n#{1,6}\s',           # Markdown headers
            r'\n\d+\.\s+[A-Z]',     # Numbered sections
            r'\n[A-Z][A-Z\s]+\n',   # ALL CAPS headers
            r'\n\n\n+',             # Triple+ newlines
        ]

        combined_pattern = '|'.join(f'({p})' for p in section_patterns)
        parts = re.split(combined_pattern, text)
        sections = [p for p in parts if p and p.strip()]

        # Merge very small sections
        merged = []
        current = ""
        for section in sections:
            if self._estimate_tokens(current + section) < self.chunk_size * 0.3:
                current += section
            else:
                if current.strip():
                    merged.append(current)
                current = section
        if current.strip():
            merged.append(current)

        return merged if merged else [text]

    def _split_with_overlap(self, text: str, metadata: dict, source: str, start_idx: int) -> list[Chunk]:
        """Split text with overlap for context preservation."""
        words = text.split()
        chunks = []
        chunk_idx = start_idx
        pos = 0

        while pos < len(words):
            end = min(pos + self.chunk_size, len(words))

            # Try to end at a sentence boundary
            chunk_words = words[pos:end]
            chunk_text = " ".join(chunk_words)

            # Find last sentence boundary
            last_period = max(chunk_text.rfind(". "), chunk_text.rfind(".\n"), chunk_text.rfind("? "), chunk_text.rfind("! "))
            if last_period > len(chunk_text) * 0.5:
                chunk_text = chunk_text[:last_period + 1]
                actual_words = len(chunk_text.split())
            else:
                actual_words = len(chunk_words)

            chunks.append(Chunk(
                content=chunk_text.strip(),
                metadata={**metadata, "chunk_index": chunk_idx},
                chunk_id=f"{source}:chunk_{chunk_idx}",
                token_count=self._estimate_tokens(chunk_text),
            ))
            chunk_idx += 1
            pos += max(actual_words - self.overlap, 1)

        return chunks

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Rough token estimation (1 token ≈ 0.75 words for English)."""
        return int(len(text.split()) / 0.75)
