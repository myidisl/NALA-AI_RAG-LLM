# Spesifikasi Teknis — NALA

**Nama Aplikasi:** NALA (*Not Another Lowkey Assistant*)
**Versi Dokumen:** 3.0
**Tanggal:** 2026-09-25
**Status:** Aktif — menggambarkan implementasi sampai Module 29

**Riwayat Perubahan:**

| Versi | Tanggal | Ringkasan |
|---|---|---|
| 1.0 | 2026-09-23 | MVP: chat streaming ke Ollama, windowing konteks, reset, deployment Docker |
| 2.0 | 2026-09-24 | RAG berbasis OpenSearch, halaman upload knowledge base, pipeline ingest (Airflow), switch RAG di UI, persona asisten pegawai perbankan, redesain UI |
| 2.1 | 2026-09-24 | Streaming real-time dari Ollama (`httpx.stream`); folder knowledge base API & Airflow disatukan lewat bind mount `./app/knowledge-base` |
| 3.0 | 2026-09-25 | BM25 & hybrid search (RRF), reranker cross-encoder, evaluasi retrieval & LLM judge, observability Langfuse, database data operasional (Postgres), agent LangGraph dengan tool SOP & SQL, login/sesi, RBAC, audit log, Redis (cache jawaban, antrian ingest RQ, rate limiting), RedisInsight & Adminer, pembaruan UI (bubble, typing indicator, badge tool, lampiran sumber, tema gelap, responsif) |

> Dokumen terkait: [BRD](./BRD.md) · [Panduan Instalasi & Operasional](./panduan-instalasi-dan-operasional.md) · [Keamanan, RBAC & Audit](./keamanan-rbac-audit.md) · [Panduan Pengguna](./panduan-pengguna.md) · [Pengujian](./pengujian.md) · [Riwayat Pengembangan](./riwayat-pengembangan.md)

---

## 1. Ringkasan Sistem

NALA adalah aplikasi web chat berbasis LLM lokal untuk pegawai **PT Nusantara Finance**. Pengguna login, lalu bertanya seputar teknologi, SOP internal, maupun data operasional melalui dua mode:

| Mode | Endpoint | Cara Kerja |
|---|---|---|
| **Chat (RAG)** — default | `POST /chat/stream` | Backend mencari potongan dokumen SOP (vector / BM25 / hybrid, opsional reranking), menyisipkannya sebagai konteks, lalu men-*stream* jawaban Ollama token per token |
| **Agent** — switch "Pakai Agent" | `POST /chat` | Agent LangGraph memutuskan sendiri kapan memanggil tool `cari_dokumen_sop` (RAG) atau `query_data_operasional` (SQL terbatas). Akses tool SQL dibatasi per role (RBAC), setiap request dicatat di audit log, dan jawaban di-*cache* di Redis |

Dokumen knowledge base (`.md`, `.txt`, `.pdf`) diunggah lewat halaman **Knowledge Base**, lalu di-*ingest* di background oleh worker RQ: dipecah menjadi *chunk*, diubah menjadi embedding oleh Ollama, dan disimpan di **OpenSearch**. Data operasional (pengajuan kredit, klaim asuransi) disimpan di **PostgreSQL** dan dapat diinput lewat halaman **Data Operasional**.

Seluruh pemrosesan (LLM, embedding, reranking, penyimpanan) berjalan di infrastruktur sendiri — tidak ada percakapan maupun dokumen yang dikirim ke penyedia pihak ketiga.

---

## 2. Arsitektur

### 2.1 Diagram Komponen

```
                          ┌──────────────────────────── Docker Compose (network default) ───────────────────────────┐
┌──────────┐  HTTP 8000   │ ┌──────────────┐  /api/chat, /api/embed   ┌─────────┐                                   │
│ Browser  │ ───────────> │ │  api         │ ───────────────────────> │ ollama  │  qwen2.5:7b, nomic-embed-text     │
│ (login,  │ <─────────── │ │  FastAPI     │                          └─────────┘                                   │
│  chat,   │  HTML/stream │ │  (main.py)   │ ── k-NN / BM25 ────────> ┌────────────┐ <── dashboards (5601)          │
│  upload, │   /JSON      │ │              │                          │ opensearch │     index "nala-docs"          │
│  data)   │              │ │              │ ── SELECT/INSERT ──────> ┌──────────┐  <── adminer (8081)             │
└──────────┘              │ │              │                          │ postgres │  nala_operasional               │
                          │ │              │ ── cache / rate limit ─> ┌───────┐ <── redisinsight (5540)            │
                          │ │              │ ── enqueue job ────────> │ redis │                                    │
                          │ │              │ ── trace ──────────────> ┌──────────┐ ── langfuse-db (Postgres)       │
                          │ └──────────────┘                          │ langfuse │  UI 3000                        │
                          │ ┌──────────────┐  rq worker ingest  ───── └──────────┘                                  │
                          │ │  worker      │ <─ job ─ redis ;  ingest ─> ollama (embed) ─> opensearch (index)       │
                          │ └──────────────┘                                                                       │
                          │ ┌──────────────┐  DAG ingest_documents (manual) ─> ollama ─> opensearch                │
                          │ │  airflow     │  UI 8080                                                              │
                          │ └──────────────┘                                                                       │
                          └───────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Alur Chat RAG (`POST /chat/stream`)

```
Browser ──> rate limit (Redis) ──> cek sesi ──> retrieval ──────────────┐
                                                 vector : embed ─> k-NN │
                                                 bm25   : match "text"  ├─> [rerank cross-encoder] ─> pilih system prompt
                                                 hybrid : BM25 + k-NN   │         (opsional)            + sisipkan konteks
                                                          digabung RRF ─┘                                    │
Browser <── text/plain (stream token) <── Ollama /api/chat (stream) <────────────────────────────────────────┘
                     └─ trace Langfuse: span retrieval, span rerank, generation llm_generate_stream
```

### 2.3 Alur Agent (`POST /chat`)

```
Browser ──> rate limit ──> sesi (user_id, role) ──> cache Redis (key: pertanyaan+role) ──hit──> audit "cache" ─> response
                                                         │ miss
                                                         v
                     ┌──────────── LangGraph ─────────────────────────────────────┐
                     │ call_model (Ollama /api/chat + ALL_TOOLS)                  │
                     │     │ tool_calls?                                          │
                     │     ├─ ya ─> call_tool ── RBAC: role boleh SQL? ─┐          │
                     │     │          cari_dokumen_sop ─> rag_search     │          │
                     │     │          query_data_operasional ─> Postgres │ (ditolak: "Akses ditolak: ...")
                     │     │        <─ hasil tool + called_tools ────────┘          │
                     │     └─ tidak ─> END (jawaban akhir)                         │
                     └────────────────────────────────────────────────────────────┘
                                   │
                                   v
      audit_log (satu baris per tool) ─> simpan cache ─> ChatResponse {reply, tool_used, sources}
```

### 2.4 Alur Ingest Dokumen

```
POST /upload ─> simpan file ke knowledge-base ─> enqueue job RQ (antrian "ingest") ─> response langsung (job ID)
                                                          │
                          worker: ingest_document_job ────┘
                            extract_text (teks / pypdf) ─> chunk (per heading .md / 500 karakter) ─> embed (Ollama)
                            ─> PUT OpenSearch /nala-docs/_doc/{file}-{i} ─> invalidate_answer_cache()

Airflow DAG ingest_documents (manual) ─> ingest_documents(folder) ─> fungsi ingest yang sama
```

### 2.5 Komponen Kode

| Komponen | File | Tanggung Jawab |
|---|---|---|
| Web server & routing | `app/main.py` | Semua endpoint; retrieval RAG; pemilihan system prompt; streaming; agent, audit, cache, badge, sumber; data operasional; rate limit |
| Autentikasi | `app/auth.py` | User demo, label role, `verify_user()`, `get_current_user()` dari sesi |
| Agent | `app/agent.py` | Graph LangGraph `call_model → call_tool → call_model`; RBAC tool SQL; pencatatan `called_tools` |
| Tool RAG | `app/tools/rag_tool.py` | `cari_dokumen_sop`: hybrid search + rerank, mengembalikan (teks, daftar sumber) |
| Tool SQL | `app/tools/sql_tool.py` | `query_data_operasional`: query SELECT tetap & berparameter (whitelist tabel/mode/status) |
| Ollama client | `app/ollama_client.py` | `chat_stream()`, `chat()` (dengan tools), `generate()` |
| Embedding | `app/embeddings.py` | Teks → vektor via Ollama `/api/embed` (`nomic-embed-text`) |
| Vector store | `app/vector_store.py` | REST OpenSearch: buat index, simpan chunk, k-NN, BM25, hybrid (RRF) |
| Reranker | `app/reranker.py` | Cross-encoder `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| Ingest | `app/ingest.py` | Ekstraksi teks, chunking, embedding, indexing |
| Antrian & job | `app/queue.py`, `app/jobs.py` | Antrian RQ `ingest`; job ingest + invalidasi cache |
| Cache | `app/cache.py` | Cache jawaban Redis per (pertanyaan, role, metode, rerank) |
| Rate limit | `app/rate_limit.py` | Fixed window per (bucket, IP), fail-open |
| Database | `app/db.py` | Koneksi Postgres role `nala_readonly` (baca) dan `nala_writer` (tulis) |
| Audit | `app/audit.py` | `log_audit()` ke tabel `audit_log` dengan role `nala_app` |
| System prompt | `app/system_prompt.py` | Persona NALA + varian (tanpa konteks, RAG mati, agent) |
| Evaluasi | `app/evaluation.py`, `app/llm_judge.py`, `app/run_evaluation.py` | Metrik retrieval (precision@k, hit rate, MRR) dan LLM-as-judge |
| Template | `app/templates/*.html` | `login`, `chat`, `upload`, `data_operasional` |
| Styling | `app/static/style.css` | Semua halaman; token warna, tema gelap, responsif |
| Library frontend lokal | `app/static/vendor/` | `marked` (Markdown) dan `DOMPurify` (sanitasi HTML) — disajikan lokal, tanpa CDN |
| Pipeline Airflow | `airflow/dags/ingest_documents_dag.py` | DAG manual `ingest_documents` |
| Database seed | `db/seed.sql` | Tabel, data contoh, role database |
| Kontainerisasi | `app/Dockerfile`, `docker-compose.yml` | Image api/worker; orkestrasi 12 service |

---

## 3. Teknologi yang Digunakan

| Kategori | Teknologi | Versi |
|---|---|---|
| Bahasa | Python | 3.12 |
| Web framework / ASGI | FastAPI / Uvicorn / Starlette | 0.141.1 / 0.53.0 / 1.6.0 |
| Sesi | Starlette `SessionMiddleware` + itsdangerous | 2.2.0 |
| HTTP client | httpx | 0.28.1 |
| Template | Jinja2 | 3.1.4 |
| Ekstraksi PDF | pypdf | 5.1.0 |
| Reranker | sentence-transformers (+ torch CPU) | 3.2.1 (torch 2.6.0+cpu) |
| Agent | LangGraph | 0.2.39 |
| Database driver | psycopg (binary) | 3.2.3 |
| Cache & antrian | redis-py / RQ | 5.0.8 / 1.16.2 |
| Observability | Langfuse SDK / server | 2.x / image `langfuse/langfuse:2` |
| LLM runtime | Ollama | latest |
| Model chat & agent | `qwen2.5:7b` (docker-compose) — fallback kode `llama3.2:3b` | — |
| Model embedding | `nomic-embed-text` (768 dimensi) | — |
| Vector store | OpenSearch (k-NN HNSW/nmslib, cosine) + Dashboards | 2.11.0 |
| Database | PostgreSQL | 16 (data operasional), 15-alpine (Langfuse) |
| Cache/queue | Redis | 7-alpine |
| GUI database | Adminer, RedisInsight | latest |
| Pipeline | Apache Airflow (standalone) | 2.10.2 |
| Frontend | HTML + CSS + vanilla JavaScript; marked + DOMPurify (lokal) | — |
| Deployment | Docker + Docker Compose | — |

---

## 4. Spesifikasi API

Semua endpoint selain `/health`, `/login`, dan `/static/*` **wajib login**. Halaman HTML yang diakses tanpa sesi di-*redirect* ke `/login` (303); endpoint JSON (`/chat`, `/chat/stream`) mengembalikan `401`.

### 4.1 Ringkasan Endpoint

| Method | Path | Login | Rate limit | Keterangan |
|---|---|---|---|---|
| GET | `/health` | – | – | Health check proses API |
| GET | `/login` | – | – | Form login; bila sudah login → redirect `/` |
| POST | `/login` | – | – | Verifikasi akun; sukses → set sesi + 303 ke `/`; gagal → 401 |
| GET | `/logout` | – | – | Hapus sesi, redirect `/login` |
| GET | `/` | ✅ | – | Halaman chat |
| POST | `/chat/stream` | ✅ (401) | `chat` 20/menit | Chat RAG streaming |
| POST | `/chat` | ✅ (401) | `chat` 20/menit | Mode agent |
| GET | `/upload` | ✅ | – | Halaman knowledge base |
| POST | `/upload` | ✅ | `upload` 5/menit | Simpan file + enqueue ingest |
| GET | `/data-operasional` | ✅ | – | Form & tabel data operasional (`?kredit_page=&klaim_page=`) |
| POST | `/data-operasional/pengajuan-kredit` | ✅ | `data-operasional` 10/menit | Tambah pengajuan kredit |
| POST | `/data-operasional/klaim-asuransi` | ✅ | `data-operasional` 10/menit | Tambah klaim asuransi |
| GET | `/static/*` | – | – | CSS, logo, library frontend |

Rate limit dihitung **sebelum** pemeriksaan login dan per IP (lihat §9). Melebihi batas → `429` dengan pesan berbahasa Indonesia.

### 4.2 `POST /login`

- **Request:** `application/x-www-form-urlencoded` — `username`, `password`.
- **Sukses:** sesi berisi `user_id`, `role`, `nama`; `303` ke `/`.
- **Gagal:** `401`, halaman login dengan pesan "Username atau password salah."

### 4.3 `POST /chat/stream`

**Request Body:**
```json
{
  "messages": [
    { "role": "user", "content": "Apa syarat pengajuan kredit?" }
  ],
  "use_rag": true,
  "search_method": "hybrid",
  "use_reranking": true
}
```

| Field | Tipe | Default | Keterangan |
|---|---|---|---|
| `messages` | array `{role, content}` | wajib | Seluruh riwayat, urut dari yang terlama; pesan terakhir wajib `user` |
| `use_rag` | boolean | `true` | `false` = lewati pencarian dokumen |
| `search_method` | `"vector"` \| `"bm25"` \| `"hybrid"` | `"hybrid"` | Nilai lain → `422` |
| `use_reranking` | boolean | `true` | Diabaikan bila server `RERANK_ENABLED=false` |

**Validasi:** `messages` kosong atau pesan terakhir bukan `user` → `400`; skema tidak sesuai → `422`; tanpa sesi → `401`.

**Pemrosesan:**
1. Ambil maksimal 10 pesan terakhir (`HISTORY_WINDOW`).
2. Bila `use_rag`: retrieval dengan pertanyaan terakhir.

   | Kondisi | Jumlah kandidat | Konteks ke model |
   |---|---|---|
   | Dengan reranking | 20 | 3 teratas hasil cross-encoder |
   | Tanpa reranking, `hybrid` | 3 | 3 |
   | Tanpa reranking, `bm25`/`vector` | 6 | 6 |

   `hybrid` menggabungkan BM25 dan k-NN (masing-masing 20 kandidat) dengan **Reciprocal Rank Fusion** (`1/(60 + peringkat)`). Error `httpx.HTTPError` → konteks kosong, chat tetap jalan.
3. Pilih system prompt: `NALA_SYSTEM_PROMPT_RAG_OFF` (RAG dimatikan), `SYSTEM_PROMPT` (ada konteks; tiap chunk diberi label `[nama file]`), atau `NALA_SYSTEM_PROMPT_NO_CONTEXT` (RAG aktif tanpa hasil).
4. Stream ke Ollama `/api/chat`; token diteruskan ke browser sebagai `text/plain`.
5. Trace Langfuse `chat_stream` dengan span `retrieval`, `rerank`, dan generation `llm_generate_stream`.

`/chat/stream` **tidak** melakukan audit log, tidak memakai cache, dan tidak memiliki tool SQL.

### 4.4 `POST /chat` (Agent)

**Request Body** (tidak ada field role/user — identitas hanya dari sesi):
```json
{ "message": "Berapa pengajuan kredit yang ditolak?", "history": [] }
```

**Response:**
```json
{
  "reply": "Ada 8 pengajuan kredit berstatus ditolak ...",
  "tool_used": "sql",
  "sources": []
}
```

| Field | Nilai |
|---|---|
| `reply` | Jawaban akhir agent (Markdown) |
| `tool_used` | `"rag"`, `"sql"`, `"mixed"` (keduanya), `"none"`, atau `"cache"`. Hanya tool yang **diizinkan** RBAC yang dihitung |
| `sources` | Nama file dokumen hasil `cari_dokumen_sop` (tanpa duplikat, urutan kemunculan). Kosong untuk jawaban dari cache |

**Pemrosesan:**
1. Rate limit → sesi (`401` bila tidak ada).
2. Bila `history` kosong: cek cache Redis dengan key `sha256(pertanyaan|role|"hybrid"|True)`. Hit → audit `tool_dipanggil="cache"` → response `tool_used="cache"` tanpa menjalankan agent.
3. Bangun agent per request; state awal: system prompt agent + 10 pesan terakhir (riwayat hanya `user`/`assistant`), `role` dari sesi, `called_tools: []`.
4. Setelah agent selesai: satu baris `audit_log` per entri `called_tools` (atau satu baris tanpa tool), simpan jawaban ke cache (hanya bila `history` kosong), hitung `tool_used` dan `sources`.
5. Trace Langfuse `chat_agent` dengan generation `agent_call_model` dan span `agent_tool:<nama>`.

### 4.5 `POST /upload`

- **Request:** `multipart/form-data`, field `file` (`.md`, `.txt`, `.pdf`; lainnya → `400`).
- **Pemrosesan:** nama file disanitasi (`os.path.basename`), file disimpan (menimpa nama yang sama), lalu `ingest_queue.enqueue("app.jobs.ingest_document_job", path)`.
- **Response:** halaman Knowledge Base dengan pesan *"… sedang diproses di background (job ID: …)"*. Bila Redis tidak terjangkau, file tetap tersimpan dan pengguna diminta mengunggah ulang atau menjalankan DAG Airflow.

### 4.6 Data Operasional

- `GET /data-operasional?kredit_page=N&klaim_page=M` — dua tabel dengan paginasi terpisah (10 baris/halaman, terbaru di atas), dibaca dengan role `nala_readonly`.
- `POST /data-operasional/pengajuan-kredit` — field `nasabah_id`, `nama_nasabah`, `jumlah_pengajuan`, `status`, `tanggal_pengajuan`, `alasan_penolakan` (opsional).
- `POST /data-operasional/klaim-asuransi` — field `nasabah_id`, `nama_nasabah`, `jenis_klaim`, `jumlah_klaim`, `status`, `tanggal_klaim`.
- INSERT memakai role `nala_writer` dan parameter `%s`. Pelanggaran constraint → `400`; database tidak terjangkau → `503`.

---

## 5. Agent & Tool

### 5.1 Graph

`call_model` memanggil Ollama `/api/chat` (non-streaming) dengan **`ALL_TOOLS`** untuk semua role. Bila respons berisi `tool_calls`, graph lanjut ke `call_tool`, lalu kembali ke `call_model`; tanpa `tool_calls` → selesai.

State: `messages` (akumulatif), `role` (dari sesi), `called_tools` (akumulatif, `[{tool, diizinkan, sumber?}]`).

### 5.2 Tool

| Tool | Fungsi | Role | Hasil |
|---|---|---|---|
| `cari_dokumen_sop(query)` | Hybrid search 20 kandidat → rerank 3 (atau 3 teratas bila reranker mati) | Semua | Teks gabungan chunk + daftar sumber |
| `query_data_operasional(tabel, mode, status?, nasabah_id?)` | `hitung_per_status` atau `detail_nasabah` (maks. 20 baris) pada `pengajuan_kredit`/`klaim_asuransi` | `staff_finance`, `supervisor` | Teks ringkas (Rupiah, tanggal ISO) |

**RBAC ditegakkan di `call_tool`, saat eksekusi**: semua role ditawari kedua tool, tetapi `query_data_operasional` untuk role di luar `SQL_ALLOWED_ROLES` **tidak dieksekusi**; model menerima pesan `"Akses ditolak: ..."` dan percobaan itu tercatat `diizinkan=False`. Argumen tidak valid (`TypeError`/`KeyError`) dikembalikan ke model sebagai teks agar bisa diperbaiki.

### 5.3 System Prompt Agent

`NALA_SYSTEM_PROMPT_AGENT` menjelaskan kedua tool, mewajibkan penggunaan tool untuk pertanyaan SOP/data, melarang mengarang nama/ID/status/jumlah nasabah, melarang mengaku punya data operasional tanpa hasil tool, dan mewajibkan pesan "Akses ditolak: ..." diteruskan apa adanya.

---

## 6. Knowledge Base & Retrieval

### 6.1 Ekstraksi & Chunking

| Format | Ekstraksi | Chunking |
|---|---|---|
| `.md` | Teks | Per heading (`#`–`######`); section > 500 karakter dipecah lagi (500, overlap 50) |
| `.txt` | Teks | 500 karakter, overlap 50 |
| `.pdf` | `pypdf` per halaman (tanpa OCR) | 500 karakter, overlap 50 |

### 6.2 Index OpenSearch `nala-docs`

| Field | Tipe |
|---|---|
| `text` | `text` (dipakai BM25) |
| `embedding` | `knn_vector` 768 dimensi, HNSW, nmslib, `cosinesimil` |
| `metadata` | `object` — `{"source": "<nama file>"}` |

ID dokumen `<nama file>-<urutan>`; ingest ulang menimpa chunk dengan ID sama. `refresh=true` di setiap PUT.

### 6.3 Metode Pencarian

| Metode | Cara | Catatan hasil uji (lihat [pengujian](./pengujian.md)) |
|---|---|---|
| Vector | k-NN embedding `nomic-embed-text` | Lemah untuk korpus bahasa Indonesia |
| BM25 | Query `match` pada `text` | Paling andal dan tercepat pada uji coba |
| Hybrid | BM25 + k-NN, digabung RRF (`rrf_k=60`) | Default UI & agent |
| + Rerank | Cross-encoder `ms-marco-MiniLM-L-6-v2` | Membantu sebagian; ±300 ms di CPU |

### 6.4 Jalur Ingest

| Jalur | Pemicu | Eksekutor |
|---|---|---|
| Upload | `POST /upload` | Worker RQ (`nala-worker`), antrian `ingest`, timeout job 30 menit; setelah selesai cache jawaban dikosongkan |
| Airflow | DAG `ingest_documents` (manual) | Container `airflow`, seluruh folder `/opt/airflow/knowledge-base` |

Folder knowledge base adalah bind mount `./app/knowledge-base` yang sama di `api`, `worker`, dan `airflow`.

---

## 7. Database Data Operasional (`nala_operasional`)

### 7.1 Tabel

**`pengajuan_kredit`**

| Kolom | Tipe | Keterangan |
|---|---|---|
| `id` | SERIAL PK | |
| `nasabah_id` | VARCHAR(10) | mis. `NSB0003` |
| `nama_nasabah` | VARCHAR(100) | |
| `jumlah_pengajuan` | NUMERIC(15,2) | Rupiah |
| `status` | VARCHAR(20) | CHECK: `pending`, `disetujui`, `ditolak`, `pencairan` |
| `tanggal_pengajuan` | DATE | |
| `alasan_penolakan` | TEXT | Hanya bila `ditolak` |

**`klaim_asuransi`**

| Kolom | Tipe | Keterangan |
|---|---|---|
| `id` | SERIAL PK | |
| `nasabah_id` | VARCHAR(10) | |
| `nama_nasabah` | VARCHAR(100) | |
| `jenis_klaim` | VARCHAR(50) | mis. Kesehatan, Kendaraan, Properti, Jiwa |
| `jumlah_klaim` | NUMERIC(15,2) | |
| `status` | VARCHAR(20) | CHECK: `pending`, `diproses`, `disetujui`, `ditolak` |
| `tanggal_klaim` | DATE | |

**`audit_log`**

| Kolom | Tipe | Keterangan |
|---|---|---|
| `id` | SERIAL PK | |
| `waktu` | TIMESTAMPTZ | default `now()` |
| `user_id` | VARCHAR(50) | dari sesi |
| `role` | VARCHAR(20) | dari sesi |
| `pertanyaan` | TEXT | |
| `tool_dipanggil` | VARCHAR(50) | NULL bila tanpa tool; `cache` untuk cache hit |
| `akses_diizinkan` | BOOLEAN | |
| `ringkasan_data_diakses` | TEXT | Belum diisi aplikasi |

### 7.2 Role Database (least privilege)

| Role | Hak | Dipakai oleh |
|---|---|---|
| `nala_admin` | Pemilik database (inisialisasi) | Seed, Adminer (admin) |
| `nala_readonly` | SELECT `pengajuan_kredit`, `klaim_asuransi` | Tool SQL, tabel halaman data operasional |
| `nala_writer` | INSERT kedua tabel (+ sequence) | Form data operasional |
| `nala_app` | INSERT + SELECT `audit_log` saja (tanpa UPDATE/DELETE) | `app/audit.py` |

`db/seed.sql` hanya dijalankan saat volume `postgres_data` masih kosong. Seed berisi 2 pengajuan kredit dan 1 klaim; data tambahan (50 baris per tabel) diinput langsung ke database berjalan.

---

## 8. Redis

| Pemakaian | Key / Nama | Detail |
|---|---|---|
| Cache jawaban agent | `nala:answer:<sha256>` | TTL `CACHE_TTL_SECONDS` (3600); `setex`; dikosongkan lewat `scan_iter` setelah ingest |
| Rate limit | `nala:ratelimit:<bucket>:<ip>:<window>` | `INCR` + `EXPIRE` hanya saat count = 1 |
| Antrian ingest | `rq:*` (antrian `ingest`) | Diproses service `worker` |

Redis dibatasi 256 MB dengan kebijakan `allkeys-lru`, tanpa volume (data boleh hilang saat restart). Semua fungsi cache dan rate limit bersifat **fail-open**: bila Redis mati, NALA tetap menjawab.

---

## 9. Keamanan (ringkas)

Rincian ada di [keamanan-rbac-audit.md](./keamanan-rbac-audit.md).

- Sesi cookie bertanda tangan (`SESSION_SECRET`, berlaku 8 jam); `user_id`/`role` tidak pernah dibaca dari body request.
- RBAC tool SQL di level eksekusi; audit log append-only.
- SQL tool: whitelist tabel/mode/status, nilai lewat parameter; tidak ada SQL buatan LLM.
- XSS: teks user via `textContent`; Markdown balasan disanitasi DOMPurify; nama file sumber di-escape.
- Upload: sanitasi nama file, validasi ekstensi.
- Rate limiting per IP (fail-open).

---

## 10. Konfigurasi

| Variabel | Default (kode) | Nilai di docker-compose | Dipakai |
|---|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | `http://ollama:11434` | api, worker, airflow |
| `OLLAMA_MODEL` | `llama3.2:3b` | `qwen2.5:7b` | api |
| `OPENSEARCH_BASE_URL` | `http://localhost:9200` | `http://opensearch:9200` | api, worker, airflow |
| `KNOWLEDGE_BASE_DIR` | `app/knowledge-base` | `/code/app/knowledge-base` | api, worker |
| `RERANK_ENABLED` | `true` | – | api |
| `HF_HOME` | – | `/app/.cache/huggingface` | api (cache model reranker) |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST` | – / – / `http://localhost:3000` | key project / `http://langfuse:3000` | api |
| `POSTGRES_READONLY_DSN` | `…nala_readonly…@localhost` | `…@postgres:5432/nala_operasional` | api |
| `POSTGRES_WRITER_DSN` | `…nala_writer…@localhost` | `…@postgres…` | api |
| `POSTGRES_APP_DSN` | `…nala_app…@localhost` | `…@postgres…` | api |
| `POSTGRES_ADMIN_PASSWORD` | – | `changeme_dev_only` | postgres |
| `SESSION_SECRET` | `nala-dev-session-secret-change-me` | `${SESSION_SECRET:-…}` | api |
| `REDIS_URL` | `redis://redis:6379/0` | worker: `redis://redis:6379/0` | api, worker |
| `CACHE_TTL_SECONDS` | `3600` | – | api |
| `RATE_LIMIT_MAX` / `RATE_LIMIT_WINDOW` | `20` / `60` | – | api |

**Konstanta penting:** `HISTORY_WINDOW=10`, `PAGE_SIZE=10`, `SQL_ALLOWED_ROLES={"staff_finance","supervisor"}`, batas upload 5/menit, batas data operasional 10/menit, ukuran chunk 500/overlap 50, timeout Ollama chat stream 120 s, agent 60 s, embedding 60 s, OpenSearch 30 s, Postgres connect 5 s.

---

## 11. Antarmuka Pengguna

| Halaman | Isi |
|---|---|
| `/login` | Form login + daftar akun demo |
| `/` (Chat) | Top bar (navigasi, banner "Masuk sebagai …", jumlah pesan, Reset), area percakapan bubble, composer dengan switch **Pakai RAG**, **BM25**, **Vector**, **Rerank hasil**, **Pakai Agent** |
| `/upload` | Form upload, pesan status (job ID), daftar dokumen |
| `/data-operasional` | Form tambah pengajuan kredit & klaim asuransi, tabel berpaginasi |

**Perilaku UI chat:**
- Pesan berupa bubble (`.msg-row > .bubble`): user di kanan, NALA di kiri dengan avatar yang berdenyut saat menunggu.
- Typing indicator tiga titik sebelum token pertama; kursor berkedip selama streaming.
- Balasan dirender sebagai Markdown (`marked`) lalu disanitasi (`DOMPurify`).
- Mode agent: badge sumber jawaban (📄 Dokumen SOP, 🗄️ Data operasional, ⚡ Dari cache) dan daftar **Sumber dokumen**.
- Saat mode agent aktif, switch retrieval dinonaktifkan (tetap terlihat).
- Tema gelap otomatis mengikuti preferensi OS/browser; tema terang tetap default.
- Responsif: breakpoint 600px dan 480px (kontrol composer menjadi satu kolom).
- Menghormati `prefers-reduced-motion`.

---

## 12. Deployment

### 12.1 Service Docker Compose

| Service | Port host | Image / Build | Catatan |
|---|---|---|---|
| `ollama` | 11434 | `ollama/ollama:latest` | Volume `ollama_data` |
| `opensearch` | 9200 | `opensearchproject/opensearch:2.11.0` | Single node, security plugin **dimatikan**, heap 512 MB, volume `opensearch_data` |
| `opensearch-dashboards` | 5601 | 2.11.0 | UI index |
| `api` | 8000 | Build `./app` | Menunggu postgres & redis *healthy* |
| `worker` | – | Build `./app` (image sama) | `rq worker ingest` |
| `airflow` | 8080 | `apache/airflow:2.10.2` | Standalone; DAG manual |
| `langfuse-db` | – | `postgres:15-alpine` | Metadata Langfuse |
| `langfuse` | 3000 | `langfuse/langfuse:2` | UI observability |
| `postgres` | 5432 | `postgres:16` | `nala_operasional`, seed otomatis, healthcheck |
| `redis` | 6379 | `redis:7-alpine` | 256 MB LRU, healthcheck, tanpa volume |
| `redisinsight` | 5540 | `redis/redisinsight:latest` | Koneksi ke Redis sudah dikonfigurasi |
| `adminer` | 8081 | `adminer:latest` | GUI Postgres |

Langkah menjalankan, reset, dan troubleshooting ada di [panduan-instalasi-dan-operasional.md](./panduan-instalasi-dan-operasional.md).

### 12.2 Image `api`/`worker`

`app/Dockerfile`: `python:3.12-slim`, install `requirements.txt` (termasuk torch CPU), lalu layer terpisah `itsdangerous==2.2.0` dan `redis==5.0.8 rq==1.16.2` agar layer torch tetap ter-*cache*. Kode di-*copy* ke image (bukan di-mount), sehingga **setiap perubahan kode, template, atau CSS memerlukan rebuild** (`docker compose up -d --build api`).

---

## 13. Batasan & Catatan Implementasi

1. **Error Ollama saat streaming tidak terdeteksi** — `chat_stream()` tidak memeriksa status HTTP; model yang belum di-*pull* menghasilkan balasan kosong.
2. **Chunk lama tidak dibersihkan** saat dokumen di-ingest ulang dengan versi lebih pendek; belum ada fitur hapus dokumen.
3. **PDF hasil scan tidak terbaca** (tanpa OCR).
4. **Tidak ada ambang skor minimum retrieval**, sehingga pertanyaan di luar knowledge base tetap mendapat konteks tak relevan.
5. **Cache jawaban agent**: data operasional bisa usang hingga 1 jam (cache tidak dikosongkan saat data diinput); cache hit tidak membawa daftar sumber; cache hit atas jawaban yang sebelumnya ditolak tercatat `akses_diizinkan = true` dengan `tool_dipanggil = "cache"`.
6. **Rate limit per IP**: di balik Docker/proxy semua pengguna tampil dengan IP gateway yang sama sehingga berbagi satu kuota.
7. **Dokumen SOP belum dibatasi per role** — RBAC hanya untuk data operasional.
8. **Nama tool > 50 karakter** (hasil karangan model) gagal ditulis ke `audit_log` (hanya tercatat di log aplikasi).
9. **`app/eval_testset.py` belum ada**, sehingga `python -m app.run_evaluation` gagal dijalankan sampai test set dibuat.
10. **Knowledge base memuat dokumen duplikat/bertentangan** (dua SOP pengajuan kredit dengan rasio DSR 40% vs 50%); dokumen di `tambahan dokumen/` belum di-ingest.
11. **Kredensial development** (password demo plaintext, password role database, kunci Langfuse) tertulis di kode/compose — hanya untuk lingkungan lokal.
12. **OpenSearch, Dashboards, Airflow, RedisInsight, Adminer** tidak memakai autentikasi aplikasi NALA; aksesnya harus dibatasi di level jaringan.
13. **DAG ganda**: `app/airflow/ingest_documents_dag.py` adalah salinan yang tidak dipakai Airflow.

---

## 14. Struktur Direktori

```
Nala/
├── airflow/dags/ingest_documents_dag.py   # DAG Airflow "ingest_documents" (manual)
├── app/
│   ├── airflow/ingest_documents_dag.py    # Salinan DAG (tidak dipakai)
│   ├── knowledge-base/                    # Dokumen SOP (bind mount ke api, worker, airflow)
│   ├── static/
│   │   ├── NALA_Logov2.jpg                # Logo & favicon
│   │   ├── style.css                      # Styling semua halaman (token warna, tema gelap, responsif)
│   │   └── vendor/                        # marked.umd.js, purify.min.js (lokal, tanpa CDN)
│   ├── templates/                         # login, chat, upload, data_operasional
│   ├── tools/
│   │   ├── rag_tool.py                    # Tool cari_dokumen_sop
│   │   └── sql_tool.py                    # Tool query_data_operasional
│   ├── agent.py                           # Agent LangGraph + RBAC
│   ├── audit.py                           # Audit log
│   ├── auth.py                            # User demo & sesi
│   ├── cache.py                           # Cache jawaban Redis
│   ├── db.py                              # Koneksi Postgres
│   ├── embeddings.py                      # Embedding via Ollama
│   ├── evaluation.py / llm_judge.py / run_evaluation.py   # Evaluasi retrieval & jawaban
│   ├── ingest.py                          # Ekstraksi, chunking, indexing
│   ├── jobs.py / queue.py                 # Job & antrian RQ
│   ├── main.py                            # Aplikasi FastAPI
│   ├── ollama_client.py                   # Client Ollama
│   ├── rate_limit.py                      # Rate limiting
│   ├── reranker.py                        # Cross-encoder
│   ├── system_prompt.py                   # System prompt
│   ├── vector_store.py                    # Client OpenSearch
│   ├── Dockerfile
│   └── requirements.txt
├── db/seed.sql                            # Skema, data contoh, role database
├── dokumentasi/                           # Dokumen proyek (lihat README.md)
├── tambahan dokumen/                      # SOP tambahan yang belum di-ingest
├── ujicoba/                               # Laporan uji coba retrieval
├── docker-compose.yml                     # Orkestrasi 12 service
└── requirements.txt                       # Salinan requirements (sama dengan app/)
```
