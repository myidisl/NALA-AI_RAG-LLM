# SOP Konfigurasi Firewall Policy

**Nomor Dokumen:** SOP-SEC-FW-002
**Versi:** 1.1
**Tanggal Berlaku:** 2026-09-23
**Unit Pemilik:** Divisi Teknologi Informasi — Network & Security Operations
**Status:** Dokumen contoh untuk basis pengetahuan (knowledge base) NALA

> **Catatan:** Dokumen ini merupakan **template acuan umum**, bukan salinan kebijakan resmi institusi tertentu. Model zona, konvensi penamaan, dan parameter teknis bersifat ilustratif dan harus disesuaikan dengan arsitektur jaringan, perangkat yang digunakan, serta ketentuan internal sebelum digunakan secara operasional.

---

## 1. Tujuan

1. Menetapkan standar teknis yang seragam dalam menyusun, mengimplementasikan, dan memelihara firewall policy.
2. Memastikan setiap rule menerapkan prinsip **default deny** dan **least privilege**.
3. Menjaga firewall policy tetap rapi, mudah dibaca, mudah diaudit, dan bebas dari rule berlebih, duplikat, atau usang.
4. Meminimalkan risiko gangguan layanan akibat kesalahan konfigurasi melalui langkah implementasi dan rollback yang baku.

---

## 2. Ruang Lingkup

Dokumen ini berlaku untuk seluruh **konfigurasi firewall policy** yang dilakukan oleh Network Security Engineer, mencakup:

- Firewall perimeter, internal, dan koneksi pihak ketiga (on-premise)
- Firewall di lingkungan cloud (security group, network ACL, cloud firewall)
- Seluruh lingkungan: Production, Disaster Recovery (DR), UAT, dan Development

SOP ini bersifat **vendor-neutral**. Istilah dan menu dapat berbeda antar produk firewall, tetapi prinsip dan langkahnya tetap berlaku.

**Tidak termasuk:** proses pengajuan dan persetujuan perubahan, yang diatur dalam **SOP-SEC-FW-001 Change Request Firewall Policy**. Setiap konfigurasi pada SOP ini **wajib** didasari CR yang telah disetujui.

---

## 3. Definisi

| Istilah | Penjelasan |
|---|---|
| **Default Deny** | Prinsip bahwa seluruh lalu lintas ditolak kecuali yang diizinkan secara eksplisit oleh rule |
| **Least Privilege** | Memberikan akses seminimal mungkin (sumber, tujuan, dan port paling spesifik) sesuai kebutuhan |
| **Object** | Definisi bernama untuk alamat (host, subnet, range, FQDN) atau layanan (protokol/port) yang dipakai dalam rule |
| **Object Group** | Kumpulan object yang dikelompokkan untuk menyederhanakan rule |
| **Shadowed Rule** | Rule yang tidak pernah tercapai karena lalu lintasnya sudah tercakup oleh rule di atasnya |
| **Redundant Rule** | Rule yang duplikat atau sepenuhnya tercakup oleh rule lain dengan aksi yang sama |
| **Hit Count** | Jumlah koneksi yang cocok dengan suatu rule, dipakai untuk menilai apakah rule masih digunakan |
| **Candidate Config** | Konfigurasi yang sudah diubah tetapi belum diterapkan (*commit*) ke konfigurasi aktif |
| **Rollback** | Mengembalikan konfigurasi ke kondisi sebelum perubahan |
| **Jump Server / PAM** | Server perantara atau sistem *Privileged Access Management* untuk akses administratif yang terkontrol dan terekam |

---

## 4. Pihak yang Terlibat

| Peran | Tanggung Jawab Utama |
|---|---|
| **Network Security Engineer (Pelaksana)** | Mengimplementasikan rule sesuai standar, melakukan pre-check, verifikasi, dan rollback bila diperlukan |
| **Network Security Engineer (Peer Reviewer)** | Memeriksa ulang konfigurasi sebelum commit untuk perubahan berisiko sedang dan tinggi |
| **Kepala Bagian Network Security** | Memastikan kepatuhan standar dan menyetujui pengecualian teknis |
| **Information Security** | Melakukan review berkala atas firewall policy dan memantau log di SIEM |
| **NOC** | Memantau ketersediaan layanan selama dan setelah perubahan |

---

## 5. Prinsip Dasar Konfigurasi

1. **Default deny:** setiap firewall wajib diakhiri dengan rule **deny all** yang di-log (*explicit cleanup rule*).
2. **Least privilege:** gunakan IP host (/32) atau subnet sekecil mungkin, serta port spesifik. Hindari nilai **any** kecuali pada kasus yang diizinkan di **Bab 10**.
3. **Gunakan object, bukan IP langsung:** seluruh alamat dan layanan didefinisikan sebagai object bernama sesuai konvensi pada **Bab 7**.
4. **Satu rule, satu tujuan bisnis:** jangan menggabungkan kebutuhan aplikasi berbeda ke dalam satu rule.
5. **Keterlacakan:** setiap rule wajib mencantumkan nomor CR dan pemilik pada kolom deskripsi/komentar.
6. **Logging:** seluruh rule deny dan rule allow menuju Restricted Zone atau dari Internet wajib di-log.
7. **Protokol aman:** utamakan protokol terenkripsi (HTTPS, SSH, SFTP, LDAPS, TLS 1.2 ke atas).
8. **Konsistensi lingkungan:** rule di site DR wajib disinkronkan dengan site Production.

---

## 6. Model Zona dan Matriks Akses Default

### 6.1 Zona Jaringan

| Zona | Tingkat Kepercayaan | Isi |
|---|---|---|
| **INET** | Tidak dipercaya | Internet |
| **DMZ** | Rendah | Web server publik, reverse proxy, mail gateway, API gateway |
| **PARTNER** | Rendah | Koneksi pihak ketiga, vendor, switching/payment network |
| **USER** | Sedang | Workstation pegawai kantor pusat dan cabang |
| **SRV** | Tinggi | Server aplikasi internal (email, HR, intranet) |
| **RESTRICTED** | Sangat tinggi | Core banking, database nasabah, sistem pembayaran, HSM |
| **MGMT** | Sangat tinggi | Interface manajemen perangkat, jump server/PAM, server monitoring |

### 6.2 Matriks Akses Default Antar Zona (Ilustratif)

Baris = zona sumber, kolom = zona tujuan. **Deny** = ditolak secara default; **CR** = dapat dibuka melalui CR yang disetujui; **Dilarang** = tidak boleh dibuka.

| Sumber \ Tujuan | INET | DMZ | PARTNER | USER | SRV | RESTRICTED | MGMT |
|---|---|---|---|---|---|---|---|
| **INET** | — | CR | Deny | Dilarang | Dilarang | Dilarang | Dilarang |
| **DMZ** | CR | — | CR | Deny | CR | Dilarang | Dilarang |
| **PARTNER** | Deny | CR | — | Dilarang | CR | CR (risiko tinggi) | Dilarang |
| **USER** | CR (via proxy) | CR | Deny | — | CR | Dilarang langsung* | Dilarang |
| **SRV** | CR (via proxy) | CR | CR | Deny | — | CR | Deny |
| **RESTRICTED** | Dilarang | Deny | CR (risiko tinggi) | Dilarang | CR | — | Deny |
| **MGMT** | Deny | CR | Deny | CR | CR | CR | — |

\* Akses pengguna ke aplikasi di Restricted Zone hanya melalui server aplikasi di zona SRV/DMZ, bukan langsung ke database atau server core banking.

> Akses **administratif** (SSH, RDP, HTTPS manajemen, SNMP) ke seluruh perangkat dan server **hanya diizinkan dari zona MGMT** melalui jump server/PAM.

---

## 7. Konvensi Penamaan

### 7.1 Object Alamat

Format: `<TIPE>_<ZONA>_<NAMA>`

| Tipe | Awalan | Contoh |
|---|---|---|
| Host | `H_` | `H_SRV_APP-LOAN-01` |
| Subnet | `N_` | `N_USER_CABANG-BDG` |
| Range | `R_` | `R_DMZ_WEB-POOL` |
| FQDN | `F_` | `F_INET_API.VENDOR.CO.ID` |
| Grup | `G_` | `G_RESTRICTED_CBS-DB` |

### 7.2 Object Layanan

Format: `<PROTOKOL>_<PORT>` atau `<PROTOKOL>_<NAMA-LAYANAN>`. Contoh: `TCP_443`, `TCP_1521_ORACLE`, `UDP_514_SYSLOG`.

### 7.3 Rule

Format: `<CR-NUMBER>_<ZONA-SUMBER>-TO-<ZONA-TUJUAN>_<APLIKASI>`. Contoh: `CR2026-0412_SRV-TO-RESTRICTED_LOAN-APP`.

### 7.4 Deskripsi/Komentar Rule (Wajib)

Format: `CR:<nomor> | Owner:<nama/unit> | Exp:<YYYY-MM-DD atau PERMANEN> | <keterangan singkat>`

Contoh: `CR:CR2026-0412 | Owner:Divisi Kredit | Exp:PERMANEN | App LOS ke DB core banking`

---

## 8. Struktur dan Urutan Rule

### 8.1 Atribut Wajib Setiap Rule

| Atribut | Ketentuan |
|---|---|
| **Nama** | Sesuai konvensi Bab 7.3 |
| **Zona sumber / tujuan** | Wajib diisi spesifik, tidak boleh any |
| **Alamat sumber / tujuan** | Menggunakan object atau object group |
| **Layanan / aplikasi** | Port spesifik; untuk firewall yang mendukung, gunakan identifikasi aplikasi (*application-aware*) |
| **Aksi** | Allow / deny / drop |
| **Logging** | Aktif sesuai Bab 5 butir 6 |
| **Security profile** | IPS/anti-malware diaktifkan untuk rule dari zona INET, PARTNER, dan USER |
| **Jadwal (schedule)** | Diisi untuk rule sementara sesuai tanggal kedaluwarsa pada CR |
| **Deskripsi** | Sesuai format Bab 7.4 |

### 8.2 Urutan Rule (dari atas ke bawah)

1. **Anti-spoofing & block list:** blokir IP berbahaya (*threat intelligence*) dan alamat privat/bogon dari Internet.
2. **Rule manajemen:** akses dari zona MGMT ke perangkat.
3. **Rule infrastruktur:** DNS, NTP, syslog, autentikasi (LDAP/RADIUS/TACACS+).
4. **Rule aplikasi:** dari yang paling spesifik ke yang lebih umum, dikelompokkan per zona.
5. **Cleanup rule:** `deny all` dengan logging aktif, selalu di posisi paling bawah.

> Rule yang sering digunakan (*hit count* tinggi) dapat dinaikkan posisinya untuk performa, **selama tidak mengubah hasil evaluasi rule lain**.

---

## 9. Langkah Implementasi Konfigurasi

### Tahap 1 — Persiapan (Pre-check)

**Pelaksana:** Network Security Engineer (Pelaksana)
**Waktu:** Sebelum maintenance window

1. Memastikan CR berstatus **disetujui** dan jadwal implementasi sesuai.
2. Memeriksa bahwa object yang dibutuhkan belum ada, agar tidak membuat object duplikat.
3. Menjalankan analisis kebijakan (*policy lookup / packet tracer*) untuk memastikan rule baru tidak **shadowed** atau **redundant**.
4. Menyiapkan skrip/langkah konfigurasi dan **rencana rollback** tertulis.
5. Untuk risiko sedang dan tinggi: meminta **peer review** atas skrip konfigurasi.

### Tahap 2 — Backup Konfigurasi

**Pelaksana:** Network Security Engineer (Pelaksana)

1. Mengekspor konfigurasi aktif (*running config*) dan menyimpannya ke repositori backup dengan nama berformat `<hostname>_<YYYYMMDD-HHMM>_pre-<nomor CR>`.
2. Memastikan file backup dapat dibuka dan utuh.
3. Ketentuan penyimpanan, retensi, dan restore mengikuti **SOP-SEC-FW-004 Backup dan Restore Konfigurasi Firewall**.

### Tahap 3 — Implementasi

**Pelaksana:** Network Security Engineer (Pelaksana)
**Waktu:** Dalam maintenance window

1. Login ke firewall atau manajemen terpusat **melalui jump server/PAM** menggunakan akun personal (bukan akun bersama).
2. Membuat object dan object group sesuai konvensi penamaan.
3. Membuat atau mengubah rule sesuai struktur Bab 8, lalu menempatkannya di posisi yang benar.
4. Meninjau perbedaan (*diff*) antara candidate config dan running config, dan memastikan hanya perubahan sesuai CR yang ikut.
5. Menerapkan konfigurasi (*commit / install policy*).
6. Untuk cluster/HA: memastikan konfigurasi tersinkron ke seluruh anggota cluster.
7. Untuk site DR: menerapkan perubahan yang sama sesuai jadwal CR.

### Tahap 4 — Verifikasi

**Pelaksana:** Network Security Engineer dan Requester

1. Memastikan tidak ada error saat commit dan status HA/cluster normal.
2. Meminta requester melakukan uji konektivitas sesuai rencana uji pada CR.
3. Memeriksa log/traffic monitor untuk memastikan lalu lintas cocok dengan rule baru (*hit count* bertambah) dan tidak ada lalu lintas lain yang ikut terbuka.
4. Berkoordinasi dengan NOC untuk memastikan tidak ada gangguan layanan lain.
5. Mengekspor konfigurasi pasca-perubahan dengan nama berformat `<hostname>_<YYYYMMDD-HHMM>_post-<nomor CR>`.

### Tahap 5 — Rollback (bila diperlukan)

**Pelaksana:** Network Security Engineer (Pelaksana)
**Pemicu:** Layanan lain terganggu, verifikasi gagal dan tidak dapat diperbaiki dalam maintenance window, atau ditemukan akses berlebih.

1. Menginformasikan rencana rollback kepada NOC dan Change Manager.
2. Mengembalikan konfigurasi menggunakan backup Tahap 2 atau fitur *revert* perangkat.
3. Memverifikasi bahwa layanan kembali normal.
4. Mencatat penyebab kegagalan pada CR dengan status **Gagal – Rollback**.

### Tahap 6 — Dokumentasi

**Pelaksana:** Network Security Engineer (Pelaksana)

1. Melampirkan bukti ke CR: tangkapan layar rule, hasil *diff*, hasil verifikasi, dan nama file backup.
2. Memperbarui diagram jaringan atau inventaris rule bila terjadi perubahan arsitektur.

---

## 10. Konfigurasi yang Dilarang

1. Rule **any-any-any** (sumber, tujuan, dan layanan bernilai any) dengan aksi allow.
2. Rule allow dengan layanan **any** menuju Restricted Zone atau dari zona INET/PARTNER.
3. Akses administratif (SSH, RDP, Telnet, SNMP, HTTPS manajemen) dari zona selain MGMT.
4. Protokol teks polos (Telnet, FTP, HTTP, SNMP v1/v2c) untuk akses administratif atau data sensitif.
5. Rule tanpa nomor CR pada deskripsi.
6. Menonaktifkan logging pada cleanup rule `deny all`.
7. Perubahan langsung di perangkat anggota cluster bila tersedia manajemen terpusat, karena dapat menyebabkan konfigurasi tidak sinkron.
8. Penggunaan akun bawaan (*default*) atau akun bersama untuk konfigurasi.

**Pengecualian terbatas:** nilai any pada **alamat tujuan** diperbolehkan untuk rule outbound dari proxy server ke Internet pada port 80/443, dan untuk rule ke server DNS/NTP publik yang ditetapkan, dengan persetujuan Kepala Bagian Network Security.

---

## 11. Hardening Manajemen Perangkat Firewall

| Aspek | Standar |
|---|---|
| **Akses manajemen** | Hanya dari zona MGMT melalui jump server/PAM; protokol SSH v2 dan HTTPS |
| **Autentikasi** | Akun personal terpusat (TACACS+/RADIUS) dengan **MFA**; akun lokal hanya untuk *break-glass* dan disimpan di vault |
| **Otorisasi** | Role-based: read-only untuk monitoring, read-write hanya untuk Network Security Engineer |
| **Session** | Timeout idle maksimal 10 menit; banner peringatan akses sah |
| **Logging** | Log traffic dan log audit administrasi dikirim ke **SIEM**; retensi sesuai ketentuan internal |
| **Waktu** | Sinkron ke server NTP internal agar timestamp log konsisten |
| **Backup** | Backup konfigurasi otomatis **harian** dan setiap sebelum/sesudah perubahan |
| **Patch** | Firmware diperbarui sesuai rekomendasi vendor dan hasil penilaian kerentanan, melalui Change Management |

Rincian pelaksanaan masing-masing aspek diatur dalam SOP terpisah:
- akses dan akun administrator → **SOP-SEC-FW-008 Manajemen Akses Administratif Firewall**;
- logging dan monitoring → **SOP-SEC-FW-005 Monitoring dan Log Management Firewall**;
- backup → **SOP-SEC-FW-004 Backup dan Restore Konfigurasi Firewall**;
- patch dan upgrade → **SOP-SEC-FW-007 Patch dan Upgrade Firmware Firewall**;
- baseline hardening perangkat baru → **SOP-SEC-FW-009 Siklus Hidup Perangkat Firewall**.

---

## 12. Review dan Pemeliharaan Berkala

| Kegiatan | Frekuensi | Pelaksana |
|---|---|---|
| Pemeriksaan rule sementara yang kedaluwarsa | Harian | Network Security Engineer |
| Pemeriksaan backup konfigurasi berhasil | Harian | Network Security Engineer |
| Rekonsiliasi log perubahan konfigurasi dengan daftar CR | Bulanan | Information Security |
| Identifikasi rule **zero hit** selama 90 hari | Triwulanan | Network Security Engineer |
| Analisis rule shadowed, redundant, dan terlalu luas | Triwulanan | Network Security Engineer |
| Review menyeluruh firewall policy dan resertifikasi rule oleh pemilik | 6 bulanan | Information Security bersama Application / System Owner |

> Rule yang teridentifikasi tidak digunakan atau tidak memiliki pemilik dihapus melalui **CR penghapusan** sesuai SOP-SEC-FW-001, bukan dihapus langsung. Tata cara review, kriteria temuan, dan resertifikasi diatur dalam **SOP-SEC-FW-003 Review dan Resertifikasi Firewall Rule**.

---

## 13. Pengendalian Internal

1. **Pemisahan fungsi:** pelaksana implementasi berbeda dengan requester dan penyetuju CR. Perubahan berisiko sedang dan tinggi wajib melalui peer review.
2. **Tidak ada perubahan tanpa CR:** setiap perubahan konfigurasi harus dapat ditelusuri ke CR yang disetujui.
3. **Jejak audit:** seluruh aktivitas administrasi firewall tercatat atas nama akun personal dan dikirim ke SIEM.
4. **Integritas backup:** backup konfigurasi disimpan di repositori terpisah dengan akses terbatas.
5. **Kerahasiaan:** konfigurasi firewall, topologi, dan alamat IP bersifat **rahasia** dan dilarang dibagikan kepada pihak yang tidak berwenang, termasuk melalui aplikasi chat atau layanan AI publik.

---

## 14. Pertanyaan yang Sering Diajukan

**Kenapa rule harus diawali nomor CR?**
Agar setiap rule dapat ditelusuri ke permintaan, justifikasi, dan persetujuannya. Hal ini dibutuhkan saat audit dan saat meninjau apakah rule masih dibutuhkan.

**Apa bedanya aksi deny dan drop?**
*Deny/reject* menolak koneksi dan mengirim balasan penolakan ke pengirim. *Drop* membuang paket tanpa balasan. Untuk lalu lintas dari Internet, umumnya digunakan drop agar tidak memberi informasi kepada penyerang.

**Rule sudah dibuat tetapi aplikasi tetap tidak bisa terhubung. Apa yang diperiksa?**
Periksa urutan rule (mungkin tertutup rule deny di atasnya), kesesuaian zona dan object, NAT, routing, firewall lokal di server tujuan, serta log firewall untuk melihat rule mana yang sebenarnya cocok.

**Bolehkah langsung mengubah rule saat ada gangguan tanpa CR?**
Tidak. Gunakan jalur **emergency change** sesuai SOP-SEC-FW-001 Bab 10, dengan persetujuan pejabat on-call dan dokumentasi paling lambat 1×24 jam.

**Mengapa akses SSH/RDP ke server harus lewat jump server?**
Agar akses administratif terpusat, dilindungi MFA, dan terekam untuk audit, sehingga risiko penyalahgunaan dan penyebaran serangan antar zona dapat ditekan.

**Berapa lama rule yang tidak terpakai dibiarkan?**
Rule tanpa lalu lintas selama 90 hari diusulkan untuk dihapus melalui CR, setelah dikonfirmasi ke pemiliknya.

---

## 15. Referensi

- POJK Nomor 11/POJK.03/2022 tentang Penyelenggaraan Teknologi Informasi oleh Bank Umum
- ISO/IEC 27001:2022 — kontrol A.8.20 (*Networks security*), A.8.22 (*Segregation of networks*), dan A.8.15 (*Logging*)
- PCI DSS v4.0 — Requirement 1 (*Install and Maintain Network Security Controls*)
- NIST SP 800-41 Rev. 1 — *Guidelines on Firewalls and Firewall Policy*
- SOP-SEC-FW-001 Change Request Firewall Policy
- SOP-SEC-FW-003 Review dan Resertifikasi Firewall Rule
- SOP-SEC-FW-004 Backup dan Restore Konfigurasi Firewall
- SOP-SEC-FW-005 Monitoring dan Log Management Firewall
- SOP-SEC-FW-007 Patch dan Upgrade Firmware Firewall
- SOP-SEC-FW-008 Manajemen Akses Administratif Firewall
- SOP-SEC-FW-009 Siklus Hidup Perangkat Firewall

---

## 16. Riwayat Revisi

| Versi | Tanggal | Perubahan | Penyusun |
|---|---|---|---|
| 1.0 | 2026-09-23 | Penerbitan dokumen pertama | Divisi Teknologi Informasi |
| 1.1 | 2026-09-23 | Menambahkan rujukan ke SOP-SEC-FW-003 s.d. 009 | Divisi Teknologi Informasi |
