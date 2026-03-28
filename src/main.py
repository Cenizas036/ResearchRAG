"""
ResearchRAG — Retrieval-Augmented Generation Research Assistant
Core pipeline: Ingest → Chunk → Embed → Store → Retrieve → Rerank → Generate → Verify
"""

import click
import asyncio
from pathlib import Path


@click.group()
def cli():
    """ResearchRAG — RAG-powered Research Assistant"""
    pass


@cli.command()
@click.option("--source", "-s", required=True, help="Source path or URL")
@click.option("--type", "src_type", type=click.Choice(["pdf", "arxiv", "web", "dir"]), default="pdf")
@click.option("--chunk-size", default=512, help="Chunk size in tokens")
@click.option("--overlap", default=50, help="Chunk overlap in tokens")
def ingest(source, src_type, chunk_size, overlap):
    """Ingest documents into the vector store."""
    from .ingestion.pdf_parser import PDFParser
    from .ingestion.chunker import SemanticChunker
    from .embeddings.embedding_engine import EmbeddingEngine
    from .vectorstore.chroma_store import ChromaStore

    async def _run():
        parser = PDFParser()
        chunker = SemanticChunker(chunk_size=chunk_size, overlap=overlap)
        embedder = EmbeddingEngine()
        store = ChromaStore()

        if src_type == "dir":
            files = list(Path(source).glob("*.pdf"))
        else:
            files = [Path(source)]

        total_chunks = 0
        for file in files:
            click.echo(f"📄 Processing: {file.name}")
            docs = parser.parse(str(file))
            chunks = chunker.chunk(docs)
            embeddings = await embedder.embed_chunks(chunks)
            store.add(chunks, embeddings)
            total_chunks += len(chunks)
            click.echo(f"   → {len(chunks)} chunks indexed")

        click.echo(f"\n✅ Ingested {len(files)} files, {total_chunks} total chunks")

    asyncio.run(_run())


@cli.command()
@click.argument("question")
@click.option("--top-k", default=10, help="Number of chunks to retrieve")
@click.option("--rerank", is_flag=True, default=True, help="Enable reranking")
@click.option("--verify", is_flag=True, default=True, help="Enable hallucination detection")
@click.option("--multi-hop", is_flag=True, help="Enable multi-hop reasoning")
def query(question, top_k, rerank, verify, multi_hop):
    """Query the knowledge base with natural language."""
    from .retrieval.retriever import HybridRetriever
    from .retrieval.reranker import CrossEncoderReranker
    from .generation.generator import RAGGenerator
    from .generation.hallucination_detector import HallucinationDetector

    async def _run():
        retriever = HybridRetriever(top_k=top_k)
        reranker = CrossEncoderReranker() if rerank else None
        generator = RAGGenerator()
        detector = HallucinationDetector() if verify else None

        # Retrieve
        chunks = await retriever.retrieve(question)
        click.echo(f"📎 Retrieved {len(chunks)} relevant chunks")

        # Rerank
        if reranker and chunks:
            chunks = reranker.rerank(question, chunks)
            chunks = chunks[:5]  # Top 5 after reranking

        # Generate
        if multi_hop:
            answer = await generator.multi_hop_generate(question, chunks)
        else:
            answer = await generator.generate(question, chunks)

        # Verify
        if detector:
            verification = detector.verify(answer, chunks)
            answer["verification"] = verification

        # Output
        click.echo(f"\n{'='*60}")
        click.echo(f"❓ {question}")
        click.echo(f"{'='*60}")
        click.echo(f"\n{answer.get('response', 'No response generated')}")

        if answer.get("citations"):
            click.echo(f"\n📚 Citations:")
            for citation in answer["citations"]:
                click.echo(f"  [{citation['index']}] {citation['source']} (p.{citation.get('page', '?')})")

        if answer.get("verification"):
            v = answer["verification"]
            click.echo(f"\n🔍 Verification: {'✅ Grounded' if v['is_grounded'] else '⚠️ Potential hallucination'}")
            click.echo(f"   Confidence: {v.get('confidence', 0):.0%}")

    asyncio.run(_run())


if __name__ == "__main__":
    cli()
