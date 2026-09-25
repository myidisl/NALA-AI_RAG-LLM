# SOP Review dan Resertifikasi Firewall Rule

**Nomor Dokumen:** SOP-SEC-FW-003
**Versi:** 1.0
**Tanggal Berlaku:** 2026-09-23
**Unit Pemilik:** Divisi Teknologi Informasi — Network & Security Operations
**Status:** Dokumen contoh untuk basis pengetahuan (knowledge base) NALA

> **Catatan:** Dokumen ini merupakan **template acuan umum**, bukan salinan kebijakan resmi institusi tertentu. Frekuensi review, batas waktu tindak lanjut, dan kriteria temuan bersifat ilustratif dan harus disesuaikan dengan ketentuan internal serta regulasi yang berlaku sebelum digunakan secara operasional.

---

## 1. Tujuan

1. Memastikan setiap firewall rule yang aktif masih dibutuhkan, memiliki pemilik, dan sesuai prinsip *least privilege*.
2. Mengidentifikasi serta membersihkan rule yang tidak terpakai, duplikat, tertutup rule lain, atau terlalu luas.
3. Menjaga firewall policy tetap ringkas agar mudah diaudit dan tidak menurunkan performa perangkat.
4. Memenuhi kewajiban review berkala atas kontrol keamanan jaringan sesuai kebijakan internal dan standar yang diacu.

---

## 2. Ruang Lingkup

Dokumen ini berlaku untuk review seluruh **firewall policy** di lingkungan Production dan Disaster Recovery (DR), mencakup firewall perimeter, internal, pihak ketiga, dan cloud sebagaimana didefinisikan dalam **SOP-SEC-FW-002 Konfigurasi Firewall Policy**.

Lingkungan UAT dan Development direview dengan frekuensi yang lebih longgar (tahunan).

**Tidak termasuk:** pelaksanaan teknis penghapusan atau perubahan rule, yang wajib melalui **SOP-SEC-FW-001 Change Request Firewall Policy** dan dikerjakan sesuai **SOP-SEC-FW-002**.

---

## 3. Definisi

| Istilah | Penjelasan |
|---|---|
| **Review Teknis** | Analisis rulebase oleh Network Security Engineer untuk menemukan rule bermasalah secara teknis |
| **Resertifikasi** | Konfirmasi dari Application / System Owner bahwa rule miliknya masih dibutuhkan dan cakupannya masih tepat |
| **Zero Hit Rule** | Rule yang tidak pernah cocok dengan lalu lintas (*hit count* = 0) selama periode pengamatan |
| **Shadowed Rule** | Rule yang tidak pernah tercapai karena lalu lintasnya sudah tercakup rule di atasnya |
| **Redundant Rule** | Rule duplikat atau sepenuhnya tercakup rule lain dengan aksi yang sama |
| **Overly Permissive Rule** | Rule dengan cakupan terlalu luas, mis. menggunakan any, subnet besar, atau rentang port lebar |
| **Orphan Rule** | Rule tanpa nomor CR yang valid atau tanpa pemilik yang masih aktif |
| **Expired Rule** | Rule sementara yang telah melewati tanggal kedaluwarsa pada CR |

---

## 4. Pihak yang Terlibat

| Peran | Tanggung Jawab Utama |
|---|---|
| **Network Security Engineer** | Menyiapkan data rulebase, melakukan review teknis, dan mengajukan CR tindak lanjut |
| **Information Security** | Mengoordinasikan resertifikasi, menilai temuan berisiko, dan menyusun laporan review |
| **Application / System Owner** | Meresertifikasi rule miliknya: tetap, dipersempit, atau dihapus |
| **Kepala Bagian Network Security** | Menyetujui hasil review teknis dan memantau penyelesaian tindak lanjut |
| **CISO** | Menerima laporan review dan memutuskan eskalasi atas temuan yang tidak ditindaklanjuti |
| **Audit Internal TI** | Menguji kepatuhan pelaksanaan review terhadap SOP ini |

---

## 5. Jenis dan Frekuensi Review

| Jenis Review | Frekuensi | Pelaksana | Fokus |
|---|---|---|---|
| **Pemeriksaan rule kedaluwarsa** | Harian | Network Security Engineer | Rule sementara yang lewat tanggal kedaluwarsa |
| **Review teknis rulebase** | Triwulanan | Network Security Engineer | Zero hit, shadowed, redundant, overly permissive, orphan |
| **Resertifikasi rule** | 6 bulanan | Information Security + Application / System Owner | Kebutuhan bisnis dan kepemilikan setiap rule |
| **Review arsitektur segmentasi** | Tahunan | Information Security + Network Security | Kesesuaian model zona dan matriks akses antar zona |
| **Review ad-hoc** | Sesuai kebutuhan | Information Security | Setelah insiden keamanan, perubahan arsitektur besar, atau temuan audit |

---

## 6. Kriteria Temuan dan Tingkat Keparahan

| Temuan | Tingkat Keparahan | Batas Waktu Tindak Lanjut |
|---|---|---|
| Rule any-any-any dengan aksi allow | **Kritis** | 7 hari kalender |
| Rule allow dari INET/PARTNER dengan layanan any, atau akses administratif dari luar zona MGMT | **Kritis** | 7 hari kalender |
| Rule menuju RESTRICTED yang overly permissive | **Tinggi** | 30 hari kalender |
| Orphan rule (tanpa CR atau pemilik tidak aktif) | **Tinggi** | 30 hari kalender |
| Expired rule yang masih aktif | **Tinggi** | 7 hari kalender |
| Zero hit rule ≥ 90 hari | **Sedang** | 60 hari kalender |
| Shadowed atau redundant rule | **Sedang** | 60 hari kalender |
| Deskripsi rule tidak sesuai konvensi, logging tidak aktif | **Rendah** | 90 hari kalender |

> Batas waktu dihitung sejak laporan review disetujui Kepala Bagian Network Security.

---

## 7. Alur Proses Review dan Resertifikasi

### Tahap 1 — Persiapan Data

**Pelaksana:** Network Security Engineer
**SLA:** 3 hari kerja sejak periode review dimulai

1. Mengekspor rulebase terbaru dari seluruh firewall dalam cakupan, termasuk hit count dan tanggal terakhir cocok (*last hit*).
2. Memastikan data hit count mencakup minimal **90 hari** pengamatan. Bila counter pernah di-reset (mis. setelah reboot atau upgrade), catat periode yang tersedia.
3. Mencocokkan setiap rule dengan data CR di sistem ITSM untuk memperoleh pemilik, masa berlaku, dan justifikasi.
4. Mencocokkan pemilik dengan data kepegawaian untuk mendeteksi pemilik yang sudah mutasi atau keluar.

### Tahap 2 — Review Teknis

**Pelaksana:** Network Security Engineer
**SLA:** 5 hari kerja

1. Menjalankan analisis rulebase, dengan alat bantu analisis kebijakan bila tersedia, untuk menemukan temuan sesuai **Bab 6**.
2. Memverifikasi setiap temuan secara manual sebelum dicatat, untuk menghindari salah identifikasi (mis. rule zero hit yang ternyata dipakai untuk proses tahunan atau DR).
3. Menyusun daftar temuan beserta rekomendasi: hapus, persempit, gabungkan, pindahkan urutan, atau perbaiki deskripsi.
4. Mengajukan hasil review kepada Kepala Bagian Network Security untuk disetujui.

### Tahap 3 — Resertifikasi oleh Pemilik

**Pelaksana:** Information Security dan Application / System Owner
**SLA:** 10 hari kerja untuk respons pemilik
**Berlaku untuk:** siklus review 6 bulanan

1. Information Security mengirimkan daftar rule kepada setiap Application / System Owner melalui sistem ITSM atau formulir resertifikasi.
2. Pemilik menyatakan untuk setiap rule: **Tetap Dibutuhkan**, **Perlu Dipersempit**, atau **Tidak Dibutuhkan**, beserta alasannya.
3. Bila pemilik tidak merespons dalam 10 hari kerja, Information Security mengeskalasi ke atasan pemilik dengan tenggat tambahan **5 hari kerja**.
4. Bila tetap tidak ada respons, rule dinyatakan **tidak tersertifikasi** dan dijadwalkan untuk dinonaktifkan melalui CR.
5. Rule milik pegawai yang telah mutasi atau keluar dialihkan ke atasan langsung atau penanggung jawab aplikasi yang baru.

### Tahap 4 — Tindak Lanjut Melalui CR

**Pelaksana:** Network Security Engineer
**SLA:** Sesuai batas waktu pada **Bab 6**

1. Mengajukan CR sesuai **SOP-SEC-FW-001** untuk setiap tindak lanjut. Beberapa rule dapat digabung dalam satu CR pembersihan (*cleanup CR*).
2. Rule yang akan dihapus terlebih dahulu **dinonaktifkan (disable)** selama **30 hari kalender** sebagai masa pengamatan.
3. Bila selama masa pengamatan terjadi gangguan layanan akibat rule dinonaktifkan, rule diaktifkan kembali melalui emergency change dan pemilik wajib meresertifikasinya.
4. Setelah masa pengamatan berakhir tanpa gangguan, rule dihapus permanen.
5. Rule yang dipersempit langsung dikonfigurasi ulang sesuai **SOP-SEC-FW-002**.

> Pengecualian: temuan **Kritis** dapat langsung dinonaktifkan atau dipersempit tanpa masa pengamatan, dengan persetujuan CISO.

### Tahap 5 — Pelaporan

**Pelaksana:** Information Security
**SLA:** 5 hari kerja setelah siklus review selesai

1. Menyusun laporan review yang memuat metrik pada **Bab 8**, daftar temuan, status tindak lanjut, dan pemilik yang tidak responsif.
2. Menyampaikan laporan kepada Kepala Divisi Operasional TI dan CISO.
3. Memantau temuan yang melewati batas waktu dan mengeskalasikannya dalam forum manajemen risiko TI.
4. Mengarsipkan laporan dan bukti resertifikasi sebagai bahan audit.

---

## 8. Metrik Pelaporan

| Metrik | Target (Ilustratif) |
|---|---|
| Persentase rule yang tersertifikasi pemilik | ≥ 95% |
| Jumlah rule tanpa nomor CR (orphan) | 0 |
| Jumlah rule any-any-any | 0 |
| Persentase temuan ditutup sesuai batas waktu | ≥ 90% |
| Jumlah expired rule yang masih aktif | 0 |
| Tren jumlah total rule per firewall | Stabil atau menurun |

---

## 9. Pengendalian Internal

1. **Pemisahan fungsi:** review teknis dilakukan Network Security Engineer, sedangkan resertifikasi diputuskan oleh Application / System Owner, bukan oleh pelaksana konfigurasi.
2. **Tidak ada penghapusan langsung:** setiap penghapusan atau perubahan rule hasil review wajib melalui CR.
3. **Bukti tertulis:** keputusan resertifikasi pemilik tersimpan di sistem ITSM atau formulir yang ditandatangani.
4. **Retensi:** laporan review dan bukti resertifikasi disimpan minimal **5 tahun**, atau sesuai ketentuan retensi internal.
5. **Kerahasiaan:** daftar rule dan hasil review bersifat **rahasia** karena memuat topologi dan celah keamanan.

---

## 10. Pertanyaan yang Sering Diajukan

**Seberapa sering firewall rule harus direview?**
Review teknis setiap triwulan, resertifikasi oleh pemilik setiap 6 bulan, dan review arsitektur segmentasi setiap tahun. Rule kedaluwarsa diperiksa harian.

**Rule saya tidak ada lalu lintasnya karena hanya dipakai saat tutup tahun atau uji DR. Apakah akan dihapus?**
Tidak otomatis. Nyatakan **Tetap Dibutuhkan** saat resertifikasi disertai alasannya. Network Security Engineer akan menandai rule tersebut sebagai pengecualian zero hit.

**Apa yang terjadi bila saya tidak merespons permintaan resertifikasi?**
Permintaan dieskalasi ke atasan Anda. Bila tetap tidak ada respons, rule dianggap tidak tersertifikasi lalu dinonaktifkan melalui CR.

**Kenapa rule dinonaktifkan dulu, tidak langsung dihapus?**
Masa pengamatan 30 hari memberi kesempatan mendeteksi ketergantungan yang tidak terdokumentasi. Rule dapat diaktifkan kembali dengan cepat tanpa harus dibuat ulang.

**Pemilik rule sudah pindah unit. Siapa yang meresertifikasi?**
Atasan langsung pemilik sebelumnya atau penanggung jawab aplikasi yang baru. Data pemilik pada rule diperbarui melalui CR.

---

## 11. Referensi

- POJK Nomor 11/POJK.03/2022 tentang Penyelenggaraan Teknologi Informasi oleh Bank Umum
- ISO/IEC 27001:2022 — kontrol A.8.20 (*Networks security*) dan A.5.18 (*Access rights*)
- PCI DSS v4.0 — Requirement 1.2.7 (review konfigurasi network security controls minimal setiap 6 bulan)
- SOP-SEC-FW-001 Change Request Firewall Policy
- SOP-SEC-FW-002 Konfigurasi Firewall Policy

---

## 12. Riwayat Revisi

| Versi | Tanggal | Perubahan | Penyusun |
|---|---|---|---|
| 1.0 | 2026-09-23 | Penerbitan dokumen pertama | Divisi Teknologi Informasi |
