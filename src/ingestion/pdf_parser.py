"""
PDF Parser — Extracts text, tables, and metadata from PDF documents.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger("ResearchRAG.PDFParser")


@dataclass
class Document:
    content: str
    metadata: dict = field(default_factory=dict)
    page_number: int = 0
    source: str = ""
    doc_type: str = "pdf"


class PDFParser:
    """Advanced PDF parsing with layout analysis and table extraction."""

    def __init__(self, extract_tables: bool = True, extract_images: bool = False):
        self.extract_tables = extract_tables
        self.extract_images = extract_images

    def parse(self, file_path: str) -> list[Document]:
        """Parse a PDF file and return structured documents."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        documents = []

        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(path))

            metadata = {
                "title": doc.metadata.get("title", path.stem),
                "author": doc.metadata.get("author", "Unknown"),
                "pages": doc.page_count,
                "source_file": str(path),
            }

            for page_num in range(doc.page_count):
                page = doc[page_num]
                text = page.get_text("text")

                if not text.strip():
                    # Try OCR fallback
                    text = page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)

                if text.strip():
                    documents.append(Document(
                        content=text,
                        metadata={**metadata, "page": page_num + 1},
                        page_number=page_num + 1,
                        source=str(path),
                    ))

                # Extract tables if pdfplumber available
                if self.extract_tables:
                    tables = self._extract_tables_from_page(str(path), page_num)
                    for i, table in enumerate(tables):
                        documents.append(Document(
                            content=table,
                            metadata={**metadata, "page": page_num + 1, "type": "table", "table_index": i},
                            page_number=page_num + 1,
                            source=str(path),
                            doc_type="table",
                        ))

            doc.close()
            logger.info(f"Parsed {path.name}: {len(documents)} document segments")

        except ImportError:
            logger.warning("PyMuPDF not installed, using fallback parser")
            documents = self._fallback_parse(path)

        return documents

    def _extract_tables_from_page(self, file_path: str, page_num: int) -> list[str]:
        """Extract tables from a specific page."""
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                if page_num < len(pdf.pages):
                    page = pdf.pages[page_num]
                    tables = page.extract_tables()
                    result = []
                    for table in tables:
                        rows = []
                        for row in table:
                            cleaned = [str(cell).strip() if cell else "" for cell in row]
                            rows.append(" | ".join(cleaned))
                        result.append("\n".join(rows))
                    return result
        except ImportError:
            pass
        return []

    def _fallback_parse(self, path: Path) -> list[Document]:
        """Fallback parser using pdfminer."""
        try:
            from pdfminer.high_level import extract_text
            text = extract_text(str(path))
            return [Document(content=text, metadata={"source": str(path)}, source=str(path))]
        except ImportError:
            logger.error("No PDF parser available. Install PyMuPDF or pdfminer.six")
            return []


class ArxivFetcher:
    """Fetches papers from ArXiv by ID or search query."""

    BASE_URL = "http://export.arxiv.org/api/query"

    async def fetch_by_id(self, arxiv_id: str) -> Optional[Document]:
        """Fetch a paper by its ArXiv ID."""
        import aiohttp
        async with aiohttp.ClientSession() as session:
            params = {"id_list": arxiv_id}
            async with session.get(self.BASE_URL, params=params) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    return self._parse_arxiv_response(text, arxiv_id)
        return None

    async def search(self, query: str, max_results: int = 10) -> list[Document]:
        """Search ArXiv for papers matching a query."""
        import aiohttp
        async with aiohttp.ClientSession() as session:
            params = {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": max_results,
                "sortBy": "relevance",
            }
            async with session.get(self.BASE_URL, params=params) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    return self._parse_arxiv_search(text)
        return []

    def _parse_arxiv_response(self, xml_text: str, arxiv_id: str) -> Optional[Document]:
        """Parse ArXiv API response."""
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns)
            summary = entry.find("atom:summary", ns)
            authors = entry.findall("atom:author/atom:name", ns)

            return Document(
                content=f"Title: {title.text.strip()}\n\nAbstract: {summary.text.strip()}",
                metadata={
                    "title": title.text.strip(),
                    "authors": [a.text for a in authors],
                    "arxiv_id": arxiv_id,
                    "source": f"https://arxiv.org/abs/{arxiv_id}",
                },
                source=f"arxiv:{arxiv_id}",
                doc_type="arxiv",
            )
        return None

    def _parse_arxiv_search(self, xml_text: str) -> list[Document]:
        """Parse multiple ArXiv search results."""
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        docs = []

        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns)
            summary = entry.find("atom:summary", ns)
            if title is not None and summary is not None:
                docs.append(Document(
                    content=f"Title: {title.text.strip()}\n\nAbstract: {summary.text.strip()}",
                    metadata={"title": title.text.strip()},
                    doc_type="arxiv",
                ))

        return docs
