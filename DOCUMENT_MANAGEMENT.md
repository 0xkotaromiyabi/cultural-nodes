# Document Category Management - Usage Guide

## Overview

Sistem sekarang memiliki fasilitas lengkap untuk mengelola dokumen berdasarkan kategori sumber (Community, Academic, Media, Archival). Ini memastikan setiap dokumen tersimpan di folder yang tepat untuk ekstraksi metadata epistemik yang akurat.

---

## Folder Structure

```
knowledge_base/
├── community/
│   ├── manifesto/      # Manifesto komunitas
│   └── transcript/     # Transkrip diskusi (default upload)
├── academic/           # Paper & penelitian akademik
├── media/              # Artikel berita & media
├── archival/           # Dokumen arsip
└── general/            # Tidak terkategorisasi
```

---

## Web Interface (Recommended)

### Access

1. Jalankan server:
   ```bash
   cd ~/cultural-nodes
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

2. Buka browser:
   ```
   file:///path/to/cultural-nodes/frontend/manage_knowledge.html
   ```

### Features

 **Drag & Drop Upload** - Seret file langsung ke area upload
 **Visual Source Cards** - Pilih kategori dengan klik card
 **Real-time Feedback** - Status upload dan error handling
 **Text Input** - Input teks langsung tanpa file
 **Auto-categorization** - File otomatis tersimpan ke folder yang sesuai

### How to Use

**Upload File:**
1. Pilih kategori sumber (Community/Academic/Media/Archival)
2. Drag & drop file atau klik area untuk browse
3. Opsional: tambah tag kategori (contoh: "teknologi", "budaya")
4. Klik "Upload & Ingest"

**Input Text:**
1. Switch ke tab "Input Text"
2. Pilih kategori sumber
3. Isi judul dan konten teks
4. Klik "Ingest Text"

---

##  API Endpoints

### 1. Upload File dengan Kategori

**Endpoint:** `POST /api/ingest/file`

**Form Data:**
- `file`: File to upload (PDF, MD, TXT)
- `source_type`: `community` | `academic` | `media` | `archival` | `general`
- `category`: Tag kategori (optional)

**Example (curl):**
```bash
curl -X POST http://localhost:8000/api/ingest/file \
  -F "file=@paper.pdf" \
  -F "source_type=academic" \
  -F "category=teknologi"
```

**Response:**
```json
{
  "status": "success",
  "message": "Ingested 15 chunks",
  "filename": "paper.pdf",
  "source_type": "academic",
  "saved_to": "./knowledge_base/academic/paper.pdf"
}
```

---

### 2. Input Text dengan Kategori

**Endpoint:** `POST /api/ingest/text`

**JSON Body:**
```json
{
  "text": "Konten dokumen...",
  "title": "Judul Dokumen",
  "source_type": "community",
  "category": "manifesto"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/ingest/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Teknologi harus dikembangkan dengan memperhatikan nilai lokal...",
    "title": "Manifesto Teknologi Lokal",
    "source_type": "community",
    "category": "teknologi"
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Ingested 3 chunks",
  "title": "Manifesto Teknologi Lokal",
  "source_type": "community",
  "saved_to": "./knowledge_base/community/manifesto/manifesto-teknologi-lokal.txt"
}
```

---

### 3. Ingest Directory

**Endpoint:** `POST /api/ingest/directory`

**JSON Body:**
```json
{
  "directory_path": "./knowledge_base/academic",
  "source_type": "academic",
  "category": "penelitian",
  "recursive": true
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/ingest/directory \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "./knowledge_base/academic",
    "source_type": "academic",
    "category": "teknologi"
  }'
```

---

##  Source Type Mapping

Setiap `source_type` otomatis mengekstrak metadata epistemik yang berbeda:

| Source Type | Authority Level | Epistemic Origin | Target Folder |
|-------------|-----------------|------------------|---------------|
| `community` | `situated` | `community_archive` | `knowledge_base/community/transcript/` |
| `academic` | `academic` | `academic_research` | `knowledge_base/academic/` |
| `media` | `media` | `media_discourse` | `knowledge_base/media/` |
| `archival` | `archival` | `institutional_record` | `knowledge_base/archival/` |

---

##  Best Practices

### 1. Pilih Source Type yang Tepat

 **Community:**
- Manifesto komunitas
- Transkrip diskusi
- Catatan lokal
- Dokumentasi grassroots

 **Academic:**
- Paper penelitian
- Thesis/disertasi
- Jurnal ilmiah
- Buku akademik

 **Media:**
- Artikel berita
- Blog post
- Wawancara media
- Op-ed

 **Archival:**
- Dokumen resmi
- Arsip institusional
- Laporan historis
- Dokumen pemerintah

### 2. Konsistensi Penamaan

Gunakan nama file yang deskriptif:
- `penelitian-kebudayaan-tanatoraja.pdf`
- `diskusi-cultural-studies.txt`
Jangan gunakan penamaan:
- `doc1.pdf`
- `untitled.txt`

### 3. Tag Kategori

Gunakan tag yang konsisten untuk filtering:
- `teknologi`, `budaya`, `bahasa`, `identitas`
- `politik`, `ekonomi`, `lingkungan`

---

##  Testing the Feature

### Test 1: Upload Academic Paper

```bash
# Via API
curl -X POST http://localhost:8000/api/ingest/file \
  -F "file=@./test_paper.pdf" \
  -F "source_type=academic" \
  -F "category=teknologi"

# Verify file location
ls -l knowledge_base/academic/
```

### Test 2: Input Community Manifesto

```bash
curl -X POST http://localhost:8000/api/ingest/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Teknologi harus dikembangkan bersama komunitas...",
    "title": "Manifesto Tech for People",
    "source_type": "community",
    "category": "manifesto"
  }'

# Verify file created
ls -l knowledge_base/community/manifesto/
```

### Test 3: Verify Metadata

```bash
# Query by source type
curl -X POST http://localhost:8000/api/cultural/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "teknologi",
    "source_type": "community",
    "k": 5
  }'

# Should return only community documents
```

---

##  Verification Checklist

After uploading documents, verify:

- [ ] File tersimpan di folder yang benar (`knowledge_base/{source_type}/`)
- [ ] Curatorial metadata diekstrak (`source_type`, `authority_level`, `epistemic_origin`)
- [ ] Chunks tersimpan di ChromaDB (vector store)
- [ ] Metadata tersimpan di knowledge store (SQLite)
- [ ] Query cultural search berfungsi dengan filter `source_type`

**Quick Check:**
```bash
# Check SQLite database
sqlite3 data/cultural_knowledge.db "SELECT source_type, COUNT(*) FROM documents GROUP BY source_type;"

# Should show counts by source type:
# community|12
# academic|8
# media|5
```

---

##  Integration with Cultural Retrieval

Dokumen yang diupload dengan kategori akan otomatis:

1. **Disimpan ke folder yang tepat** → Curatorial gate mendeteksi source dari path
2. **Diekstrak metadata epistemik** → Authority level & epistemic origin otomatis
3. **Ter-chunk dengan discourse awareness** → Tema dan posisi wacana dideteksi
4. **Tersimpan dual storage** → Vector store + Knowledge store
5. **Bisa diquery dengan filter** → Cultural search support source_type filtering

**Example Cultural Query:**
```python
from app.core.cultural_rag_chain import get_cultural_rag_chain

chain = get_cultural_rag_chain()

# Get only community perspectives
result = chain.invoke_epistemic(
    question="Bagaimana komunitas menggunakan teknologi?",
    source_type="community",
    authority_level="situated"
)

print(result['answer'])
# Answer akan HANYA dari dokumen community yang kamu upload!
```

---

##  Next Steps

1. **Upload Real Documents:** Mulai upload dokumen real ke kategori yang sesuai
2. **Test Cultural Query:** Coba query dengan filter source_type berbeda
3. **Verify Quality:** Check apakah discourse detection dan theme extraction akurat
4. **Iterate:** Adjust theme keywords di `discourse_chunker.py` jika perlu

---

##  Troubleshooting

**File tidak terdeteksi sumbersource:**
- Pastikan menggunakan `source_type` parameter
- Check bahwa folder target sudah ada

**Metadata tidak akurat:**
- Verifikasi file tersimpan di folder yang benar
- Check curatorial gate logic di `curator.py`

**API error:**
- Pastikan server running (`uvicorn app.main:app --reload`)
- Check CORS settings jika akses dari browser

---

Selamat! Sistem Anda sekarang memiliki **Knowledge Base Management** yang lengkap dengan kesadaran epistemik!




