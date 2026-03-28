"""
RAG Generator — Generates answers with citations from retrieved chunks.
"""

import logging
import json

logger = logging.getLogger("ResearchRAG.Generator")


class RAGGenerator:
    """Generates grounded answers from retrieved context chunks."""

    def __init__(self, model: str = "gpt-4o", temperature: float = 0.1):
        self.model = model
        self.temperature = temperature

    async def generate(self, question: str, chunks: list) -> dict:
        """Generate answer from retrieved chunks."""
        context = self._build_context(chunks)

        prompt = f"""You are a research assistant. Answer the following question based ONLY on the provided context.
If the context doesn't contain enough information, say so clearly.
Include inline citations using [1], [2], etc. referencing the source chunks.

CONTEXT:
{context}

QUESTION: {question}

Provide:
1. A comprehensive answer with inline citations
2. A confidence score (0.0-1.0) based on context relevance
3. Key entities and concepts mentioned

Format your response as JSON:
{{
    "response": "your detailed answer with [1] citations",
    "confidence": 0.85,
    "key_concepts": ["concept1", "concept2"],
    "citations_used": [1, 2, 3]
}}"""

        try:
            from openai import AsyncOpenAI
            import os
            client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=2000,
            )
            content = response.choices[0].message.content
            result = json.loads(content)
            result["citations"] = self._build_citations(chunks, result.get("citations_used", []))
            return result
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return {"response": f"Generation failed: {e}", "confidence": 0.0}

    async def multi_hop_generate(self, question: str, chunks: list, max_hops: int = 3) -> dict:
        """Multi-hop reasoning: iteratively refine the query and retrieve more context."""
        all_context = list(chunks)
        intermediate_answers = []

        for hop in range(max_hops):
            answer = await self.generate(question, all_context)
            intermediate_answers.append(answer)

            if answer.get("confidence", 0) > 0.85:
                break

            # Generate follow-up query
            follow_up = await self._generate_followup(question, answer)
            if not follow_up:
                break

            # TODO: retrieve more chunks with follow-up query
            logger.info(f"Multi-hop {hop+1}: follow-up query: {follow_up}")

        final = intermediate_answers[-1] if intermediate_answers else {}
        final["hops"] = len(intermediate_answers)
        return final

    async def _generate_followup(self, original_question: str, current_answer: dict) -> str:
        """Generate a follow-up question to fill knowledge gaps."""
        if current_answer.get("confidence", 0) > 0.8:
            return ""

        prompt = f"""Original question: {original_question}
Current answer (confidence: {current_answer.get('confidence', 0)}): {current_answer.get('response', '')[:500]}

What specific follow-up question would help fill the knowledge gaps? Return just the question."""

        try:
            from openai import AsyncOpenAI
            import os
            client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return ""

    def _build_context(self, chunks: list) -> str:
        """Build context string from chunks."""
        parts = []
        for i, chunk in enumerate(chunks):
            source = getattr(chunk, "metadata", {}).get("source_file", "Unknown")
            page = getattr(chunk, "metadata", {}).get("page", "?")
            content = getattr(chunk, "content", str(chunk))
            parts.append(f"[{i+1}] (Source: {source}, Page: {page})\n{content}")
        return "\n\n---\n\n".join(parts)

    def _build_citations(self, chunks: list, used_indices: list) -> list:
        """Build citation list."""
        citations = []
        for idx in used_indices:
            if 0 < idx <= len(chunks):
                chunk = chunks[idx - 1]
                meta = getattr(chunk, "metadata", {})
                citations.append({
                    "index": idx,
                    "source": meta.get("source_file", meta.get("title", "Unknown")),
                    "page": meta.get("page", "?"),
                })
        return citations


class HallucinationDetector:
    """Detects potential hallucinations by cross-referencing answers with source chunks."""

    def verify(self, answer: dict, chunks: list) -> dict:
        """Verify answer against source chunks."""
        response_text = answer.get("response", "")
        chunk_texts = [getattr(c, "content", str(c)) for c in chunks]
        combined_context = " ".join(chunk_texts).lower()

        # Simple claim verification: check key phrases
        sentences = [s.strip() for s in response_text.split(".") if s.strip()]
        grounded_count = 0
        ungrounded = []

        for sentence in sentences:
            # Remove citation markers
            import re
            clean = re.sub(r'\[\d+\]', '', sentence).strip().lower()
            if len(clean) < 10:
                continue

            # Check if key words appear in context
            words = clean.split()
            key_words = [w for w in words if len(w) > 4]
            if key_words:
                matches = sum(1 for w in key_words if w in combined_context)
                if matches / len(key_words) > 0.3:
                    grounded_count += 1
                else:
                    ungrounded.append(sentence)

        total = grounded_count + len(ungrounded)
        confidence = grounded_count / max(total, 1)

        return {
            "is_grounded": confidence > 0.6,
            "confidence": round(confidence, 3),
            "grounded_claims": grounded_count,
            "ungrounded_claims": len(ungrounded),
            "suspicious_sentences": ungrounded[:3],
        }
