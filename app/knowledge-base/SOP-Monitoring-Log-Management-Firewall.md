# SOP Monitoring dan Log Management Firewall

**Nomor Dokumen:** SOP-SEC-FW-005
**Versi:** 1.0
**Tanggal Berlaku:** 2026-09-23
**Unit Pemilik:** Divisi Teknologi Informasi — Network & Security Operations
**Status:** Dokumen contoh untuk basis pengetahuan (knowledge base) NALA

> **Catatan:** Dokumen ini merupakan **template acuan umum**, bukan salinan kebijakan resmi institusi tertentu. Ambang batas alert, waktu respons, dan masa retensi log bersifat ilustratif dan harus disesuaikan dengan ketentuan internal serta regulasi yang berlaku sebelum digunakan secara operasional.

---

## 1. Tujuan

1. Memastikan kondisi kesehatan (*health*) dan kinerja firewall terpantau terus-menerus sehingga gangguan dapat dideteksi sebelum berdampak ke layanan.
2. Memastikan log keamanan firewall terkumpul lengkap di SIEM untuk mendeteksi serangan, akses tidak sah, dan perubahan konfigurasi tidak sah.
3. Menetapkan ambang batas alert, waktu respons, dan jalur eskalasi yang baku.
4. Menjaga log firewall tetap utuh dan tersedia selama masa retensi untuk kebutuhan investigasi, audit, dan pemeriksaan regulator.

---

## 2. Ruang Lingkup

Dokumen ini berlaku untuk seluruh firewall dan sistem manajemen firewall di lingkungan Production dan DR, mencakup:

- **Monitoring kesehatan dan kinerja**, dilaksanakan oleh NOC
- **Monitoring keamanan dan analisis log**, dilaksanakan oleh SOC
- **Pengelolaan log**: pengiriman, penyimpanan, retensi, dan integritas log

Lingkungan UAT dan Development cukup dipantau ketersediaannya.

**Tidak termasuk:** penanganan insiden setelah dieskalasi, yang diatur dalam **SOP-SEC-FW-006 Penanganan Insiden dan Gangguan Firewall**.

---

## 3. Definisi

| Istilah | Penjelasan |
|---|---|
| **NOC** | *Network Operations Center* — tim yang memantau ketersediaan dan kinerja infrastruktur 24×7 |
| **SOC** | *Security Operations Center* — tim di bawah Information Security yang memantau dan menganalisis kejadian keamanan 24×7 |
| **SIEM** | *Security Information and Event Management* — sistem pengumpul, penyimpan, dan korelasi log keamanan |
| **Traffic Log** | Catatan koneksi yang diizinkan atau ditolak oleh rule firewall |
| **Threat Log** | Catatan deteksi IPS, anti-malware, URL filtering, dan fitur keamanan lainnya |
| **Audit Log** | Catatan aktivitas administrator: login, perubahan konfigurasi, commit |
| **System Log** | Catatan kejadian sistem: HA failover, interface down, error hardware |
| **Use Case** | Aturan korelasi di SIEM untuk mendeteksi pola kejadian tertentu |
| **False Positive** | Alert yang ternyata bukan kejadian berbahaya |

---

## 4. Pihak yang Terlibat

| Peran | Tanggung Jawab Utama |
|---|---|
| **NOC** | Memantau health dan kinerja firewall, menangani alert operasional, dan melakukan eskalasi |
| **SOC (Information Security)** | Memantau alert keamanan di SIEM, melakukan triase dan analisis, serta mengeskalasi insiden |
| **Network Security Engineer** | Mengonfigurasi pengiriman log dan monitoring pada firewall, serta menangani alert yang dieskalasi |
| **Tim SIEM / Security Engineering** | Mengelola platform SIEM, parser log, use case korelasi, dan retensi log |
| **Kepala Bagian Network Security** | Menerima eskalasi gangguan dan memantau laporan kinerja firewall |
| **CISO** | Menerima eskalasi insiden keamanan dan laporan monitoring keamanan |

---

## 5. Ketentuan Pengiriman Log

1. Seluruh firewall wajib mengirim **traffic log, threat log, audit log, dan system log** ke SIEM.
2. Traffic log wajib diaktifkan minimal untuk rule yang ditetapkan dalam SOP-SEC-FW-002 Bab 5 butir 6, yaitu seluruh rule deny, cleanup rule, rule dari INET/PARTNER, dan rule menuju RESTRICTED.
3. Pengiriman log menggunakan protokol yang andal dan aman (mis. syslog over TLS). Bila perangkat tidak mendukung, gunakan jaringan MGMT yang terisolasi.
4. Seluruh firewall wajib tersinkron ke **server NTP internal** agar timestamp log konsisten untuk korelasi.
5. Firewall dikonfigurasi dengan **buffer log lokal** agar log tidak hilang saat koneksi ke SIEM terputus sementara.
6. Setiap firewall baru wajib terdaftar sebagai sumber log di SIEM sebelum go-live (lihat SOP-SEC-FW-009).

---

## 6. Parameter Monitoring dan Ambang Batas Alert (Ilustratif)

### 6.1 Monitoring Kesehatan dan Kinerja (NOC)

| Parameter | Warning | Critical |
|---|---|---|
| **Utilisasi CPU / dataplane** | > 75% selama 15 menit | > 90% selama 5 menit |
| **Utilisasi memori** | > 80% selama 15 menit | > 90% selama 5 menit |
| **Session table** | > 75% kapasitas | > 90% kapasitas |
| **Throughput interface** | > 70% kapasitas link | > 90% kapasitas link |
| **Status interface / link** | — | Interface produksi down |
| **Status HA** | Sinkronisasi konfigurasi gagal | Failover terjadi, anggota cluster down, atau *split-brain* |
| **Ketersediaan perangkat** | — | Tidak merespons monitoring selama 3 menit |
| **Sertifikat** | Kedaluwarsa ≤ 30 hari | Kedaluwarsa ≤ 7 hari |
| **Lisensi / subscription (IPS, anti-malware, URL)** | Kedaluwarsa ≤ 60 hari | Kedaluwarsa ≤ 14 hari |
| **Update signature** | Gagal update > 24 jam | Gagal update > 72 jam |

### 6.2 Monitoring Keamanan (SOC)

| Use Case | Kondisi Pemicu | Severity Awal |
|---|---|---|
| **Perubahan konfigurasi tanpa CR** | Commit konfigurasi yang tidak dapat dikorelasikan dengan CR yang disetujui | Tinggi |
| **Brute force login admin** | ≥ 5 login gagal dalam 10 menit pada akun yang sama | Tinggi |
| **Login admin dari luar zona MGMT** | Login berhasil maupun gagal dari alamat di luar jump server/PAM | Kritis |
| **Penggunaan akun break-glass** | Login menggunakan akun lokal darurat | Tinggi |
| **Lalu lintas terlarang dari RESTRICTED** | Koneksi dari RESTRICTED ke INET atau ke zona yang dilarang, tertangkap cleanup rule | Tinggi |
| **Deteksi IPS kritikal** | Signature berseverity kritikal/tinggi yang lolos (*allowed*) | Tinggi |
| **Komunikasi ke IP/domain berbahaya** | Lalu lintas outbound ke indikator *threat intelligence* | Tinggi |
| **Pemindaian port** | Satu sumber mencoba ≥ 100 port/host tujuan berbeda dalam 5 menit | Sedang |
| **Lonjakan deny** | Jumlah deny dari satu sumber internal melonjak signifikan dibanding baseline | Sedang |
| **Sumber log berhenti** | Firewall tidak mengirim log ke SIEM selama > 15 menit | Tinggi |
| **Logging dinonaktifkan** | Perubahan konfigurasi yang mematikan logging rule atau log forwarding | Kritis |

---

## 7. Waktu Respons Alert (Ilustratif)

| Severity | Waktu Respons Awal (Triase) | Eskalasi |
|---|---|---|
| **Kritis** | 15 menit | Langsung ke Network Security Engineer on-call dan Kepala Bagian Network Security; untuk alert keamanan, juga ke CISO |
| **Tinggi** | 30 menit | Network Security Engineer on-call |
| **Sedang** | 4 jam | Tiket ke antrean Network Security |
| **Rendah** | 1 hari kerja | Tiket ke antrean Network Security |

---

## 8. Alur Penanganan Alert

### Tahap 1 — Deteksi

**Pelaksana:** NOC (alert operasional) dan SOC (alert keamanan)

1. Alert muncul di dashboard monitoring atau SIEM dan otomatis membuat tiket.
2. Petugas yang bertugas mengambil alih (*acknowledge*) tiket sesuai waktu respons pada **Bab 7**.

### Tahap 2 — Triase

**Pelaksana:** NOC / SOC

1. Memverifikasi kebenaran alert dengan memeriksa log dan dashboard terkait.
2. Mengecek apakah alert berkaitan dengan aktivitas terencana, mis. CR yang sedang diimplementasikan dalam maintenance window.
3. Menetapkan hasil: **False Positive**, **Kejadian Terencana**, atau **Perlu Tindak Lanjut**.
4. Mencatat hasil triase dan bukti pada tiket.

### Tahap 3 — Penanganan atau Eskalasi

1. Alert operasional ringan, seperti ambang warning, ditangani NOC sesuai runbook dan dipantau hingga normal.
2. Alert yang memenuhi kriteria gangguan atau insiden keamanan dieskalasi dan ditangani sesuai **SOP-SEC-FW-006**.
3. Perubahan konfigurasi tanpa CR **selalu** dieskalasi ke SOC dan Kepala Bagian Network Security, meskipun pelakunya pegawai internal.

### Tahap 4 — Penutupan dan Penyempurnaan

1. Tiket ditutup dengan catatan penyebab dan tindakan.
2. SOC mereview alert false positive berulang dan mengusulkan penyesuaian use case kepada Tim SIEM.
3. Penyesuaian use case atau ambang batas didokumentasikan dan disetujui Information Security.

---

## 9. Retensi dan Integritas Log (Ilustratif)

| Jenis Log | Online di SIEM (dapat dicari) | Arsip |
|---|---|---|
| Audit log administrator | 12 bulan | 5 tahun |
| Threat log | 12 bulan | 5 tahun |
| Traffic log | 3 bulan | 12 bulan |
| System log | 3 bulan | 12 bulan |

1. Log di SIEM dan arsip dilindungi dari perubahan dan penghapusan oleh pengguna biasa (*write-once* atau kontrol akses ketat).
2. Akses ke log dibatasi sesuai peran dan setiap pencarian/ekspor log tercatat.
3. Bila terjadi investigasi insiden atau permintaan hukum, log terkait ditandai **legal hold** dan dikecualikan dari penghapusan otomatis.

---

## 10. Pelaporan

| Laporan | Frekuensi | Isi Utama | Penerima |
|---|---|---|---|
| **Laporan shift** | Setiap pergantian shift | Alert terbuka, kejadian penting, tindakan yang sedang berjalan | NOC / SOC shift berikutnya |
| **Laporan harian** | Harian | Ringkasan alert kritis/tinggi dan status firewall | Kepala Bagian Network Security |
| **Laporan bulanan kinerja** | Bulanan | Tren CPU, memori, session, throughput, kapasitas, dan prediksi kebutuhan upgrade | Kepala Divisi Operasional TI |
| **Laporan bulanan keamanan** | Bulanan | Statistik serangan terblokir, top sumber/tujuan deny, perubahan tanpa CR, dan status use case | CISO |

---

## 11. Pengendalian Internal

1. **Kelengkapan sumber log:** SOC memeriksa setiap minggu bahwa seluruh firewall dalam inventaris aktif mengirim log ke SIEM.
2. **Pemisahan fungsi:** administrator firewall tidak memiliki hak menghapus atau mengubah log di SIEM.
3. **Sinkronisasi waktu:** status NTP seluruh firewall diperiksa sebagai bagian dari monitoring kesehatan.
4. **Kerahasiaan:** log firewall bersifat **rahasia** karena memuat alamat IP internal, pola akses, dan dapat memuat informasi pengguna.
5. **Audit:** Audit Internal TI melakukan uji petik atas kelengkapan log, penanganan alert, dan kepatuhan retensi.

---

## 12. Pertanyaan yang Sering Diajukan

**Apa bedanya monitoring oleh NOC dan SOC?**
NOC memantau apakah firewall sehat dan berkinerja baik (CPU, memori, link, HA). SOC memantau apakah ada ancaman atau aktivitas mencurigakan berdasarkan log keamanan.

**Log apa saja dari firewall yang wajib dikirim ke SIEM?**
Traffic log, threat log, audit log administrator, dan system log.

**Berapa lama log firewall disimpan?**
Audit log dan threat log dapat dicari di SIEM selama 12 bulan dan diarsipkan 5 tahun. Traffic log dan system log 3 bulan online dan 12 bulan arsip (ilustratif).

**Mengapa firewall harus tersinkron ke NTP?**
Agar waktu di log sama dengan sistem lain. Tanpa waktu yang konsisten, korelasi kejadian saat investigasi insiden menjadi sulit dan tidak akurat.

**Alert muncul saat saya sedang mengerjakan CR. Apa yang harus dilakukan?**
Pastikan CR tercatat dalam status implementasi di ITSM agar NOC/SOC dapat mengategorikan alert sebagai kejadian terencana. Bila alert tidak sesuai dampak yang diperkirakan, evaluasi kebutuhan rollback.

---

## 13. Referensi

- POJK Nomor 11/POJK.03/2022 tentang Penyelenggaraan Teknologi Informasi oleh Bank Umum
- ISO/IEC 27001:2022 — kontrol A.8.15 (*Logging*), A.8.16 (*Monitoring activities*), dan A.8.17 (*Clock synchronization*)
- PCI DSS v4.0 — Requirement 10 (*Log and Monitor All Access to System Components and Cardholder Data*)
- NIST SP 800-92 — *Guide to Computer Security Log Management*
- SOP-SEC-FW-002 Konfigurasi Firewall Policy
- SOP-SEC-FW-006 Penanganan Insiden dan Gangguan Firewall

---

## 14. Riwayat Revisi

| Versi | Tanggal | Perubahan | Penyusun |
|---|---|---|---|
| 1.0 | 2026-09-23 | Penerbitan dokumen pertama | Divisi Teknologi Informasi |
