# Curation Workflow Guide

Panduan lengkap untuk sistem kurasi dan kontribusi pengetahuan pada Cultural-Nodes AI RAG.

## Overview

Sistem ini memperkenalkan **Curation Workflow** untuk memastikan kualitas data yang masuk ke knowledge base. Tidak semua dokumen langsung di-ingest; dokumen harus melalui proses review oleh **Curator**.

### Peran (Roles)

1. **Contributor** (Publik/Anonim)
    - Dapat meng-upload file atau input teks.
    - Dokumen masuk ke status `pending`.
    - Tidak perlu login.
2. **Curator** (Admin)
    - Memiliki akses ke Dashboard khusus.
    - Dapat melihat submission yang `pending`.
    - Melakukan **Approve** (Ingest) atau **Reject**.
    - Membutuhkan login.

---

## Authentication

Saat ini sistem menggunakan autentikasi sederhana untuk Curator.

- **Login Page:** `http://localhost:8000/static/curator_login.html`
- **Username:** `admin`
- **Password:** `admin123`

> [!NOTE]
> Token sesi disimpan di LocalStorage browser.

---

## 🚀 User Guide

### 1. Untuk Contributor (Upload Dokumen)

Siapapun dapat berkontribusi data.

1. Buka **Contribution Portal**:
    `http://localhost:8000/static/manage_knowledge.html`
2. Pilih **Upload File** atau **Input Text**.
3. Pilih **Source Category** yang sesuai (Community, Academic, Media, Archival).
4. Isi **Judul** dan upload file/isi konten.
5. Klik **Submit for Curation**.
    - ✅ Sukses: Muncul pesan "Submission received! Pending curator review."

### 2. Untuk Curator (Review Dokumen)

Hanya kurator yang bisa memproses dokumen masuk.

1. Login di **Curator Login Page**.
2. Anda akan diarahkan ke **Curator Dashboard**:
    `http://localhost:8000/static/curator_dashboard.html`
3. Di tab **Pending Review**, Anda akan melihat daftar submission.
4. **Actions:**
    - **Approve & Ingest**: Dokumen akan diproses oleh sistem RAG, metadata diekstrak, dan masuk ke database vector. Status berubah menjadi `approved`.
    - **Reject**: Dokumen ditolak dan tidak akan diproses. Status berubah menjadi `rejected`.

---

## 🛠️ Technical Details

### Database Schema

Tabel `submissions` di SQLite (`data/cultural_knowledge.db`):

- `id`, `title`, `content`, `status` ('pending'/'approved'/'rejected'), `curator_id`, `created_at`, dll.

### API Endpoints

| Method | Endpoint | Role | Deskripsi |
|--------|----------|------|-----------|
| POST | `/api/auth/login` | Public | Login untuk mendapatkan token |
| POST | `/api/curation/submit` | Public | Submit teks/file baru |
| GET | `/api/curation/submissions` | Curator | List submissions (filter by status) |
| POST | `/api/curation/submissions/{id}/approve` | Curator | Approve & trigger ingestion |
| POST | `/api/curation/submissions/{id}/reject` | Curator | Reject submission |

### Folder Structure

- **Frontend Pages:**
  - `frontend/static/manage_knowledge.html` (Public Portal)
  - `frontend/static/curator_login.html` (Login)
  - `frontend/static/curator_dashboard.html` (Dashboard)
