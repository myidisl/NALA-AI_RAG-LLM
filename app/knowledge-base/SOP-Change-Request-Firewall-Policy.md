# SOP Change Request Firewall Policy

**Nomor Dokumen:** SOP-SEC-FW-001
**Versi:** 1.1
**Tanggal Berlaku:** 2026-09-23
**Unit Pemilik:** Divisi Teknologi Informasi — Network & Security Operations
**Status:** Dokumen contoh untuk basis pengetahuan (knowledge base) NALA

> **Catatan:** Dokumen ini merupakan **template acuan umum**, bukan salinan kebijakan resmi institusi tertentu. Angka SLA, matriks persetujuan, dan klasifikasi risiko bersifat ilustratif dan harus disesuaikan dengan ketentuan internal serta regulasi yang berlaku sebelum digunakan secara operasional.

---

## 1. Tujuan

1. Menyediakan panduan baku dalam mengajukan, menilai, menyetujui, dan menutup permintaan perubahan (*change request*) atas firewall policy.
2. Memastikan setiap akses jaringan yang dibuka memiliki justifikasi bisnis yang jelas, pemilik yang bertanggung jawab, serta telah dinilai risikonya.
3. Mencegah perubahan firewall yang tidak sah (*unauthorized change*) yang dapat membuka celah keamanan atau mengganggu layanan perbankan.
4. Menjaga jejak audit (*audit trail*) yang lengkap untuk kebutuhan audit internal, audit eksternal, dan pemeriksaan regulator.

---

## 2. Ruang Lingkup

Dokumen ini berlaku untuk seluruh permintaan perubahan pada **firewall policy** di lingkungan bank, mencakup:

- Firewall perimeter (Internet, DMZ)
- Firewall internal / segmentasi antar zona (server farm, core banking, user, management)
- Firewall untuk koneksi pihak ketiga (vendor, mitra, switching/payment network)
- Firewall di lingkungan cloud (security group, network ACL, cloud firewall)
- Web Application Firewall (WAF) — khusus perubahan rule allow/block

Jenis perubahan yang dicakup: **penambahan, perubahan, perpanjangan, dan penghapusan** rule maupun object (alamat, grup, service).

**Tidak termasuk:**
- Upgrade firmware/OS firewall, yang diatur dalam **SOP-SEC-FW-007 Patch dan Upgrade Firmware Firewall**. Upgrade tetap diajukan melalui CR sesuai alur dokumen ini.
- Pengadaan, penggantian, dan penghapusan perangkat, yang diatur dalam **SOP-SEC-FW-009 Siklus Hidup Perangkat Firewall**.
- Perubahan routing, yang diatur dalam SOP Change Management TI tersendiri.

Standar teknis penulisan rule diatur dalam **SOP-SEC-FW-002 Konfigurasi Firewall Policy**.

---

## 3. Definisi

| Istilah | Penjelasan |
|---|---|
| **Change Request (CR)** | Permintaan resmi untuk mengubah firewall policy, dicatat dalam sistem ITSM dengan nomor unik |
| **Firewall Policy / Rule** | Aturan yang menentukan lalu lintas jaringan yang diizinkan atau ditolak berdasarkan sumber, tujuan, layanan, dan aksi |
| **Requester** | Pegawai yang mengajukan CR atas nama unit bisnis atau aplikasi |
| **Application / System Owner** | Pejabat yang bertanggung jawab atas aplikasi/sistem yang aksesnya diminta dan menjamin justifikasi bisnisnya |
| **Zona** | Segmen jaringan dengan tingkat kepercayaan tertentu (mis. Internet, DMZ, Internal, Restricted) |
| **Restricted Zone** | Zona berisi sistem kritikal atau data sensitif, seperti core banking, database nasabah, dan sistem pembayaran |
| **CAB** | *Change Advisory Board* — forum yang menilai dan menyetujui perubahan berisiko |
| **Maintenance Window** | Jadwal yang ditetapkan untuk melakukan perubahan pada sistem produksi |
| **Rule Sementara** | Rule dengan masa berlaku terbatas yang wajib dihapus atau diperpanjang saat kedaluwarsa |
| **Rule Recertification** | Peninjauan ulang berkala untuk memastikan rule masih dibutuhkan dan tetap sesuai |

---

## 4. Pihak yang Terlibat

| Peran | Tanggung Jawab Utama |
|---|---|
| **Requester** | Mengisi formulir CR secara lengkap dan benar, melakukan uji konektivitas setelah implementasi |
| **Application / System Owner** | Menyetujui justifikasi bisnis dan bertanggung jawab atas akses yang diminta sepanjang masa berlakunya |
| **Network Security Engineer** | Melakukan review teknis, mendesain rule sesuai standar, dan mengimplementasikan perubahan |
| **Information Security (Unit Keamanan Informasi)** | Melakukan penilaian risiko dan memberikan rekomendasi keamanan |
| **Change Manager / CAB** | Menyetujui CR berisiko sedang–tinggi dan menetapkan jadwal implementasi |
| **Service Desk / NOC** | Memantau layanan saat dan setelah implementasi, menjadi titik eskalasi gangguan |
| **Audit Internal TI** | Melakukan uji petik kepatuhan proses dan kelengkapan jejak audit |

---

## 5. Kategori Change Request

| Kategori | Kriteria | Contoh |
|---|---|---|
| **Standard** | Perubahan berisiko rendah yang sudah pra-disetujui dan berulang dengan pola baku | Menambahkan IP server baru ke object group yang sudah memiliki rule disetujui |
| **Normal** | Perubahan yang harus melalui penilaian risiko dan persetujuan penuh | Membuka akses aplikasi baru ke database di server farm |
| **Emergency** | Perubahan mendesak untuk memulihkan layanan kritikal atau menahan insiden keamanan | Memblokir IP penyerang aktif; membuka akses DR saat gangguan core banking |

---

## 6. Klasifikasi Risiko

Klasifikasi risiko menentukan jenjang persetujuan pada **Bab 8**.

| Tingkat Risiko | Kriteria (salah satu terpenuhi) |
|---|---|
| **Tinggi** | Akses masuk (*inbound*) dari Internet ke zona internal; akses ke **Restricted Zone** (core banking, database nasabah, sistem pembayaran); akses dari/ke pihak ketiga; membuka port administratif (SSH, RDP, SMB, Telnet, database) dari zona yang kurang dipercaya; rule dengan sumber/tujuan/layanan bernilai **any** |
| **Sedang** | Akses antar zona internal di luar Restricted Zone; akses keluar (*outbound*) ke Internet untuk server; perubahan pada rule berisiko tinggi yang sudah ada |
| **Rendah** | Akses antar server dalam zona yang sama; penghapusan rule; penambahan object ke grup dengan rule yang sudah disetujui |

> Rule dengan nilai **any** pada sumber, tujuan, **dan** layanan sekaligus (*any-any-any*) **dilarang** dan tidak dapat diajukan melalui kategori apa pun.

---

## 7. Alur Proses Change Request

### Tahap 1 — Pengajuan CR

**Pelaksana:** Requester
**SLA:** —

1. Mengisi formulir CR di sistem ITSM dengan data sesuai **Bab 9**.
2. Melampirkan dokumen pendukung: diagram alur data, dokumen desain aplikasi, atau kontrak/perjanjian kerja sama untuk akses pihak ketiga.
3. Menetapkan **masa berlaku** akses: permanen atau sementara (maksimal 90 hari).
4. Meminta persetujuan **Application / System Owner** atas justifikasi bisnis di dalam sistem ITSM.

> CR tanpa persetujuan Application / System Owner **tidak diteruskan** ke tahap review teknis.

### Tahap 2 — Review Teknis

**Pelaksana:** Network Security Engineer
**SLA:** 1 hari kerja

1. Memeriksa kelengkapan dan keakuratan data (alamat IP, port, protokol, arah koneksi).
2. Memverifikasi zona sumber dan tujuan, serta memastikan jalur (*path*) lalu lintas melewati firewall yang dimaksud.
3. Memeriksa apakah akses sudah tercakup oleh rule yang ada, untuk menghindari rule duplikat (*redundant*) atau tertutup rule lain (*shadowed*).
4. Mengusulkan desain rule yang **paling spesifik** (*least privilege*), mis. mempersempit rentang IP atau port.
5. Menetapkan kategori CR dan klasifikasi risiko awal.
6. Mengembalikan CR kepada requester bila data tidak lengkap atau tidak valid, disertai catatan perbaikan.

### Tahap 3 — Penilaian Risiko Keamanan

**Pelaksana:** Information Security
**SLA:** 2 hari kerja (risiko tinggi); 1 hari kerja (risiko sedang)
**Berlaku untuk:** CR berisiko sedang dan tinggi

1. Menilai dampak akses terhadap kerahasiaan, integritas, dan ketersediaan sistem.
2. Memastikan layanan yang dibuka menggunakan protokol aman (mis. HTTPS, SSH, SFTP, TLS 1.2 ke atas) dan bukan protokol teks polos.
3. Untuk akses pihak ketiga: memastikan adanya perjanjian kerahasiaan (NDA), hasil penilaian risiko vendor, dan batas waktu akses.
4. Memberikan rekomendasi: **disetujui**, **disetujui dengan syarat** (mis. wajib melalui jump server, wajib MFA, masa berlaku dipersingkat), atau **ditolak**.

### Tahap 4 — Persetujuan

**Pelaksana:** Pejabat sesuai matriks persetujuan (**Bab 8**)
**SLA:** 2 hari kerja

1. CR diajukan kepada pejabat penyetuju sesuai tingkat risiko.
2. CR berisiko tinggi dibahas dalam rapat **CAB** mingguan, atau CAB darurat bila mendesak.
3. Keputusan dicatat di sistem ITSM: **disetujui**, **disetujui dengan perubahan**, atau **ditolak** beserta alasannya.

### Tahap 5 — Penjadwalan

**Pelaksana:** Change Manager
**SLA:** 1 hari kerja setelah persetujuan

1. Menetapkan jadwal implementasi dalam **maintenance window** (mis. hari kerja pukul 22.00–04.00 atau akhir pekan).
2. Menghindari periode *change freeze*, seperti akhir bulan, akhir tahun, dan periode puncak transaksi (hari raya, tanggal gajian).
3. Menginformasikan jadwal kepada requester, NOC, dan pemilik layanan terdampak.

### Tahap 6 — Implementasi

**Pelaksana:** Network Security Engineer
**SLA:** Sesuai jadwal yang ditetapkan

1. Melakukan implementasi sesuai standar teknis **SOP-SEC-FW-002 Konfigurasi Firewall Policy**.
2. Mencadangkan (*backup*) konfigurasi sebelum perubahan.
3. Mencantumkan **nomor CR** pada kolom komentar/deskripsi setiap rule yang dibuat atau diubah.
4. Menyiapkan dan, bila diperlukan, menjalankan **rencana rollback**.

> Pelaksana implementasi **dilarang** sama dengan requester maupun pejabat penyetuju (*prinsip pemisahan fungsi / four eyes principle*).

### Tahap 7 — Verifikasi dan Penutupan

**Pelaksana:** Requester dan Network Security Engineer
**SLA:** 1 hari kerja setelah implementasi

1. Requester melakukan uji konektivitas dan fungsi aplikasi, lalu mengonfirmasi hasilnya di sistem ITSM.
2. Network Security Engineer memeriksa log firewall untuk memastikan lalu lintas sesuai rule yang dibuat, tanpa akses berlebih.
3. Melampirkan bukti implementasi (tangkapan layar rule, hasil uji, atau potongan log) ke CR.
4. CR ditutup dengan status **Berhasil**, **Berhasil Sebagian**, atau **Gagal – Rollback**.

### Tahap 8 — Pemantauan Masa Berlaku dan Resertifikasi

**Pelaksana:** Network Security Engineer dan Application / System Owner
**Frekuensi:** Harian (rule sementara); 6 bulanan (resertifikasi)

1. Sistem memberikan notifikasi kepada requester **7 hari** sebelum rule sementara kedaluwarsa.
2. Rule sementara yang tidak diperpanjang melalui CR baru **dinonaktifkan** pada tanggal kedaluwarsa dan dihapus 30 hari kemudian.
3. Setiap **6 bulan**, Application / System Owner meninjau ulang seluruh rule miliknya dan menyatakan masih dibutuhkan atau dapat dihapus.
4. Rule tanpa pemilik atau tanpa lalu lintas (*zero hit*) selama 90 hari diusulkan untuk dihapus melalui CR.
5. Tata cara lengkap review dan resertifikasi diatur dalam **SOP-SEC-FW-003 Review dan Resertifikasi Firewall Rule**.

---

## 8. Matriks Persetujuan (Ilustratif)

| Tingkat Risiko | Application / System Owner | Information Security | Penyetuju Akhir |
|---|---|---|---|
| **Rendah** | Wajib | — | Kepala Bagian Network Security |
| **Sedang** | Wajib | Wajib | Kepala Divisi Operasional TI |
| **Tinggi** | Wajib | Wajib | CAB, dengan persetujuan Kepala Unit Keamanan Informasi (CISO) |
| **Emergency** | Wajib (dapat lisan, dicatat) | Wajib (dapat lisan, dicatat) | Kepala Divisi Operasional TI atau pejabat on-call yang ditunjuk |

---

## 9. Data Wajib pada Formulir CR

| Data | Keterangan |
|---|---|
| **Nama aplikasi / layanan** | Aplikasi atau sistem yang membutuhkan akses |
| **Justifikasi bisnis** | Alasan akses dibutuhkan dan dampak bila tidak diberikan |
| **Alamat sumber** | IP/subnet dan hostname, beserta zonanya |
| **Alamat tujuan** | IP/subnet, hostname, atau FQDN, beserta zonanya |
| **Layanan** | Protokol (TCP/UDP/ICMP) dan nomor port spesifik; rentang port harus disertai alasan |
| **Arah koneksi** | Inbound / outbound / antar zona internal |
| **Aksi** | Allow / deny |
| **Masa berlaku** | Permanen atau sementara, dengan tanggal kedaluwarsa |
| **Lingkungan** | Production / DR / UAT / Development |
| **Pemilik akses** | Nama Application / System Owner yang bertanggung jawab |
| **Rencana uji** | Cara requester memverifikasi akses setelah implementasi |

---

## 10. Prosedur Emergency Change

1. Emergency change hanya boleh digunakan untuk:
   - memulihkan layanan kritikal yang sedang terganggu; atau
   - menahan atau menanggulangi insiden keamanan yang sedang berlangsung.
2. Requester menghubungi Network Security Engineer on-call dan pejabat penyetuju emergency melalui telepon atau kanal resmi, lalu mencatat CR emergency di sistem ITSM **sebelum atau segera setelah** implementasi.
3. Rule emergency yang membuka akses bersifat **sementara**, maksimal **7 hari kalender**.
4. Dokumentasi lengkap dan persetujuan formal pasca-implementasi (*retroactive approval*) wajib diselesaikan paling lambat **1×24 jam**.
5. Emergency change ditinjau pada rapat CAB berikutnya untuk menilai kewajaran penggunaannya.
6. Penanganan gangguan atau insiden yang memicu emergency change mengikuti **SOP-SEC-FW-006 Penanganan Insiden dan Gangguan Firewall**.

> Penyalahgunaan jalur emergency untuk menghindari proses persetujuan normal merupakan **pelanggaran SOP**.

---

## 11. Ringkasan SLA Proses (Change Normal)

| Tahap | SLA (Hari Kerja) |
|---|---|
| Review teknis | 1 |
| Penilaian risiko keamanan | 1–2 |
| Persetujuan | 2 |
| Penjadwalan | 1 |
| Verifikasi dan penutupan | 1 |
| **Total (risiko rendah)** | **5 hari kerja** |
| **Total (risiko sedang/tinggi)** | **6–7 hari kerja**, ditambah menunggu jadwal CAB dan maintenance window |

> SLA dihitung sejak CR dinyatakan **lengkap** dan disetujui Application / System Owner. Waktu tunggu perbaikan data oleh requester tidak diperhitungkan.

---

## 12. Alasan Umum Penolakan CR

1. Justifikasi bisnis tidak jelas atau tidak disetujui Application / System Owner.
2. Permintaan menggunakan nilai **any** atau rentang IP/port yang terlalu luas tanpa alasan kuat.
3. Menggunakan protokol tidak aman (Telnet, FTP, HTTP) untuk data sensitif atau akses administratif.
4. Akses administratif langsung dari zona user atau Internet ke server, tanpa melalui jump server/PAM.
5. Akses pihak ketiga tanpa perjanjian kerja sama, NDA, atau batas waktu.
6. Akses sudah tercakup oleh rule yang ada.
7. Data teknis tidak valid, misalnya IP tidak terdaftar di inventaris aset.
8. Bertentangan dengan arsitektur segmentasi zona yang ditetapkan.

---

## 13. Pengendalian Internal

1. **Pemisahan fungsi:** requester, penyetuju, dan pelaksana implementasi wajib merupakan orang yang berbeda.
2. **Keterlacakan:** setiap rule wajib memuat nomor CR sehingga dapat ditelusuri ke permintaan dan persetujuannya.
3. **Rekonsiliasi:** setiap bulan, Unit Keamanan Informasi membandingkan log perubahan konfigurasi firewall dengan daftar CR yang disetujui untuk mendeteksi perubahan tidak sah.
4. **Retensi:** dokumen CR dan bukti implementasi disimpan minimal **5 tahun**, atau sesuai ketentuan retensi internal.
5. **Audit:** Audit Internal TI melakukan uji petik berkala atas kepatuhan terhadap SOP ini.
6. **Kerahasiaan:** informasi topologi jaringan, alamat IP, dan konfigurasi firewall bersifat **rahasia** dan dilarang dibagikan kepada pihak yang tidak berwenang.

---

## 14. Pertanyaan yang Sering Diajukan

**Berapa lama proses CR firewall?**
Sekitar 5 hari kerja untuk risiko rendah dan 6–7 hari kerja untuk risiko sedang/tinggi sejak CR lengkap, ditambah waktu tunggu jadwal CAB dan maintenance window.

**Apakah saya bisa meminta akses "any" supaya tidak perlu mengajukan CR berulang kali?**
Tidak. Akses harus spesifik sesuai kebutuhan (*least privilege*). Nilai any hanya dapat dipertimbangkan dengan justifikasi kuat dan dinilai sebagai risiko tinggi.

**Siapa yang harus menyetujui CR saya?**
Application / System Owner wajib menyetujui semua CR. Persetujuan berikutnya bergantung pada tingkat risiko (lihat Bab 8).

**Akses saya untuk vendor sudah kedaluwarsa, bagaimana memperpanjangnya?**
Ajukan CR perpanjangan sebelum tanggal kedaluwarsa, dengan melampirkan bukti bahwa kontrak/perjanjian vendor masih berlaku.

**Kapan jalur emergency boleh digunakan?**
Hanya untuk memulihkan layanan kritikal yang terganggu atau menanggulangi insiden keamanan yang sedang berlangsung, bukan karena tenggat proyek.

**Setelah CR selesai, akses masih tidak bisa. Apa yang harus dilakukan?**
Jangan tutup CR. Laporkan hasil uji di CR yang sama agar Network Security Engineer memeriksa log firewall dan jalur jaringan.

---

## 15. Referensi

- POJK Nomor 11/POJK.03/2022 tentang Penyelenggaraan Teknologi Informasi oleh Bank Umum
- ISO/IEC 27001:2022 — kontrol A.8.20 (*Networks security*) dan A.8.32 (*Change management*)
- PCI DSS v4.0 — Requirement 1 (*Install and Maintain Network Security Controls*)
- SOP-SEC-FW-002 Konfigurasi Firewall Policy
- SOP-SEC-FW-003 Review dan Resertifikasi Firewall Rule
- SOP-SEC-FW-006 Penanganan Insiden dan Gangguan Firewall
- SOP-SEC-FW-007 Patch dan Upgrade Firmware Firewall
- SOP-SEC-FW-009 Siklus Hidup Perangkat Firewall

---

## 16. Riwayat Revisi

| Versi | Tanggal | Perubahan | Penyusun |
|---|---|---|---|
| 1.0 | 2026-09-23 | Penerbitan dokumen pertama | Divisi Teknologi Informasi |
| 1.1 | 2026-09-23 | Menambahkan rujukan ke SOP-SEC-FW-003, 006, 007, dan 009; memperjelas ruang lingkup | Divisi Teknologi Informasi |
