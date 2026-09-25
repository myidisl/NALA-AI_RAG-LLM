# SOP Penanganan Insiden dan Gangguan Firewall

**Nomor Dokumen:** SOP-SEC-FW-006
**Versi:** 1.0
**Tanggal Berlaku:** 2026-09-23
**Unit Pemilik:** Divisi Teknologi Informasi — Network & Security Operations
**Status:** Dokumen contoh untuk basis pengetahuan (knowledge base) NALA

> **Catatan:** Dokumen ini merupakan **template acuan umum**, bukan salinan kebijakan resmi institusi tertentu. Klasifikasi prioritas, target waktu, dan jalur eskalasi bersifat ilustratif dan harus disesuaikan dengan ketentuan internal serta regulasi yang berlaku sebelum digunakan secara operasional.

---

## 1. Tujuan

1. Menyediakan langkah baku dalam menangani gangguan operasional dan insiden keamanan yang melibatkan firewall.
2. Memulihkan layanan perbankan yang terdampak secepat mungkin dengan risiko seminimal mungkin.
3. Menahan (*contain*) serangan atau akses tidak sah agar tidak menyebar antar zona jaringan.
4. Memastikan bukti terlindungi, komunikasi dan eskalasi berjalan tepat waktu, serta pelajaran dari setiap kejadian ditindaklanjuti.

---

## 2. Ruang Lingkup

Dokumen ini berlaku untuk kejadian pada firewall di seluruh lingkungan, terutama Production dan DR, yang terbagi menjadi dua jenis:

| Jenis | Contoh |
|---|---|
| **Gangguan Operasional** | Firewall down, HA failover tidak terduga, *split-brain*, kinerja menurun, lalu lintas sah terblokir setelah perubahan, VPN pihak ketiga terputus, sertifikat kedaluwarsa |
| **Insiden Keamanan** | Serangan dari Internet yang lolos atau membebani firewall, perubahan konfigurasi tidak sah, akun administrator disalahgunakan, eksploitasi kerentanan firewall, komunikasi internal ke infrastruktur penyerang |

**Tidak termasuk:** penanganan insiden keamanan di luar firewall, seperti malware di endpoint, yang diatur dalam SOP Penanganan Insiden Keamanan Informasi tingkat bank. Firewall tetap dapat digunakan sebagai alat penahanan untuk insiden tersebut sesuai SOP ini.

---

## 3. Definisi

| Istilah | Penjelasan |
|---|---|
| **Gangguan (Incident Operasional)** | Kejadian yang menghentikan atau menurunkan kualitas layanan firewall |
| **Insiden Keamanan** | Kejadian yang mengancam kerahasiaan, integritas, atau ketersediaan sistem dan data melalui atau terhadap firewall |
| **Penahanan (Containment)** | Tindakan membatasi dampak dan penyebaran, mis. memblokir IP, mengisolasi segmen |
| **Pemulihan (Recovery)** | Tindakan mengembalikan layanan ke kondisi normal |
| **RCA** | *Root Cause Analysis* — analisis akar penyebab kejadian |
| **Incident Commander** | Pejabat yang memimpin koordinasi penanganan insiden prioritas P1 |
| **Bukti Digital** | Log, konfigurasi, dan data sistem yang diamankan untuk investigasi |

---

## 4. Pihak yang Terlibat

| Peran | Tanggung Jawab Utama |
|---|---|
| **NOC** | Mendeteksi dan mencatat gangguan, koordinasi awal, serta pemantauan pemulihan layanan |
| **SOC (Information Security)** | Mendeteksi dan menganalisis insiden keamanan, serta memimpin investigasi dan pengamanan bukti |
| **Network Security Engineer (on-call)** | Melakukan diagnosis teknis, penahanan, dan pemulihan pada firewall |
| **Kepala Bagian Network Security** | Menjadi Incident Commander untuk gangguan P1 dan menyetujui tindakan darurat |
| **CISO** | Menjadi Incident Commander untuk insiden keamanan P1 dan memutuskan pelaporan eksternal |
| **Kepala Divisi Operasional TI** | Menerima eskalasi P1 dan berkoordinasi dengan unit bisnis |
| **Vendor Firewall** | Memberikan dukungan teknis sesuai kontrak (tiket prioritas, RMA) |
| **Unit Komunikasi / Customer Care** | Menyiapkan komunikasi kepada nasabah bila layanan publik terdampak |

---

## 5. Klasifikasi Prioritas (Ilustratif)

| Prioritas | Kriteria | Respons Awal | Target Pemulihan / Penahanan |
|---|---|---|---|
| **P1 — Kritis** | Layanan kritikal (core banking, mobile/internet banking, ATM, payment) terhenti; atau insiden keamanan aktif dengan indikasi kompromi atau kebocoran data | 15 menit | 4 jam |
| **P2 — Tinggi** | Layanan kritikal terdegradasi, redundansi HA hilang, satu kantor cabang/wilayah terputus; atau upaya serangan signifikan tanpa indikasi kompromi | 30 menit | 8 jam |
| **P3 — Sedang** | Layanan non-kritikal terganggu, akses sebagian pengguna terblokir; atau aktivitas mencurigakan yang perlu investigasi | 4 jam | 2 hari kerja |
| **P4 — Rendah** | Dampak minimal, ada solusi sementara | 1 hari kerja | 5 hari kerja |

> Prioritas dapat dinaikkan kapan saja bila dampak meluas. Setiap perubahan konfigurasi tidak sah **minimal P2** hingga terbukti bukan tindakan berbahaya.

---

## 6. Alur Penanganan

### Tahap 1 — Deteksi dan Pelaporan

**Pelaksana:** NOC, SOC, atau pegawai yang menemukan kejadian

1. Kejadian dapat berasal dari alert monitoring (SOP-SEC-FW-005), laporan pengguna ke Service Desk, notifikasi vendor, atau informasi *threat intelligence*.
2. Mencatat tiket insiden di ITSM berisi waktu kejadian, gejala, layanan terdampak, dan perangkat terkait.
3. Menghubungi Network Security Engineer on-call untuk kejadian P1/P2.

### Tahap 2 — Triase dan Klasifikasi

**Pelaksana:** NOC / SOC bersama Network Security Engineer

1. Menentukan jenis kejadian: **gangguan operasional** atau **insiden keamanan**.
2. Menetapkan prioritas sesuai **Bab 5**.
3. Memeriksa CR yang baru diimplementasikan, karena perubahan terakhir merupakan penyebab gangguan yang paling umum.
4. Untuk P1: menunjuk **Incident Commander** dan membuka jalur koordinasi (*war room*/bridge call).

### Tahap 3 — Pengamanan Bukti

**Pelaksana:** SOC dan Network Security Engineer
**Berlaku untuk:** insiden keamanan

1. **Sebelum** melakukan reboot, restore, atau perubahan besar, amankan terlebih dahulu:
   - konfigurasi aktif (running config) saat itu;
   - audit log, system log, dan traffic/threat log periode terkait;
   - daftar sesi aktif dan akun administrator yang sedang login;
   - file diagnostik/tech-support dari perangkat.
2. Hitung checksum setiap bukti dan simpan di lokasi terpisah dengan akses terbatas.
3. Catat rantai penguasaan bukti (*chain of custody*): siapa mengambil, kapan, dan di mana disimpan.

> Bila layanan kritikal terhenti dan pengamanan bukti akan menunda pemulihan secara signifikan, Incident Commander memutuskan prioritas dan mencatat keputusannya.

### Tahap 4 — Penahanan

**Pelaksana:** Network Security Engineer atas instruksi SOC/Incident Commander

Contoh tindakan penahanan:
- memblokir IP/domain penyerang melalui block list (lihat runbook pada **Bab 7**);
- mengisolasi host atau segmen yang terkompromi dengan rule deny antar zona;
- menonaktifkan akun administrator yang dicurigai disalahgunakan dan memutus sesinya;
- menonaktifkan sementara akses VPN pihak ketiga yang menjadi sumber serangan;
- mengaktifkan proteksi DoS/rate limiting pada rule dari zona INET.

Setiap perubahan konfigurasi untuk penahanan dicatat sebagai **emergency change** sesuai SOP-SEC-FW-001 Bab 10.

### Tahap 5 — Pemulihan

**Pelaksana:** Network Security Engineer

1. Menjalankan langkah pemulihan sesuai runbook pada **Bab 7**.
2. Bila penyebabnya perubahan konfigurasi, lakukan rollback/restore sesuai **SOP-SEC-FW-004**.
3. Bila penyebabnya kerusakan perangkat, lakukan failover ke anggota HA atau site DR, lalu buka tiket RMA ke vendor.
4. Bila penyebabnya kerentanan firewall, terapkan patch atau mitigasi sementara sesuai **SOP-SEC-FW-007**.
5. Untuk insiden keamanan dengan indikasi perangkat terkompromi: ganti seluruh kredensial administrator, kunci VPN, dan sertifikat terkait, lalu pertimbangkan reinstalasi dari image bersih.
6. Memverifikasi layanan pulih bersama NOC dan pemilik aplikasi, lalu memantau kondisi minimal 24 jam.

### Tahap 6 — Komunikasi dan Eskalasi

**Pelaksana:** Incident Commander

| Prioritas | Pihak yang Diinformasikan | Frekuensi Update |
|---|---|---|
| **P1** | Kepala Divisi Operasional TI, CISO, Direktur yang membawahkan TI, unit bisnis terdampak | Setiap 30 menit hingga pulih |
| **P2** | Kepala Bagian Network Security, Kepala Divisi Operasional TI, unit bisnis terdampak | Setiap 2 jam |
| **P3/P4** | Pemohon/pelapor melalui tiket | Saat ada perkembangan |

Untuk insiden yang memenuhi kriteria insiden signifikan, CISO berkoordinasi dengan unit Kepatuhan untuk **pelaporan kepada OJK** sesuai ketentuan pelaporan insiden yang berlaku.

### Tahap 7 — Penutupan dan Post-Incident Review

**Pelaksana:** Network Security Engineer, SOC, dan Kepala Bagian Network Security
**SLA:** Laporan RCA paling lambat 5 hari kerja setelah pemulihan (P1/P2)

1. Menyusun laporan RCA: kronologi, akar penyebab, dampak, tindakan yang dilakukan, dan rekomendasi pencegahan.
2. Memastikan seluruh emergency change telah memperoleh persetujuan formal dan rule penahanan sementara memiliki tanggal kedaluwarsa.
3. Menindaklanjuti rekomendasi melalui CR, pembaruan SOP, atau pembaruan use case monitoring.
4. Menutup tiket setelah seluruh tindak lanjut dicatat.

---

## 7. Runbook Singkat Kejadian Umum

| Kejadian | Langkah Utama |
|---|---|
| **Lalu lintas sah terblokir setelah CR** | Cek log deny untuk menemukan rule yang cocok → bandingkan dengan CR terakhir → perbaiki rule atau rollback sesuai SOP-SEC-FW-004 |
| **Firewall tunggal down (anggota HA)** | Pastikan anggota lain aktif dan layanan normal → amankan log/diagnostik → cek power, hardware, dan console → buka tiket vendor/RMA → status minimal P2 karena redundansi hilang |
| **HA split-brain** | Identifikasi anggota dengan konfigurasi dan sesi yang benar → putus/nonaktifkan anggota lainnya secara terkontrol → perbaiki link HA → sinkronkan ulang |
| **CPU/session tinggi mendadak** | Identifikasi sumber/tujuan dengan sesi terbanyak → bedakan lonjakan sah dan serangan → terapkan rate limiting atau blokir sumber berbahaya → eskalasi ke SOC bila indikasi serangan |
| **Serangan DoS dari Internet** | Koordinasi dengan penyedia layanan anti-DDoS/ISP → blokir sumber pada perimeter → aktifkan proteksi DoS → pantau layanan publik bersama NOC |
| **Perubahan konfigurasi tanpa CR** | Amankan audit log dan konfigurasi → identifikasi akun dan sumber login → konfirmasi ke pemilik akun → bila tidak sah: nonaktifkan akun, kembalikan konfigurasi, tangani sebagai insiden keamanan |
| **Akun administrator dicurigai disalahgunakan** | Nonaktifkan akun di TACACS+/RADIUS dan PAM → putus sesi aktif → reset kredensial → tinjau seluruh perubahan oleh akun tersebut |
| **Kerentanan firewall dieksploitasi aktif** | Terapkan mitigasi vendor (mis. nonaktifkan fitur rentan, batasi akses manajemen) → patch darurat sesuai SOP-SEC-FW-007 → periksa indikator kompromi |
| **VPN pihak ketiga terputus** | Cek status tunnel, log IKE/IPsec, masa berlaku sertifikat/PSK → koordinasi dengan pihak ketiga → jangan mengubah parameter kriptografi tanpa CR |
| **Sertifikat kedaluwarsa** | Terapkan sertifikat pengganti melalui emergency change → verifikasi layanan (VPN, SSL inspection, portal) → evaluasi mengapa alert kedaluwarsa tidak ditindaklanjuti |

---

## 8. Pengendalian Internal

1. **Keterlacakan:** seluruh tindakan selama penanganan dicatat dengan waktu, pelaku, dan alasan pada tiket insiden.
2. **Tidak ada perubahan tanpa jejak:** tindakan darurat tetap dicatat sebagai emergency change dan disetujui formal paling lambat 1×24 jam.
3. **Rule penahanan sementara:** setiap rule blokir darurat wajib memiliki tanggal kedaluwarsa dan ditinjau ulang setelah insiden ditutup.
4. **Kerahasiaan:** informasi insiden hanya dibagikan kepada pihak yang berkepentingan. Komunikasi eksternal hanya melalui unit yang berwenang.
5. **Latihan:** simulasi penanganan insiden firewall (*tabletop exercise*) dilaksanakan minimal **setahun sekali**.

---

## 9. Pertanyaan yang Sering Diajukan

**Aplikasi tiba-tiba tidak bisa terhubung setelah ada perubahan firewall semalam. Siapa yang dihubungi?**
Laporkan ke Service Desk untuk dibuatkan tiket insiden. Sertakan nama aplikasi, alamat sumber-tujuan, dan waktu mulai terjadi. Network Security Engineer akan memeriksa log deny dan CR terakhir.

**Apa bedanya gangguan dan insiden keamanan firewall?**
Gangguan berkaitan dengan ketersediaan atau kinerja, mis. perangkat down atau lalu lintas sah terblokir. Insiden keamanan berkaitan dengan ancaman, mis. serangan, akses tidak sah, atau perubahan konfigurasi tanpa izin.

**Kenapa tidak langsung reboot saja saat firewall bermasalah?**
Untuk insiden keamanan, reboot dapat menghapus bukti penting seperti sesi aktif dan log di memori. Bukti diamankan terlebih dahulu, kecuali Incident Commander memutuskan pemulihan layanan lebih mendesak.

**Bolehkah memblokir IP penyerang tanpa CR?**
Boleh melalui jalur **emergency change**, dengan persetujuan pejabat on-call, dan dicatat serta disetujui formal paling lambat 1×24 jam.

**Kapan laporan RCA harus selesai?**
Paling lambat 5 hari kerja setelah pemulihan untuk kejadian P1 dan P2.

---

## 10. Referensi

- POJK Nomor 11/POJK.03/2022 tentang Penyelenggaraan Teknologi Informasi oleh Bank Umum
- ISO/IEC 27001:2022 — kontrol A.5.24–A.5.28 (manajemen insiden keamanan informasi dan pengumpulan bukti)
- NIST SP 800-61 — *Computer Security Incident Handling Guide*
- SOP-SEC-FW-001 Change Request Firewall Policy
- SOP-SEC-FW-004 Backup dan Restore Konfigurasi Firewall
- SOP-SEC-FW-005 Monitoring dan Log Management Firewall
- SOP-SEC-FW-007 Patch dan Upgrade Firmware Firewall
- SOP-SEC-FW-008 Manajemen Akses Administratif Firewall

---

## 11. Riwayat Revisi

| Versi | Tanggal | Perubahan | Penyusun |
|---|---|---|---|
| 1.0 | 2026-09-23 | Penerbitan dokumen pertama | Divisi Teknologi Informasi |
