# Uji Coba 3 — SOP Konfigurasi Firewall: Naive RAG, BM25, Vector, Hybrid ± Rerank

**Tanggal:** 2026-09-24
**Tujuan:** Mengukur efek reranker cross-encoder (Module 20) pada setiap metode pencarian, menggunakan pertanyaan seputar **SOP Konfigurasi Firewall Policy** (`SOP-SEC-FW-002`).

---

## 1. Lingkungan

| Komponen | Nilai |
|---|---|
| Lokasi eksekusi | Di dalam container `api` (kode sama dengan `/chat/stream`) |
| Index | `nala-docs` — 615 chunk, 11 dokumen |
| Model embedding | `nomic-embed-text` (768 dimensi) via Ollama |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` (CPU, torch 2.6.0+cpu, sentence-transformers 3.2.1) |
| Hardware inferensi | CPU (tanpa GPU) |

### Konfigurasi yang diuji

| Konfigurasi | Retrieval | Rerank | Chunk ke LLM |
|---|---|---|---|
| **Naive RAG** | Vector top-3 (baseline Module 13, tanpa hybrid/rerank) | — | 3 |
| BM25 | `search_bm25(top_k=6)` | — | 6 |
| BM25 + rerank | `search_bm25(top_k=20)` | 20 → 3 | 3 |
| Vector | `search(top_k=6)` | — | 6 |
| Vector + rerank | `search(top_k=20)` | 20 → 3 | 3 |
| Hybrid | `search_hybrid(top_k=3)` | — | 3 |
| Hybrid + rerank | `search_hybrid(top_k=20)` | 20 → 3 | 3 |

Parameter di atas sama persis dengan logika `pool_size` di `chat_stream()` (`app/main.py`).

---

## 2. Pertanyaan Uji & Chunk Jawaban

Label `Konfigurasi-FW-N` = chunk ke-N dari `SOP-Konfigurasi-Firewall-Policy.md`. Sebuah konfigurasi dianggap berhasil bila **salah satu** chunk jawaban masuk konteks akhir.

| Pertanyaan | Kalimat uji | Chunk jawaban |
|---|---|---|
| Urutan rule | bagaimana urutan rule firewall dari atas ke bawah | `Konfigurasi-FW-27`, `-28` — "8.2 Urutan Rule" |
| Penamaan rule | format penamaan rule firewall | `Konfigurasi-FW-22` — "7.3 Rule" |
| Konfigurasi dilarang | konfigurasi firewall apa saja yang dilarang | `Konfigurasi-FW-40`, `-41` — "10. Konfigurasi yang Dilarang" |
| Default deny | apa itu prinsip default deny pada firewall | `Konfigurasi-FW-10` — "5. Prinsip Dasar", `Konfigurasi-FW-5` — Definisi |
| Rollback | langkah rollback jika perubahan konfigurasi firewall gagal | `Konfigurasi-FW-37`, `-38` — "Tahap 5 — Rollback" |
| Parafrase troubleshoot | sudah bikin rule baru tapi aplikasinya masih belum bisa konek, harus cek apa | `Konfigurasi-FW-52` — FAQ "Rule sudah dibuat tetapi aplikasi tetap tidak bisa terhubung"; `SOP-Change-Request-Firewall-Policy.md-46` — FAQ "Setelah CR selesai, akses masih tidak bisa" |
| Frekuensi review | seberapa sering rule firewall harus direview | `Konfigurasi-FW-46`, `-47` — "12. Review dan Pemeliharaan Berkala"; `SOP-Review-Resertifikasi-Firewall-Rule.md-26` — FAQ "Seberapa sering firewall rule harus direview?"; `SOP-Review-Resertifikasi-Firewall-Rule.md-9` — "5. Jenis dan Frekuensi Review" |

> **Koreksi ground truth:** pada putaran pertama, chunk jawaban hanya diambil dari SOP Konfigurasi Firewall. Pemeriksaan isi seluruh chunk di konteks akhir menemukan dua FAQ dari SOP lain yang menjawab pertanyaan secara langsung (`Change-Request…md-46` dan `Review-Resertifikasi…md-26`), sehingga ditambahkan dan pengujian dijalankan ulang. Angka di laporan ini adalah hasil putaran kedua. Chunk lain yang muncul (mis. judul bab tanpa isi seperti `## 7. Konvensi Penamaan`, atau bagian Tujuan/Ruang Lingkup) diperiksa dan **tidak** dihitung sebagai jawaban.

---

## 3. Ringkasan Hasil

| Konfigurasi | Jawaban masuk konteks | MRR | Chunk ke LLM | Latensi retrieval rata-rata | Waktu rerank rata-rata |
|---|---|---|---|---|---|
| Naive RAG (vector top-3) | 1/7 | 0.14 | 3 | 121 ms | — |
| **BM25** | **6/7** | **0.79** | 6 | **15 ms** | — |
| BM25 + rerank | 5/7 | 0.64 | 3 | 348 ms | 311 ms |
| Vector | 3/7 | 0.21 | 6 | 113 ms | — |
| Vector + rerank | 3/7 | 0.43 | 3 | 387 ms | 270 ms |
| Hybrid | 4/7 | 0.50 | 3 | 133 ms | — |
| Hybrid + rerank | 5/7 | 0.64 | 3 | 427 ms | 295 ms |

Latensi = embedding + pencarian + rerank (tidak termasuk waktu LLM menjawab). BM25 tidak memerlukan embedding sehingga paling cepat.

### Posisi chunk jawaban di konteks akhir

| Pertanyaan | Naive | BM25 | BM25+RR | Vector | Vector+RR | Hybrid | Hybrid+RR |
|---|---|---|---|---|---|---|---|
| Urutan rule | ❌ | ✅1 | ✅1 | ✅5 | ✅**1** | ✅1 | ✅1 |
| Penamaan rule | ❌ | ✅1 | ❌ *(dibuang)* | ❌ | ❌ | ❌ | ❌ |
| Konfigurasi dilarang | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Default deny | ✅1 | ✅1 | ✅1 | ✅1 | ✅1 | ✅1 | ✅1 |
| Rollback | ❌ | ✅2 | ✅2 | ❌ | ❌ | ✅2 | ✅2 |
| Parafrase troubleshoot | ❌ | ✅1 | ✅1 | ❌ | ❌ | ❌ | ✅**1** *(dari #9)* |
| Frekuensi review | ❌ | ✅1 | ✅1 | ✅4 | ✅**1** | ✅1 | ✅1 |

### Efek reranker

Posisi chunk jawaban **pertama** di 20 kandidat (sebelum rerank) dibanding konteks akhir (sesudah rerank):

| Kasus | Di kandidat | Sesudah rerank | Efek |
|---|---|---|---|
| Urutan rule — vector | #5 | #1 | ✅ Naik |
| Frekuensi review — vector | #4 | #1 | ✅ Naik |
| Parafrase — hybrid | #9 | #1 | ✅ Naik (menyelamatkan pertanyaan yang gagal tanpa rerank) |
| Penamaan rule — BM25 | #1 | tidak masuk top-3 | ❌ **Dibuang** |
| Penamaan rule — hybrid | #9 | tidak masuk top-3 | ➖ Tidak terangkat |
| Rollback — vector | #8 | tidak masuk top-3 | ➖ Tidak terangkat |
| Parafrase — vector | tidak ada di 20 kandidat | — | ➖ Reranker tidak bisa membantu |
| Konfigurasi dilarang — semua metode | tidak ada di 20 kandidat | — | ➖ Reranker tidak bisa membantu |
| Kasus lain (sudah #1/#2) | #1–#2 | tetap | ➖ Tidak berubah |

---

## 4. Temuan

1. **Naive RAG paling lemah (1/7).** Vector search top-3 konsisten meleset ke chunk generik (tujuan, ruang lingkup, referensi) di korpus berbahasa Indonesia.
2. **BM25 tanpa rerank terbaik dan tercepat (6/7, MRR 0.79, 15 ms).** Pertanyaan SOP umumnya memakai istilah yang sama dengan isi dokumen, dan BM25 tidak butuh embedding.
3. **Reranker membantu bila jawaban sudah ada di 20 kandidat tetapi peringkatnya rendah** — tiga kasus naik ke #1 (vector #5 → #1, vector #4 → #1, hybrid #9 → #1). Hybrid naik 4/7 → 5/7 dan MRR vector dua kali lipat (0.21 → 0.43).
4. **Reranker juga bisa merusak**: pada "format penamaan rule", BM25 sudah menaruh jawaban di #1, tetapi cross-encoder membuangnya dari top-3 sehingga BM25 + rerank turun 6/7 → 5/7. Dugaan kuat: `ms-marco-MiniLM-L-6-v2` hanya dilatih data bahasa Inggris (MS MARCO) sehingga penilaiannya pada teks bahasa Indonesia tidak andal.
5. **"Konfigurasi dilarang" gagal di semua konfigurasi** — chunk `Konfigurasi-FW-40` bahkan tidak masuk 20 kandidat metode mana pun; masalahnya di tahap retrieval, bukan reranking.
6. **Biaya rerank ±270–310 ms per request** di CPU untuk 20 kandidat — menambah latensi ±20× dibanding BM25 saja.
7. **Catatan keadilan perbandingan**: BM25 & Vector tanpa rerank mengirim 6 chunk ke LLM, konfigurasi lain 3 chunk — sedikit menguntungkan BM25/Vector tanpa rerank pada metrik "masuk konteks". MRR lebih adil karena memperhitungkan posisi.
8. **Pelajaran metodologi**: ground truth yang hanya diambil dari satu dokumen membuat hasil tampak lebih buruk dari kenyataan (putaran pertama: BM25 5/7, hybrid + rerank 4/7). Knowledge base ini punya banyak FAQ lintas SOP yang saling tumpang-tindih, sehingga ground truth perlu mencakup seluruh korpus.

---

## 5. Rekomendasi

1. **Uji reranker multibahasa** yang dilatih juga dengan bahasa Indonesia, mis. `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` — cukup ganti `model_name` di `Reranker()` lalu pre-pull ke volume `hf_cache`. Ulangi uji coba ini sebagai pembanding, terutama kasus "penamaan rule".
2. Sebelum reranker multibahasa terbukti lebih baik, **BM25 tanpa rerank** adalah pilihan default paling akurat dan paling cepat untuk korpus ini. Bila tetap memakai hybrid, **hybrid + rerank** lebih baik daripada hybrid saja.
3. Untuk kasus seperti *Konfigurasi dilarang* (jawaban tidak masuk kandidat), perbaikan ada di sisi retrieval/chunking — mis. model embedding multibahasa atau menyertakan judul section di setiap chunk — bukan di reranker.

---

## 6. Detail per Pertanyaan

Angka dalam kurung pada konfigurasi `+ rerank` adalah `rerank_score` dari cross-encoder. Kolom "Posisi di 20 kandidat" = posisi chunk jawaban pertama sebelum rerank.

### Urutan rule

| Konfigurasi | Hasil | Posisi di 20 kandidat (sebelum rerank) | Retrieval | Rerank | Konteks akhir (urut) |
|---|---|---|---|---|---|
| naive (vector top-3) | ❌ | — | 16 ms | 0 ms | `SOP-Change-Request-Firewall-Policy.md-4`<br>`SOP-Review-Resertifikasi-Firewall-Rule.md-2`<br>`SOP-Change-Request-Firewall-Policy.md-5` |
| bm25 | ✅ #1 | — | 25 ms | 0 ms | `Konfigurasi-FW-27`<br>`Konfigurasi-FW-24`<br>`Konfigurasi-FW-28`<br>`Konfigurasi-FW-11`<br>`Konfigurasi-FW-52`<br>`SOP-Monitoring-Log-Management-Firewall.md-10` |
| bm25 + rerank | ✅ #1 | #1 | 26 ms | 445 ms | `Konfigurasi-FW-27` (5.82)<br>`Konfigurasi-FW-52` (4.50)<br>`SOP-Review-Resertifikasi-Firewall-Rule.md-2` (2.97) |
| vector | ✅ #5 | — | 10 ms | 0 ms | `SOP-Change-Request-Firewall-Policy.md-4`<br>`SOP-Review-Resertifikasi-Firewall-Rule.md-2`<br>`SOP-Change-Request-Firewall-Policy.md-5`<br>`SOP-Monitoring-Log-Management-Firewall.md-7`<br>`Konfigurasi-FW-27`<br>`SOP-Patch-Upgrade-Firmware-Firewall.md-4` |
| vector + rerank | ✅ #1 | #5 | 14 ms | 295 ms | `Konfigurasi-FW-27` (5.82)<br>`SOP-Monitoring-Log-Management-Firewall.md-7` (3.23)<br>`SOP-Review-Resertifikasi-Firewall-Rule.md-3` (3.18) |
| hybrid | ✅ #1 | — | 31 ms | 0 ms | `Konfigurasi-FW-27`<br>`SOP-Review-Resertifikasi-Firewall-Rule.md-2`<br>`SOP-Manajemen-Akses-Administratif-Firewall.md-31` |
| hybrid + rerank | ✅ #1 | #1 | 29 ms | 298 ms | `Konfigurasi-FW-27` (5.82)<br>`Konfigurasi-FW-52` (4.50)<br>`SOP-Monitoring-Log-Management-Firewall.md-7` (3.23) |

### Penamaan rule

| Konfigurasi | Hasil | Posisi di 20 kandidat (sebelum rerank) | Retrieval | Rerank | Konteks akhir (urut) |
|---|---|---|---|---|---|
| naive (vector top-3) | ❌ | — | 15 ms | 0 ms | `SOP-Change-Request-Firewall-Policy.md-4`<br>`Konfigurasi-FW-55`<br>`SOP-Review-Resertifikasi-Firewall-Rule.md-2` |
| bm25 | ✅ #1 | — | 15 ms | 0 ms | `Konfigurasi-FW-22`<br>`Konfigurasi-FW-26`<br>`Konfigurasi-FW-19`<br>`Konfigurasi-FW-33`<br>`Konfigurasi-FW-23`<br>`SOP-Siklus-Hidup-Perangkat-Firewall.md-20` |
| bm25 + rerank | ❌ | #1 | 20 ms | 257 ms | `SOP-Change-Request-Firewall-Policy.md-5` (3.64)<br>`Konfigurasi-FW-33` (2.95)<br>`Konfigurasi-FW-0` (0.73) |
| vector | ❌ | — | 10 ms | 0 ms | `SOP-Change-Request-Firewall-Policy.md-4`<br>`Konfigurasi-FW-55`<br>`SOP-Review-Resertifikasi-Firewall-Rule.md-2`<br>`SOP-Monitoring-Log-Management-Firewall.md-7`<br>`SOP-Patch-Upgrade-Firmware-Firewall.md-4`<br>`SOP-Change-Request-Firewall-Policy.md-5` |
| vector + rerank | ❌ | tidak ada | 14 ms | 237 ms | `SOP-Change-Request-Firewall-Policy.md-5` (3.64)<br>`SOP-Monitoring-Log-Management-Firewall.md-7` (1.90)<br>`Konfigurasi-FW-2` (0.55) |
| hybrid | ❌ | — | 32 ms | 0 ms | `SOP-Review-Resertifikasi-Firewall-Rule.md-2`<br>`Konfigurasi-FW-55`<br>`SOP-Change-Request-Firewall-Policy.md-4` |
| hybrid + rerank | ❌ | #9 | 31 ms | 286 ms | `SOP-Change-Request-Firewall-Policy.md-5` (3.64)<br>`Konfigurasi-FW-33` (2.95)<br>`SOP-Monitoring-Log-Management-Firewall.md-7` (1.90) |

### Konfigurasi dilarang

| Konfigurasi | Hasil | Posisi di 20 kandidat (sebelum rerank) | Retrieval | Rerank | Konteks akhir (urut) |
|---|---|---|---|---|---|
| naive (vector top-3) | ❌ | — | 17 ms | 0 ms | `SOP-Siklus-Hidup-Perangkat-Firewall.md-35`<br>`Konfigurasi-FW-3`<br>`SOP-Penanganan-Insiden-Gangguan-Firewall.md-4` |
| bm25 | ❌ | — | 16 ms | 0 ms | `SOP-Monitoring-Log-Management-Firewall.md-30`<br>`Konfigurasi-FW-50`<br>`SOP-Change-Request-Firewall-Policy.md-25`<br>`SOP-Change-Request-Firewall-Policy.md-43`<br>`SOP-Penanganan-Insiden-Gangguan-Firewall.md-32`<br>`Konfigurasi-FW-16` |
| bm25 + rerank | ❌ | tidak ada | 17 ms | 323 ms | `SOP-Change-Request-Firewall-Policy.md-25` (5.35)<br>`Konfigurasi-FW-50` (5.05)<br>`SOP-Penanganan-Insiden-Gangguan-Firewall.md-31` (4.27) |
| vector | ❌ | — | 11 ms | 0 ms | `SOP-Siklus-Hidup-Perangkat-Firewall.md-35`<br>`Konfigurasi-FW-3`<br>`SOP-Penanganan-Insiden-Gangguan-Firewall.md-4`<br>`SOP-Patch-Upgrade-Firmware-Firewall.md-4`<br>`SOP-Change-Request-Firewall-Policy.md-6`<br>`SOP-Siklus-Hidup-Perangkat-Firewall.md-33` |
| vector + rerank | ❌ | tidak ada | 15 ms | 267 ms | `SOP-Backup-Restore-Konfigurasi-Firewall.md-2` (5.19)<br>`SOP-Siklus-Hidup-Perangkat-Firewall.md-33` (5.08)<br>`Konfigurasi-FW-3` (4.89) |
| hybrid | ❌ | — | 31 ms | 0 ms | `SOP-Penanganan-Insiden-Gangguan-Firewall.md-32`<br>`SOP-Change-Request-Firewall-Policy.md-6`<br>`SOP-Change-Request-Firewall-Policy.md-46` |
| hybrid + rerank | ❌ | tidak ada | 29 ms | 299 ms | `SOP-Change-Request-Firewall-Policy.md-25` (5.35)<br>`SOP-Backup-Restore-Konfigurasi-Firewall.md-2` (5.19)<br>`SOP-Siklus-Hidup-Perangkat-Firewall.md-33` (5.08) |

### Default deny

| Konfigurasi | Hasil | Posisi di 20 kandidat (sebelum rerank) | Retrieval | Rerank | Konteks akhir (urut) |
|---|---|---|---|---|---|
| naive (vector top-3) | ✅ #1 | — | 40 ms | 0 ms | `Konfigurasi-FW-10`<br>`Konfigurasi-FW-2`<br>`Konfigurasi-FW-55` |
| bm25 | ✅ #1 | — | 15 ms | 0 ms | `Konfigurasi-FW-10`<br>`Konfigurasi-FW-2`<br>`Konfigurasi-FW-16`<br>`Konfigurasi-FW-5`<br>`Konfigurasi-FW-41`<br>`SOP-Penanganan-Insiden-Gangguan-Firewall.md-31` |
| bm25 + rerank | ✅ #1 | #1 | 19 ms | 328 ms | `Konfigurasi-FW-10` (5.85)<br>`Konfigurasi-FW-2` (4.22)<br>`Konfigurasi-FW-41` (2.71) |
| vector | ✅ #1 | — | 11 ms | 0 ms | `Konfigurasi-FW-10`<br>`Konfigurasi-FW-2`<br>`Konfigurasi-FW-55`<br>`SOP-Patch-Upgrade-Firmware-Firewall.md-4`<br>`SOP-Penanganan-Insiden-Gangguan-Firewall.md-31`<br>`Konfigurasi-FW-4` |
| vector + rerank | ✅ #1 | #1 | 15 ms | 257 ms | `Konfigurasi-FW-10` (5.85)<br>`Konfigurasi-FW-2` (4.22)<br>`Konfigurasi-FW-41` (2.71) |
| hybrid | ✅ #1 | — | 29 ms | 0 ms | `Konfigurasi-FW-10`<br>`Konfigurasi-FW-2`<br>`SOP-Penanganan-Insiden-Gangguan-Firewall.md-31` |
| hybrid + rerank | ✅ #1 | #1 | 29 ms | 305 ms | `Konfigurasi-FW-10` (5.85)<br>`Konfigurasi-FW-2` (4.22)<br>`Konfigurasi-FW-41` (2.71) |

### Rollback

| Konfigurasi | Hasil | Posisi di 20 kandidat (sebelum rerank) | Retrieval | Rerank | Konteks akhir (urut) |
|---|---|---|---|---|---|
| naive (vector top-3) | ❌ | — | 14 ms | 0 ms | `SOP-Siklus-Hidup-Perangkat-Firewall.md-35`<br>`Konfigurasi-FW-55`<br>`SOP-Patch-Upgrade-Firmware-Firewall.md-21` |
| bm25 | ✅ #2 | — | 10 ms | 0 ms | `SOP-Backup-Restore-Konfigurasi-Firewall.md-21`<br>`Konfigurasi-FW-37`<br>`SOP-Penanganan-Insiden-Gangguan-Firewall.md-18`<br>`Konfigurasi-FW-2`<br>`Konfigurasi-FW-38`<br>`SOP-Change-Request-Firewall-Policy.md-28` |
| bm25 + rerank | ✅ #2 | #2 | 139 ms | 270 ms | `SOP-Penanganan-Insiden-Gangguan-Firewall.md-18` (4.53)<br>`Konfigurasi-FW-37` (3.96)<br>`SOP-Backup-Restore-Konfigurasi-Firewall.md-2` (3.85) |
| vector | ❌ | — | 10 ms | 0 ms | `SOP-Siklus-Hidup-Perangkat-Firewall.md-35`<br>`Konfigurasi-FW-55`<br>`SOP-Patch-Upgrade-Firmware-Firewall.md-21`<br>`Konfigurasi-FW-2`<br>`SOP-Penanganan-Insiden-Gangguan-Firewall.md-32`<br>`SOP-Backup-Restore-Konfigurasi-Firewall.md-29` |
| vector + rerank | ❌ | #8 | 14 ms | 288 ms | `SOP-Backup-Restore-Konfigurasi-Firewall.md-2` (3.85)<br>`Konfigurasi-FW-2` (3.70)<br>`SOP-Patch-Upgrade-Firmware-Firewall.md-2` (3.00) |
| hybrid | ✅ #2 | — | 29 ms | 0 ms | `Konfigurasi-FW-2`<br>`Konfigurasi-FW-38`<br>`SOP-Backup-Restore-Konfigurasi-Firewall.md-2` |
| hybrid + rerank | ✅ #2 | #2 | 33 ms | 268 ms | `SOP-Penanganan-Insiden-Gangguan-Firewall.md-18` (4.53)<br>`Konfigurasi-FW-37` (3.96)<br>`SOP-Backup-Restore-Konfigurasi-Firewall.md-2` (3.85) |

### Parafrase troubleshoot

| Konfigurasi | Hasil | Posisi di 20 kandidat (sebelum rerank) | Retrieval | Rerank | Konteks akhir (urut) |
|---|---|---|---|---|---|
| naive (vector top-3) | ❌ | — | 14 ms | 0 ms | `SOP-Review-Resertifikasi-Firewall-Rule.md-28`<br>`Konfigurasi-FW-28`<br>`Konfigurasi-FW-6` |
| bm25 | ✅ #1 | — | 10 ms | 0 ms | `SOP-Change-Request-Firewall-Policy.md-46`<br>`Konfigurasi-FW-6`<br>`Konfigurasi-FW-52`<br>`SOP-Review-Resertifikasi-Firewall-Rule.md-28`<br>`SOP-Change-Request-Firewall-Policy.md-12`<br>`Konfigurasi-FW-51` |
| bm25 + rerank | ✅ #1 | #1 | 15 ms | 274 ms | `Konfigurasi-FW-52` (2.65)<br>`SOP-Review-Resertifikasi-Firewall-Rule.md-28` (1.91)<br>`Konfigurasi-FW-6` (0.39) |
| vector | ❌ | — | 11 ms | 0 ms | `SOP-Review-Resertifikasi-Firewall-Rule.md-28`<br>`Konfigurasi-FW-28`<br>`Konfigurasi-FW-6`<br>`Konfigurasi-FW-51`<br>`SOP-Review-Resertifikasi-Firewall-Rule.md-27`<br>`SOP-Review-Resertifikasi-Firewall-Rule.md-11` |
| vector + rerank | ❌ | tidak ada | 15 ms | 274 ms | `SOP-Review-Resertifikasi-Firewall-Rule.md-28` (1.91)<br>`Konfigurasi-FW-6` (0.39)<br>`Konfigurasi-FW-51` (0.21) |
| hybrid | ❌ | — | 29 ms | 0 ms | `SOP-Review-Resertifikasi-Firewall-Rule.md-28`<br>`Konfigurasi-FW-6`<br>`Konfigurasi-FW-51` |
| hybrid + rerank | ✅ #1 | #9 | 31 ms | 340 ms | `Konfigurasi-FW-52` (2.65)<br>`SOP-Review-Resertifikasi-Firewall-Rule.md-28` (1.91)<br>`Konfigurasi-FW-6` (0.39) |

### Frekuensi review

| Konfigurasi | Hasil | Posisi di 20 kandidat (sebelum rerank) | Retrieval | Rerank | Konteks akhir (urut) |
|---|---|---|---|---|---|
| naive (vector top-3) | ❌ | — | 17 ms | 0 ms | `Konfigurasi-FW-55`<br>`SOP-Change-Request-Firewall-Policy.md-6`<br>`SOP-Change-Request-Firewall-Policy.md-4` |
| bm25 | ✅ #1 | — | 15 ms | 0 ms | `SOP-Review-Resertifikasi-Firewall-Rule.md-26`<br>`SOP-Backup-Restore-Konfigurasi-Firewall.md-29`<br>`SOP-Siklus-Hidup-Perangkat-Firewall.md-34`<br>`SOP-Siklus-Hidup-Perangkat-Firewall.md-33`<br>`SOP-Review-Resertifikasi-Firewall-Rule.md-3`<br>`Konfigurasi-FW-51` |
| bm25 + rerank | ✅ #1 | #1 | 19 ms | 283 ms | `SOP-Review-Resertifikasi-Firewall-Rule.md-26` (6.58)<br>`SOP-Siklus-Hidup-Perangkat-Firewall.md-34` (1.62)<br>`SOP-Siklus-Hidup-Perangkat-Firewall.md-33` (1.57) |
| vector | ✅ #4 | — | 10 ms | 0 ms | `Konfigurasi-FW-55`<br>`SOP-Change-Request-Firewall-Policy.md-6`<br>`SOP-Change-Request-Firewall-Policy.md-4`<br>`SOP-Review-Resertifikasi-Firewall-Rule.md-26`<br>`SOP-Patch-Upgrade-Firmware-Firewall.md-4`<br>`Konfigurasi-FW-3` |
| vector + rerank | ✅ #1 | #4 | 16 ms | 271 ms | `SOP-Review-Resertifikasi-Firewall-Rule.md-26` (6.58)<br>`SOP-Review-Resertifikasi-Firewall-Rule.md-3` (-1.85)<br>`SOP-Review-Resertifikasi-Firewall-Rule.md-2` (-2.05) |
| hybrid | ✅ #1 | — | 32 ms | 0 ms | `SOP-Review-Resertifikasi-Firewall-Rule.md-26`<br>`SOP-Review-Resertifikasi-Firewall-Rule.md-3`<br>`Konfigurasi-FW-48` |
| hybrid + rerank | ✅ #1 | #1 | 29 ms | 267 ms | `SOP-Review-Resertifikasi-Firewall-Rule.md-26` (6.58)<br>`SOP-Siklus-Hidup-Perangkat-Firewall.md-34` (1.62)<br>`SOP-Siklus-Hidup-Perangkat-Firewall.md-33` (1.57) |
