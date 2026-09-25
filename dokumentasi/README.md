# Dokumentasi NALA

NALA (*Not Another Lowkey Assistant*) adalah asisten AI internal PT Nusantara Finance yang berjalan sepenuhnya di infrastruktur sendiri: menjawab pertanyaan teknologi, SOP internal (RAG), dan data operasional (agent dengan RBAC dan audit log).

**Versi dokumentasi:** 3.0 · **Tanggal:** 2026-09-25 · **Cakupan:** implementasi sampai Module 29

## Daftar Dokumen

| Dokumen | Isi | Untuk |
|---|---|---|
| [BRD.md](./BRD.md) | Kebutuhan bisnis: tujuan, ruang lingkup, persona & role, kebutuhan fungsional/non-fungsional, alur proses, risiko, rencana, kriteria penerimaan | Business owner, semua pihak |
| [spesifikasi.md](./spesifikasi.md) | Spesifikasi teknis: arsitektur & alur, komponen, API, agent & tool, retrieval, database, Redis, konfigurasi, UI, deployment, batasan | Pengembang |
| [keamanan-rbac-audit.md](./keamanan-rbac-audit.md) | Autentikasi, matriks RBAC, keamanan query, role database, audit log, cache per role, rate limiting, XSS, celah yang diketahui | Keamanan informasi, audit, pengembang |
| [panduan-instalasi-dan-operasional.md](./panduan-instalasi-dan-operasional.md) | Instalasi dari nol, alamat layanan, operasional harian, reset/backup, troubleshooting | IT Ops, pengembang |
| [panduan-pengguna.md](./panduan-pengguna.md) | Cara memakai chat, mode agent, knowledge base, data operasional; arti pesan yang muncul | Pengguna akhir |
| [pengujian.md](./pengujian.md) | Evaluasi retrieval, hasil uji fitur Module 27–29, skenario uji manual regresi | QA, pengembang |
| [riwayat-pengembangan.md](./riwayat-pengembangan.md) | Kronologi per module, keputusan desain, penyimpangan dari materi, pekerjaan terbuka | Pengembang berikutnya |

Laporan uji coba retrieval rinci: [`../ujicoba/`](../ujicoba/README.md).

## Mulai Cepat

```bash
docker compose up -d --build
docker compose exec ollama ollama pull qwen2.5:7b
docker compose exec ollama ollama pull nomic-embed-text
```

Buka http://localhost:8000 dan login dengan `sari.finance` / `nala123`. Rincian di [panduan instalasi](./panduan-instalasi-dan-operasional.md).

## Gambaran Arsitektur

```
Browser ─> api (FastAPI) ─┬─> Ollama (LLM & embedding)
                          ├─> OpenSearch (knowledge base: BM25 + k-NN)
                          ├─> PostgreSQL (data operasional + audit log)
                          ├─> Redis (cache jawaban, rate limit, antrian ingest) ─> worker (RQ)
                          └─> Langfuse (trace)
Airflow ─> ingest ulang knowledge base (manual)
Adminer · RedisInsight · OpenSearch Dashboards ─> GUI pengembangan
```
