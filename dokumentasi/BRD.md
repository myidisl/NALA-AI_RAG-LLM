# Business Requirements Document (BRD) — NALA

**Nama Proyek:** NALA (*Not Another Lowkey Assistant*)
**Organisasi:** PT Nusantara Finance (studi kasus)
**Versi Dokumen:** 3.0
**Tanggal:** 2026-09-25
**Status:** Draft — beberapa bagian berisi asumsi yang perlu dikonfirmasi *business owner* (ditandai ⚠)

**Riwayat Perubahan:**

| Versi | Tanggal | Ringkasan |
|---|---|---|
| 1.0 | 2026-09-23 | MVP asisten tanya-jawab teknologi umum |
| 2.0 | 2026-09-24 | Fokus ke pegawai perbankan; tanya-jawab berbasis dokumen SOP internal (RAG); upload knowledge base; pipeline ingest |
| 2.1 | 2026-09-24 | FR-02, FR-18, NFR-02, NFR-10 terpenuhi (streaming real-time, folder knowledge base persisten & seragam) |
| 3.0 | 2026-09-25 | Kualitas retrieval (BM25, hybrid, reranking, evaluasi); data operasional & mode agent; login, RBAC, dan audit log; cache, antrian ingest, rate limiting; observability; pembaruan UI. FR-20 dan NFR-11 terpenuhi; FR-24 s.d. FR-40 ditambahkan |

> Dokumen terkait: [Spesifikasi Teknis](./spesifikasi.md) · [Keamanan, RBAC & Audit](./keamanan-rbac-audit.md) · [Panduan Pengguna](./panduan-pengguna.md) · [Riwayat Pengembangan](./riwayat-pengembangan.md)

---

## 1. Latar Belakang

Pegawai bank setiap hari membutuhkan jawaban cepat atas tiga jenis pertanyaan:

1. **Pertanyaan teknologi** — aplikasi kantor, perangkat, sistem perbankan digital, keamanan informasi.
2. **Pertanyaan prosedur** — tersebar di banyak dokumen SOP internal (kredit, layanan, firewall, pengadaan, dsb.).
3. **Pertanyaan data operasional** — status dan jumlah pengajuan kredit atau klaim asuransi, termasuk data nasabah tertentu.

Mencari prosedur dan data secara manual memakan waktu, sementara asisten AI berbasis cloud menimbulkan dua hambatan: **biaya per token** dan **risiko kerahasiaan data**. Selain itu, data nasabah tidak boleh dapat diakses semua pegawai — akses harus mengikuti peran dan dapat diaudit.

NALA menjawab kebutuhan tersebut: asisten AI yang berjalan **sepenuhnya di infrastruktur sendiri**, menjawab berdasarkan **dokumen SOP internal** dan **data operasional**, dengan **login, pembatasan akses per peran, dan jejak audit**.

---

## 2. Tujuan Bisnis

| No | Tujuan | Indikator Keberhasilan ⚠ |
|---|---|---|
| B-1 | Menyediakan akses tanya-jawab teknologi yang cepat dan mudah dipahami | Pegawai memperoleh jawaban relevan tanpa berpindah ke mesin pencari |
| B-2 | Mempercepat akses ke prosedur internal (SOP) | Pertanyaan prosedur dijawab dengan merujuk dokumen SOP sumbernya |
| B-3 | Menjaga kerahasiaan data percakapan, dokumen, dan data nasabah | 0% data keluar dari jaringan internal |
| B-4 | Menekan biaya operasional asisten AI | Tidak ada biaya per-token; biaya terbatas pada infrastruktur server |
| B-5 | Knowledge base dapat diperbarui tanpa tim pengembang | Dokumen baru diunggah lewat web dan dapat ditanyakan setelah proses background selesai |
| B-6 | Fondasi teknis yang dapat dikembangkan | Arsitektur modular; model, endpoint, dan batas dikonfigurasi lewat *environment variable* |
| B-7 | Menyediakan jawaban atas data operasional secara aman | Staf berwenang mendapat angka/status transaksi lewat chat; staf tidak berwenang ditolak |
| B-8 | Memastikan akses data dapat dipertanggungjawabkan | Setiap pertanyaan mode agent tercatat (siapa, role, tool, diizinkan/ditolak) |
| B-9 | Menjaga layanan tetap stabil saat beban naik | Pertanyaan berulang dijawab dari cache; request berlebihan dibatasi; ingest tidak memblokir pengguna |

---

## 3. Ruang Lingkup

### 3.1 Termasuk dalam Lingkup (In Scope)

- Login berbasis sesi dengan akun demo per role; logout
- Antarmuka web chat (bubble, streaming, Markdown, tema gelap, responsif)
- Tanya-jawab teknologi dan SOP (RAG) dengan pilihan metode pencarian (BM25 / Vector / Hybrid) dan reranking
- **Mode Agent**: model memilih sendiri tool dokumen SOP atau data operasional; badge tool dan lampiran dokumen sumber
- **RBAC** akses data operasional per role, ditegakkan saat eksekusi tool
- **Audit log** setiap pertanyaan mode agent
- Halaman Knowledge Base: upload `.md`, `.txt`, `.pdf`; ingest di background (antrian RQ); daftar dokumen
- Pipeline ingest ulang seluruh folder lewat Airflow (manual)
- Halaman Data Operasional: input dan daftar pengajuan kredit & klaim asuransi
- Cache jawaban (Redis) dan rate limiting per IP
- Observability (Langfuse) dan evaluasi kualitas retrieval
- GUI admin pengembangan: OpenSearch Dashboards, Adminer, RedisInsight, Airflow, Langfuse
- Deployment melalui Docker Compose

### 3.2 Tidak Termasuk dalam Lingkup (Out of Scope)

- Manajemen pengguna sungguhan (registrasi, ganti password, integrasi SSO/LDAP) — akun masih demo
- Penyimpanan permanen riwayat percakapan
- Pembatasan akses **dokumen SOP** per role (RBAC saat ini hanya untuk data operasional)
- Pengelolaan dokumen lanjutan (hapus, versi, persetujuan)
- Ubah/hapus data operasional dari UI (hanya tambah & lihat)
- OCR untuk dokumen hasil scan
- Integrasi dengan sistem inti (core banking, ticketing)
- Aplikasi mobile native dan dukungan suara

---

## 4. Pemangku Kepentingan ⚠

| Peran | Tanggung Jawab |
|---|---|
| *Business Owner* | Menetapkan tujuan, cakupan, prioritas |
| Pemilik Dokumen SOP / Unit Kepatuhan | Menjamin dokumen knowledge base valid, terbaru, dan tidak saling bertentangan |
| Divisi Kredit & Asuransi | Pemilik data operasional; menentukan siapa boleh mengakses |
| Tim Keamanan Informasi / Audit Intern | Menetapkan kebijakan akses, meninjau audit log |
| Tim Pengembang | Implementasi, pemeliharaan, deployment |
| Tim Infrastruktur / IT Ops | Server, kapasitas (CPU/GPU/RAM), monitoring layanan pendukung |
| Pengguna Akhir | Pegawai: staf umum, staf finance, supervisor, tim NetSec |

---

## 5. Persona & Role Pengguna

| Persona | Role sistem | Akun demo | Akses data operasional | SOP paling relevan |
|---|---|---|---|---|
| Staf Umum / General Affairs | `staff_umum` | `budi.umum` | ❌ | Pengadaan Barang & Jasa, Pengelolaan Aset Umum, Pengaduan Nasabah |
| Staf Finance / Kredit | `staff_finance` | `sari.finance` | ✅ | SOP kredit (pengajuan, UMKM, Multiguna, KKB, KPR, penagihan, pelunasan), klaim asuransi, APU-PPT |
| Supervisor | `supervisor` | `andi.super` | ✅ | Seluruh SOP bisnis, terutama limit kewenangan |
| Staf Network Security | `staff_netsec` | `thoriq.netsec` | ❌ | 8 SOP firewall, POJK 11/2022, SEOJK 29/2022 |
| Supervisor Network Security | `spv_netsec` | `zein.netsec` | ❌ | Sama dengan staf NetSec, fokus persetujuan change request & resertifikasi |

Semua akun demo memakai password `nala123` (khusus pengembangan).

---

## 6. Kebutuhan Fungsional

| ID | Kebutuhan | Prioritas | Status |
|---|---|---|---|
| FR-01 | Pengguna dapat mengirim pertanyaan melalui antarmuka web | Wajib | ✅ Selesai |
| FR-02 | Jawaban tampil bertahap (streaming) | Wajib | ✅ Selesai (mode chat) |
| FR-03 | Sistem mempertahankan konteks percakapan | Wajib | ✅ Selesai (kedua mode) |
| FR-04 | Konteks dibatasi 10 pesan terakhir | Wajib | ✅ Selesai |
| FR-05 | Info jumlah pesan dan pemberitahuan pemangkasan konteks | Sedang | ✅ Selesai |
| FR-06 | Reset percakapan dengan konfirmasi | Sedang | ✅ Selesai |
| FR-07 | Request tidak valid ditolak dengan pesan jelas | Wajib | ✅ Selesai |
| FR-08 | Endpoint health check | Sedang | ✅ Selesai |
| FR-09 | Jawaban mengikuti persona NALA | Sedang | ✅ Selesai |
| FR-10 | Menolak pertanyaan di luar lingkup | Wajib | ✅ Selesai |
| FR-11 | Model dan alamat server dapat dikonfigurasi tanpa ubah kode | Wajib | ✅ Selesai |
| FR-12 | Pesan error ramah di UI saat backend gagal | Wajib | ⚠ Sebagian — error HTTP/jaringan tampil; error internal Ollama saat streaming masih menghasilkan balasan kosong |
| FR-13 | Menjawab pertanyaan prosedur berdasarkan SOP (RAG) | Wajib | ✅ Selesai |
| FR-14 | RAG dapat diaktifkan/dinonaktifkan per pertanyaan | Sedang | ✅ Selesai |
| FR-15 | Upload `.md`, `.txt`, `.pdf` ke knowledge base | Wajib | ✅ Selesai (ingest di background) |
| FR-16 | Melihat daftar dokumen knowledge base | Sedang | ✅ Selesai |
| FR-17 | Chat tetap berfungsi tanpa konteks bila pencarian dokumen gagal | Wajib | ✅ Selesai |
| FR-18 | Ingest ulang seluruh folder lewat pipeline | Sedang | ✅ Selesai (manual via Airflow; belum terjadwal) |
| FR-19 | Mengingatkan pengguna tidak membagikan data rahasia | Wajib | ✅ Selesai (system prompt) |
| FR-20 | Jawaban mencantumkan dokumen sumber | Sedang | ✅ Selesai untuk mode Agent (lampiran "Sumber dokumen"); mode chat belum |
| FR-21 | Hapus/perbarui dokumen di knowledge base | Sedang | ❌ Belum |
| FR-22 | Riwayat percakapan tersimpan permanen | Rendah | ❌ Belum |
| FR-23 | Memilih model dari antarmuka | Rendah | ❌ Belum |
| FR-24 | Memilih metode pencarian (BM25 / Vector / Hybrid) dari UI | Sedang | ✅ Selesai |
| FR-25 | Mengaktifkan reranking hasil pencarian | Sedang | ✅ Selesai |
| FR-26 | Login dan logout; semua halaman wajib login | Wajib | ✅ Selesai (akun demo) |
| FR-27 | Identitas pengguna ditampilkan (nama & role) | Rendah | ✅ Selesai |
| FR-28 | Menjawab pertanyaan data operasional (jumlah per status, detail nasabah) | Wajib | ✅ Selesai (mode Agent) |
| FR-29 | Akses data operasional dibatasi per role | Wajib | ✅ Selesai (`staff_finance`, `supervisor`) |
| FR-30 | Setiap pertanyaan mode Agent tercatat di audit log | Wajib | ✅ Selesai |
| FR-31 | Pengguna melihat tool yang dipakai (badge) | Sedang | ✅ Selesai |
| FR-32 | Input data pengajuan kredit & klaim asuransi lewat web | Sedang | ✅ Selesai |
| FR-33 | Daftar data operasional berpaginasi | Rendah | ✅ Selesai |
| FR-34 | Pertanyaan berulang dijawab dari cache | Sedang | ✅ Selesai (mode Agent, tanpa riwayat) |
| FR-35 | Cache dikosongkan setelah dokumen baru selesai di-ingest | Sedang | ✅ Selesai |
| FR-36 | Pembatasan jumlah request per menit | Sedang | ✅ Selesai (per IP) |
| FR-37 | Upload tidak menunggu proses ingest | Sedang | ✅ Selesai (job ID ditampilkan) |
| FR-38 | Tema gelap | Rendah | ✅ Selesai (mengikuti OS/browser) |
| FR-39 | Tampilan nyaman di ponsel | Sedang | ✅ Selesai (breakpoint 600px & 480px) |
| FR-40 | Pembatasan akses dokumen SOP per role | Rendah | ❌ Belum |

---

## 7. Kebutuhan Non-Fungsional

| ID | Kategori | Kebutuhan | Status |
|---|---|---|---|
| NFR-01 | Privasi | Seluruh pemrosesan berjalan di infrastruktur internal | ✅ |
| NFR-02 | Responsivitas | Token pertama tampil sesegera mungkin (streaming) | ✅ |
| NFR-03 | Keamanan | Input/output aman dari XSS | ✅ (textContent, DOMPurify, escapeHtml) |
| NFR-04 | Keamanan Upload | Sanitasi nama file & validasi ekstensi | ✅ (batas ukuran belum) |
| NFR-05 | Portabilitas | Berjalan via Docker Compose | ✅ |
| NFR-06 | Skalabilitas | Backend stateless; ingest dipindah ke worker | ✅ (multi-host perlu penyimpanan bersama & Redis bersama) |
| NFR-07 | Konfigurasi | Perubahan lewat *environment variable* | ✅ |
| NFR-08 | Ketersediaan | Health check | ✅ (belum memeriksa dependensi) |
| NFR-09 | Aksesibilitas | Responsif, `prefers-reduced-motion`, tema gelap | ✅ |
| NFR-10 | Persistensi | Dokumen & data tetap ada setelah container dibuat ulang | ✅ (bind mount & named volume) |
| NFR-11 | Keamanan Akses | Aplikasi wajib login | ✅ (akun demo; layanan pendukung belum) |
| NFR-12 | Observability | Trace LLM, audit, metrik | ⚠ Sebagian — Langfuse & audit log ada; metrik penggunaan belum |
| NFR-13 | Ketahanan | Retry ke Ollama/OpenSearch | ❌ Belum (fail-open untuk Redis sudah) |
| NFR-14 | Least privilege database | Role database terpisah per kebutuhan | ✅ (readonly, writer, app) |
| NFR-15 | Integritas audit | Audit log tidak dapat diubah/dihapus aplikasi | ✅ (role `nala_app` tanpa UPDATE/DELETE) |
| NFR-16 | Keamanan query | Model tidak menulis SQL sendiri | ✅ (query tetap + whitelist + parameter) |
| NFR-17 | Kualitas jawaban | Kualitas retrieval dapat diukur | ✅ (precision@k, hit rate, MRR, LLM judge; lihat [pengujian](./pengujian.md)) |

---

## 8. Alur Proses Bisnis

### 8.1 Login

1. Pengguna membuka NALA → diarahkan ke halaman login.
2. Mengisi username & password → sistem memverifikasi dan menyimpan identitas (user, role, nama) di sesi selama 8 jam.
3. Banner "Masuk sebagai <nama> [<role>]" tampil di semua halaman; **Logout** menghapus sesi.

### 8.2 Tanya-Jawab Mode Chat (RAG)

1. Pengguna mengetik pertanyaan, memilih **Pakai RAG**, metode pencarian, dan **Rerank hasil**.
2. Sistem mencari potongan SOP paling relevan dan menyisipkannya sebagai konteks.
3. Jawaban tampil bertahap. Tanpa hasil relevan, model menjawab dari pengetahuan umum dan menyarankan pengunggahan SOP.

### 8.3 Tanya-Jawab Mode Agent

1. Pengguna menyalakan **Pakai Agent** dan bertanya (prosedur, data, atau keduanya).
2. Bila pertanyaan identik pernah dijawab untuk role yang sama (≤ 1 jam), jawaban diambil dari cache (badge ⚡).
3. Selain itu, agent memilih tool: **dokumen SOP** dan/atau **data operasional**.
4. Bila role pengguna tidak berwenang atas data operasional, tool tidak dijalankan dan NALA menyampaikan "Akses ditolak".
5. Jawaban tampil beserta badge tool dan daftar dokumen sumber.
6. Sistem mencatat pertanyaan, role, tool, dan status izin ke audit log.

### 8.4 Pembaruan Knowledge Base

1. Pengguna mengunggah dokumen di halaman **Knowledge Base**.
2. Sistem menyimpan file dan langsung membalas dengan nomor job; ingest berjalan di background.
3. Setelah selesai, dokumen dapat ditanyakan dan cache jawaban dikosongkan.
4. Tim IT dapat menjalankan DAG Airflow untuk meng-ingest ulang seluruh folder.

### 8.5 Input Data Operasional

1. Pengguna membuka **Data Operasional**, mengisi form pengajuan kredit atau klaim asuransi.
2. Sistem memvalidasi (status sesuai aturan, format angka/tanggal) dan menyimpan data.
3. Data baru langsung tampil di halaman pertama tabel dan dapat ditanyakan lewat mode Agent.

### 8.6 Peninjauan Audit

1. Tim audit/keamanan membuka `audit_log` (mis. lewat Adminer).
2. Meninjau percobaan akses yang ditolak (`akses_diizinkan = false`) dan pola pertanyaan per role.

---

## 9. Asumsi

| No | Asumsi |
|---|---|
| A-1 | Model chat (`qwen2.5:7b`) dan embedding (`nomic-embed-text`) sudah di-*pull* ke Ollama |
| A-2 | Kapasitas komputasi memadai untuk Ollama, OpenSearch, Postgres, Redis, Airflow, Langfuse secara bersamaan |
| A-3 | Aplikasi diakses dari jaringan internal tepercaya; akun demo hanya untuk pengembangan |
| A-4 | Pengguna memahami riwayat percakapan hilang saat halaman ditutup |
| A-5 | Dokumen SOP yang diunggah valid, terbaru, tidak saling bertentangan, dan boleh dibaca semua pengguna ⚠ |
| A-6 | Jawaban NALA bersifat bantuan; keputusan resmi tetap merujuk SOP asli/unit terkait |
| A-7 | Data operasional di lingkungan pengembangan adalah data fiktif |
| A-8 | Pembagian akses data operasional (`staff_finance`, `supervisor`) sudah sesuai kebijakan ⚠ |

---

## 10. Ketergantungan

| No | Ketergantungan | Dampak Bila Tidak Tersedia |
|---|---|---|
| D-1 | Ollama aktif, model sudah di-*pull* | Tidak ada jawaban maupun ingest |
| D-2 | OpenSearch aktif | Chat tanpa konteks dokumen; ingest gagal |
| D-3 | PostgreSQL aktif | Data operasional & tool SQL tidak tersedia; audit gagal (dicatat di log aplikasi); api tidak start (menunggu healthcheck) |
| D-4 | Redis aktif | Cache & rate limit nonaktif (fail-open); upload tidak masuk antrian; api tidak start (menunggu healthcheck) |
| D-5 | Worker RQ berjalan | Dokumen upload tersimpan tetapi tidak ter-index |
| D-6 | Langfuse | Trace tidak tercatat; chat tetap jalan |
| D-7 | Docker & Docker Compose | Deployment manual |
| D-8 | Dokumen dalam format teks (bukan scan) | PDF scan tidak dapat ditanyakan |

---

## 11. Risiko & Mitigasi

| No | Risiko | Dampak | Mitigasi |
|---|---|---|---|
| R-1 | Model mengarang jawaban atau data | Tinggi | System prompt melarang mengarang data nasabah; data hanya dari tool SQL; disclaimer UI; lampiran sumber |
| R-2 | Pengguna tidak berwenang mengakses data nasabah | Tinggi | RBAC saat eksekusi tool; audit log; identitas hanya dari sesi |
| R-3 | Akun demo/kredensial development terbawa ke produksi | Tinggi | Ganti dengan manajemen pengguna sungguhan dan secret management sebelum rilis |
| R-4 | Layanan pendukung (OpenSearch, Adminer, RedisInsight, Airflow) tanpa autentikasi | Tinggi | Batasi di level jaringan; aktifkan security plugin; jangan publikasikan port |
| R-5 | Dokumen SOP kedaluwarsa/bertentangan | Tinggi | Pemilik dokumen; hapus duplikat; fitur hapus/versi dokumen |
| R-6 | Jawaban cache usang setelah data berubah | Sedang | TTL 1 jam; invalidasi saat ingest; perlu invalidasi saat data operasional berubah |
| R-7 | Pengguna membagikan data sensitif di chat | Tinggi | System prompt menolak & mengingatkan; riwayat tidak disimpan server |
| R-8 | Lonjakan pengguna | Sedang | Cache, rate limit, ingest di worker; perencanaan kapasitas Ollama |
| R-9 | Rate limit per IP tidak akurat di balik proxy | Sedang | Ganti kunci rate limit ke `user_id` sesi |
| R-10 | Kualitas retrieval rendah untuk bahasa Indonesia | Sedang | BM25/hybrid + rerank; evaluasi berkala; uji model embedding & reranker multibahasa |

---

## 12. Rencana Pengembangan ⚠

| Fase | Fokus | Status | Cakupan |
|---|---|---|---|
| 1 | MVP | ✅ Selesai | Chat streaming, windowing, reset, Docker |
| 2 | Knowledge Base & RAG | ✅ Selesai | Upload, ingest OpenSearch, switch RAG, persona perbankan |
| 3 | Kualitas Retrieval | ✅ Selesai | Chunk per heading, BM25, hybrid RRF, reranker, evaluasi, LLM judge, Langfuse |
| 4 | Data Operasional & Agent | ✅ Selesai | Postgres, halaman input, agent LangGraph, tool SQL terbatas |
| 5 | Keamanan & Audit | ✅ Selesai | Login/sesi, RBAC tool SQL, audit log, role database |
| 6 | Performa & Ketahanan | ✅ Selesai | Redis cache, antrian ingest RQ, rate limiting, RedisInsight |
| 7 | Pengalaman Pengguna | ✅ Selesai | Bubble, typing indicator, badge tool, lampiran sumber, tema gelap, responsif |
| 8 | Produksi | Rencana | Manajemen pengguna nyata/SSO, secret management, autentikasi layanan pendukung, rate limit per user, hapus/versi dokumen, RBAC dokumen, metrik, retry, ambang skor retrieval, reranker & embedding multibahasa |

---

## 13. Kriteria Penerimaan

| No | Kriteria | Status |
|---|---|---|
| AC-1 | Pengguna mengirim pertanyaan dan menerima jawaban dari model lokal | ✅ |
| AC-2 | Jawaban mode chat tampil bertahap | ✅ |
| AC-3 | Pertanyaan lanjutan mempertimbangkan konteks sebelumnya | ✅ |
| AC-4 | Request tidak valid ditolak dengan kode status yang tepat | ✅ |
| AC-5 | Aplikasi berjalan melalui `docker compose up` | ✅ |
| AC-6 | Tidak ada data dikirim ke layanan eksternal | ✅ |
| AC-7 | Dokumen yang diunggah dapat dijadikan rujukan jawaban | ✅ |
| AC-8 | Chat tetap berfungsi saat OpenSearch tidak tersedia | ✅ |
| AC-9 | Jawaban tanpa pencarian dokumen saat RAG dimatikan | ✅ |
| AC-10 | Tanpa login, halaman diarahkan ke login dan API mengembalikan 401 | ✅ |
| AC-11 | `staff_umum` yang menanyakan data operasional menerima "Akses ditolak" dan tool SQL tidak dijalankan | ✅ |
| AC-12 | `staff_finance`/`supervisor` menerima jawaban berbasis data operasional | ✅ |
| AC-13 | Setiap pertanyaan mode Agent tercatat di `audit_log` dengan role dan status izin | ✅ |
| AC-14 | Role/user_id di body request diabaikan | ✅ |
| AC-15 | Pertanyaan identik kedua dijawab dari cache (badge ⚡) | ✅ |
| AC-16 | Melebihi batas request menghasilkan HTTP 429 | ✅ |
| AC-17 | Upload langsung dibalas dengan job ID; dokumen ter-index oleh worker | ✅ |
| AC-18 | Semua kontrol composer tetap terlihat pada layar 375px | ✅ |

---

## 14. Dokumen Terkait

- [`spesifikasi.md`](./spesifikasi.md) — spesifikasi teknis, arsitektur, API, database, konfigurasi
- [`keamanan-rbac-audit.md`](./keamanan-rbac-audit.md) — desain keamanan, RBAC, audit
- [`panduan-instalasi-dan-operasional.md`](./panduan-instalasi-dan-operasional.md) — instalasi, operasional, troubleshooting
- [`panduan-pengguna.md`](./panduan-pengguna.md) — cara pakai per role
- [`pengujian.md`](./pengujian.md) — hasil uji & skenario uji
- [`riwayat-pengembangan.md`](./riwayat-pengembangan.md) — kronologi pengembangan
