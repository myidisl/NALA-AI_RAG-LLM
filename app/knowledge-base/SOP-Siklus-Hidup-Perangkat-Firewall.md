# SOP Siklus Hidup Perangkat Firewall

**Nomor Dokumen:** SOP-SEC-FW-009
**Versi:** 1.0
**Tanggal Berlaku:** 2026-09-23
**Unit Pemilik:** Divisi Teknologi Informasi — Network & Security Operations
**Status:** Dokumen contoh untuk basis pengetahuan (knowledge base) NALA

> **Catatan:** Dokumen ini merupakan **template acuan umum**, bukan salinan kebijakan resmi institusi tertentu. Parameter sizing, frekuensi uji, dan batas waktu penggantian bersifat ilustratif dan harus disesuaikan dengan ketentuan internal serta regulasi yang berlaku sebelum digunakan secara operasional.

---

## 1. Tujuan

1. Mengatur pengelolaan perangkat firewall secara menyeluruh, sejak perencanaan hingga penghapusan (*decommission*).
2. Memastikan setiap firewall baru memenuhi standar keamanan (*baseline hardening*) sebelum digunakan di Production.
3. Menjamin ketersediaan firewall melalui desain redundan (HA/DR) yang diuji secara berkala.
4. Memastikan perangkat yang dihentikan tidak meninggalkan data sensitif, akses, atau konfigurasi yang masih aktif.

---

## 2. Ruang Lingkup

Dokumen ini berlaku untuk seluruh perangkat firewall fisik, virtual appliance, dan layanan firewall cloud di lingkungan bank, mencakup tahapan:

1. Perencanaan dan pengadaan
2. Instalasi dan baseline hardening
3. Migrasi rule (penggantian perangkat)
4. Go-live
5. Operasional dan uji ketahanan (HA/DR)
6. Pemantauan masa dukungan (lisensi, kontrak, EoL/EoS)
7. Penghapusan (*decommission*) dan disposal

**Tidak termasuk:** pengelolaan policy, backup, monitoring, patch, dan akses sehari-hari, yang masing-masing diatur dalam **SOP-SEC-FW-001 s.d. SOP-SEC-FW-008**.

---

## 3. Definisi

| Istilah | Penjelasan |
|---|---|
| **Baseline Hardening** | Konfigurasi keamanan minimum yang wajib diterapkan pada setiap firewall sebelum go-live |
| **HA (High Availability)** | Konfigurasi dua atau lebih firewall yang saling menggantikan bila salah satu gagal |
| **DR (Disaster Recovery)** | Firewall di site cadangan untuk kelangsungan layanan saat site utama tidak dapat beroperasi |
| **CMDB** | *Configuration Management Database* — inventaris aset TI beserta atribut dan relasinya |
| **End of Sale (EoSale)** | Tanggal vendor berhenti menjual model perangkat |
| **End of Support / End of Life (EoS/EoL)** | Tanggal vendor berhenti menyediakan patch, dukungan teknis, dan penggantian hardware |
| **RMA** | *Return Merchandise Authorization* — proses penggantian perangkat rusak oleh vendor |
| **Sanitasi Media** | Penghapusan data pada media penyimpanan sehingga tidak dapat dipulihkan |

---

## 4. Pihak yang Terlibat

| Peran | Tanggung Jawab Utama |
|---|---|
| **Network Security Engineer** | Menyusun kebutuhan teknis, instalasi, hardening, migrasi, uji HA/DR, dan decommission |
| **Network Architect** | Menyusun desain penempatan firewall, zona, dan redundansi |
| **Kepala Bagian Network Security** | Menyetujui desain, hasil hardening, dan rencana penggantian perangkat |
| **Information Security** | Mereview desain dan hasil baseline hardening sebelum go-live |
| **Unit Pengadaan** | Melaksanakan proses pengadaan perangkat, lisensi, dan kontrak dukungan |
| **Pengelola Aset TI / CMDB** | Mencatat perangkat di CMDB sepanjang siklus hidupnya |
| **Tim Data Center / Facility** | Menyediakan rak, daya, pendinginan, serta akses fisik |
| **Change Manager / CAB** | Menyetujui go-live, migrasi, uji DR, dan decommission |

---

## 5. Alur Siklus Hidup

### Tahap 1 — Perencanaan Kebutuhan

**Pelaksana:** Network Architect dan Network Security Engineer

1. Mengidentifikasi kebutuhan: firewall baru (layanan/site baru), penambahan kapasitas, atau penggantian perangkat EoL.
2. Menyusun sizing berdasarkan data monitoring (SOP-SEC-FW-005) dan proyeksi pertumbuhan **3–5 tahun**:
   - throughput **dengan fitur keamanan aktif** (IPS, anti-malware, SSL inspection), bukan throughput firewall murni;
   - jumlah sesi bersamaan dan koneksi baru per detik;
   - jumlah tunnel VPN;
   - jumlah dan jenis interface.
3. Menetapkan desain redundansi: firewall di **Production wajib HA** dan memiliki padanan di site DR untuk layanan kritikal.
4. Mereview desain bersama Information Security, lalu memperoleh persetujuan Kepala Bagian Network Security.

### Tahap 2 — Pengadaan

**Pelaksana:** Unit Pengadaan bersama Network Security Engineer

1. Menyusun spesifikasi teknis dan kriteria evaluasi vendor: fitur keamanan, kinerja, rekam jejak kerentanan, dukungan lokal, dan integrasi dengan sistem yang ada.
2. Memastikan pengadaan mencakup **kontrak dukungan** (mis. penggantian hardware hari kerja berikutnya atau 4 jam untuk perangkat kritikal) dan **lisensi/subscription** fitur keamanan.
3. Memastikan model yang dibeli tidak mendekati tanggal **EoSale/EoS** (minimal **5 tahun** dukungan tersisa).
4. Memastikan perangkat diperoleh dari distributor resmi untuk menghindari perangkat palsu atau yang sudah dimodifikasi.

### Tahap 3 — Penerimaan dan Instalasi

**Pelaksana:** Network Security Engineer dan Tim Data Center

1. Memeriksa kondisi fisik, nomor seri, dan kelengkapan perangkat sesuai dokumen pengadaan.
2. Mendaftarkan perangkat ke **CMDB** dengan status *In Staging*: nomor seri, model, lokasi, pemilik, dan tanggal EoS.
3. Mendaftarkan perangkat ke portal dukungan vendor dan mengaktifkan lisensi.
4. Memasang perangkat di rak dengan catu daya redundan dari sumber listrik berbeda, serta pelabelan kabel yang jelas.
5. Melakukan konfigurasi awal di lingkungan **staging** yang terisolasi, bukan langsung terhubung ke jaringan Production.

### Tahap 4 — Baseline Hardening

**Pelaksana:** Network Security Engineer
**Direview oleh:** Information Security

Setiap firewall wajib memenuhi checklist berikut sebelum go-live:

| No | Item Baseline | Acuan |
|---|---|---|
| 1 | Firmware sesuai **versi baseline** yang disetujui | SOP-SEC-FW-007 |
| 2 | Kata sandi akun default diganti, lalu akun default dinonaktifkan/diganti nama | SOP-SEC-FW-008 |
| 3 | Autentikasi via TACACS+/RADIUS dengan MFA; akun lokal hanya break-glass | SOP-SEC-FW-008 |
| 4 | Interface manajemen hanya di zona MGMT; hanya SSH v2 dan HTTPS | SOP-SEC-FW-002 |
| 5 | Layanan yang tidak digunakan dinonaktifkan (Telnet, HTTP, SNMP v1/v2c, dsb.) | SOP-SEC-FW-002 |
| 6 | SNMP v3 dengan autentikasi dan enkripsi untuk monitoring | SOP-SEC-FW-005 |
| 7 | NTP ke server internal; zona waktu sesuai standar | SOP-SEC-FW-005 |
| 8 | Log forwarding ke SIEM aktif dan terverifikasi diterima | SOP-SEC-FW-005 |
| 9 | Banner peringatan akses sah dan session timeout 10 menit | SOP-SEC-FW-008 |
| 10 | Cleanup rule `deny all` dengan logging | SOP-SEC-FW-002 |
| 11 | Job backup otomatis terdaftar dan backup pertama berhasil | SOP-SEC-FW-004 |
| 12 | Update signature otomatis aktif | SOP-SEC-FW-007 |
| 13 | Sertifikat manajemen diganti dengan sertifikat dari CA internal (bukan self-signed default) | — |
| 14 | Monitoring health terdaftar di NOC | SOP-SEC-FW-005 |

Hasil checklist didokumentasikan dan ditandatangani oleh Network Security Engineer dan Information Security.

### Tahap 5 — Migrasi Rule (untuk Penggantian Perangkat)

**Pelaksana:** Network Security Engineer

1. Melakukan **pembersihan rulebase** pada perangkat lama sebelum migrasi sesuai SOP-SEC-FW-003, agar rule usang tidak ikut terbawa.
2. Mengonversi rule menggunakan alat migrasi vendor atau secara manual, dengan konvensi penamaan SOP-SEC-FW-002.
3. Membandingkan hasil konversi dengan rulebase lama: jumlah rule, object, NAT, dan VPN.
4. Menyusun **daftar uji** berisi alur lalu lintas kritikal per aplikasi bersama pemilik aplikasi.
5. Menyiapkan rencana cutover dan **rollback** (mis. mengembalikan kabel/routing ke perangkat lama).

### Tahap 6 — Go-Live

**Pelaksana:** Network Security Engineer
**Persetujuan:** CAB melalui CR

1. Mengajukan CR go-live/cutover sesuai SOP-SEC-FW-001, dengan melampirkan hasil baseline hardening dan rencana uji.
2. Melaksanakan cutover dalam maintenance window.
3. Menjalankan daftar uji bersama pemilik aplikasi dan NOC.
4. Menguji failover HA sebelum maintenance window berakhir.
5. Memperbarui status CMDB menjadi *In Production* dan memperbarui diagram jaringan.
6. Memantau secara intensif selama **7 hari** setelah go-live. Perangkat lama dipertahankan dalam kondisi siap (*standby*) selama masa tersebut sebagai opsi rollback.

### Tahap 7 — Operasional dan Uji Ketahanan

**Pelaksana:** Network Security Engineer bersama NOC

Selama operasional, perangkat dikelola sesuai SOP-SEC-FW-001 s.d. SOP-SEC-FW-008, dengan uji ketahanan berikut:

| Uji | Frekuensi | Keterangan |
|---|---|---|
| **Uji failover HA** | 6 bulanan | Failover terkontrol antar anggota cluster dalam maintenance window; verifikasi sesi dan layanan tetap berjalan |
| **Uji DR** | Tahunan, atau mengikuti jadwal uji DR bank | Memastikan firewall di site DR dapat menangani layanan kritikal dan rule tersinkron dengan Production |
| **Review kapasitas** | Tahunan | Membandingkan utilisasi dengan kapasitas dan proyeksi pertumbuhan |

Hasil uji didokumentasikan. Kegagalan uji ditindaklanjuti sebagai temuan dengan pemilik dan batas waktu perbaikan.

### Tahap 8 — Pemantauan Masa Dukungan

**Pelaksana:** Network Security Engineer dan Pengelola Aset TI

1. CMDB mencatat tanggal berakhir **kontrak dukungan, lisensi/subscription, dan EoS** setiap perangkat.
2. Perpanjangan kontrak dan lisensi diajukan minimal **90 hari** sebelum berakhir.
3. Perangkat yang akan memasuki EoS dimasukkan ke rencana anggaran penggantian minimal **12 bulan** sebelumnya.
4. Perangkat yang telah melewati EoS dan belum diganti dicatat sebagai **pengecualian risiko** dengan mitigasi dan persetujuan CISO.

### Tahap 9 — Decommission dan Disposal

**Pelaksana:** Network Security Engineer, Pengelola Aset TI, dan Information Security
**Persetujuan:** CR sesuai SOP-SEC-FW-001

1. Memastikan seluruh layanan telah dipindahkan dan tidak ada lalu lintas aktif yang melewati perangkat (periksa log/sesi minimal **7 hari**).
2. Mengambil **backup konfigurasi final** dan mengarsipkannya sesuai retensi SOP-SEC-FW-004.
3. Melepas perangkat dari seluruh integrasi:
   - cluster HA dan sistem manajemen terpusat;
   - monitoring NOC dan sumber log SIEM;
   - TACACS+/RADIUS, PAM, dan akun layanan;
   - job backup otomatis.
4. **Mencabut** sertifikat yang terpasang, dan mengganti *pre-shared key* VPN yang pernah digunakan bersama pihak lain.
5. Mengembalikan atau memindahkan lisensi sesuai ketentuan vendor.
6. Melakukan **factory reset** dan **sanitasi media penyimpanan** sesuai standar internal. Bila sanitasi tidak dapat dijamin, media penyimpanan dimusnahkan secara fisik.
7. Menerbitkan **berita acara sanitasi/pemusnahan** yang ditandatangani pelaksana dan saksi dari Information Security.
8. Memperbarui CMDB menjadi *Decommissioned/Disposed* dan memperbarui diagram jaringan.

> Perangkat yang dikembalikan ke vendor melalui RMA juga wajib disanitasi terlebih dahulu bila kondisi perangkat memungkinkan.

---

## 6. Pengendalian Internal

1. **Tidak ada go-live tanpa baseline:** perangkat tidak boleh terhubung ke jaringan Production sebelum checklist baseline hardening disetujui Information Security.
2. **Inventaris akurat:** setiap perangkat firewall aktif harus tercatat di CMDB, terdaftar di monitoring, dan mengirim log ke SIEM. Rekonsiliasi dilakukan triwulanan.
3. **Redundansi:** firewall Production tanpa HA wajib dicatat sebagai pengecualian risiko.
4. **Keamanan disposal:** tidak ada perangkat yang keluar dari lingkungan bank tanpa berita acara sanitasi/pemusnahan.
5. **Audit:** Audit Internal TI melakukan uji petik atas kelengkapan checklist baseline, hasil uji HA/DR, dan berita acara disposal.

---

## 7. Pertanyaan yang Sering Diajukan

**Apakah firewall baru boleh langsung dipasang di jaringan Production?**
Tidak. Firewall dikonfigurasi di lingkungan staging, lalu seluruh checklist baseline hardening harus disetujui Information Security. Setelah itu go-live dilakukan melalui CR.

**Kenapa sizing firewall harus memakai throughput dengan fitur keamanan aktif?**
Karena kinerja firewall turun signifikan saat IPS, anti-malware, dan SSL inspection diaktifkan. Sizing dengan throughput firewall murni akan menghasilkan perangkat yang terlalu kecil.

**Seberapa sering failover HA diuji?**
Setiap 6 bulan dalam maintenance window. Uji DR mengikuti jadwal uji DR bank, minimal setahun sekali.

**Apa yang dilakukan bila firewall sudah End of Support tetapi anggaran penggantian belum tersedia?**
Catat sebagai pengecualian risiko dengan mitigasi, seperti pembatasan akses manajemen dan monitoring yang diperketat, serta persetujuan CISO, sambil menjadwalkan penggantian.

**Bolehkah firewall bekas langsung dijual atau dihibahkan?**
Tidak sebelum factory reset, sanitasi media, dan berita acara diterbitkan, karena perangkat dapat menyimpan konfigurasi, kunci VPN, dan sertifikat.

---

## 8. Referensi

- POJK Nomor 11/POJK.03/2022 tentang Penyelenggaraan Teknologi Informasi oleh Bank Umum
- ISO/IEC 27001:2022 — kontrol A.5.9 (*Inventory of information and other associated assets*), A.7.14 (*Secure disposal or re-use of equipment*), A.8.9 (*Configuration management*), dan A.8.14 (*Redundancy of information processing facilities*)
- NIST SP 800-88 Rev. 1 — *Guidelines for Media Sanitization*
- SOP-SEC-FW-001 s.d. SOP-SEC-FW-008 (seluruh SOP pengelolaan firewall)

---

## 9. Riwayat Revisi

| Versi | Tanggal | Perubahan | Penyusun |
|---|---|---|---|
| 1.0 | 2026-09-23 | Penerbitan dokumen pertama | Divisi Teknologi Informasi |
