# Uji Coba 1 — BM25 vs Vector vs Hybrid (Sebelum Dedup)

**Tanggal:** 2026-09-24
**Tujuan:** Membandingkan hasil retrieval tiga metode pencarian (Module 18–19) pada data yang ada di OpenSearch.
**Status data:** index `nala-docs` masih berisi dokumen duplikat.

---

## 1. Lingkungan

| Komponen | Nilai |
|---|---|
| Index | `nala-docs` — **857 chunk** dari 13 file |
| Model embedding | `nomic-embed-text` (768 dimensi) via Ollama |
| OpenSearch | 2.11.0 (k-NN HNSW, cosine) |
| Parameter | Sama seperti `/chat/stream`: BM25 top-6, Vector top-6, Hybrid top-3 (RRF, `candidate_pool=20`, `rrf_k=60`); juga dicatat Hybrid top-6 sebagai pembanding |
| Reranker | Belum ada |

### Isi index

| Chunk | Dokumen |
|---|---|
| 210 | POJK-11-POJK.3.2022-PenyelenggaraanTeknologiInformasiBankUmum.pdf |
| 210 | POJK_11-03-2022.pdf ⚠ duplikat |
| 57 | SOP-Konfigurasi-Firewall-Policy.md |
| 50 | SOP-Change-Request-Firewall-Policy.md |
| 44 | SOP-Patch-Upgrade-Firmware-Firewall.md |
| 41 | SOP-pengajuan-kredit.md |
| 38 | SOP-Siklus-Hidup-Perangkat-Firewall.md |
| 37 | SOP-Manajemen-Akses-Administratif-Firewall.md |
| 37 | SOP-Penanganan-Insiden-Gangguan-Firewall.md |
| 36 | SOP-Monitoring-Log-Management-Firewall.md |
| 34 | SOP-Backup-Restore-Konfigurasi-Firewall.md |
| 32 | SOP-pengajuan-kredit.pdf ⚠ duplikat |
| 31 | SOP-Review-Resertifikasi-Firewall-Rule.md |

---

## 2. Pertanyaan Uji

| Jenis | Pertanyaan |
|---|---|
| Kata kunci / istilah teknis | backup konfigurasi firewall harian dan retensi |
| Parafrase (tanpa istilah SOP) | apa yang harus dilakukan kalau internet kantor tiba-tiba mati gara-gara perangkat keamanan jaringan rusak |
| Regulasi | kewajiban bank menempatkan pusat data dan pusat pemulihan bencana di Indonesia |
| Proses bisnis | dokumen apa saja yang dibutuhkan untuk mengajukan kredit |
| Akronim | MFA untuk akun admin firewall |
| Di luar knowledge base | cara membuat pivot table di Excel |

---

## 3. Hasil

| Pertanyaan | BM25 (top-6) | Vector (top-6) | Hybrid (top-3) |
|---|---|---|---|
| Kata kunci | ✅ #1 tabel masa retensi (jawaban persis) | ⚠ FAQ frekuensi backup; tabel retensi tidak masuk 100 besar | ⚠ tabel retensi turun ke **#9** — tidak terpakai |
| Parafrase | ✅ #1 FAQ SOP Penanganan Insiden | ❌ definisi DRC (POJK), SOP Change Request | ❌ SOP Insiden di #5, di luar top-3 |
| Regulasi | ✅ #1 pasal "Bank wajib menempatkan … di wilayah Indonesia" | ⚠ pasal pengecualian terkait, pasal utama tidak ada | ⚠ pasal utama hilang; 1 dari 3 slot berisi duplikat |
| Proses bisnis | ❌ FAQ lama proses (chunk jawaban di #32) | ❌ judul "Alur Proses" (chunk jawaban di #13) | ❌ chunk jawaban di #18 |
| Akronim | ✅ #1 tabel hardening yang memuat MFA | ❌ ruang lingkup / judul umum | ⚠ tabel hardening turun ke #6 |
| Di luar KB | ❌ chunk firewall tak relevan (skor rendah 8,1) | ❌ tak relevan (cosine 0,69) | ❌ tak relevan |

### Irisan hasil BM25 ∩ Vector (top-6)

| Pertanyaan | Irisan |
|---|---|
| Kata kunci | 1 |
| Parafrase | 1 |
| Regulasi | 4 (seluruhnya pasangan duplikat POJK) |
| Proses bisnis | 0 |
| Akronim | 0 |
| Di luar KB | 0 |

### Contoh dampak duplikasi — pertanyaan regulasi

Keenam hasil BM25 dan Vector berisi **3 pasal yang masing-masing muncul dua kali** (dari `POJK_11-03-2022.pdf` dan `POJK-11-POJK.3.2022-…pdf`):

| # | BM25 | Vector |
|---|---|---|
| 1 | POJK_11-03-2022.pdf-66 | POJK_11-03-2022.pdf-73 |
| 2 | POJK-11-POJK…pdf-66 | POJK-11-POJK…pdf-73 |
| 3 | POJK_11-03-2022.pdf-77 | POJK_11-03-2022.pdf-77 |
| 4 | POJK-11-POJK…pdf-77 | POJK-11-POJK…pdf-77 |
| 5 | POJK_11-03-2022.pdf-73 | POJK_11-03-2022.pdf-72 |
| 6 | POJK-11-POJK…pdf-73 | POJK-11-POJK…pdf-72 |

---

## 4. Temuan

1. **Vector lemah di korpus ini** — condong ke chunk generik (judul, ruang lingkup), jarang ke chunk berisi jawaban. Dugaan: `nomic-embed-text` berorientasi bahasa Inggris, sementara seluruh dokumen berbahasa Indonesia.
2. **Hybrid top-3 kalah dari BM25 top-6**: pada RRF, chunk #1 di satu daftar saja (≈0,0164) dikalahkan chunk yang muncul di peringkat ±10 di kedua daftar (≈0,029). Karena vector sering meleset, jawaban terbaik BM25 ikut tergeser. Ditambah hybrid hanya memberi 3 chunk ke LLM.
3. **Duplikasi di index membuang slot konteks** — POJK 11/2022 ter-index dua kali (210 chunk masing-masing), SOP pengajuan kredit ada versi `.md` dan `.pdf`.
4. **Fallback "tanpa konteks" tidak pernah terpicu** — tidak ada ambang skor minimum, sehingga pertanyaan di luar KB tetap mendapat 3–6 chunk tak relevan dan `NALA_SYSTEM_PROMPT_NO_CONTEXT` tidak pernah dipakai.
5. **Pertanyaan "dokumen kredit" gagal di semua metode**, namun chunk jawabannya sudah berada di 20 besar Vector (#13) dan Hybrid (#18) — kandidat ideal untuk reranking.

---

## 5. Tindak Lanjut

- ✅ Duplikasi dihapus: `POJK_11-03-2022.pdf` (identik byte-per-byte, MD5 sama) dan `SOP-pengajuan-kredit.pdf` (teks 100% sama dengan versi `.md`) dihapus dari folder knowledge base dan index (242 chunk). Lihat [Uji Coba 2](./02-bm25-vector-hybrid-setelah-dedup.md).
