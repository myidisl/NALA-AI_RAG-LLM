# SOP Backup dan Restore Konfigurasi Firewall

**Nomor Dokumen:** SOP-SEC-FW-004
**Versi:** 1.0
**Tanggal Berlaku:** 2026-09-23
**Unit Pemilik:** Divisi Teknologi Informasi — Network & Security Operations
**Status:** Dokumen contoh untuk basis pengetahuan (knowledge base) NALA

> **Catatan:** Dokumen ini merupakan **template acuan umum**, bukan salinan kebijakan resmi institusi tertentu. Jadwal backup, masa retensi, serta target RPO/RTO bersifat ilustratif dan harus disesuaikan dengan ketentuan internal serta regulasi yang berlaku sebelum digunakan secara operasional.

---

## 1. Tujuan

1. Memastikan konfigurasi seluruh firewall selalu tercadangkan secara lengkap, aman, dan dapat dipulihkan.
2. Menyediakan langkah baku untuk memulihkan (*restore*) konfigurasi saat terjadi kegagalan perubahan, kerusakan perangkat, atau insiden keamanan.
3. Melindungi file backup yang memuat informasi sensitif (topologi, kredensial terenkripsi, kunci VPN, sertifikat) dari akses tidak sah.
4. Menjamin waktu pemulihan firewall sesuai target kelangsungan layanan perbankan.

---

## 2. Ruang Lingkup

Dokumen ini berlaku untuk backup dan restore konfigurasi seluruh firewall di lingkungan Production, DR, UAT, dan Development, termasuk sistem manajemen terpusat (*firewall management server*) dan firewall di lingkungan cloud.

**Tidak termasuk:** backup log firewall (diatur dalam **SOP-SEC-FW-005 Monitoring dan Log Management Firewall**) serta penggantian perangkat keras (diatur dalam **SOP-SEC-FW-009 Siklus Hidup Perangkat Firewall**).

---

## 3. Definisi

| Istilah | Penjelasan |
|---|---|
| **Running Config** | Konfigurasi yang sedang aktif dan dijalankan perangkat |
| **Full Backup** | Cadangan lengkap berisi konfigurasi, policy, object, VPN, sertifikat, dan pengaturan sistem |
| **Backup Terjadwal** | Backup otomatis yang berjalan sesuai jadwal tanpa intervensi manual |
| **Backup Ad-hoc** | Backup manual sebelum/sesudah perubahan, upgrade, atau pemeliharaan |
| **Repositori Backup** | Media penyimpanan terpusat, terpisah dari perangkat firewall, untuk menyimpan file backup |
| **Checksum** | Nilai hash (mis. SHA-256) untuk memastikan file backup tidak berubah atau rusak |
| **RPO** | *Recovery Point Objective* — batas maksimal kehilangan perubahan konfigurasi yang dapat diterima |
| **RTO** | *Recovery Time Objective* — batas maksimal waktu untuk memulihkan fungsi firewall |

---

## 4. Pihak yang Terlibat

| Peran | Tanggung Jawab Utama |
|---|---|
| **Network Security Engineer** | Mengelola job backup, memantau keberhasilan backup, dan melaksanakan restore |
| **Kepala Bagian Network Security** | Menyetujui restore di Production dan memantau hasil uji restore |
| **Tim Infrastruktur / Storage** | Menyediakan repositori backup beserta replikasinya ke site DR |
| **Information Security** | Menetapkan kontrol akses dan enkripsi repositori, serta mereview hasil uji restore |
| **NOC** | Memantau ketersediaan layanan selama proses restore |

---

## 5. Cakupan Data yang Dicadangkan

| Komponen | Keterangan |
|---|---|
| **Running config / system config** | Interface, routing, zona, NAT, HA, pengaturan sistem |
| **Security policy dan object** | Rule, object alamat/layanan, object group, security profile |
| **Konfigurasi VPN** | Site-to-site dan remote access, termasuk *pre-shared key* dalam bentuk terenkripsi |
| **Sertifikat dan private key** | Sertifikat SSL inspection, VPN, dan manajemen; diekspor dengan kata sandi |
| **Konfigurasi manajemen terpusat** | Database policy, template, dan daftar perangkat terkelola |
| **Informasi lisensi dan versi** | Nomor seri, lisensi aktif, versi firmware (untuk referensi saat restore) |

---

## 6. Jenis dan Jadwal Backup

| Jenis Backup | Waktu | Pelaksana |
|---|---|---|
| **Terjadwal harian** | Setiap hari pukul 01.00, otomatis | Sistem, dipantau Network Security Engineer |
| **Terjadwal mingguan (full)** | Setiap Minggu, termasuk sertifikat dan konfigurasi manajemen terpusat | Sistem, dipantau Network Security Engineer |
| **Pre-change** | Sebelum setiap implementasi CR | Network Security Engineer (Pelaksana CR) |
| **Post-change** | Setelah implementasi CR berhasil diverifikasi | Network Security Engineer (Pelaksana CR) |
| **Pre-upgrade** | Sebelum upgrade firmware sesuai SOP-SEC-FW-007 | Network Security Engineer |

**Konvensi nama file:** `<hostname>_<YYYYMMDD-HHMM>_<jenis>[-<nomor CR>]`

Contoh: `FW-DC-INT-01_20260923-0100_daily`, `FW-DC-INT-01_20260923-2215_pre-CR2026-0412`.

---

## 7. Penyimpanan dan Retensi

### 7.1 Ketentuan Penyimpanan

1. File backup disimpan di **repositori terpusat yang terpisah** dari perangkat firewall, di segmen jaringan MGMT.
2. Repositori direplikasi ke **site DR** sehingga backup tetap tersedia saat site utama tidak dapat diakses.
3. File backup **dienkripsi saat disimpan** (*encryption at rest*) dan ditransfer melalui protokol aman (SCP/SFTP/HTTPS).
4. Akses ke repositori dibatasi hanya untuk Network Security Engineer dan akun layanan backup, serta tercatat di log audit.
5. Setiap file backup disertai **checksum SHA-256** yang dihitung saat file dibuat.

### 7.2 Masa Retensi (Ilustratif)

| Jenis Backup | Retensi |
|---|---|
| Harian | 35 hari |
| Mingguan (full) | 12 minggu |
| Akhir bulan | 12 bulan |
| Akhir tahun | 5 tahun |
| Pre/post-change dan pre-upgrade | Mengikuti retensi dokumen CR, minimal 5 tahun |

---

## 8. Pemantauan dan Pengujian Backup

### 8.1 Pemantauan Harian

**Pelaksana:** Network Security Engineer
**Frekuensi:** Setiap hari kerja pagi

1. Memeriksa laporan status backup untuk memastikan seluruh perangkat berhasil dicadangkan.
2. Memastikan ukuran file wajar, yaitu tidak kosong dan tidak berbeda drastis dari backup sebelumnya tanpa alasan.
3. Menindaklanjuti backup yang gagal pada hari yang sama. Bila gagal **2 hari berturut-turut**, eskalasi ke Kepala Bagian Network Security.

### 8.2 Uji Restore Berkala

**Pelaksana:** Network Security Engineer, direview Information Security
**Frekuensi:** Triwulanan

1. Memilih sampel backup secara acak, minimal satu dari setiap jenis/vendor firewall.
2. Melakukan restore ke **perangkat lab, perangkat cadangan, atau virtual appliance**, bukan ke perangkat Production.
3. Membandingkan hasil restore dengan konfigurasi sumber: jumlah rule, object, VPN, dan sertifikat.
4. Mencatat waktu yang dibutuhkan untuk memvalidasi pencapaian RTO.
5. Mendokumentasikan hasil uji dan menindaklanjuti kegagalan.

---

## 9. Prosedur Restore Konfigurasi

### Tahap 1 — Penetapan Kebutuhan Restore

**Pelaksana:** Network Security Engineer

Restore dilakukan bila terjadi salah satu kondisi berikut:
- implementasi CR gagal dan perlu rollback (sesuai SOP-SEC-FW-002 Tahap 5);
- konfigurasi rusak atau perangkat tidak dapat boot normal;
- penggantian perangkat karena kerusakan (RMA);
- insiden keamanan yang mengindikasikan perubahan konfigurasi tidak sah (sesuai SOP-SEC-FW-006).

### Tahap 2 — Persetujuan

**Pelaksana:** Kepala Bagian Network Security

1. Restore dalam rangka rollback CR mengikuti persetujuan CR yang bersangkutan.
2. Restore di luar rollback CR diajukan sebagai **emergency change** sesuai SOP-SEC-FW-001 Bab 10.
3. Untuk insiden keamanan, restore dilakukan **setelah bukti forensik diamankan** (lihat SOP-SEC-FW-006).

### Tahap 3 — Pemilihan dan Validasi File Backup

1. Memilih backup terakhir yang diketahui baik (*last known good*), dengan mempertimbangkan perubahan yang telah terjadi sejak backup tersebut.
2. Memverifikasi **checksum** file sesuai catatan di repositori.
3. Memastikan versi firmware perangkat tujuan kompatibel dengan file backup.
4. Mengidentifikasi CR yang diimplementasikan setelah tanggal backup, karena perubahan tersebut perlu diterapkan ulang.

### Tahap 4 — Pelaksanaan Restore

1. Menginformasikan rencana restore kepada NOC dan pemilik layanan terdampak.
2. Untuk cluster HA: melakukan restore pada perangkat pasif terlebih dahulu bila memungkinkan, lalu melakukan failover terkontrol.
3. Mengimpor file backup dan mengimpor ulang sertifikat/private key bila tidak ikut terpulihkan.
4. Menerapkan kembali CR yang terlewat sesuai daftar pada Tahap 3.

### Tahap 5 — Verifikasi dan Dokumentasi

1. Memastikan status HA, interface, routing, VPN, dan koneksi ke SIEM normal.
2. Melakukan uji konektivitas layanan kritikal bersama NOC.
3. Mengambil backup post-restore baru.
4. Mendokumentasikan alasan, file yang digunakan, durasi, dan hasil restore pada tiket/CR.

---

## 10. Target Pemulihan (Ilustratif)

| Parameter | Target |
|---|---|
| **RPO konfigurasi** | Maksimal 24 jam (backup harian), atau 0 untuk perubahan melalui CR (backup pre/post-change) |
| **RTO restore konfigurasi pada perangkat yang sama** | 2 jam |
| **RTO penggantian perangkat (dengan unit cadangan tersedia)** | 8 jam |

---

## 11. Pengendalian Internal

1. **Kerahasiaan backup:** file backup diperlakukan sebagai informasi **rahasia** karena memuat topologi, hash kredensial, kunci VPN, dan private key.
2. **Integritas:** seluruh file backup dilengkapi checksum yang diverifikasi sebelum digunakan.
3. **Pemisahan lokasi:** backup tidak boleh hanya disimpan di perangkat firewall itu sendiri atau di laptop pegawai.
4. **Jejak audit:** akses, unduhan, dan penghapusan file backup tercatat di log repositori.
5. **Audit:** Audit Internal TI melakukan uji petik atas keberhasilan backup dan bukti uji restore triwulanan.

---

## 12. Pertanyaan yang Sering Diajukan

**Seberapa sering konfigurasi firewall dicadangkan?**
Otomatis setiap hari, full backup setiap minggu, dan secara manual sebelum serta sesudah setiap perubahan atau upgrade.

**Bolehkah menyimpan backup konfigurasi firewall di laptop untuk berjaga-jaga?**
Tidak. Backup hanya disimpan di repositori resmi yang terenkripsi dan aksesnya terkontrol, karena berisi informasi sensitif.

**Bagaimana memastikan backup benar-benar bisa dipakai?**
Melalui uji restore triwulanan ke perangkat lab atau virtual appliance, dengan membandingkan hasilnya terhadap konfigurasi sumber.

**Setelah restore dari backup kemarin, apa yang harus diperhatikan?**
Terapkan kembali CR yang diimplementasikan setelah waktu backup tersebut agar tidak ada akses yang hilang.

**Apakah sertifikat ikut ter-restore?**
Tergantung perangkat. Sertifikat dan private key dicadangkan terpisah dalam full backup mingguan dan diimpor ulang bila tidak ikut terpulihkan.

---

## 13. Referensi

- POJK Nomor 11/POJK.03/2022 tentang Penyelenggaraan Teknologi Informasi oleh Bank Umum
- ISO/IEC 27001:2022 — kontrol A.8.13 (*Information backup*) dan A.8.9 (*Configuration management*)
- SOP-SEC-FW-001 Change Request Firewall Policy
- SOP-SEC-FW-002 Konfigurasi Firewall Policy
- SOP-SEC-FW-006 Penanganan Insiden dan Gangguan Firewall
- SOP-SEC-FW-007 Patch dan Upgrade Firmware Firewall

---

## 14. Riwayat Revisi

| Versi | Tanggal | Perubahan | Penyusun |
|---|---|---|---|
| 1.0 | 2026-09-23 | Penerbitan dokumen pertama | Divisi Teknologi Informasi |
