# Panduan Instalasi & Operasional — NALA

**Versi Dokumen:** 1.0
**Tanggal:** 2026-09-25
**Pembaca:** tim pengembang, IT Ops

Panduan ini menjelaskan cara menjalankan NALA dari nol, mengoperasikan layanan sehari-hari, dan mengatasi masalah yang sudah pernah terjadi selama pengembangan. Detail teknis ada di [spesifikasi.md](./spesifikasi.md).

---

## 1. Prasyarat

| Kebutuhan | Keterangan |
|---|---|
| Docker Desktop / Docker Engine + Compose v2 | Semua layanan berjalan sebagai container |
| RAM | Disarankan ≥ 16 GB (Ollama `qwen2.5:7b` ± 5 GB, OpenSearch 512 MB heap, Airflow, Langfuse, Postgres) |
| Disk | ± 15 GB (model Ollama, image torch, volume data) |
| Port bebas | 3000, 5432, 5540, 5601, 6379, 8000, 8080, 8081, 9200, 11434 |
| Git | Untuk mengambil kode dari repository |

Repository: `https://github.com/myidisl/NALA-AI_RAG-LLM`

---

## 2. Instalasi Pertama

```bash
git clone https://github.com/myidisl/NALA-AI_RAG-LLM.git Nala
cd Nala

# 1. Build & jalankan semua service (pertama kali cukup lama: image torch, Airflow, Langfuse)
docker compose up -d --build

# 2. Unduh model ke Ollama
docker compose exec ollama ollama pull qwen2.5:7b
docker compose exec ollama ollama pull nomic-embed-text

# 3. Cek status
docker compose ps
curl http://localhost:8000/health        # {"status":"ok"}
```

### 2.1 Langfuse (sekali di awal)

1. Buka `http://localhost:3000`, buat akun & project **NALA**.
2. *Settings → API Keys* → buat key baru.
3. Isi `LANGFUSE_PUBLIC_KEY` dan `LANGFUSE_SECRET_KEY` di service `api` pada `docker-compose.yml`, lalu `docker compose up -d api`.

> Kunci yang ada di repository hanya berlaku untuk instance Langfuse lokal pengembang. Bila database Langfuse di-reset, buat key baru.

### 2.2 Isi Knowledge Base

Pilih salah satu:

- **Lewat UI**: login → **Knowledge Base** → upload file satu per satu (diproses worker di background).
- **Sekaligus**: salin file ke `app/knowledge-base/`, lalu jalankan DAG Airflow `ingest_documents` (lihat §4.3).

Dokumen di folder `tambahan dokumen/` **belum** otomatis masuk knowledge base.

### 2.3 Akun Demo

| Username | Role | Akses data operasional |
|---|---|---|
| `budi.umum` | Staff Umum | ❌ |
| `sari.finance` | Staff Finance | ✅ |
| `andi.super` | Supervisor | ✅ |
| `thoriq.netsec` | Staff NetSec | ❌ |
| `zein.netsec` | Supervisor NetSec | ❌ |

Password semua akun: `nala123`.

---

## 3. Alamat Layanan

| Layanan | URL | Login |
|---|---|---|
| NALA | http://localhost:8000 | Akun demo di atas |
| Langfuse | http://localhost:3000 | Akun yang dibuat di §2.1 |
| Airflow | http://localhost:8080 | `admin`, password dicetak di log start pertama (`docker compose logs airflow`) |
| OpenSearch Dashboards | http://localhost:5601 | – (security dimatikan) |
| Adminer (Postgres) | http://localhost:8081 | System **PostgreSQL**, Server **postgres**, user `nala_admin` / password `changeme_dev_only` (atau role lain) |
| RedisInsight | http://localhost:5540 | – (database "NALA Redis" sudah terhubung) |
| OpenSearch API | http://localhost:9200 | – |
| Ollama API | http://localhost:11434 | – |

---

## 4. Operasional Harian

### 4.1 Menerapkan Perubahan Kode

Kode, template, dan CSS di-*copy* ke image (tidak di-mount), sehingga setiap perubahan butuh rebuild:

```bash
docker compose up -d --build api            # perubahan app/*.py, templates, static
docker compose up -d --build api worker     # bila mengubah kode yang dipakai worker (ingest, cache, jobs)
```

Lalu refresh browser dengan **Ctrl+F5** agar CSS/JS lama tidak terpakai dari cache.

Perubahan `app/requirements.txt` membuat layer torch dibangun ulang (lama). Dependency kecil sebaiknya ditambahkan sebagai layer terpisah di `app/Dockerfile`, seperti `itsdangerous`, `redis`, dan `rq`.

### 4.2 Melihat Log

```bash
docker compose logs -f api          # request, error aplikasi, "Gagal menulis audit_log"
docker logs -f nala-worker          # job ingest: "ingest: app.jobs.ingest_document_job(...)" / "Job OK"
docker compose logs -f airflow
```

### 4.3 Ingest Ulang Seluruh Folder (Airflow)

1. Buka http://localhost:8080 → DAG **ingest_documents**.
2. Aktifkan (toggle) lalu **Trigger DAG**.
3. Lihat log task untuk jumlah dokumen yang ter-index.

Ingest ulang aman: ID chunk `<file>-<n>` menimpa chunk lama (bukan duplikat).

### 4.4 Memantau Redis

RedisInsight → database **NALA Redis**:

| Pola key | Isi |
|---|---|
| `nala:answer:*` | Cache jawaban agent (lihat TTL) |
| `nala:ratelimit:*` | Counter rate limit per bucket/IP/jendela |
| `rq:*` | Antrian, job, dan worker RQ |

Workbench: `INFO stats` (`keyspace_hits`/`keyspace_misses`) untuk rasio cache hit.

Mengosongkan cache jawaban secara manual:
```bash
docker exec nala-worker python -c "from app.cache import invalidate_answer_cache; print(invalidate_answer_cache())"
```

### 4.5 Meninjau Audit Log

Adminer → database `nala_operasional` → tabel `audit_log`, atau:

```sql
SELECT waktu, user_id, role, pertanyaan, tool_dipanggil, akses_diizinkan
FROM audit_log ORDER BY id DESC LIMIT 50;

-- Percobaan akses yang ditolak RBAC
SELECT user_id, role, pertanyaan, waktu FROM audit_log WHERE NOT akses_diizinkan ORDER BY id DESC;
```

### 4.6 Menambah Data Operasional Massal

Gunakan role admin (bukan role aplikasi):

```bash
docker compose exec -T postgres psql -U nala_admin -d nala_operasional < skrip.sql
```

---

## 5. Reset & Pemulihan

### 5.1 Menerapkan Perubahan `db/seed.sql`

`seed.sql` **hanya dijalankan saat volume `postgres_data` kosong**. Dua pilihan:

- **Pertahankan data**: jalankan blok SQL baru secara manual lewat Adminer sebagai `nala_admin`.
- **Reset total** (menghapus semua data operasional & audit log):
  ```bash
  docker compose down
  docker volume rm nala_postgres_data
  docker compose up -d
  ```

### 5.2 Volume Data

| Volume | Isi | Dampak bila dihapus |
|---|---|---|
| `ollama_data` | Model Ollama | Perlu `ollama pull` ulang |
| `opensearch_data` | Index `nala-docs` | Perlu ingest ulang seluruh dokumen |
| `hf_cache` | Model reranker | Diunduh ulang saat api start |
| `postgres_data` | Data operasional & audit log | Kembali ke isi `seed.sql` |
| `langfuse_db_data` | Trace & akun Langfuse | Perlu buat project & API key baru |

Redis tidak memakai volume; cache, counter, dan antrian hilang saat restart (by design).

Backup yang disarankan: folder `app/knowledge-base/` (dokumen asli) dan dump Postgres:
```bash
docker compose exec -T postgres pg_dump -U nala_admin nala_operasional > backup.sql
```

---

## 6. Troubleshooting

| Gejala | Penyebab umum | Solusi |
|---|---|---|
| Balasan NALA kosong | Model belum di-*pull* / nama model salah | `docker compose exec ollama ollama list`; pull model sesuai `OLLAMA_MODEL` |
| API gagal di request pertama setelah menambah login | `itsdangerous` belum terpasang | Rebuild image api (layer itsdangerous ada di Dockerfile) |
| `api` tidak mau start | Menunggu `postgres`/`redis` *healthy* | `docker compose ps`; cek log postgres/redis |
| Tabel `audit_log` tidak ada | Volume Postgres dibuat sebelum seed diperbarui | Lihat §5.1 |
| Log api: "Gagal menulis audit_log" | `POSTGRES_APP_DSN` salah / tabel belum ada / Postgres mati | Periksa env di compose dan §5.1; chat tetap berjalan |
| Upload berhasil tapi dokumen tidak bisa ditanyakan | Worker mati atau Ollama/OpenSearch tidak terjangkau | `docker logs nala-worker`; `docker compose up -d worker` |
| Pesan "belum masuk antrian proses (Redis belum terjangkau)" | Redis mati | `docker compose up -d redis`, lalu upload ulang |
| HTTP 429 "Terlalu banyak permintaan" | Batas rate limit tercapai (dihitung per IP, semua user di satu mesin berbagi kuota) | Tunggu ≤ 60 detik; ubah `RATE_LIMIT_MAX`/`RATE_LIMIT_WINDOW` bila perlu |
| Jawaban data operasional tidak berubah setelah input data baru | Jawaban diambil dari cache (badge ⚡) | Tunggu TTL 1 jam, kosongkan cache (§4.4), atau tanyakan dengan kalimat berbeda |
| "Akses ditolak" untuk pertanyaan data | Role tidak ada di `SQL_ALLOWED_ROLES` | By design; login sebagai `sari.finance`/`andi.super` |
| Tampilan tidak berubah setelah edit CSS/template | Image belum di-rebuild / cache browser | `docker compose up -d --build api` lalu Ctrl+F5 |
| Airflow DAG gagal `ModuleNotFoundError` | Dependency belum terpasang di container Airflow | Cek `_PIP_ADDITIONAL_REQUIREMENTS` di compose, restart airflow |
| Port bentrok | Aplikasi lain memakai port yang sama | Ubah mapping port host di `docker-compose.yml` |

---

## 7. Evaluasi Retrieval

```bash
docker compose exec api python -m app.run_evaluation
```

Skrip membandingkan hybrid search sebelum dan sesudah reranking (precision@3, hit rate@3, MRR). **Catatan:** skrip membutuhkan `app/eval_testset.py` (variabel `QA_TESTSET` berisi `question` dan `must_contain`) yang belum ada di repository. Hasil uji coba manual ada di folder `ujicoba/` dan dirangkum di [pengujian.md](./pengujian.md).

---

## 8. Git & Repository

```bash
git status
git add -A
git commit -m "pesan perubahan"
git push                       # branch main → origin/main
```

`.gitignore` mengecualikan `__pycache__/`, `*.log`, `log-airflow.txt`, `.env`, dan folder editor. Kunci Langfuse dan password development saat ini ikut ter-*commit* di `docker-compose.yml`; pindahkan ke `.env` bila repository bersifat publik.
