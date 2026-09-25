# Riwayat Pengembangan — NALA

**Versi Dokumen:** 1.0
**Tanggal:** 2026-09-25

Kronologi pembangunan NALA per module pelatihan, beserta keputusan desain dan penyimpangan dari spesifikasi materi yang perlu diketahui pengembang berikutnya. Nomor module diambil dari materi dan referensi di kode; module yang nomornya tidak tercatat ditandai "–". Module 1–14 sesuai dokumen versi 1.0–2.1 (2026-09-23 s.d. 2026-09-24); Module 27–29 dikerjakan 2026-09-25; tanggal module di antaranya tidak tercatat.

---

## 1. Ringkasan Kronologi

| Module | Fitur | File utama |
|---|---|---|
| 1–6 | MVP: FastAPI + Ollama, chat streaming, windowing 10 pesan, reset, Docker Compose, health check | `main.py`, `ollama_client.py`, `chat.html` |
| 7–8 | Styling halaman chat, meta jumlah pesan & tombol reset | `style.css`, `chat.html` |
| 13 | *Naive RAG*: embedding `nomic-embed-text`, k-NN OpenSearch | `embeddings.py`, `vector_store.py` |
| 14 | Halaman upload knowledge base, ingest dokumen (`metadata.source`), switch RAG, DAG Airflow, persona perbankan | `ingest.py`, `upload.html`, `airflow/dags/` |
| 15 | Chunking Markdown per heading (level chunk) | `ingest.py` |
| 18–19 | BM25 dan hybrid search (RRF); pilihan metode di UI (BM25/Vector) | `vector_store.py`, `chat.html` |
| 20 | Reranker cross-encoder; switch "Rerank hasil" | `reranker.py` |
| 21 | Evaluasi retrieval (precision@k, hit rate, MRR) dan LLM-as-judge | `evaluation.py`, `llm_judge.py`, `run_evaluation.py` |
| – | Observability Langfuse (trace retrieval, rerank, generate) | `main.py`, `docker-compose.yml` |
| 23 | Database data operasional Postgres (role readonly & writer), halaman Data Operasional + paginasi | `db/seed.sql`, `db.py`, `data_operasional.html` |
| 25 | Agent LangGraph dengan tool `cari_dokumen_sop` & `query_data_operasional`; mode Agent di UI; riwayat multi-turn di `/chat` | `agent.py`, `tools/`, `system_prompt.py` |
| 27 | Login/sesi, audit log, RBAC tool SQL, audit terhubung ke `/chat` | `auth.py`, `audit.py`, `agent.py`, `login.html` |
| 28 | Redis: cache jawaban, antrian ingest RQ + worker, rate limiting, RedisInsight | `cache.py`, `queue.py`, `jobs.py`, `rate_limit.py` |
| 29 | UI: typing indicator, badge tool, tema gelap, bubble, lampiran sumber, responsif ≤ 480px | `chat.html`, `style.css`, `rag_tool.py` |
| – | Konten: 5 SOP baru di `tambahan dokumen/`, data operasional 50 baris per tabel, dokumentasi v3.0, komentar kode | `tambahan dokumen/`, `dokumentasi/` |

---

## 2. Module 27 — Identitas, RBAC, Audit

| Tahap | Isi | Catatan |
|---|---|---|
| 0 | `auth.py` (3 user demo, `verify_user`, `get_current_user`), `login.html`, `SessionMiddleware`, proteksi semua halaman, 401 di `/chat` & `/chat/stream`, banner di 3 template, layer `itsdangerous` di Dockerfile, `SESSION_SECRET` | Kemudian ditambah 2 user NetSec (`staff_netsec`, `spv_netsec`) |
| A | Tabel `audit_log`, role `nala_app` (INSERT+SELECT saja), service Adminer (port 8081) | `nala_app` sebenarnya role keempat (sudah ada `nala_writer`). Seed hanya berlaku di volume kosong → volume Postgres di-reset |
| B | `audit.py` → `log_audit()` | Tangkapan diperluas dari `OperationalError` ke `psycopg.Error` (Tahap D) agar DataError tidak menggagalkan `/chat` |
| C | RBAC di `call_tool`; `called_tools` di state; `ALL_TOOLS` untuk semua role; penguatan system prompt agent | Bagian Module 25/26 yang disebut "sudah ada" di spesifikasi (try/except `(TypeError, KeyError)`, `name`/`tool_call_id`) ternyata belum ada dan dibangun di tahap ini. **`force_answer` (Module 26) tidak ditemukan** dan tidak dibuat |
| D | `/chat` memakai role dari sesi, audit per tool, `POSTGRES_APP_DSN` di compose | – |

## 3. Module 28 — Redis

| Tahap/Langkah | Isi | Catatan |
|---|---|---|
| A.1 | Service `redis` (256 MB, allkeys-lru, healthcheck), `api` menunggu redis, layer `redis`+`rq` | Dockerfile berada di `app/Dockerfile`, bukan `Nala/Dockerfile` |
| A.2 | `cache.py` (key memuat role, `setex`, `scan_iter`, fail-open) | – |
| A.3 | Cache di `/chat` (tanpa history), audit `tool_dipanggil="cache"` | Field `tool_used` ditambahkan ke `ChatResponse`; belum ada rate limit saat itu |
| B.4–5 | `queue.py`, `jobs.py`, service `worker` | Build, env (`KNOWLEDGE_BASE_DIR`), dan volume disamakan dengan `api`; opensearch memakai `service_started` karena tidak punya healthcheck |
| B.6 | `/upload` → enqueue job | Ditambah `except redis.RedisError` agar upload tidak 500 saat Redis mati |
| C.7–8 | `rate_limit.py` di 5 endpoint | Semua endpoint sudah punya parameter `Request`; IP terlihat sebagai gateway Docker |
| D.9 | RedisInsight (port 5540) dengan koneksi otomatis | – |

## 4. Module 29 — Pengalaman Pengguna

| Tahap/Langkah | Isi | Catatan |
|---|---|---|
| A.1–2 | Typing indicator `.typing-indicator` | Class `.typing` lama dipertahankan (`class="typing typing-indicator"`) agar avatar berdenyut & kursor tetap bekerja |
| B.4 | Badge tool (`tool_used`: rag/sql/mixed/none/cache) | Hanya tool `diizinkan=True` yang dihitung |
| C.5 | Tema gelap | Tema terang tetap default; tema gelap via `prefers-color-scheme` + `data-theme`; seluruh warna ditokenisasi. Aturan layout materi (body 760px, `#history` 420px) tidak diterapkan karena layout layar penuh |
| C.6 | Bubble `.msg-row > .bubble`, helper `addRow()` | Bubble NALA `white-space: normal` (Markdown); aturan avatar, kursor, dan Markdown dipindah ke struktur baru |
| C.7 | Lampiran sumber (`sources`) | `rag_search()` mengembalikan tuple; nama file di-escape |
| D.8 | Media query ≤ 480px | `#history` memakai `min-height: 260px`; toggle `display: flex` (tetap satu per baris) |

---

## 5. Keputusan Desain Penting

| Keputusan | Alasan |
|---|---|
| RBAC di level eksekusi tool, bukan menyembunyikan tool | Mencegah halusinasi dan celah audit (lihat [keamanan](./keamanan-rbac-audit.md)) |
| Role wajib masuk key cache | Mencegah kebocoran jawaban data antar role |
| Cache & rate limit fail-open | Redis adalah optimasi; NALA tetap harus menjawab |
| Dependency kecil sebagai layer Dockerfile terpisah | Menghindari rebuild layer torch yang besar |
| Worker memakai image yang sama dengan api | Satu Dockerfile; kode ingest identik |
| Audit ditulis setelah jawaban didapat | Kegagalan audit tidak memengaruhi jawaban |
| Library Markdown/sanitasi disajikan lokal | Tetap berjalan di jaringan tanpa internet |
| Tema terang tetap default | Permintaan pengguna: "jangan ubah default color palet" |

---

## 6. Pekerjaan Terbuka

| No | Item | Referensi |
|---|---|---|
| 1 | Buat `app/eval_testset.py` agar `run_evaluation.py` bisa dijalankan | [pengujian](./pengujian.md) |
| 2 | Selaraskan 5 SOP baru dengan SOP-KRD-001 (DSR 40%, LTV KPR 80%, tenor Multiguna 5 tahun, usia lunas 55/65, limit pemutus) dan keluarkan SOP pengajuan kredit versi lama dari knowledge base | Review SOP per role |
| 3 | Ingest dokumen `tambahan dokumen/` (5 SOP baru, POJK 22/2023); jangan upload `POJK11-…pdf` (duplikat) | – |
| 4 | Audit cache hit atas jawaban penolakan | [keamanan §6.3](./keamanan-rbac-audit.md) |
| 5 | Invalidasi cache saat data operasional berubah | [spesifikasi §13](./spesifikasi.md) |
| 6 | Rate limit per `user_id` | [keamanan §8](./keamanan-rbac-audit.md) |
| 7 | Deskripsi tool `cari_dokumen_sop` masih menyebut "lihat Module 25" (teks ini dibaca model) | `app/tools/rag_tool.py` |
| 8 | Hapus DAG salinan `app/airflow/ingest_documents_dag.py` | – |
| 9 | Pindahkan secret ke `.env` bila repository publik | [instalasi §8](./panduan-instalasi-dan-operasional.md) |
