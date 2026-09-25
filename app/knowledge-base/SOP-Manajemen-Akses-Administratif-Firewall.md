# SOP Manajemen Akses Administratif Firewall

**Nomor Dokumen:** SOP-SEC-FW-008
**Versi:** 1.0
**Tanggal Berlaku:** 2026-09-23
**Unit Pemilik:** Divisi Teknologi Informasi — Network & Security Operations
**Status:** Dokumen contoh untuk basis pengetahuan (knowledge base) NALA

> **Catatan:** Dokumen ini merupakan **template acuan umum**, bukan salinan kebijakan resmi institusi tertentu. Peran akses, batas waktu, dan parameter kata sandi bersifat ilustratif dan harus disesuaikan dengan ketentuan internal serta regulasi yang berlaku sebelum digunakan secara operasional.

---

## 1. Tujuan

1. Memastikan hanya personel yang berwenang yang dapat mengakses dan mengelola firewall, dengan hak akses sesuai tugasnya.
2. Mengatur siklus hidup akun administratif firewall: pemberian, perubahan, peninjauan, dan pencabutan.
3. Mengendalikan penggunaan akun darurat (*break-glass*), akun vendor, dan akun layanan untuk otomasi.
4. Menjamin setiap aktivitas administratif dapat dikaitkan dengan individu dan terekam untuk audit.

---

## 2. Ruang Lingkup

Dokumen ini berlaku untuk seluruh akses administratif ke:

- Perangkat firewall (CLI, web GUI, API) di seluruh lingkungan
- Sistem manajemen terpusat firewall
- Konsol firewall cloud (security group, network ACL, cloud firewall)
- Akses fisik/console dan out-of-band ke perangkat firewall

**Tidak termasuk:** akses pengguna yang **melewati** firewall (mis. VPN pengguna), yang diatur dalam kebijakan akses jaringan tersendiri.

---

## 3. Definisi

| Istilah | Penjelasan |
|---|---|
| **Akun Personal** | Akun yang melekat pada satu individu dan diautentikasi melalui direktori terpusat |
| **Akun Bersama (Shared Account)** | Akun yang digunakan lebih dari satu orang; **dilarang** untuk administrasi firewall |
| **Akun Break-Glass** | Akun lokal darurat yang hanya digunakan saat autentikasi terpusat tidak tersedia |
| **Akun Layanan (Service Account)** | Akun non-manusia untuk otomasi, mis. job backup, integrasi SIEM, orkestrasi policy |
| **TACACS+ / RADIUS** | Protokol autentikasi, otorisasi, dan pencatatan terpusat untuk akses perangkat jaringan |
| **PAM** | *Privileged Access Management* — sistem yang mengontrol, memvault kredensial, dan merekam sesi akses istimewa |
| **MFA** | *Multi-Factor Authentication* — autentikasi dengan lebih dari satu faktor |
| **RBAC** | *Role-Based Access Control* — pemberian hak akses berdasarkan peran |
| **User Access Review (UAR)** | Peninjauan berkala atas kesesuaian akun dan hak akses |

---

## 4. Pihak yang Terlibat

| Peran | Tanggung Jawab Utama |
|---|---|
| **Pemohon** | Mengajukan permintaan akses sesuai kebutuhan tugas |
| **Atasan Langsung Pemohon** | Menyetujui kebutuhan akses bawahannya |
| **Kepala Bagian Network Security** | Pemilik akses firewall; menyetujui pemberian peran dan meninjau akses berkala |
| **Tim Identity & Access Management (IAM)** | Membuat, mengubah, dan menonaktifkan akun di direktori, TACACS+/RADIUS, dan PAM |
| **Unit SDM** | Menginformasikan mutasi, cuti panjang, dan pemberhentian pegawai secara tepat waktu |
| **Information Security** | Menetapkan standar akses, memantau penggunaan akun istimewa, dan mengoordinasikan UAR |
| **Pengelola Vault Break-Glass** | Menyimpan dan mengelola kredensial break-glass sesuai prosedur dua orang |

---

## 5. Peran dan Hak Akses (Ilustratif)

| Peran | Diberikan Kepada | Hak Akses |
|---|---|---|
| **FW-SuperAdmin** | Maksimal 2 orang yang ditunjuk Kepala Bagian Network Security | Seluruh fungsi, termasuk pengelolaan akun lokal dan pengaturan sistem |
| **FW-Admin** | Network Security Engineer | Membuat/mengubah policy, object, NAT, dan VPN, serta commit konfigurasi |
| **FW-Operator** | NOC | Melihat status, dashboard, dan log; menjalankan perintah diagnostik; **tanpa** mengubah konfigurasi |
| **FW-SecurityAnalyst** | SOC | Read-only konfigurasi dan log keamanan |
| **FW-Auditor** | Audit Internal TI, Information Security | Read-only konfigurasi, audit log, dan laporan |
| **FW-Vendor** | Engineer vendor, per tiket | Sesuai kebutuhan tiket; hanya melalui PAM, sementara, dan didampingi |
| **FW-API** | Akun layanan | Hak minimal sesuai fungsi otomasi (mis. read-only untuk backup dan SIEM) |

> Hak akses diberikan berdasarkan prinsip **least privilege** dan **need to know**. Satu orang tidak boleh memiliki peran yang memungkinkan mengajukan, menyetujui, dan mengimplementasikan CR sekaligus.

---

## 6. Standar Autentikasi dan Akses

1. Seluruh akses administratif menggunakan **akun personal** yang diautentikasi melalui TACACS+/RADIUS dan terhubung ke direktori terpusat.
2. Akses wajib menggunakan **MFA** dan dilakukan **melalui jump server/PAM** dari zona MGMT, sesuai SOP-SEC-FW-002.
3. Protokol manajemen yang diizinkan hanya **SSH v2, HTTPS, dan API melalui TLS**.
4. Sesi administratif **terekam** di PAM, dan seluruh perintah/perubahan tercatat di audit log yang dikirim ke SIEM.
5. Timeout sesi idle maksimal **10 menit**. Akun terkunci setelah **5 kali** gagal login berturut-turut.
6. Akun bawaan pabrikan (*default*) wajib **dinonaktifkan atau diganti namanya**, dan kata sandinya diganti saat instalasi.
7. Akun lokal hanya diperbolehkan untuk **break-glass** (lihat **Bab 8**).

---

## 7. Siklus Hidup Akun

### Tahap 1 — Permohonan Akses

**Pelaksana:** Pemohon
**SLA:** —

1. Mengajukan permohonan akses melalui sistem ITSM dengan mencantumkan peran yang diminta, perangkat/lingkungan, justifikasi, dan masa berlaku (khusus akses sementara).
2. Pemohon wajib telah menandatangani pernyataan kerahasiaan dan mengikuti pelatihan keamanan informasi.

### Tahap 2 — Persetujuan

**Pelaksana:** Atasan Langsung dan Kepala Bagian Network Security
**SLA:** 2 hari kerja

1. Atasan langsung memverifikasi kebutuhan tugas.
2. Kepala Bagian Network Security memverifikasi kesesuaian peran dan pemisahan fungsi.
3. Permohonan peran **FW-SuperAdmin** juga memerlukan persetujuan **CISO**.

### Tahap 3 — Pemberian Akses (Provisioning)

**Pelaksana:** Tim IAM
**SLA:** 1 hari kerja setelah persetujuan

1. Menambahkan akun ke grup peran yang sesuai di TACACS+/RADIUS dan PAM.
2. Mendaftarkan faktor MFA pengguna.
3. Menginformasikan kepada pemohon bahwa akses aktif, beserta kewajiban penggunaannya.
4. Mencatat bukti pemberian akses pada tiket.

### Tahap 4 — Perubahan Akses

1. Perubahan peran (mis. karena mutasi tugas) diajukan sebagai permohonan baru dan melalui persetujuan yang sama.
2. Hak akses lama **dicabut** pada saat hak akses baru diberikan, tidak ditumpuk.

### Tahap 5 — Pencabutan Akses

**Pelaksana:** Tim IAM berdasarkan informasi Unit SDM atau atasan

| Kondisi | Batas Waktu Pencabutan |
|---|---|
| Pemberhentian (terutama tidak dengan hormat) | **Seketika**, paling lambat pada hari yang sama saat pemberitahuan |
| Pengunduran diri / pensiun | Paling lambat pada hari kerja terakhir |
| Mutasi ke unit yang tidak memerlukan akses | 1 hari kerja sejak efektif mutasi |
| Cuti panjang (> 30 hari) | Dinonaktifkan sementara selama cuti |
| Akun tidak digunakan > 90 hari | Dinonaktifkan dan dikonfirmasi ke atasan |
| Akses sementara/vendor berakhir | Otomatis pada tanggal berakhir |

Saat pencabutan akun personal dengan peran FW-SuperAdmin/FW-Admin, kredensial akun break-glass dan akun layanan yang pernah diketahui pengguna tersebut **wajib dirotasi**.

---

## 8. Akun Break-Glass

1. Setiap firewall memiliki **satu akun lokal break-glass** dengan kata sandi kuat (minimal **20 karakter** acak).
2. Kredensial disimpan di **vault PAM** atau amplop tersegel di brankas, dengan prinsip **dua orang** (*dual control*) untuk membukanya.
3. Akun hanya boleh digunakan bila **autentikasi terpusat tidak tersedia** dan terdapat kebutuhan operasional mendesak, mis. insiden P1/P2.
4. Penggunaan wajib:
   - disetujui Kepala Bagian Network Security atau pejabat on-call;
   - dicatat pada tiket insiden (siapa, kapan, alasan, tindakan yang dilakukan);
   - dilaporkan kepada SOC, karena penggunaan akun break-glass memicu alert sesuai SOP-SEC-FW-005.
5. Kata sandi **dirotasi segera setelah digunakan** dan secara berkala minimal setiap **90 hari**.
6. Uji fungsi akun break-glass dilakukan setiap **6 bulan** dalam kondisi terkontrol.

---

## 9. Akses Vendor

1. Vendor hanya mendapat akses berdasarkan **tiket atau CR** yang aktif dan perjanjian kerja sama/NDA yang berlaku.
2. Akses diberikan melalui **PAM** dengan akun personal vendor (bukan akun bersama), MFA, dan **perekaman sesi**.
3. Akses berlaku sementara, maksimal sesuai durasi pekerjaan, dan diaktifkan hanya saat pekerjaan berlangsung.
4. Sesi vendor untuk perubahan di Production wajib **didampingi** Network Security Engineer.
5. Pengiriman file konfigurasi atau diagnostik kepada vendor dilakukan melalui kanal resmi. Informasi sensitif (kata sandi, kunci, alamat IP publik bila tidak diperlukan) disamarkan terlebih dahulu.

---

## 10. Akun Layanan dan API Key

1. Setiap akun layanan memiliki **pemilik** (pegawai yang bertanggung jawab) dan tercatat di inventaris akun.
2. Hak akses dibatasi hanya untuk fungsi yang dibutuhkan, mis. akun backup cukup read-only dan ekspor konfigurasi.
3. Akses akun layanan dibatasi dari alamat sumber tertentu (server otomasi di zona MGMT).
4. Kredensial/API key disimpan di **vault**, tidak boleh ditulis di skrip, repositori kode, atau file teks.
5. Kredensial dirotasi minimal setiap **12 bulan** dan setiap kali pemilik atau personel yang mengetahuinya berganti.
6. Akun layanan **tidak boleh** digunakan untuk login interaktif oleh manusia.

---

## 11. Peninjauan Hak Akses (User Access Review)

**Pelaksana:** Information Security bersama Kepala Bagian Network Security
**Frekuensi:** Triwulanan untuk FW-SuperAdmin/FW-Admin; 6 bulanan untuk peran lainnya

1. Mengekspor daftar akun dan peran dari TACACS+/RADIUS, PAM, akun lokal perangkat, dan konsol cloud.
2. Mencocokkan daftar dengan data kepegawaian aktif dan permohonan akses yang disetujui.
3. Mengidentifikasi akun tidak sah, akun milik pegawai non-aktif, hak akses berlebih, dan akun lokal selain break-glass.
4. Mencabut atau menyesuaikan akses yang tidak sesuai paling lambat **5 hari kerja** setelah review.
5. Mendokumentasikan hasil review sebagai bukti audit.

---

## 12. Pengendalian Internal

1. **Akuntabilitas individu:** setiap aktivitas administratif harus dapat dikaitkan dengan satu orang. Akun bersama dilarang.
2. **Pemisahan fungsi:** peran penyetuju CR tidak diberikan hak commit konfigurasi pada lingkup yang sama.
3. **Pemantauan akun istimewa:** SOC memantau login di luar jam kerja, login dari luar zona MGMT, dan penggunaan akun break-glass.
4. **Retensi:** bukti permohonan, persetujuan, pencabutan, dan UAR disimpan minimal **5 tahun**, atau sesuai ketentuan retensi internal.
5. **Audit:** Audit Internal TI melakukan uji petik atas kesesuaian akun dengan data pegawai dan bukti persetujuan.

---

## 13. Pertanyaan yang Sering Diajukan

**Bagaimana cara mendapatkan akses ke firewall?**
Ajukan permohonan melalui sistem ITSM dengan menyebutkan peran, perangkat, dan justifikasinya. Permohonan disetujui atasan langsung dan Kepala Bagian Network Security, lalu diproses Tim IAM.

**Bolehkah memakai satu akun admin bersama untuk tim?**
Tidak. Setiap orang wajib menggunakan akun personal agar setiap perubahan dapat ditelusuri ke individu yang melakukannya.

**Server TACACS+ sedang down dan ada gangguan kritikal. Bagaimana login ke firewall?**
Gunakan akun break-glass dengan persetujuan pejabat on-call, catat penggunaannya di tiket insiden, dan pastikan kata sandinya dirotasi setelah selesai.

**Vendor perlu troubleshooting langsung di firewall. Apa yang harus disiapkan?**
Tiket/CR yang aktif, akun vendor personal di PAM dengan masa berlaku terbatas, serta pendampingan Network Security Engineer selama sesi di Production.

**Seberapa cepat akses dicabut saat pegawai keluar?**
Paling lambat pada hari kerja terakhir, dan seketika untuk pemberhentian tidak dengan hormat.

---

## 14. Referensi

- POJK Nomor 11/POJK.03/2022 tentang Penyelenggaraan Teknologi Informasi oleh Bank Umum
- ISO/IEC 27001:2022 — kontrol A.5.15–A.5.18 (kontrol akses, manajemen identitas, informasi autentikasi, hak akses) dan A.8.2 (*Privileged access rights*)
- PCI DSS v4.0 — Requirement 7 dan 8 (pembatasan akses dan identifikasi/autentikasi pengguna)
- SOP-SEC-FW-002 Konfigurasi Firewall Policy
- SOP-SEC-FW-005 Monitoring dan Log Management Firewall
- SOP-SEC-FW-006 Penanganan Insiden dan Gangguan Firewall

---

## 15. Riwayat Revisi

| Versi | Tanggal | Perubahan | Penyusun |
|---|---|---|---|
| 1.0 | 2026-09-23 | Penerbitan dokumen pertama | Divisi Teknologi Informasi |
