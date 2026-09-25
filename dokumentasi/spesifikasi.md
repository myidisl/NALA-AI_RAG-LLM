# Spesifikasi Teknis — NALA

**Nama Aplikasi:** NALA (*Not Another Lowkey Assistant*)
**Versi Dokumen:** 2.1
**Tanggal:** 2026-09-24
**Status:** Aktif — menggambarkan implementasi saat ini

**Riwayat Perubahan:**

| Versi | Tanggal | Ringkasan |
|---|---|---|
| 1.0 | 2026-09-23 | MVP: chat streaming ke Ollama, windowing konteks, reset, deployment Docker |
| 2.0 | 2026-09-24 | RAG berbasis OpenSearch, halaman upload knowledge base, pipeline ingest (Airflow), switch RAG di UI, persona asisten pegawai perbankan, redesain UI |
| 2.1 | 2026-09-24 | Streaming real-time dari Ollama (`httpx.stream`); folder knowledge base API & Airflow disatukan lewat bind mount `./app/knowledge-base` |

---

## 1. Ringkasan Sistem

NALA adalah aplikasi web chat berbasis LLM lokal untuk **pegawai perbankan**. Pengguna bertanya seputar teknologi maupun SOP internal bank melalui halaman web. Backend mencari potongan dokumen SOP yang relevan dari **knowledge base** (Retrieval-Augmented Generation / RAG), menyisipkannya sebagai konteks, lalu meneruskan percakapan ke server **Ollama** yang menjalankan model bahasa secara lokal. Jawaban dikirim balik ke browser sebagai *stream* teks.

Dokumen knowledge base (`.md`, `.txt`, `.pdf`) diunggah lewat halaman **Knowledge Base**, dipecah menjadi *chunk*, diubah menjadi vektor embedding oleh Ollama, dan disimpan di **OpenSearch** untuk pencarian kemiripan (k-NN).

Seluruh pemrosesan (LLM, embedding, penyimpanan vektor) berjalan di infrastruktur sendiri — tidak ada data percakapan maupun dokumen yang dikirim ke penyedia pihak ketiga.

---

## 2. Arsitektur

### 2.1 Diagram Alur Chat (RAG)

```
┌──────────────┐  POST /chat/stream  ┌──────────────┐  1. /api/embed        ┌──────────────────┐
│   Browser    │ ──────────────────> │   FastAPI    │ ────────────────────> │     Ollama       │
│  (chat.html) │                     │  (main.py)   │  3. /api/chat         │ nomic-embed-text │
│              │ <────────────────── │              │ <──────────────────── │ llama3.2:3b      │
└──────────────┘   text/plain        └──────┬───────┘   NDJSON              └──────────────────┘
                   (stream)                 │ 2. k-NN search (top 6)
                                            v
                                     ┌──────────────┐
                                     │  OpenSearch  │  index "nala-docs"
                                     └──────────────┘
```

### 2.2 Diagram Alur Ingest Dokumen

```
Upload (POST /upload)  ─┐                                   ┌─> Ollama /api/embed (per chunk)
                        ├─> simpan file ─> extract_text ─> chunk ─┤
Airflow DAG (manual)  ──┘   (pypdf / baca teks)                  └─> OpenSearch PUT /nala-docs/_doc/{file}-{i}
```

### 2.3 Komponen

| Komponen | File | Tanggung Jawab |
|---|---|---|
| Web Server & Routing | `app/main.py` | Endpoint chat, upload, dan halaman; retrieval konteks RAG; pemilihan system prompt; streaming response |
| Ollama Client | `app/ollama_client.py` | Wrapper HTTP ke API Ollama (`/api/generate`, `/api/chat`) |
| Embedding | `app/embeddings.py` | Mengubah teks menjadi vektor lewat Ollama `/api/embed` (model `nomic-embed-text`) |
| Vector Store | `app/vector_store.py` | Wrapper REST OpenSearch: buat index k-NN, simpan chunk, pencarian k-NN |
| Ingest | `app/ingest.py` | Ekstraksi teks (`.md`/`.txt`/`.pdf`), chunking, embedding, dan indexing ke OpenSearch |
| System Prompt | `app/system_prompt.py` | Persona & batasan NALA, plus 2 varian (tanpa konteks dokumen, RAG dimatikan) |
| Halaman Chat | `app/templates/chat.html` | UI chat + logika frontend (vanilla JavaScript) |
| Halaman Knowledge Base | `app/templates/upload.html` | Form upload dokumen dan daftar dokumen tersimpan (Jinja2, tanpa JavaScript) |
| Styling | `app/static/style.css` | Tampilan kedua halaman; aset logo `app/static/NALA_Logov2.jpg` |
| Pipeline Ingest | `airflow/dags/ingest_documents_dag.py` | DAG Airflow `ingest_documents` untuk ingest seluruh folder knowledge base |
| Kontainerisasi | `app/Dockerfile`, `docker-compose.yml` | Build image API dan orkestrasi 5 service |

---

## 3. Teknologi yang Digunakan

| Kategori | Teknologi | Versi |
|---|---|---|
| Bahasa | Python | 3.12 |
| Web Framework | FastAPI | 0.141.1 |
| ASGI Server | Uvicorn | 0.53.0 |
| HTTP Client | httpx | 0.28.1 (API) / 0.27.2 (Airflow) |
| Validasi Data | Pydantic | 2.13.5 |
| Template Engine | Jinja2 | 3.1.4 |
| ASGI Toolkit | Starlette | 1.6.0 |
| Upload Multipart | python-multipart | 0.0.12 |
| Ekstraksi PDF | pypdf | 5.1.0 |
| LLM Runtime | Ollama | latest |
| Model Chat | llama3.2:3b | — |
| Model Embedding | nomic-embed-text (768 dimensi) | — |
| Vector Store | OpenSearch (+ plugin k-NN, HNSW/nmslib, cosine similarity) | 2.11.0 |
| UI Vector Store | OpenSearch Dashboards | 2.11.0 |
| Orkestrasi Pipeline | Apache Airflow (mode standalone) | 2.10.2 |
| Frontend | HTML + CSS + JavaScript (tanpa framework) | — |
| Deployment | Docker + Docker Compose | — |

---

## 4. Spesifikasi API

### 4.1 `GET /`

Menampilkan halaman chat utama.

- **Response:** `text/html` — render dari `app/templates/chat.html`

### 4.2 `GET /health`

Health check untuk monitoring/orkestrator. Hanya menandakan proses API hidup; **tidak** memeriksa Ollama maupun OpenSearch.

- **Response:** `200 OK`
  ```json
  { "status": "ok" }
  ```

### 4.3 `POST /chat/stream`

Mengirim percakapan ke model dan menerima balasan sebagai stream teks.

**Request Body:**
```json
{
  "messages": [
    { "role": "user", "content": "Apa syarat pengajuan kredit?" },
    { "role": "assistant", "content": "Syaratnya ..." },
    { "role": "user", "content": "Berapa lama prosesnya?" }
  ],
  "use_rag": true
}
```

| Field | Tipe | Wajib | Keterangan |
|---|---|---|---|
| `messages` | array `{role, content}` | Ya | Seluruh riwayat percakapan, urut dari yang terlama |
| `use_rag` | boolean | Tidak (default `true`) | `false` = lewati pencarian dokumen |

**Aturan Validasi:**

| Kondisi | Hasil |
|---|---|
| `messages` kosong | `400 Bad Request` |
| Pesan terakhir bukan `role: "user"` | `400 Bad Request` |
| Struktur body tidak sesuai skema | `422 Unprocessable Entity` (otomatis oleh Pydantic) |

**Response:** `200 OK`, `Content-Type: text/plain`, body berupa aliran potongan teks balasan.

**Pemrosesan Internal:**
1. Ambil maksimal **10 pesan terakhir** (`HISTORY_WINDOW`) dari `messages`.
2. Jika `use_rag = true`: buat embedding dari **pesan user terakhir**, lalu cari **6 chunk** paling mirip (`top_k=6`) di index `nala-docs`. Bila Ollama/OpenSearch gagal (`httpx.HTTPError`), hasil dianggap kosong dan chat tetap berjalan.
3. Pilih system prompt dan isi pesan terakhir:

   | Kondisi | System prompt | Isi pesan user terakhir |
   |---|---|---|
   | `use_rag = false` | `NALA_SYSTEM_PROMPT_RAG_OFF` | Pertanyaan apa adanya |
   | RAG aktif, ada hasil | `SYSTEM_PROMPT` | `Konteks:\n[sumber]\nteks ...\n\nPertanyaan: ...` |
   | RAG aktif, tanpa hasil | `NALA_SYSTEM_PROMPT_NO_CONTEXT` | Pertanyaan apa adanya |

   Setiap chunk konteks diberi label nama file sumber (`[SOP-xxx.md]`) agar model tidak mencampur isi antar-dokumen. Konteks hanya disisipkan ke giliran terakhir, bukan ke riwayat.
4. Kirim ke Ollama `POST /api/chat` (`stream: true`) dengan urutan pesan: system → riwayat → pesan terakhir, memakai `httpx.stream()` sehingga respons dibaca sambil berjalan.
5. Parse respons NDJSON baris per baris, *yield* `message.content` tiap chunk begitu diterima (token langsung diteruskan ke browser), berhenti saat `done: true`.

### 4.4 `GET /upload`

Menampilkan halaman Knowledge Base: form upload dan daftar dokumen tersimpan.

- **Response:** `text/html` — render `app/templates/upload.html` dengan `documents` = nama file `.md`/`.txt`/`.pdf` di `KNOWLEDGE_BASE_DIR` (urut alfabetis, tanpa subfolder).

### 4.5 `POST /upload`

Menyimpan dokumen baru ke knowledge base lalu langsung meng-*ingest*-nya.

- **Request:** `multipart/form-data`, field `file`.
- **Validasi:**

  | Kondisi | Hasil |
  |---|---|
  | Ekstensi bukan `.md`, `.txt`, atau `.pdf` | `400 Bad Request` |
  | Field `file` tidak ada | `422 Unprocessable Entity` |

- **Pemrosesan:**
  1. Nama file disanitasi dengan `os.path.basename()` (mencegah *path traversal*).
  2. File disimpan ke `KNOWLEDGE_BASE_DIR` — **menimpa** file dengan nama sama.
  3. `ingest_document()` dijalankan (lihat §6).
  4. Jika ingest gagal karena `httpx.HTTPError` (Ollama/OpenSearch tidak terjangkau), file tetap tersimpan dan pengguna diminta mengunggah ulang atau menjalankan DAG `ingest_documents` di Airflow setelah layanan aktif.
- **Response:** `200 OK`, `text/html` — halaman Knowledge Base dengan pesan status dan daftar dokumen terbaru.

---

## 5. Manajemen Konteks Percakapan

- **Penyimpanan:** riwayat percakapan disimpan **di memori browser** (variabel `conversation` pada JavaScript). Tidak ada database maupun session di sisi server — server bersifat *stateless*.
- **Windowing:** hanya **10 pesan terakhir** yang dikirim ke model untuk mencegah prompt membengkak dan menjaga latensi tetap stabil. Pemangkasan dilakukan di server; browser tetap mengirim seluruh riwayat.
- **Indikator UI:** setelah riwayat mencapai 10 pesan (pesan berikutnya mulai memotong riwayat terlama), UI menampilkan catatan bahwa hanya 10 pesan terakhir yang menjadi konteks.
- **Retrieval:** pencarian dokumen hanya memakai pesan user terakhir, bukan seluruh riwayat.
- **Reset:** tombol Reset mengosongkan riwayat setelah konfirmasi pengguna.
- **Konsekuensi:** menutup atau me-*refresh* halaman akan menghapus seluruh riwayat percakapan.

---

## 6. Knowledge Base & Pipeline Ingest

### 6.1 Format & Ekstraksi

| Format | Cara Ekstraksi | Cara Chunking |
|---|---|---|
| `.md` | Dibaca sebagai teks | Per *heading* (`#` s.d. `######`); section > 500 karakter dipecah lagi per ukuran tetap |
| `.txt` | Dibaca sebagai teks | Ukuran tetap |
| `.pdf` | `pypdf`, teks per halaman digabung. **Tanpa OCR** — PDF hasil scan menghasilkan teks kosong | Ukuran tetap |

Chunking ukuran tetap: **500 karakter** dengan **overlap 50 karakter**.

### 6.2 Index OpenSearch

- **Nama index:** `nala-docs` (dibuat otomatis oleh `ensure_index()` bila belum ada).
- **Mapping:**

  | Field | Tipe | Keterangan |
  |---|---|---|
  | `text` | `text` | Isi chunk |
  | `embedding` | `knn_vector`, 768 dimensi | HNSW, engine `nmslib`, `cosinesimil` |
  | `metadata` | `object` | `{"source": "<nama file>"}` |

- **ID dokumen:** `<nama file>-<urutan chunk>` (di-*URL-encode*). Ingest ulang file yang sama menimpa chunk dengan ID yang sama.
- **Refresh:** setiap `PUT` memakai `refresh=true` sehingga chunk langsung bisa dicari.

### 6.3 Jalur Ingest

| Jalur | Pemicu | Folder Sumber |
|---|---|---|
| Upload | `POST /upload` — satu file, langsung setelah disimpan | `/code/app/knowledge-base` di container `api` |
| Airflow DAG `ingest_documents` | Manual dari UI/CLI Airflow (`schedule=None`) — seluruh folder | `/opt/airflow/knowledge-base` di container `airflow` |

Kedua path di atas adalah **bind mount dari folder host yang sama, `./app/knowledge-base`**. Dengan begitu dokumen hasil upload tersimpan permanen di host, ikut di-*ingest* ulang oleh DAG, dan dokumen yang disalin langsung ke folder tersebut juga tampil di halaman Knowledge Base. Kedua jalur memakai fungsi yang sama (`app/ingest.py`) dan menulis ke index yang sama.

---

## 7. Konfigurasi

Konfigurasi dibaca dari *environment variable*; untuk `OllamaClient` berlaku fallback **argumen konstruktor → environment variable → nilai default**.

| Variabel | Default | Keterangan |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Alamat server Ollama (chat & embedding). Pada Docker Compose: `http://ollama:11434` |
| `OLLAMA_MODEL` | `llama3.2:3b` | Model untuk endpoint chat |
| `OPENSEARCH_BASE_URL` | `http://localhost:9200` | Alamat OpenSearch. Pada Docker Compose: `http://opensearch:9200` |
| `KNOWLEDGE_BASE_DIR` | `app/knowledge-base` | Folder dokumen yang ditampilkan & menjadi tujuan upload. Pada Docker Compose: `/code/app/knowledge-base` (bind mount dari `./app/knowledge-base`) |

**Konstanta dalam kode:**

| Konstanta | Nilai | Lokasi |
|---|---|---|
| `HISTORY_WINDOW` | `10` pesan | `app/main.py` |
| Jumlah chunk konteks (`top_k`) | `6` | `app/main.py` |
| Nama index | `nala-docs` | `app/main.py`, `app/ingest.py` |
| Model embedding | `nomic-embed-text` | `app/embeddings.py` |
| Dimensi vektor | `768` | `app/vector_store.py` |
| Ukuran / overlap chunk | `500` / `50` karakter | `app/ingest.py` |
| Ekstensi yang didukung | `.md`, `.txt`, `.pdf` | `app/main.py`, `app/ingest.py` |
| Timeout Ollama chat/generate | `120` detik | `app/ollama_client.py` |
| Timeout Ollama embedding | `60` detik | `app/embeddings.py` |
| Timeout OpenSearch | `30` detik | `app/vector_store.py` |

---

## 8. Perilaku Model (System Prompt)

`SYSTEM_PROMPT` mendefinisikan lima aspek:

| Aspek | Ketentuan |
|---|---|
| **Role** | Asisten pribadi pegawai perbankan yang serba tahu teknologi: software, hardware, jaringan, cloud, keamanan siber, data & AI, teknologi perbankan (core banking, mobile/internet banking, sistem pembayaran, fintech) |
| **Task** | Menjawab akurat dan jelas dikaitkan dengan konteks kerja bank; membantu pekerjaan sehari-hari (aplikasi kantor, troubleshooting, pengolahan data, otomasi); memakai analogi; memberi langkah praktis; mengingatkan praktik keamanan informasi |
| **Context** | Pengguna beragam (frontliner, operasional, marketing, analis, manajemen, tim IT); jawaban ringkas; info yang cepat berubah disampaikan sebagai perkiraan disertai saran verifikasi |
| **Persona** | Ramah, sabar, antusias; gaya bahasa Gen-Z; menutup setiap jawaban dengan pantun pendek |
| **Constraints** | Dilarang mengarang fakta; menolak permintaan ilegal/merusak; mengakui diri sebagai AI; maksimal 50 kalimat; **menolak pertanyaan di luar lingkup teknologi dan SOP**; tidak meminta/memproses data rahasia nasabah maupun kredensial; untuk kebijakan internal/regulasi (OJK/BI) merujuk ke SOP atau unit terkait |

**Varian:**

| Konstanta | Dipakai Saat | Tambahan Aturan |
|---|---|---|
| `NALA_SYSTEM_PROMPT_NO_CONTEXT` | RAG aktif tapi tidak ada chunk yang ditemukan / retrieval gagal | Jawab dari pengetahuan umum dan sebutkan bahwa jawaban akan lebih akurat setelah dokumen SOP diunggah |
| `NALA_SYSTEM_PROMPT_RAG_OFF` | Pengguna mematikan switch RAG | Jawab dari pengetahuan umum tanpa merujuk SOP; untuk prosedur internal sarankan mengaktifkan kembali "Pakai RAG" |

---

## 9. Antarmuka Pengguna

### 9.1 Halaman Chat (`/`)

**Elemen halaman:**
- **Top bar:** logo & nama NALA, navigasi (Chat | Knowledge Base), jumlah pesan, tombol Reset.
- **Area percakapan:** mengisi tinggi layar dan dapat di-*scroll*, auto-scroll ke pesan terbaru. Saat kosong menampilkan layar sambutan (logo + sapaan).
- **Pesan:** pesan user berupa *bubble* di kanan; balasan NALA tanpa *bubble* dengan avatar dan nama.
- **Composer:** kotak input, switch **"Pakai RAG (cari dari dokumen)"** (default aktif), tombol Kirim, catatan windowing, dan disclaimer *"NALA bisa keliru. Untuk prosedur resmi, selalu cek kembali ke SOP internal."*

**Logika frontend:**
- **Streaming render:** token tampil segera setelah dihasilkan Ollama; respons dibaca via `ReadableStream` reader dan `TextDecoder`, elemen balasan diperbarui setiap chunk masuk.
- **Indikator status:** teks "sedang mengetik" beranimasi sebelum chunk pertama; input & tombol dikunci selama menunggu (tombol menampilkan spinner); kursor berkedip selama stream berlangsung.
- **Penanganan error:** status HTTP non-2xx atau error jaringan menampilkan pesan *"Gagal mendapatkan balasan (...). Coba lagi."* di tempat balasan.
- **Formatting ringan:** `**teks**` → tebal, `*teks*` → miring, baris baru → `<br>`.
- **Keamanan:** seluruh teks di-*escape* melalui `escapeHtml()` sebelum disisipkan ke DOM untuk mencegah XSS. Formatting markdown diterapkan **setelah** proses escape.

### 9.2 Halaman Knowledge Base (`/upload`)

- Form upload (`accept=".md,.txt,.pdf"`) yang dikirim sebagai `multipart/form-data` biasa — tanpa JavaScript.
- Pesan status hasil upload/ingest.
- Daftar nama dokumen di `KNOWLEDGE_BASE_DIR`.

### 9.3 Tampilan

- Responsif (breakpoint 600px): nama brand dan label tombol Reset disembunyikan di layar sempit.
- Menghormati `prefers-reduced-motion` (animasi dimatikan).

---

## 10. Deployment

### 10.1 Docker Compose

| Service | Port | Keterangan |
|---|---|---|
| `ollama` | 11434 | Image `ollama/ollama:latest`; volume `ollama_data` mem-*persist* model |
| `opensearch` | 9200 | Image `opensearchproject/opensearch:2.11.0`; single-node, **security plugin dimatikan**, heap 512 MB; volume `opensearch_data` |
| `opensearch-dashboards` | 5601 | UI web untuk melihat index & dokumen; security plugin dimatikan |
| `api` | 8000 | Build dari `./app/Dockerfile`; bind mount `./app/knowledge-base` → `/code/app/knowledge-base`; `depends_on: ollama, opensearch` |
| `airflow` | 8080 | Image `apache/airflow:2.10.2`, mode `standalone`; me-mount `./airflow/dags`, `./app` (ke `dags/app`), dan `./app/knowledge-base` (ke `/opt/airflow/knowledge-base`); memasang `pypdf` & `httpx` via `_PIP_ADDITIONAL_REQUIREMENTS` |

`depends_on` hanya mengatur urutan start, tidak menunggu service siap.

**Menjalankan:**
```bash
docker compose up -d --build
docker compose exec ollama ollama pull llama3.2:3b
docker compose exec ollama ollama pull nomic-embed-text
```

| Aplikasi | URL |
|---|---|
| NALA (chat & knowledge base) | `http://localhost:8000` |
| OpenSearch Dashboards | `http://localhost:5601` |
| Airflow (user `admin`, password dicetak di log saat start pertama) | `http://localhost:8080` |

### 10.2 Menjalankan Lokal (tanpa Docker)

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Prasyarat: dijalankan dari root project (path `app/static`, `app/templates`, `app/knowledge-base` relatif terhadap working directory); Ollama berjalan di `localhost:11434` dengan model `llama3.2:3b` dan `nomic-embed-text` sudah di-*pull*; OpenSearch berjalan di `localhost:9200` (opsional — tanpa OpenSearch chat tetap jalan tanpa konteks dokumen).

---

## 11. Kebutuhan Non-Fungsional

| Aspek | Ketentuan / Kondisi Saat Ini |
|---|---|
| **Privasi** | Inferensi, embedding, dan penyimpanan vektor berjalan lokal; tidak ada data keluar ke pihak ketiga |
| **Persistensi** | Riwayat chat tidak disimpan (hilang saat halaman ditutup). Dokumen knowledge base tersimpan di host (`./app/knowledge-base`); index OpenSearch dan model Ollama di-*persist* lewat named volume |
| **Autentikasi** | Belum ada — baik aplikasi NALA, halaman upload, maupun OpenSearch/Dashboards (security plugin dimatikan) |
| **Ketahanan** | Chat tetap berjalan tanpa konteks bila Ollama embedding/OpenSearch gagal; upload tetap menyimpan file bila ingest gagal |
| **Timeout** | 120 detik (chat), 60 detik (embedding), 30 detik (OpenSearch) |
| **Skalabilitas** | Backend stateless untuk chat; throughput dibatasi kapasitas Ollama. Dokumen upload disimpan di folder host lewat bind mount, sehingga instance di host lain perlu penyimpanan bersama |
| **Logging & Monitoring** | Log bawaan Uvicorn dan Airflow; endpoint `/health` hanya memeriksa proses API |
| **Keamanan Upload** | Nama file disanitasi, ekstensi divalidasi di server; belum ada batas ukuran file |

---

## 12. Batasan & Catatan Implementasi

1. **Error dari Ollama saat chat tidak terdeteksi.** `chat_stream()` tidak memanggil `raise_for_status()`; bila model belum di-*pull* atau Ollama mengembalikan error, balasan tampil kosong tanpa pesan error.
2. **Chunk lama tidak dibersihkan.** Ingest ulang file yang versinya lebih pendek menyisakan chunk lama dengan nomor urut lebih tinggi; belum ada fitur hapus dokumen dari UI maupun index.
3. **PDF hasil scan tidak terbaca** karena belum ada OCR.
4. **Encoding file teks.** `extract_text()` membuka file tanpa `encoding="utf-8"`; saat dijalankan langsung di Windows, dokumen UTF-8 berkarakter khusus dapat gagal dibaca.
5. **DAG ganda.** `app/airflow/ingest_documents_dag.py` merupakan salinan `airflow/dags/ingest_documents_dag.py` dan tidak dipakai oleh Airflow.
6. **Kualitas jawaban terbatas oleh model.** `llama3.2:3b` adalah model kecil (3 miliar parameter) — cocok untuk perangkat modest, namun akurasinya di bawah model besar.
7. **Tidak ada retry** ke Ollama/OpenSearch.
8. **Method `generate()` belum dipakai.** `OllamaClient.generate()` (endpoint `/api/generate`, non-streaming) tersedia tetapi belum dipanggil.
9. **Tanpa rate limiting** dan tanpa batas ukuran upload.

---

## 13. Struktur Direktori

```
NALA/
├── airflow/
│   └── dags/
│       └── ingest_documents_dag.py   # DAG Airflow "ingest_documents"
├── app/
│   ├── airflow/
│   │   └── ingest_documents_dag.py   # Salinan DAG (tidak dipakai Airflow)
│   ├── knowledge-base/               # Dokumen SOP untuk RAG (di-mount ke api & airflow)
│   ├── static/
│   │   ├── NALA_Logov2.jpg           # Logo & favicon
│   │   └── style.css                 # Styling halaman chat & knowledge base
│   ├── templates/
│   │   ├── chat.html                 # UI chat + logika frontend
│   │   └── upload.html               # Halaman upload & daftar dokumen
│   ├── Dockerfile                    # Image service API
│   ├── embeddings.py                 # Embedding teks via Ollama
│   ├── ingest.py                     # Ekstraksi, chunking, indexing dokumen
│   ├── main.py                       # Endpoint FastAPI
│   ├── ollama_client.py              # Client HTTP ke Ollama
│   ├── system_prompt.py              # Persona & batasan asisten (+ varian)
│   ├── vector_store.py               # Client REST OpenSearch (k-NN)
│   └── requirements.txt
├── dokumentasi/
│   ├── spesifikasi.md                # Dokumen ini
│   └── BRD.md                        # Business Requirements Document
├── tambahan dokumen/                 # Dokumen SOP tambahan yang belum masuk knowledge base
├── docker-compose.yml                # Orkestrasi 5 service
└── requirements.txt
```
