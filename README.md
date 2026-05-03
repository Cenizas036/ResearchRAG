# 📚 ResearchRAG — Retrieval-Augmented Generation Research Assistant

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![RAG](https://img.shields.io/badge/RAG-Hybrid--Search-orange)

> **Fusion: LLM + Information Retrieval + Vector Databases**

🚀 **[Live Demo on Vercel](https://researchrag-three.vercel.app/)**

![ResearchRAG Interface](docs/screenshot.png)

A production-grade AI-powered Research Assistant web application featuring a stunning atmospheric design, real-time AI capabilities, and interactive UX. 

## 🌐 Architecture Details

### Frontend (Vercel)
- **Framework**: HTML, CSS, Vanilla JS, Vite.
- **Styling**: Custom modern atmospheric design system with glassmorphism, dynamic scrolling effects, scroll-spy navigation, and micro-animations.
- **Hosting**: Deployed seamlessly on Vercel.

### Backend (Hugging Face Spaces)
- **Framework**: FastAPI (Python).
- **AI Integration**: Uses the Hugging Face Free Inference API async client.
- **Model**: `Qwen/Qwen2.5-72B-Instruct` for highly accurate and contextual research answers.
- **Hosting**: Deployed on Hugging Face Spaces for highly available serverless compute.

## ✨ Features

- **Multi-format Ingestion** — PDF, ArXiv, web pages, DOI lookup
- **Hybrid Search** — Dense embeddings (OpenAI/sentence-transformers) + BM25 sparse retrieval
- **Vector Stores** — ChromaDB, FAISS, Pinecone adapters
- **Citation Tracking** — Auto-generates citations with page numbers
- **Multi-hop Reasoning** — Chain-of-thought with iterative retrieval
- **Hallucination Detection** — Cross-references answers with source chunks
- **Conversation Memory** — Context-aware follow-up queries

## 🚀 Quick Start

```bash
pip install -r requirements.txt
python -m src.main ingest --source ./papers/ --type pdf
python -m src.main query "What are the latest advances in RLHF?"
```

## 📦 Structure

```text
ResearchRAG/
├── frontend/
│   ├── index.html        # Main atmospheric landing page
│   ├── src/
│   │   ├── main.js       # App logic and API integration
│   │   └── style.css     # Modern design system
│   ├── public/
│   ├── package.json
│   └── vercel.json
├── api/
│   ├── index.py          # FastAPI backend logic
│   └── requirements.txt  # Python dependencies
├── deploy_hf.py          # Hugging Face deployment script
└── README.md
```
