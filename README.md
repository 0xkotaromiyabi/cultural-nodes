# Cultural AI RAG System

AI berbasis RAG (Retrieval-Augmented Generation) untuk **Cultural Studies**, **Sastra**, **Linguistik**, dan **Ilmu Bahasa**. Menggunakan Ollama dengan model llama3.1 untuk generasi teks dan ChromaDB untuk penyimpanan vektor.

## Arsitektur

```
Knowledge Base → Document Loaders → Chunker → Embeddings → ChromaDB
                                                               ↓
User Query → Retriever → Context Assembly → Prompt → Ollama LLM → Response
```

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) terinstall dan running
- Minimal 8GB RAM

## Quick Start

### 1. Setup Environment

```bash
cd ~/cultural-nodes

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Ollama Models

```bash
# Make script executable
chmod +x scripts/setup_ollama.sh

# Run setup (pulls llama3.1 and nomic-embed-text)
./scripts/setup_ollama.sh
```

Atau manual:

```bash
ollama pull llama3.1
ollama pull nomic-embed-text
```

### 3. Ingest Documents

Letakkan dokumen (PDF, MD, TXT) di folder `knowledge_base/`:

```bash
# Ingest seluruh direktori
python scripts/ingest.py --path ./knowledge_base/

# Ingest file spesifik
python scripts/ingest.py --path ./knowledge_base/pdf/teori-budaya.pdf --category cultural

# Ingest dari URL
python scripts/ingest.py --url https://id.wikipedia.org/wiki/Semiotika --category linguistic

# Lihat statistik
python scripts/ingest.py --stats
```

### 4. Start Server

```bash
uvicorn app.main:app --reload
```

Server berjalan di `http://localhost:8000`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Tanya jawab dengan AI |
| `/api/analyze` | POST | Analisis mendalam topik |
| `/api/ingest/text` | POST | Ingest teks |
| `/api/ingest/url` | POST | Ingest dari URL |
| `/api/ingest/file` | POST | Upload & ingest file |
| `/api/search` | POST | Similarity search |
| `/api/stats` | GET | Statistik knowledge base |
| `/api/health` | GET | Health check |

### Contoh Request

**Chat:**

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Apa itu hegemoni menurut Gramsci?"}'
```

**Ingest Text:**

```bash
curl -X POST http://localhost:8000/api/ingest/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Semiotika adalah ilmu tentang tanda...",
    "title": "Pengantar Semiotika",
    "category": "linguistic"
  }'
```

## Interactive Docs

Buka `http://localhost:8000/docs` untuk Swagger UI interaktif.

## Curation & Contribution

System ini memiliki workflow kurasi untuk menjamin kualitas data:

- **Dokumentasi Lengkap:** [CURATION_GUIDE.md](CURATION_GUIDE.md)
- **Contribution Portal:** `http://localhost:8000/static/manage_knowledge.html`
- **Curator Dashboard:** `http://localhost:8000/static/curator_login.html` (Login: `admin`/`admin123`)

## Project Structure

```
cultural-nodes/
├── app/
│   ├── main.py            # FastAPI entry point
│   ├── config.py          # Configuration
│   ├── api/routes.py      # REST endpoints
│   ├── core/
│   │   ├── embeddings.py  # Ollama embeddings
│   │   ├── vectorstore.py # ChromaDB operations
│   │   ├── retriever.py   # Document retrieval
│   │   ├── llm.py         # Ollama LLM
│   │   └── rag_chain.py   # RAG pipeline
│   ├── ingestion/
│   │   ├── loaders.py     # Document loaders
│   │   ├── chunker.py     # Text chunking
│   │   └── pipeline.py    # Ingestion orchestration
│   └── prompts/
│       └── templates.py   # Prompt templates
├── knowledge_base/        # Your documents here
├── data/chroma/           # Vector database
├── scripts/
│   ├── ingest.py          # CLI ingestion tool
│   └── setup_ollama.sh    # Ollama setup
├── requirements.txt
└── .env
```

## Configuration

Edit `.env` untuk kustomisasi:

```env
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.1
EMBEDDING_MODEL=nomic-embed-text
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

## License

MIT
