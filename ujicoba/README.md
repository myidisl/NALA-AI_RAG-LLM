# Hasil Uji Coba Retrieval NALA

Kumpulan hasil uji coba kualitas retrieval (bagian "R" dari RAG) pada knowledge base NALA di index OpenSearch `nala-docs`.

**Tanggal pengujian:** 2026-09-24

| No | Uji Coba | Fokus | File |
|---|---|---|---|
| 1 | BM25 vs Vector vs Hybrid (sebelum dedup) | Perbandingan awal 3 metode pencarian; menemukan duplikasi dokumen | [01-bm25-vector-hybrid-sebelum-dedup.md](./01-bm25-vector-hybrid-sebelum-dedup.md) |
| 2 | BM25 vs Vector vs Hybrid (setelah dedup) | Uji ulang setelah duplikasi POJK & SOP kredit dihapus, dengan chunk jawaban (ground truth) | [02-bm25-vector-hybrid-setelah-dedup.md](./02-bm25-vector-hybrid-setelah-dedup.md) |
| 3 | SOP Konfigurasi Firewall: Naive RAG, BM25, Vector, Hybrid ± Rerank | Efek reranker cross-encoder (Module 20) di tiap metode | [03-sop-konfigurasi-firewall-rerank.md](./03-sop-konfigurasi-firewall-rerank.md) |

---

## Ringkasan Temuan

### Hasil terakhir (Uji Coba 3 — 7 pertanyaan SOP Konfigurasi Firewall)

| Konfigurasi | Jawaban masuk konteks | MRR | Chunk ke LLM | Latensi retrieval |
|---|---|---|---|---|
| Naive RAG (vector top-3) | 1/7 | 0.14 | 3 | 121 ms |
| **BM25** | **6/7** | **0.79** | 6 | **15 ms** |
| BM25 + rerank | 5/7 | 0.64 | 3 | 348 ms |
| Vector | 3/7 | 0.21 | 6 | 113 ms |
| Vector + rerank | 3/7 | 0.43 | 3 | 387 ms |
| Hybrid | 4/7 | 0.50 | 3 | 133 ms |
| Hybrid + rerank | 5/7 | 0.64 | 3 | 427 ms |

### Kesimpulan lintas uji coba

1. **BM25 paling andal dan paling cepat** untuk korpus SOP berbahasa Indonesia ini — konsisten di ketiga uji coba.
2. **Vector search (`nomic-embed-text`) lemah**: cenderung mengembalikan chunk generik (tujuan, ruang lingkup, referensi) daripada chunk yang berisi jawaban. Dugaan kuat: model embedding berorientasi bahasa Inggris.
3. **Hybrid (RRF) terseret kelemahan vector**: chunk peringkat #1 BM25 sering tergeser oleh chunk yang muncul "lumayan" di kedua daftar; ditambah hybrid hanya memberi 3 chunk ke LLM.
4. **Reranker (`cross-encoder/ms-marco-MiniLM-L-6-v2`) membantu sebagian**: mengangkat jawaban dari peringkat rendah ke #1 (vector #5 → #1, vector #4 → #1, hybrid #9 → #1) sehingga hybrid naik 4/7 → 5/7, tetapi juga pernah **membuang** jawaban #1 BM25 — model ini dilatih pada data bahasa Inggris. Biaya ±270–310 ms per request di CPU.
5. **Duplikasi dokumen membuang slot konteks** — sudah diperbaiki (lihat Uji Coba 1 → 2): index turun dari 857 ke 615 chunk.
6. **Tidak ada ambang skor minimum**, sehingga pertanyaan di luar knowledge base tetap mendapat konteks tak relevan dan prompt `NALA_SYSTEM_PROMPT_NO_CONTEXT` tidak pernah terpakai. Skor BM25 cukup membedakan (±7,5 di luar KB vs ±18,8 di dalam KB); skor RRF tidak.

### Rekomendasi

| Prioritas | Rekomendasi |
|---|---|
| Tinggi | Uji reranker multibahasa (mis. `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`) — cukup ganti `model_name` di `Reranker()` |
| Tinggi | Pertimbangkan BM25 (atau BM25 + rerank multibahasa) sebagai default sampai kualitas vector membaik |
| Sedang | Tambahkan ambang skor minimum (berbasis skor BM25) agar pertanyaan di luar KB memakai prompt `NO_CONTEXT` |
| Sedang | Uji model embedding multibahasa (memerlukan reindex seluruh dokumen) |
| Rendah | Samakan jumlah chunk konteks antar metode (saat ini 3 vs 6) agar perbandingan adil |

---

## Catatan Metodologi

- Pengujian memakai kode aplikasi yang sama dengan endpoint `/chat/stream` (`VectorStore`, `embed_text`, `Reranker`), dijalankan terhadap OpenSearch dan Ollama yang aktif.
- "Chunk jawaban" (ground truth) ditentukan manual dengan memeriksa isi chunk di index. Pada Uji Coba 3, ground truth dikoreksi setelah ditemukan FAQ di SOP lain yang juga menjawab pertanyaan (lihat catatan di laporan 03). Ground truth Uji Coba 2 berupa satu chunk per pertanyaan dan belum diperiksa lintas dokumen, sehingga angkanya bisa sedikit meremehkan hasil sebenarnya.
- **MRR** (*Mean Reciprocal Rank*): rata-rata 1/posisi chunk jawaban di konteks akhir (0 bila tidak ada). 1,0 = jawaban selalu di peringkat #1.
- Jumlah pertanyaan kecil (5–7 per uji coba), sehingga hasil adalah **indikasi arah**, bukan benchmark statistik.
