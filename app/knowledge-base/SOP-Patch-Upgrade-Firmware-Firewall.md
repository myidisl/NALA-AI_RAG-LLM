# SOP Patch dan Upgrade Firmware Firewall

**Nomor Dokumen:** SOP-SEC-FW-007
**Versi:** 1.0
**Tanggal Berlaku:** 2026-09-23
**Unit Pemilik:** Divisi Teknologi Informasi — Network & Security Operations
**Status:** Dokumen contoh untuk basis pengetahuan (knowledge base) NALA

> **Catatan:** Dokumen ini merupakan **template acuan umum**, bukan salinan kebijakan resmi institusi tertentu. Batas waktu patch, kriteria prioritas, dan kebijakan versi bersifat ilustratif dan harus disesuaikan dengan ketentuan internal serta regulasi yang berlaku sebelum digunakan secara operasional.

---

## 1. Tujuan

1. Memastikan kerentanan pada firmware/sistem operasi firewall ditangani tepat waktu sesuai tingkat risikonya.
2. Menjaga firewall tetap berjalan pada versi yang didukung vendor dan stabil.
3. Menyediakan langkah baku upgrade yang aman, teruji, dan memiliki rencana rollback, sehingga risiko gangguan layanan dapat ditekan.
4. Memastikan update signature keamanan (IPS, anti-malware, aplikasi, URL) selalu mutakhir.

---

## 2. Ruang Lingkup

Dokumen ini berlaku untuk:

- Patch keamanan (*hotfix*) dan upgrade versi firmware/OS firewall
- Upgrade sistem manajemen terpusat firewall
- Update signature/content keamanan (IPS, anti-malware, application ID, URL category, threat intelligence feed)
- Firewall on-premise dan virtual appliance di cloud, di seluruh lingkungan

**Tidak termasuk:** penggantian perangkat keras dan penanganan perangkat *End of Life*, yang diatur dalam **SOP-SEC-FW-009 Siklus Hidup Perangkat Firewall**.

---

## 3. Definisi

| Istilah | Penjelasan |
|---|---|
| **Patch / Hotfix** | Perbaikan dalam versi yang sama untuk menutup kerentanan atau bug tertentu |
| **Upgrade Mayor** | Perpindahan ke versi utama baru yang dapat membawa perubahan fitur dan perilaku |
| **Security Advisory** | Pemberitahuan resmi vendor mengenai kerentanan dan perbaikannya |
| **CVSS** | *Common Vulnerability Scoring System* — skor tingkat keparahan kerentanan (0–10) |
| **Known Exploited Vulnerability** | Kerentanan yang terbukti sudah dieksploitasi secara aktif oleh penyerang |
| **Versi Rekomendasi Vendor** | Versi yang dinyatakan stabil dan direkomendasikan vendor untuk lingkungan produksi |
| **End of Support (EoS)** | Tanggal vendor berhenti menyediakan patch untuk suatu versi atau perangkat |
| **Mitigasi Sementara** | Tindakan pengganti untuk menurunkan risiko selama patch belum dapat diterapkan |

---

## 4. Pihak yang Terlibat

| Peran | Tanggung Jawab Utama |
|---|---|
| **Network Security Engineer** | Memantau advisory, mengevaluasi dan menguji versi, serta melaksanakan upgrade |
| **Information Security** | Menilai risiko kerentanan, menetapkan prioritas, dan memantau kepatuhan batas waktu patch |
| **Change Manager / CAB** | Menyetujui dan menjadwalkan upgrade di Production |
| **Kepala Bagian Network Security** | Menetapkan versi standar (*baseline version*) dan menyetujui pengecualian teknis |
| **Vendor Firewall** | Menyediakan advisory, dukungan teknis, dan pendampingan upgrade bila diperlukan |
| **NOC** | Memantau layanan selama dan setelah upgrade |

---

## 5. Sumber Informasi Kerentanan

1. Security advisory dan notifikasi dari portal dukungan vendor (berlangganan notifikasi email).
2. Hasil pemindaian kerentanan (*vulnerability scan*) dan penetration test.
3. Katalog kerentanan yang dieksploitasi aktif dan informasi *threat intelligence*.
4. Peringatan dari regulator, CSIRT sektor keuangan, atau lembaga siber nasional.

Network Security Engineer memeriksa sumber tersebut **minimal setiap hari kerja** dan mencatat advisory yang relevan dengan perangkat/versi yang digunakan.

---

## 6. Prioritas dan Batas Waktu Patch (Ilustratif)

| Prioritas | Kriteria | Batas Waktu Penerapan di Production |
|---|---|---|
| **Darurat** | Kerentanan dieksploitasi aktif **dan** fitur rentan terekspos (mis. portal VPN atau interface manajemen dapat dijangkau dari Internet) | Mitigasi dalam 24 jam; patch dalam **72 jam** |
| **Kritis** | CVSS ≥ 9.0, atau dieksploitasi aktif tetapi fitur tidak terekspos | **14 hari kalender** |
| **Tinggi** | CVSS 7.0–8.9 | **30 hari kalender** |
| **Sedang** | CVSS 4.0–6.9 | **90 hari kalender** |
| **Rendah** | CVSS < 4.0 atau fitur rentan tidak digunakan | Siklus upgrade berikutnya |

> Prioritas ditetapkan Information Security berdasarkan skor CVSS **dan** keterpaparan nyata di lingkungan bank. Kerentanan pada fitur yang tidak diaktifkan dapat diturunkan prioritasnya dengan justifikasi tertulis.

---

## 7. Kebijakan Versi

1. Firewall Production menggunakan **versi rekomendasi vendor** yang telah diuji internal, bukan otomatis versi terbaru.
2. Seluruh firewall dengan fungsi dan model sejenis dijaga pada **versi baseline yang sama**.
3. Upgrade mayor dievaluasi **minimal setahun sekali** untuk menghindari ketertinggalan versi.
4. Versi yang akan memasuki EoS dalam **6 bulan** wajib direncanakan upgradenya.
5. Anggota cluster HA wajib berada pada versi yang sama, kecuali sesaat selama proses upgrade.

---

## 8. Alur Proses Patch dan Upgrade Firmware

### Tahap 1 — Identifikasi dan Penilaian

**Pelaksana:** Network Security Engineer dan Information Security
**SLA:** 1 hari kerja sejak advisory terbit (2 jam untuk kategori Darurat)

1. Mencocokkan advisory dengan inventaris perangkat, model, versi, dan fitur yang aktif.
2. Menilai keterpaparan: apakah fitur rentan aktif dan apakah dapat dijangkau dari zona tidak dipercaya.
3. Menetapkan prioritas sesuai **Bab 6** dan mencatatnya di register kerentanan.
4. Menentukan mitigasi sementara bila patch tidak dapat segera diterapkan.

### Tahap 2 — Evaluasi Versi Target

**Pelaksana:** Network Security Engineer
**SLA:** 3 hari kerja (lebih cepat untuk kategori Darurat/Kritis)

1. Membaca *release notes*: kerentanan yang ditutup, *known issues*, perubahan perilaku, dan fitur yang dihapus.
2. Memastikan jalur upgrade (*upgrade path*) yang didukung, termasuk versi perantara yang wajib dilalui.
3. Memeriksa kompatibilitas dengan sistem manajemen terpusat, lisensi, dan integrasi (SIEM, TACACS+, PAM).
4. Memastikan kapasitas penyimpanan dan memori perangkat mencukupi.
5. Mengunduh image hanya dari portal resmi vendor dan **memverifikasi checksum/tanda tangan digital**.

### Tahap 3 — Pengujian

**Pelaksana:** Network Security Engineer

1. Melakukan upgrade di **lab, UAT, atau perangkat non-kritikal** terlebih dahulu.
2. Menguji fungsi utama: pemrosesan rule, NAT, VPN, HA failover, logging ke SIEM, autentikasi administrator, dan fitur keamanan (IPS, SSL inspection).
3. Menjalankan beban uji bila tersedia untuk memastikan tidak ada penurunan kinerja.
4. Mendokumentasikan hasil uji.

> Untuk kategori **Darurat**, pengujian dapat dipersingkat dengan persetujuan Kepala Bagian Network Security dan CISO, disertai rencana rollback yang siap dijalankan.

### Tahap 4 — Pengajuan dan Persetujuan Perubahan

**Pelaksana:** Network Security Engineer

1. Mengajukan CR di sistem ITSM yang memuat: versi asal dan tujuan, alasan (nomor advisory/CVE), hasil uji, urutan perangkat, estimasi durasi, dampak, dan rencana rollback.
2. Upgrade firmware Production dikategorikan **risiko tinggi** dan disetujui melalui CAB.
3. Patch kategori Darurat diajukan sebagai **emergency change** sesuai SOP-SEC-FW-001 Bab 10.
4. Menjadwalkan pelaksanaan dalam maintenance window, di luar periode *change freeze*.

### Tahap 5 — Persiapan Pelaksanaan

**Pelaksana:** Network Security Engineer

1. Mengambil backup konfigurasi **pre-upgrade** sesuai SOP-SEC-FW-004.
2. Mencatat kondisi awal (*baseline*): jumlah sesi, status HA, status VPN, dan utilisasi, sebagai pembanding setelah upgrade.
3. Memastikan akses console/out-of-band tersedia bila akses jaringan manajemen terputus.
4. Memastikan tiket dukungan vendor dapat dibuka dengan prioritas tinggi selama pelaksanaan.
5. Menginformasikan jadwal kepada NOC dan pemilik layanan terdampak.

### Tahap 6 — Pelaksanaan Upgrade

**Pelaksana:** Network Security Engineer

Urutan untuk cluster HA (*active-passive*):
1. Upgrade sistem manajemen terpusat terlebih dahulu bila diperlukan versi yang lebih baru.
2. Upgrade anggota **pasif** → verifikasi perangkat kembali normal dan tersinkron.
3. Lakukan **failover terkontrol** sehingga anggota yang sudah di-upgrade menjadi aktif → verifikasi layanan.
4. Upgrade anggota yang kini pasif → verifikasi sinkronisasi HA.
5. Kembalikan peran aktif/pasif sesuai desain bila diperlukan.

Untuk perangkat tunggal (tanpa HA), upgrade menyebabkan **gangguan layanan**, sehingga dampaknya wajib dinyatakan dalam CR dan dikomunikasikan kepada unit terdampak.

### Tahap 7 — Verifikasi

**Pelaksana:** Network Security Engineer bersama NOC

1. Memastikan versi terpasang sesuai target di seluruh anggota cluster.
2. Membandingkan kondisi dengan baseline Tahap 5: sesi, VPN, HA, dan utilisasi.
3. Memastikan log terkirim ke SIEM, autentikasi TACACS+/RADIUS berfungsi, dan update signature berjalan.
4. Melakukan uji layanan kritikal bersama pemilik aplikasi.
5. Mengambil backup **post-upgrade**.
6. Memantau secara intensif selama **24–72 jam** setelah upgrade.

### Tahap 8 — Rollback (bila diperlukan)

**Pemicu:** layanan kritikal terganggu, HA tidak stabil, atau ditemukan bug yang berdampak dan tidak dapat diperbaiki dalam maintenance window.

1. Menggunakan partisi/image sebelumnya (fitur *boot to previous version*) atau reinstall versi lama.
2. Merestore konfigurasi pre-upgrade sesuai SOP-SEC-FW-004.
3. Memverifikasi layanan pulih, lalu mencatat penyebab kegagalan pada CR.
4. Bila rollback dilakukan untuk patch keamanan, terapkan **mitigasi sementara** dan jadwalkan ulang upgrade.

### Tahap 9 — Penutupan

1. Memperbarui inventaris/CMDB dengan versi baru.
2. Menutup item kerentanan pada register kerentanan.
3. Menutup CR dengan bukti pelaksanaan dan hasil verifikasi.

---

## 9. Mitigasi Sementara

Bila patch belum dapat diterapkan sesuai batas waktu, Information Security menyetujui mitigasi sementara, mis.:

1. Menonaktifkan fitur rentan yang tidak kritikal.
2. Membatasi akses ke interface manajemen atau portal VPN hanya dari alamat tertentu.
3. Menerapkan signature IPS/virtual patch dari vendor.
4. Meningkatkan monitoring di SIEM untuk indikator eksploitasi kerentanan tersebut.

Mitigasi sementara dicatat sebagai **pengecualian risiko** dengan tanggal berakhir, pemilik, dan persetujuan CISO.

---

## 10. Update Signature dan Content Keamanan

1. Update signature IPS, anti-malware, application ID, dan URL category dikonfigurasi **otomatis** minimal harian, dan dikategorikan sebagai **standard change**.
2. Untuk signature IPS baru yang berpotensi memblokir lalu lintas sah, gunakan mode *alert only* terlebih dahulu sesuai rekomendasi vendor, lalu tinjau sebelum diubah ke mode blok.
3. Kegagalan update dipantau sesuai ambang batas pada SOP-SEC-FW-005.
4. Bila update signature menyebabkan lalu lintas sah terblokir, tangani sesuai SOP-SEC-FW-006, dan lakukan revert ke versi signature sebelumnya bila diperlukan.

---

## 11. Pengendalian Internal

1. **Integritas image:** hanya image resmi dengan checksum/tanda tangan digital yang terverifikasi yang boleh dipasang.
2. **Register kerentanan:** setiap advisory yang relevan tercatat dengan prioritas, batas waktu, status, dan pengecualian.
3. **Kepatuhan batas waktu:** Information Security melaporkan setiap bulan kerentanan yang melewati batas waktu kepada CISO.
4. **Keseragaman versi:** penyimpangan dari versi baseline wajib memiliki justifikasi dan persetujuan Kepala Bagian Network Security.
5. **Audit:** Audit Internal TI melakukan uji petik atas kepatuhan patch dan kelengkapan dokumentasi CR upgrade.

---

## 12. Pertanyaan yang Sering Diajukan

**Berapa lama batas waktu menambal kerentanan kritis pada firewall?**
14 hari kalender untuk kerentanan kritis, dan 72 jam bila kerentanan dieksploitasi aktif serta fitur rentan terekspos ke Internet (ilustratif).

**Kenapa tidak langsung pakai versi firmware terbaru?**
Versi terbaru belum tentu stabil. Bank menggunakan versi rekomendasi vendor yang sudah diuji internal agar risiko bug yang mengganggu layanan lebih kecil.

**Apakah upgrade firewall menyebabkan layanan terputus?**
Pada cluster HA, upgrade dilakukan bergantian sehingga gangguan minimal, umumnya hanya sesaat saat failover. Pada perangkat tunggal akan ada downtime, sehingga harus dijadwalkan dan dikomunikasikan.

**Bagaimana bila patch belum bisa dipasang karena menunggu jadwal?**
Terapkan mitigasi sementara yang disetujui Information Security, seperti membatasi akses ke fitur rentan atau mengaktifkan virtual patch IPS.

**Apakah update signature IPS perlu CR?**
Tidak per update. Update signature otomatis dikategorikan sebagai standard change, tetapi hasilnya tetap dipantau.

---

## 13. Referensi

- POJK Nomor 11/POJK.03/2022 tentang Penyelenggaraan Teknologi Informasi oleh Bank Umum
- ISO/IEC 27001:2022 — kontrol A.8.8 (*Management of technical vulnerabilities*) dan A.8.32 (*Change management*)
- PCI DSS v4.0 — Requirement 6.3 (identifikasi dan penanganan kerentanan keamanan)
- SOP-SEC-FW-001 Change Request Firewall Policy
- SOP-SEC-FW-004 Backup dan Restore Konfigurasi Firewall
- SOP-SEC-FW-005 Monitoring dan Log Management Firewall
- SOP-SEC-FW-006 Penanganan Insiden dan Gangguan Firewall

---

## 14. Riwayat Revisi

| Versi | Tanggal | Perubahan | Penyusun |
|---|---|---|---|
| 1.0 | 2026-09-23 | Penerbitan dokumen pertama | Divisi Teknologi Informasi |
