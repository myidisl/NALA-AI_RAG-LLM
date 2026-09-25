# Pengujian — NALA

**Versi Dokumen:** 1.0
**Tanggal:** 2026-09-25

Dokumen ini merangkum pengujian yang sudah dilakukan selama pengembangan dan menyediakan skenario uji manual untuk regresi. Laporan rinci uji retrieval ada di folder [`ujicoba/`](../ujicoba/README.md).

---

## 1. Evaluasi Kualitas Retrieval

### 1.1 Alat Evaluasi

| File | Fungsi |
|---|---|
| `app/evaluation.py` | Metrik murni: `is_relevant` (heuristik kata kunci `must_contain`, ambang ≥ separuh istilah), `precision_at_k`, `hit_rate_at_k`, `reciprocal_rank` (dasar MRR) |
| `app/llm_judge.py` | LLM-as-judge lokal: skor **faithfulness** dan **relevance** 1–5 |
| `app/run_evaluation.py` | Membandingkan hybrid top-3 vs hybrid top-20 → rerank top-3 (`docker compose exec api python -m app.run_evaluation`) |

> `run_evaluation.py` memerlukan `app/eval_testset.py` (list `QA_TESTSET` berisi `question` dan `must_contain`) yang belum ada di repository.

### 1.2 Hasil Uji Coba (ringkasan `ujicoba/`)

Uji coba 3 — 7 pertanyaan SOP Konfigurasi Firewall:

| Konfigurasi | Jawaban masuk konteks | MRR | Chunk ke LLM | Latensi retrieval |
|---|---|---|---|---|
| Naive RAG (vector top-3) | 1/7 | 0.14 | 3 | 121 ms |
| **BM25** | **6/7** | **0.79** | 6 | **15 ms** |
| BM25 + rerank | 5/7 | 0.64 | 3 | 348 ms |
| Vector | 3/7 | 0.21 | 6 | 113 ms |
| Vector + rerank | 3/7 | 0.43 | 3 | 387 ms |
| Hybrid | 4/7 | 0.50 | 3 | 133 ms |
| Hybrid + rerank | 5/7 | 0.64 | 3 | 427 ms |

Temuan utama:
1. BM25 paling andal dan tercepat untuk korpus SOP berbahasa Indonesia.
2. Embedding `nomic-embed-text` lemah untuk bahasa Indonesia; hybrid ikut terseret.
3. Reranker membantu sebagian (hybrid 4/7 → 5/7) tetapi pernah membuang jawaban #1 BM25 — model reranker berbahasa Inggris.
4. Menghapus dokumen duplikat menurunkan index dari 857 ke 615 chunk dan memperbaiki hasil.
5. Belum ada ambang skor minimum, sehingga pertanyaan di luar knowledge base tetap mendapat konteks.

Rekomendasi: uji reranker multibahasa (mis. `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`), pertimbangkan BM25 sebagai default, tambahkan ambang skor BM25.

---

## 2. Pengujian Fitur Module 27–29

Pengujian berikut dijalankan dengan FastAPI `TestClient`, database Postgres sementara (container dibuang setelah uji), Redis, dan LLM tiruan (*fake LLM*) agar hasil deterministik. Beberapa diverifikasi ulang terhadap stack yang berjalan.

### 2.1 Login & Sesi

| Skenario | Hasil |
|---|---|
| Akses `/`, `/upload`, `/data-operasional` (GET/POST) tanpa login | 303 → `/login` ✅ |
| `/chat`, `/chat/stream` tanpa login | 401 ✅ |
| Login password salah | 401 + pesan error ✅ |
| Login benar | 303 → `/`, banner "Masuk sebagai Sari [Staff Finance]" ✅ |
| `/login` saat sudah login | 303 → `/` ✅ |
| Logout | Sesi dihapus, halaman kembali ke login ✅ |

### 2.2 Role Database (`nala_app`)

| Operasi sebagai `nala_app` | Hasil |
|---|---|
| INSERT / SELECT `audit_log` | Berhasil ✅ |
| UPDATE / DELETE `audit_log` | `permission denied` ✅ |
| SELECT `pengajuan_kredit`, INSERT `klaim_asuransi` | `permission denied` ✅ |

### 2.3 Audit Log

| Skenario | Hasil |
|---|---|
| Penulisan normal 6 kolom | Tersimpan ✅ |
| Pertanyaan berisi `x'); DROP TABLE audit_log;--` | Tersimpan sebagai teks (placeholder `%s`) ✅ |
| Database mati / password salah | Tidak raise; error tercatat di log `nala.audit`; `/chat` tetap 200 ✅ |
| Nama tool > 50 karakter | Error tertangkap (`psycopg.Error`), `/chat` tetap 200 ✅ |

### 2.4 RBAC Agent

| Role | Tool SQL dieksekusi | `called_tools` SQL | Pesan |
|---|---|---|---|
| `staff_umum`, `staff_netsec`, tanpa role | Tidak (0 kali) | `diizinkan: False` | "Akses ditolak: ..." ✅ |
| `staff_finance`, `supervisor` | Ya | `diizinkan: True` | Data ✅ |

Tambahan: semua role ditawari kedua tool ✅; argumen tidak valid ditangkap dan dikembalikan ke model ✅; `name` dan `tool_call_id` ada di setiap pesan tool ✅; field `role`/`user_id` di body request diabaikan (Budi tetap ditolak) ✅.

### 2.5 Cache Jawaban

| Skenario | Panggilan LLM | `tool_used` |
|---|---|---|
| Pertanyaan pertama | 2 | – |
| Pertanyaan identik, role sama | 0 | `cache` ✅ |
| Pertanyaan identik, role berbeda | 2 (tidak berbagi cache) | – ✅ |
| Dengan `history` | Cache dilewati dan tidak disimpan ✅ | – |
| Redis mati | Menjawab normal (200) ✅ | – |

Fungsi `app/cache.py`: miss → `None`, hit → jawaban, TTL sesuai `CACHE_TTL_SECONDS`, `invalidate_answer_cache()` hanya menghapus `nala:answer:*` ✅.

### 2.6 Antrian Ingest (RQ)

| Skenario | Hasil |
|---|---|
| Job `ingest_document_job('sop-klaim-asuransi.md')` | `finished`, 15 chunk, cache dikosongkan ✅ |
| `POST /upload` | Response 0,075 detik dengan job ID; worker memproses job (`Job OK`) ✅ |

### 2.7 Rate Limiting

| Bucket | Hasil |
|---|---|
| `chat` | Request ke-21 → 429; `/chat/stream` ikut 429 (berbagi bucket) ✅ |
| `upload` | Request ke-6 → 429 ✅ |
| `data-operasional` | Gabungan kedua endpoint, request ke-11 → 429 ✅ |
| TTL key | ±60 detik, dipasang sekali ✅ |
| Redis mati | Request tetap dilayani (fail-open) ✅ |

### 2.8 Badge Tool & Lampiran Sumber

| Tool yang diminta model | Sari (`staff_finance`) | Budi (`staff_umum`) |
|---|---|---|
| SOP saja | `rag` | `rag` |
| SQL saja | `sql` | `none` (ditolak tidak dihitung) |
| SOP + SQL | `mixed` | `rag` |
| Tanpa tool | `none` | `none` |

`rag_search()` mengembalikan tuple di ketiga jalur (normal, kosong, error) ✅; sumber tanpa duplikat, `metadata` tanpa `source` menjadi `(tanpa nama)` ✅; nama file `<img src=x onerror=...>.md` tampil sebagai teks, 0 elemen `<img>` terbentuk ✅.

### 2.9 Tampilan

| Skenario | Hasil |
|---|---|
| Tema terang tidak berubah setelah tokenisasi warna | Sesuai tangkapan layar ✅ |
| Tema gelap (`prefers-color-scheme: dark`) | Latar #212121, aksen hijau, scrollbar gelap ✅ |
| Bubble user (baris baru dipertahankan) & bubble NALA (Markdown tanpa baris kosong ekstra) | ✅ |
| Lebar 375px | Tanpa scroll horizontal; 5 toggle satu kolom; area chat ≥ 260px ✅ |
| Lebar 1000px | Tidak berubah dari sebelumnya ✅ |

---

## 3. Skenario Uji Manual (Regresi)

Jalankan setelah perubahan besar. Semua dengan mode agent kecuali disebut lain.

| No | Langkah | Hasil yang diharapkan |
|---|---|---|
| M-01 | Buka `/` tanpa login | Diarahkan ke `/login` |
| M-02 | Login `budi.umum`, tanya "berapa pengajuan kredit yang ditolak?" | "Akses ditolak", tanpa badge 🗄️; `audit_log` baris `staff_umum`, `query_data_operasional`, `false` |
| M-03 | Login `sari.finance`, pertanyaan sama | Jawaban berisi angka + badge 🗄️; `audit_log` `true` |
| M-04 | Ulangi M-03 dengan kalimat identik | Badge ⚡ Dari cache; `audit_log` `tool_dipanggil = cache` |
| M-05 | `sari.finance`: "apa syarat KPR?" | Badge 📄 + daftar "Sumber dokumen" |
| M-06 | Mode chat (agent mati), RAG aktif, BM25 saja | Jawaban streaming bertahap |
| M-07 | Matikan RAG, tanya prosedur | Jawaban umum + saran mengaktifkan RAG |
| M-08 | Upload file `.md` kecil | Pesan job ID; `docker logs nala-worker` menunjukkan `Job OK` |
| M-09 | Upload file `.exe` | 400 |
| M-10 | Tambah data pengajuan kredit status `ditolak` | Tampil di baris teratas tabel |
| M-11 | Kirim 21 request chat dalam 1 menit | Request ke-21 → pesan "Terlalu banyak permintaan" |
| M-12 | Hentikan Redis (`docker stop nala-redis`), kirim chat | Tetap dijawab; nyalakan kembali Redis |
| M-13 | Set OS ke mode gelap, Ctrl+F5 | Tema gelap |
| M-14 | DevTools device mode 375px | Semua kontrol terlihat, tanpa scroll horizontal |
| M-15 | Logout | Kembali ke login; `/chat` → 401 |
