# Uji Coba 2 — BM25 vs Vector vs Hybrid (Setelah Dedup)

**Tanggal:** 2026-09-24
**Tujuan:** Mengulang [Uji Coba 1](./01-bm25-vector-hybrid-sebelum-dedup.md) setelah duplikasi dihapus, kali ini dengan **chunk jawaban (ground truth)** yang ditentukan manual agar hasil bisa diukur.

---

## 1. Lingkungan

| Komponen | Nilai |
|---|---|
| Index | `nala-docs` — **615 chunk** dari 11 dokumen (tanpa duplikat) |
| Model embedding | `nomic-embed-text` (768 dimensi) via Ollama |
| Parameter | Sama seperti `/chat/stream`: BM25 top-6, Vector top-6, Hybrid top-3 (RRF, `candidate_pool=20`, `rrf_k=60`) |
| Reranker | Belum ada |
| Kedalaman pencarian peringkat | BM25 & Vector top-100, Hybrid top-40 (untuk mencari posisi chunk jawaban) |

### Isi index setelah dedup

| Chunk | Dokumen |
|---|---|
| 210 | POJK-11-POJK.3.2022-PenyelenggaraanTeknologiInformasiBankUmum.pdf |
| 57 | SOP-Konfigurasi-Firewall-Policy.md |
| 50 | SOP-Change-Request-Firewall-Policy.md |
| 44 | SOP-Patch-Upgrade-Firmware-Firewall.md |
| 41 | SOP-pengajuan-kredit.md |
| 38 | SOP-Siklus-Hidup-Perangkat-Firewall.md |
| 37 | SOP-Manajemen-Akses-Administratif-Firewall.md |
| 37 | SOP-Penanganan-Insiden-Gangguan-Firewall.md |
| 36 | SOP-Monitoring-Log-Management-Firewall.md |
| 34 | SOP-Backup-Restore-Konfigurasi-Firewall.md |
| 31 | SOP-Review-Resertifikasi-Firewall-Rule.md |

---

## 2. Ringkasan Hasil

Peringkat chunk jawaban di tiap metode. ✅ = chunk jawaban masuk konteks yang dikirim ke LLM.

> **Catatan:** ground truth di uji coba ini berupa satu–dua chunk per pertanyaan dan belum diperiksa lintas dokumen. Pada [Uji Coba 3](./03-sop-konfigurasi-firewall-rerank.md) ditemukan bahwa FAQ di SOP lain kadang juga menjawab pertanyaan yang sama, sehingga angka di sini bisa sedikit meremehkan hasil sebenarnya. Pola perbandingan antar metode tetap berlaku.

| Pertanyaan | BM25 (top-6) | Vector (top-6) | Hybrid (top-3) |
|---|---|---|---|
| Kata kunci: backup & retensi | ✅ #1 | ❌ >100 | ❌ #9 |
| Parafrase: internet kantor mati | ✅ #1 | ❌ #91 | ❌ #5 |
| Regulasi: pusat data di Indonesia | ✅ #1 | ❌ #12 | ❌ #5 |
| Proses bisnis: dokumen kredit | ❌ #16 | ❌ #9 | ❌ #7 |
| Akronim: MFA admin firewall | ✅ #1 | ❌ #46 | ❌ #6 |
| **Total masuk konteks** | **4/5** | **0/5** | **0/5** |

### Skor tertinggi — pertanyaan di luar KB vs rata-rata skor #1 pertanyaan dalam KB

| Metode | Di luar KB | Rata-rata dalam KB | Bisa jadi ambang batas? |
|---|---|---|---|
| BM25 | 7,48 | 18,78 | ✅ selisih jelas |
| Vector | 0,693 | 0,840 | ⚠ selisih tipis |
| Hybrid (RRF) | 0,0283 | 0,0314 | ❌ hampir sama (RRF hanya memakai peringkat) |

---

## 3. Perbandingan dengan Uji Coba 1

- **Duplikat hilang dari hasil**: pertanyaan regulasi kini berisi 6 pasal berbeda di BM25 (66, 77, 73, 74, 76, 75), bukan 3 pasal × 2.
- **Peringkat hybrid membaik**: chunk jawaban regulasi dari tidak ada → #5; dokumen kredit dari #18 → #7 — namun tetap di luar top-3.
- **Pola umum tidak berubah**: BM25 menemukan jawaban di #1 untuk 4 dari 5 pertanyaan; vector tidak sekali pun.

---

## 4. Temuan

1. **Hybrid gagal terutama karena `top_k=3`.** Bila diberi 6 slot seperti metode lain, hybrid akan lolos pada 2 pertanyaan (Parafrase #5, Regulasi #5); Akronim tepat di #6 dan ikut lolos bila chunk jawaban kedua dihitung. Tetap ada masalah dasar: vector sering meleset dan menarik turun peringkat #1 BM25 di RRF.
2. **Vector lemah di korpus bahasa Indonesia** — mengembalikan judul, ruang lingkup, dan FAQ umum.
3. **Pertanyaan dokumen kredit gagal di semua metode**, tetapi chunk jawabannya ada di 20 besar ketiganya (#16 / #9 / #7) — kasus yang tepat untuk reranking (Module 20).
4. **Ambang skor**: hanya skor BM25 yang cukup membedakan pertanyaan di luar KB.

---

## 5. Detail per Pertanyaan

Label `POJK` = `POJK-11-POJK.3.2022-PenyelenggaraanTeknologiInformasiBankUmum.pdf`.

### Kata kunci — "backup konfigurasi firewall harian dan retensi"

Chunk jawaban: `SOP-Backup-Restore-Konfigurasi-Firewall.md-15`

| Metode | Peringkat chunk jawaban | Masuk konteks? |
|---|---|---|
| bm25 (top-6) | `SOP-Backup-Restore-Konfigurasi-Firewall.md-15` #1 | ✅ |
| vector (top-6) | `SOP-Backup-Restore-Konfigurasi-Firewall.md-15` #>100 | ❌ |
| hybrid (top-3) | `SOP-Backup-Restore-Konfigurasi-Firewall.md-15` #9 | ❌ |

<details><summary>bm25 — top-6 yang dikirim ke LLM</summary>

| # | _id | Skor | Cuplikan |
|---|---|---|---|
| 1 | `SOP-Backup-Restore-Konfigurasi-Firewall.md-15` ◀ jawaban | 13.926 | ### 7.2 Masa Retensi (Ilustratif) \| Jenis Backup \| Retensi \| \|---\|---\| \| Harian \| 35 hari \| \| Mingguan (full) … |
| 2 | `Konfigurasi-FW-32` | 13.270 | ### Tahap 2 — Backup Konfigurasi **Pelaksana:** Network Security Engineer (Pelaksana) 1. Mengekspor konfiguras… |
| 3 | `Konfigurasi-FW-44` | 12.929 | maksimal 10 menit; banner peringatan akses sah \| \| **Logging** \| Log traffic dan log audit administrasi dikiri… |
| 4 | `SOP-Backup-Restore-Konfigurasi-Firewall.md-26` | 11.310 | ## 10. Target Pemulihan (Ilustratif) \| Parameter \| Target \| \|---\|---\| \| **RPO konfigurasi** \| Maksimal 24 jam … |
| 5 | `Konfigurasi-FW-46` | 11.185 | ## 12. Review dan Pemeliharaan Berkala \| Kegiatan \| Frekuensi \| Pelaksana \| \|---\|---\|---\| \| Pemeriksaan rule s… |
| 6 | `SOP-Backup-Restore-Konfigurasi-Firewall.md-0` | 10.375 | # SOP Backup dan Restore Konfigurasi Firewall **Nomor Dokumen:** SOP-SEC-FW-004 **Versi:** 1.0 **Tanggal Berla… |

</details>

<details><summary>vector — top-6 yang dikirim ke LLM</summary>

| # | _id | Skor | Cuplikan |
|---|---|---|---|
| 1 | `SOP-Backup-Restore-Konfigurasi-Firewall.md-29` | 0.879 | ## 12. Pertanyaan yang Sering Diajukan **Seberapa sering konfigurasi firewall dicadangkan?** Otomatis setiap h… |
| 2 | `SOP-Backup-Restore-Konfigurasi-Firewall.md-0` | 0.873 | # SOP Backup dan Restore Konfigurasi Firewall **Nomor Dokumen:** SOP-SEC-FW-004 **Versi:** 1.0 **Tanggal Berla… |
| 3 | `SOP-Backup-Restore-Konfigurasi-Firewall.md-3` | 0.868 | ## 2. Ruang Lingkup Dokumen ini berlaku untuk backup dan restore konfigurasi seluruh firewall di lingkungan Pr… |
| 4 | `Konfigurasi-FW-55` | 0.854 | w dan Resertifikasi Firewall Rule - SOP-SEC-FW-004 Backup dan Restore Konfigurasi Firewall - SOP-SEC-FW-005 Mo… |
| 5 | `SOP-Backup-Restore-Konfigurasi-Firewall.md-2` | 0.848 | ## 1. Tujuan 1. Memastikan konfigurasi seluruh firewall selalu tercadangkan secara lengkap, aman, dan dapat di… |
| 6 | `SOP-Siklus-Hidup-Perangkat-Firewall.md-35` | 0.848 | ang diperketat, serta persetujuan CISO, sambil menjadwalkan penggantian. **Bolehkah firewall bekas langsung di… |

</details>

<details><summary>hybrid — top-3 yang dikirim ke LLM</summary>

| # | _id | Skor | Cuplikan |
|---|---|---|---|
| 1 | `SOP-Backup-Restore-Konfigurasi-Firewall.md-0` | rrf 0.0313 | # SOP Backup dan Restore Konfigurasi Firewall **Nomor Dokumen:** SOP-SEC-FW-004 **Versi:** 1.0 **Tanggal Berla… |
| 2 | `SOP-Backup-Restore-Konfigurasi-Firewall.md-29` | rrf 0.0311 | ## 12. Pertanyaan yang Sering Diajukan **Seberapa sering konfigurasi firewall dicadangkan?** Otomatis setiap h… |
| 3 | `Konfigurasi-FW-32` | rrf 0.0311 | ### Tahap 2 — Backup Konfigurasi **Pelaksana:** Network Security Engineer (Pelaksana) 1. Mengekspor konfiguras… |

</details>

### Parafrase — "apa yang harus dilakukan kalau internet kantor tiba-tiba mati gara-gara perangkat keamanan jaringan rusak"

Chunk jawaban: `SOP-Penanganan-Insiden-Gangguan-Firewall.md-31`

| Metode | Peringkat chunk jawaban | Masuk konteks? |
|---|---|---|
| bm25 (top-6) | `SOP-Penanganan-Insiden-Gangguan-Firewall.md-31` #1 | ✅ |
| vector (top-6) | `SOP-Penanganan-Insiden-Gangguan-Firewall.md-31` #91 | ❌ |
| hybrid (top-3) | `SOP-Penanganan-Insiden-Gangguan-Firewall.md-31` #5 | ❌ |

<details><summary>bm25 — top-6 yang dikirim ke LLM</summary>

| # | _id | Skor | Cuplikan |
|---|---|---|---|
| 1 | `SOP-Penanganan-Insiden-Gangguan-Firewall.md-31` ◀ jawaban | 23.230 | ## 9. Pertanyaan yang Sering Diajukan **Aplikasi tiba-tiba tidak bisa terhubung setelah ada perubahan firewall… |
| 2 | `SOP-Change-Request-Firewall-Policy.md-46` | 15.626 | Hanya untuk memulihkan layanan kritikal yang terganggu atau menanggulangi insiden keamanan yang sedang berlang… |
| 3 | `SOP-Siklus-Hidup-Perangkat-Firewall.md-31` | 12.593 | ## 6. Pengendalian Internal 1. **Tidak ada go-live tanpa baseline:** perangkat tidak boleh terhubung ke jaring… |
| 4 | `SOP-Backup-Restore-Konfigurasi-Firewall.md-21` | 12.575 | ### Tahap 1 — Penetapan Kebutuhan Restore **Pelaksana:** Network Security Engineer Restore dilakukan bila terj… |
| 5 | `POJK-22` | 11.696 | gara TI; b. direktur yang membawahkan satuan kerja manajemen risiko; c. pejabat tertinggi yang memimpin satuan… |
| 6 | `Konfigurasi-FW-1` | 11.636 | dan harus disesuaikan dengan arsitektur jaringan, perangkat yang digunakan, serta ketentuan internal sebelum d… |

</details>

<details><summary>vector — top-6 yang dikirim ke LLM</summary>

| # | _id | Skor | Cuplikan |
|---|---|---|---|
| 1 | `POJK-8` | 0.768 | dalah suatu fasilitas yang digunakan untuk memulihkan kembali data atau informasi serta fungsi penting Sistem … |
| 2 | `SOP-Change-Request-Firewall-Policy.md-40` | 0.766 | ## 12. Alasan Umum Penolakan CR 1. Justifikasi bisnis tidak jelas atau tidak disetujui Application / System Ow… |
| 3 | `SOP-Change-Request-Firewall-Policy.md-46` | 0.765 | Hanya untuk memulihkan layanan kritikal yang terganggu atau menanggulangi insiden keamanan yang sedang berlang… |
| 4 | `SOP-Patch-Upgrade-Firmware-Firewall.md-38` | 0.762 | ## 12. Pertanyaan yang Sering Diajukan **Berapa lama batas waktu menambal kerentanan kritis pada firewall?** 1… |
| 5 | `SOP-Change-Request-Firewall-Policy.md-15` | 0.760 | tujuan/layanan bernilai **any** \| \| **Sedang** \| Akses antar zona internal di luar Restricted Zone; akses kelu… |
| 6 | `SOP-Change-Request-Firewall-Policy.md-44` | 0.759 | ## 14. Pertanyaan yang Sering Diajukan **Berapa lama proses CR firewall?** Sekitar 5 hari kerja untuk risiko r… |

</details>

<details><summary>hybrid — top-3 yang dikirim ke LLM</summary>

| # | _id | Skor | Cuplikan |
|---|---|---|---|
| 1 | `SOP-Change-Request-Firewall-Policy.md-46` | rrf 0.0320 | Hanya untuk memulihkan layanan kritikal yang terganggu atau menanggulangi insiden keamanan yang sedang berlang… |
| 2 | `POJK-8` | rrf 0.0297 | dalah suatu fasilitas yang digunakan untuk memulihkan kembali data atau informasi serta fungsi penting Sistem … |
| 3 | `Konfigurasi-FW-1` | rrf 0.0278 | dan harus disesuaikan dengan arsitektur jaringan, perangkat yang digunakan, serta ketentuan internal sebelum d… |

</details>

### Regulasi — "kewajiban bank menempatkan pusat data dan pusat pemulihan bencana di Indonesia"

Chunk jawaban: `POJK-66`

| Metode | Peringkat chunk jawaban | Masuk konteks? |
|---|---|---|
| bm25 (top-6) | `POJK-66` #1 | ✅ |
| vector (top-6) | `POJK-66` #12 | ❌ |
| hybrid (top-3) | `POJK-66` #5 | ❌ |

<details><summary>bm25 — top-6 yang dikirim ke LLM</summary>

| # | _id | Skor | Cuplikan |
|---|---|---|---|
| 1 | `POJK-66` ◀ jawaban | 34.664 | Bank wajib mene mpatkan Sistem Elektronik pada Pusat Data dan Pusat Pemulihan Bencana di wilayah Indonesia. - … |
| 2 | `POJK-77` | 33.009 | an peraturan perundang-undangan, Otoritas Jasa Keuangan dapat meminta Bank untuk menempatkan Sistem Elektronik… |
| 3 | `POJK-73` | 28.093 | r wilayah - 25 - Indonesia bagi Bank lebih besar daripada beban yang ditanggung oleh Bank; i. menyampaikan ren… |
| 4 | `POJK-74` | 26.113 | an Sistem Elektronik pada Pusat Data dan/atau Pusat Pemulihan Bencana di luar wilayah Indonesia sebagaimana di… |
| 5 | `POJK-76` | 25.761 | usat Data dan/atau Pusat Pemulihan Bencana di luar wilayah Indonesia: a. tidak sesuai dengan permohonan izin p… |
| 6 | `POJK-75` | 25.449 | dokumen permohonan diterima secara lengkap oleh Otoritas Jasa Keuangan. (3) Bank wajib memastikan bahwa data y… |

</details>

<details><summary>vector — top-6 yang dikirim ke LLM</summary>

| # | _id | Skor | Cuplikan |
|---|---|---|---|
| 1 | `POJK-73` | 0.870 | r wilayah - 25 - Indonesia bagi Bank lebih besar daripada beban yang ditanggung oleh Bank; i. menyampaikan ren… |
| 2 | `POJK-77` | 0.865 | an peraturan perundang-undangan, Otoritas Jasa Keuangan dapat meminta Bank untuk menempatkan Sistem Elektronik… |
| 3 | `POJK-72` | 0.863 | di luar wilayah Indonesia bahwa Otoritas Jasa Keuangan dapat melakukan pemeriksaan terhadap pihak penyedia jas… |
| 4 | `POJK-76` | 0.854 | usat Data dan/atau Pusat Pemulihan Bencana di luar wilayah Indonesia: a. tidak sesuai dengan permohonan izin p… |
| 5 | `POJK-181` | 0.852 | akses terhadap pangkalan data dan memiliki struktur pangkalan data dari setiap aplikasi yang digunakan. Huruf … |
| 6 | `POJK-87` | 0.852 | NGGARAAN TI BANK Bagian Kesatu Pengelolaan Data oleh Bank Pasal 43 (1) Bank wajib mengelola data secara efekti… |

</details>

<details><summary>hybrid — top-3 yang dikirim ke LLM</summary>

| # | _id | Skor | Cuplikan |
|---|---|---|---|
| 1 | `POJK-73` | rrf 0.0323 | r wilayah - 25 - Indonesia bagi Bank lebih besar daripada beban yang ditanggung oleh Bank; i. menyampaikan ren… |
| 2 | `POJK-77` | rrf 0.0323 | an peraturan perundang-undangan, Otoritas Jasa Keuangan dapat meminta Bank untuk menempatkan Sistem Elektronik… |
| 3 | `POJK-76` | rrf 0.0310 | usat Data dan/atau Pusat Pemulihan Bencana di luar wilayah Indonesia: a. tidak sesuai dengan permohonan izin p… |

</details>

### Proses bisnis — "dokumen apa saja yang dibutuhkan untuk mengajukan kredit"

Chunk jawaban: `SOP-pengajuan-kredit.md-28`

| Metode | Peringkat chunk jawaban | Masuk konteks? |
|---|---|---|
| bm25 (top-6) | `SOP-pengajuan-kredit.md-28` #16 | ❌ |
| vector (top-6) | `SOP-pengajuan-kredit.md-28` #9 | ❌ |
| hybrid (top-3) | `SOP-pengajuan-kredit.md-28` #7 | ❌ |

<details><summary>bm25 — top-6 yang dikirim ke LLM</summary>

| # | _id | Skor | Cuplikan |
|---|---|---|---|
| 1 | `SOP-pengajuan-kredit.md-37` | 11.656 | ## 10. Pertanyaan yang Sering Diajukan **Berapa lama proses pengajuan kredit?** Umumnya 11–14 hari kerja sejak… |
| 2 | `SOP-pengajuan-kredit.md-4` | 10.334 | ## 3. Definisi \| Istilah \| Penjelasan \| \|---\|---\| \| **Pemohon** \| Perorangan yang mengajukan permohonan fasili… |
| 3 | `SOP-Monitoring-Log-Management-Firewall.md-30` | 9.860 | ## 12. Pertanyaan yang Sering Diajukan **Apa bedanya monitoring oleh NOC dan SOC?** NOC memantau apakah firewa… |
| 4 | `SOP-pengajuan-kredit.md-3` | 9.854 | ## 2. Ruang Lingkup Dokumen ini berlaku untuk seluruh pengajuan **kredit konsumer** yang diterima melalui kant… |
| 5 | `Konfigurasi-FW-51` | 9.693 | ## 14. Pertanyaan yang Sering Diajukan **Kenapa rule harus diawali nomor CR?** Agar setiap rule dapat ditelusu… |
| 6 | `SOP-pengajuan-kredit.md-0` | 9.009 | # SOP Pengajuan Kredit **Nomor Dokumen:** SOP-KRD-001 **Versi:** 1.0 **Tanggal Berlaku:** 2026-09-23 **Unit Pe… |

</details>

<details><summary>vector — top-6 yang dikirim ke LLM</summary>

| # | _id | Skor | Cuplikan |
|---|---|---|---|
| 1 | `SOP-pengajuan-kredit.md-8` | 0.848 | ## 5. Alur Proses Pengajuan Kredit… |
| 2 | `POJK-189` | 0.839 | sahaan dan digunakan sebagai pendukung penyusunan laporan keuangan. Contoh: akad kredit atau pembiayaan dan do… |
| 3 | `SOP-pengajuan-kredit.md-3` | 0.811 | ## 2. Ruang Lingkup Dokumen ini berlaku untuk seluruh pengajuan **kredit konsumer** yang diterima melalui kant… |
| 4 | `SOP-pengajuan-kredit.md-0` | 0.805 | # SOP Pengajuan Kredit **Nomor Dokumen:** SOP-KRD-001 **Versi:** 1.0 **Tanggal Berlaku:** 2026-09-23 **Unit Pe… |
| 5 | `SOP-pengajuan-kredit.md-7` | 0.804 | an taksasi nilai agunan \| \| **Komite Kredit / Pemutus** \| Memberikan keputusan persetujuan atau penolakan sesu… |
| 6 | `SOP-pengajuan-kredit.md-37` | 0.803 | ## 10. Pertanyaan yang Sering Diajukan **Berapa lama proses pengajuan kredit?** Umumnya 11–14 hari kerja sejak… |

</details>

<details><summary>hybrid — top-3 yang dikirim ke LLM</summary>

| # | _id | Skor | Cuplikan |
|---|---|---|---|
| 1 | `SOP-pengajuan-kredit.md-37` | rrf 0.0315 | ## 10. Pertanyaan yang Sering Diajukan **Berapa lama proses pengajuan kredit?** Umumnya 11–14 hari kerja sejak… |
| 2 | `SOP-pengajuan-kredit.md-3` | rrf 0.0315 | ## 2. Ruang Lingkup Dokumen ini berlaku untuk seluruh pengajuan **kredit konsumer** yang diterima melalui kant… |
| 3 | `POJK-189` | rrf 0.0311 | sahaan dan digunakan sebagai pendukung penyusunan laporan keuangan. Contoh: akad kredit atau pembiayaan dan do… |

</details>

### Akronim — "MFA untuk akun admin firewall"

Chunk jawaban: `SOP-Manajemen-Akses-Administratif-Firewall.md-12`, `Konfigurasi-FW-43`

| Metode | Peringkat chunk jawaban | Masuk konteks? |
|---|---|---|
| bm25 (top-6) | `SOP-Manajemen-Akses-Administratif-Firewall.md-12` #15, `Konfigurasi-FW-43` #1 | ✅ |
| vector (top-6) | `SOP-Manajemen-Akses-Administratif-Firewall.md-12` #>100, `Konfigurasi-FW-43` #46 | ❌ |
| hybrid (top-3) | `SOP-Manajemen-Akses-Administratif-Firewall.md-12` #26, `Konfigurasi-FW-43` #6 | ❌ |

<details><summary>bm25 — top-6 yang dikirim ke LLM</summary>

| # | _id | Skor | Cuplikan |
|---|---|---|---|
| 1 | `Konfigurasi-FW-43` ◀ jawaban | 10.413 | ## 11. Hardening Manajemen Perangkat Firewall \| Aspek \| Standar \| \|---\|---\| \| **Akses manajemen** \| Hanya dari… |
| 2 | `SOP-Manajemen-Akses-Administratif-Firewall.md-31` | 9.929 | ## 13. Pertanyaan yang Sering Diajukan **Bagaimana cara mendapatkan akses ke firewall?** Ajukan permohonan mel… |
| 3 | `SOP-Manajemen-Akses-Administratif-Firewall.md-27` | 9.730 | ## 11. Peninjauan Hak Akses (User Access Review) **Pelaksana:** Information Security bersama Kepala Bagian Net… |
| 4 | `SOP-Monitoring-Log-Management-Firewall.md-15` | 9.632 | ### 6.2 Monitoring Keamanan (SOC) \| Use Case \| Kondisi Pemicu \| Severity Awal \| \|---\|---\|---\| \| **Perubahan ko… |
| 5 | `SOP-Siklus-Hidup-Perangkat-Firewall.md-16` | 9.226 | ### Tahap 4 — Baseline Hardening **Pelaksana:** Network Security Engineer **Direview oleh:** Information Secur… |
| 6 | `SOP-Manajemen-Akses-Administratif-Firewall.md-20` | 9.197 | nonaktifkan sementara selama cuti \| \| Akun tidak digunakan > 90 hari \| Dinonaktifkan dan dikonfirmasi ke atasa… |

</details>

<details><summary>vector — top-6 yang dikirim ke LLM</summary>

| # | _id | Skor | Cuplikan |
|---|---|---|---|
| 1 | `SOP-Manajemen-Akses-Administratif-Firewall.md-3` | 0.836 | ## 2. Ruang Lingkup Dokumen ini berlaku untuk seluruh akses administratif ke: - Perangkat firewall (CLI, web G… |
| 2 | `Konfigurasi-FW-55` | 0.824 | w dan Resertifikasi Firewall Rule - SOP-SEC-FW-004 Backup dan Restore Konfigurasi Firewall - SOP-SEC-FW-005 Mo… |
| 3 | `SOP-Patch-Upgrade-Firmware-Firewall.md-4` | 0.820 | dalam **SOP-SEC-FW-009 Siklus Hidup Perangkat Firewall**. ---… |
| 4 | `Konfigurasi-FW-45` | 0.818 | Rincian pelaksanaan masing-masing aspek diatur dalam SOP terpisah: - akses dan akun administrator → **SOP-SEC-… |
| 5 | `SOP-Manajemen-Akses-Administratif-Firewall.md-0` | 0.818 | # SOP Manajemen Akses Administratif Firewall **Nomor Dokumen:** SOP-SEC-FW-008 **Versi:** 1.0 **Tanggal Berlak… |
| 6 | `SOP-Penanganan-Insiden-Gangguan-Firewall.md-4` | 0.817 | bebani firewall, perubahan konfigurasi tidak sah, akun administrator disalahgunakan, eksploitasi kerentanan fi… |

</details>

<details><summary>hybrid — top-3 yang dikirim ke LLM</summary>

| # | _id | Skor | Cuplikan |
|---|---|---|---|
| 1 | `SOP-Manajemen-Akses-Administratif-Firewall.md-31` | rrf 0.0298 | ## 13. Pertanyaan yang Sering Diajukan **Bagaimana cara mendapatkan akses ke firewall?** Ajukan permohonan mel… |
| 2 | `SOP-Penanganan-Insiden-Gangguan-Firewall.md-4` | rrf 0.0290 | bebani firewall, perubahan konfigurasi tidak sah, akun administrator disalahgunakan, eksploitasi kerentanan fi… |
| 3 | `Konfigurasi-FW-45` | rrf 0.0284 | Rincian pelaksanaan masing-masing aspek diatur dalam SOP terpisah: - akses dan akun administrator → **SOP-SEC-… |

</details>

### Di luar KB — "cara membuat pivot table di Excel"

Chunk jawaban: _tidak ada (di luar knowledge base)_

<details><summary>bm25 — top-6 yang dikirim ke LLM</summary>

| # | _id | Skor | Cuplikan |
|---|---|---|---|
| 1 | `Konfigurasi-FW-33` | 7.483 | ### Tahap 3 — Implementasi **Pelaksana:** Network Security Engineer (Pelaksana) **Waktu:** Dalam maintenance w… |
| 2 | `SOP-Monitoring-Log-Management-Firewall.md-20` | 7.043 | ### Tahap 1 — Deteksi **Pelaksana:** NOC (alert operasional) dan SOC (alert keamanan) 1. Alert muncul di dashb… |
| 3 | `SOP-Manajemen-Akses-Administratif-Firewall.md-7` | 6.043 | ## 4. Pihak yang Terlibat \| Peran \| Tanggung Jawab Utama \| \|---\|---\| \| **Pemohon** \| Mengajukan permintaan aks… |
| 4 | `SOP-Monitoring-Log-Management-Firewall.md-13` | 5.419 | ### 6.1 Monitoring Kesehatan dan Kinerja (NOC) \| Parameter \| Warning \| Critical \| \|---\|---\|---\| \| **Utilisasi … |
| 5 | `POJK-181` | 5.277 | akses terhadap pangkalan data dan memiliki struktur pangkalan data dari setiap aplikasi yang digunakan. Huruf … |
| 6 | `POJK-159` | 4.973 | keamanan siber berdasarkan skenario antara lain cyber incident response , table-top exercise , dan cyber range… |

</details>

<details><summary>vector — top-6 yang dikirim ke LLM</summary>

| # | _id | Skor | Cuplikan |
|---|---|---|---|
| 1 | `POJK-190` | 0.693 | a peningk atan pemberian kredit atau pembiayaan dan peningkatan pembiayaan ekspor - impor. Ayat (6) Cukup jela… |
| 2 | `SOP-Backup-Restore-Konfigurasi-Firewall.md-20` | 0.689 | ## 9. Prosedur Restore Konfigurasi… |
| 3 | `SOP-Patch-Upgrade-Firmware-Firewall.md-33` | 0.688 | **pengecualian risiko** dengan tanggal berakhir, pemilik, dan persetujuan CISO. ---… |
| 4 | `SOP-pengajuan-kredit.md-20` | 0.685 | n yang terdokumentasi. **Limit kewenangan memutus (ilustratif):** \| Jenjang Pemutus \| Batas Plafon \| \|---\|---\|… |
| 5 | `SOP-Penanganan-Insiden-Gangguan-Firewall.md-28` | 0.684 | ubah parameter kriptografi tanpa CR \| \| **Sertifikat kedaluwarsa** \| Terapkan sertifikat pengganti melalui eme… |
| 6 | `Konfigurasi-FW-23` | 0.684 | ### 7.4 Deskripsi/Komentar Rule (Wajib) Format: `CR:<nomor> \| Owner:<nama/unit> \| Exp:<YYYY-MM-DD atau PERMANE… |

</details>

<details><summary>hybrid — top-3 yang dikirim ke LLM</summary>

| # | _id | Skor | Cuplikan |
|---|---|---|---|
| 1 | `POJK-49` | rrf 0.0283 | unaan pihak penyedia jasa TI sebagaimana dimaksud pada ayat (1) paling sedikit memuat: a. proses identifikasi … |
| 2 | `Konfigurasi-FW-33` | rrf 0.0164 | ### Tahap 3 — Implementasi **Pelaksana:** Network Security Engineer (Pelaksana) **Waktu:** Dalam maintenance w… |
| 3 | `POJK-190` | rrf 0.0164 | a peningk atan pemberian kredit atau pembiayaan dan peningkatan pembiayaan ekspor - impor. Ayat (6) Cukup jela… |

</details>
