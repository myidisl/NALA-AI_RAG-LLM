# NALA — Not Another Lowkey Assistant

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688?logo=fastapi&logoColor=white)
![Ollama](https://img.shields.io/badge/LLM-Ollama%20(lokal)-000000)
![OpenSearch](https://img.shields.io/badge/OpenSearch-2.11-005EB8?logo=opensearch&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

Asisten AI internal untuk pegawai perbankan (studi kasus **PT Nusantara Finance**) yang berjalan **sepenuhnya di infrastruktur sendiri**. NALA menjawab pertanyaan teknologi, isi **SOP internal** lewat Retrieval-Augmented Generation (RAG), dan **data operasional** lewat agent dengan tool SQL terbatas — lengkap dengan login, pembatasan akses per role (RBAC), dan audit log.

> Tidak ada percakapan, dokumen, maupun data yang dikirim ke layanan pihak ketiga: LLM, embedding, reranker, dan penyimpanan semuanya lokal.

---

## Daftar Isi

- [Fitur](#fitur)
- [Arsitektur](#arsitektur)
- [Tech Stack](#tech-stack)
- [Memulai](#memulai)
- [Akun Demo](#akun-demo)
- [Penggunaan](#penggunaan)
- [Konfigurasi](#konfigurasi)
- [Struktur Proyek](#struktur-proyek)
- [Pengujian & Evaluasi](#pengujian--evaluasi)
- [Dokumentasi](#dokumentasi)
- [Keterbatasan](#keterbatasan)
- [Kontribusi](#kontribusi)

---

## Fitur

**Tanya-jawab**
- 💬 Chat streaming token per token dengan konteks 10 pesan terakhir
- 📚 RAG atas dokumen SOP (`.md`, `.txt`, `.pdf`) dengan pilihan metode **BM25**, **Vector**, atau **Hybrid (RRF)**, plus **reranking** cross-encoder
- 🤖 **Mode Agent** (LangGraph): model memilih sendiri tool `cari_dokumen_sop` atau `query_data_operasional`
- 🏷️ Badge sumber jawaban (📄 Dokumen SOP · 🗄️ Data operasional · ⚡ Dari cache) dan lampiran **dokumen sumber**

**Keamanan & tata kelola**
- 🔐 Login berbasis sesi; identitas & role hanya dari sesi, bukan body request
- 🛡️ **RBAC** akses data operasional ditegakkan saat eksekusi tool (`staff_finance`, `supervisor`)
- 📝 **Audit log** append-only untuk setiap pertanyaan mode agent
- 🧱 Role database *least privilege*; model tidak pernah menulis SQL sendiri

**Performa & operasional**
- ⚡ Cache jawaban di Redis (terpisah per role)
- 📥 Ingest dokumen di background (antrian **RQ** + worker)
- 🚦 Rate limiting per IP (fail-open)
- 🔭 Observability dengan **Langfuse**; evaluasi retrieval (precision@k, hit rate, MRR) & LLM-as-judge
- 🗂️ Halaman input & daftar data operasional (pengajuan kredit, klaim asuransi)

**Antarmuka**
- Bubble chat, typing indicator, Markdown tersanitasi, tema gelap otomatis, responsif hingga layar 375px

---

## Arsitektur

```
Browser ─> api (FastAPI) ─┬─> Ollama        LLM (qwen2.5:7b) & embedding (nomic-embed-text)
                          ├─> OpenSearch    knowledge base: BM25 + k-NN
                          ├─> PostgreSQL    data operasional + audit log
                          ├─> Redis         cache jawaban, rate limit, antrian ingest ─> worker (RQ)
                          └─> Langfuse      trace retrieval & generate
Airflow ─> ingest ulang seluruh knowledge base (manual)
Adminer · RedisInsight · OpenSearch Dashboards ─> GUI pengembangan
```

Alur agent:

```
pertanyaan ─> sesi (user, role) ─> cache? ──hit──> jawaban ⚡
                                      │ miss
                                      v
              call_model ⇄ call_tool (RBAC: role boleh SQL?) ─> jawaban
                                      │
                      audit_log · simpan cache · {reply, tool_used, sources}
```

Detail lengkap: [dokumentasi/spesifikasi.md](./dokumentasi/spesifikasi.md).

---

## Tech Stack

| Lapisan | Teknologi |
|---|---|
| Backend | Python 3.12, FastAPI, Uvicorn, Jinja2, httpx |
| LLM & embedding | Ollama (`qwen2.5:7b`, `nomic-embed-text`) |
| Retrieval | OpenSearch 2.11 (k-NN HNSW + BM25), sentence-transformers (`ms-marco-MiniLM-L-6-v2`) |
| Agent | LangGraph |
| Database | PostgreSQL 16 (psycopg 3) |
| Cache & antrian | Redis 7, RQ |
| Observability | Langfuse v2 |
| Pipeline | Apache Airflow 2.10 |
| Frontend | HTML, CSS, vanilla JavaScript, marked + DOMPurify (lokal) |
| Deployment | Docker Compose (12 service) |

---

## Memulai

### Prasyarat

- Docker & Docker Compose v2
- RAM ≥ 16 GB disarankan, disk ± 15 GB
- Port bebas: 3000, 5432, 5540, 5601, 6379, 8000, 8080, 8081, 9200, 11434

### Instalasi

```bash
git clone https://github.com/myidisl/NALA-AI_RAG-LLM.git
cd NALA-AI_RAG-LLM

# build & jalankan semua service
docker compose up -d --build

# unduh model ke Ollama
docker compose exec ollama ollama pull qwen2.5:7b
docker compose exec ollama ollama pull nomic-embed-text

# cek
curl http://localhost:8000/health   # {"status":"ok"}
```

Buka **http://localhost:8000** dan login dengan salah satu akun demo.

Langkah tambahan (API key Langfuse, isi knowledge base, reset database) ada di [panduan instalasi & operasional](./dokumentasi/panduan-instalasi-dan-operasional.md).

### Layanan

| Layanan | URL |
|---|---|
| NALA | http://localhost:8000 |
| Langfuse | http://localhost:3000 |
| Airflow | http://localhost:8080 |
| OpenSearch Dashboards | http://localhost:5601 |
| Adminer (Postgres) | http://localhost:8081 |
| RedisInsight | http://localhost:5540 |

---

## Akun Demo

Password semua akun: `nala123` (khusus pengembangan).

| Username | Role | Akses data operasional |
|---|---|---|
| `budi.umum` | Staff Umum | ❌ |
| `sari.finance` | Staff Finance | ✅ |
| `andi.super` | Supervisor | ✅ |
| `thoriq.netsec` | Staff NetSec | ❌ |
| `zein.netsec` | Supervisor NetSec | ❌ |

---

## Penggunaan

1. **Chat (RAG)** — ketik pertanyaan; atur *Pakai RAG*, metode *BM25/Vector*, dan *Rerank hasil*.
2. **Mode Agent** — aktifkan *Pakai Agent* untuk pertanyaan data, mis. *"Berapa pengajuan kredit yang ditolak?"*. Role tanpa akses akan menerima *"Akses ditolak"*.
3. **Knowledge Base** — upload dokumen SOP; ingest berjalan di background (job ID ditampilkan).
4. **Data Operasional** — tambah dan lihat pengajuan kredit & klaim asuransi.

Contoh API mode agent (butuh cookie sesi hasil login):

```bash
curl -c cj.txt -d "username=sari.finance&password=nala123" http://localhost:8000/login
curl -b cj.txt -H "Content-Type: application/json" \
     -d '{"message":"Berapa pengajuan kredit per status?","history":[]}' \
     http://localhost:8000/chat
# {"reply":"...","tool_used":"sql","sources":[]}
```

Panduan lengkap: [dokumentasi/panduan-pengguna.md](./dokumentasi/panduan-pengguna.md).

---

## Konfigurasi

Semua konfigurasi lewat *environment variable* di `docker-compose.yml`. Yang paling sering diubah:

| Variabel | Default | Keterangan |
|---|---|---|
| `OLLAMA_MODEL` | `qwen2.5:7b` (compose) | Model chat & agent |
| `RERANK_ENABLED` | `true` | Matikan reranker tanpa ubah kode |
| `SESSION_SECRET` | nilai development | **Wajib diganti** di luar lingkungan lokal |
| `CACHE_TTL_SECONDS` | `3600` | Umur cache jawaban |
| `RATE_LIMIT_MAX` / `RATE_LIMIT_WINDOW` | `20` / `60` | Batas request chat per IP |

Daftar lengkap: [spesifikasi §10](./dokumentasi/spesifikasi.md#10-konfigurasi).

> Kode di-*copy* ke image, jadi perubahan kode/template/CSS memerlukan `docker compose up -d --build api`.

---

## Struktur Proyek

```
.
├── app/                    # Aplikasi FastAPI (api & worker memakai image yang sama)
│   ├── main.py             # Endpoint & orkestrasi
│   ├── agent.py            # Agent LangGraph + RBAC
│   ├── tools/              # cari_dokumen_sop (RAG), query_data_operasional (SQL)
│   ├── auth.py · audit.py · cache.py · rate_limit.py · queue.py · jobs.py
│   ├── ingest.py · vector_store.py · embeddings.py · reranker.py
│   ├── evaluation.py · llm_judge.py · run_evaluation.py
│   ├── templates/          # login, chat, upload, data_operasional
│   ├── static/             # style.css, logo, vendor JS
│   ├── knowledge-base/     # Dokumen SOP (bind mount)
│   └── Dockerfile
├── airflow/dags/           # DAG ingest_documents
├── db/seed.sql             # Skema, data contoh, role database
├── dokumentasi/            # BRD, spesifikasi, panduan, pengujian, riwayat
├── ujicoba/                # Laporan uji coba retrieval
├── tambahan dokumen/       # SOP tambahan (belum di-ingest)
└── docker-compose.yml
```

---

## Pengujian & Evaluasi

- Laporan uji retrieval (BM25 vs Vector vs Hybrid ± Rerank): [ujicoba/](./ujicoba/README.md)
- Hasil uji fitur & skenario regresi manual: [dokumentasi/pengujian.md](./dokumentasi/pengujian.md)
- Evaluasi otomatis (membutuhkan `app/eval_testset.py`):
  ```bash
  docker compose exec api python -m app.run_evaluation
  ```

---

## Dokumentasi

| Dokumen | Isi |
|---|---|
| [BRD](./dokumentasi/BRD.md) | Kebutuhan bisnis, persona, FR/NFR, risiko |
| [Spesifikasi Teknis](./dokumentasi/spesifikasi.md) | Arsitektur, API, database, konfigurasi |
| [Keamanan, RBAC & Audit](./dokumentasi/keamanan-rbac-audit.md) | Desain keamanan & celah yang diketahui |
| [Instalasi & Operasional](./dokumentasi/panduan-instalasi-dan-operasional.md) | Setup, operasional, troubleshooting |
| [Panduan Pengguna](./dokumentasi/panduan-pengguna.md) | Cara pakai per role |
| [Pengujian](./dokumentasi/pengujian.md) | Hasil uji & skenario regresi |
| [Riwayat Pengembangan](./dokumentasi/riwayat-pengembangan.md) | Kronologi & pekerjaan terbuka |

---

## Keterbatasan

Proyek ini adalah **lingkungan pengembangan/pembelajaran**, belum siap produksi:

- Akun demo dengan password plaintext; kredensial development tertulis di `docker-compose.yml`
- OpenSearch, Adminer, RedisInsight, Airflow tidak memakai autentikasi — jangan dibuka ke jaringan publik
- Dokumen SOP belum dibatasi per role (RBAC hanya untuk data operasional)
- Rate limit dihitung per IP (di balik proxy semua pengguna berbagi kuota)
- PDF hasil scan belum didukung (tanpa OCR)

Daftar lengkap: [spesifikasi §13](./dokumentasi/spesifikasi.md#13-batasan--catatan-implementasi) dan [keamanan §11](./dokumentasi/keamanan-rbac-audit.md#11-celah-yang-diketahui--rekomendasi-sebelum-produksi).

---

## Kontribusi

1. Buat branch dari `main`.
2. Terapkan perubahan dan perbarui dokumen terkait di `dokumentasi/`.
3. Jalankan skenario regresi di [pengujian.md](./dokumentasi/pengujian.md#3-skenario-uji-manual-regresi).
4. Buka pull request dengan ringkasan perubahan.

## Lisensi

Belum ada lisensi. Tanpa lisensi, hak cipta tetap pada pemilik repository. Tambahkan file `LICENSE` bila proyek ingin dibagikan dengan ketentuan tertentu.

Data nasabah dan dokumen SOP di repository ini bersifat **fiktif** dan hanya untuk keperluan demonstrasi.
