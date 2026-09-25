# SOP Layanan Kartu Debit dan Mobile Banking

**Nomor Dokumen:** SOP-LYN-002
**Versi:** 1.0
**Tanggal Berlaku:** 2026-09-23
**Unit Pemilik:** Divisi Layanan Digital dan E-Channel
**Status:** Dokumen contoh untuk basis pengetahuan (knowledge base) NALA

> **Catatan:** Dokumen ini merupakan **template acuan umum**, bukan salinan kebijakan resmi institusi tertentu. Limit transaksi, biaya, SLA, dan fitur bersifat ilustratif dan harus disesuaikan dengan ketentuan internal serta regulasi yang berlaku sebelum digunakan secara operasional.

---

## 1. Tujuan

1. Menyediakan panduan baku penerbitan, pemblokiran, dan penggantian kartu debit.
2. Menyediakan panduan registrasi, reset, dan pemblokiran layanan *mobile banking*.
3. Menetapkan penanganan sanggahan (*dispute*) transaksi dan indikasi pembobolan akun.
4. Memastikan keamanan kredensial nasabah (PIN, password, OTP) tidak pernah diketahui petugas.

---

## 2. Ruang Lingkup

Dokumen ini berlaku untuk nasabah perorangan pemilik rekening tabungan/giro, meliputi:

- Penerbitan dan aktivasi kartu debit
- Blokir dan penggantian kartu (hilang, rusak, tertelan ATM)
- Reset PIN kartu
- Registrasi, aktivasi, pergantian perangkat, dan blokir *mobile banking*
- Sanggahan transaksi dan penanganan indikasi *fraud*

---

## 3. Definisi

| Istilah | Penjelasan |
|---|---|
| **Kartu Debit** | Kartu yang terhubung langsung ke rekening untuk transaksi tarik tunai, transfer, dan belanja |
| **PIN** | Nomor identifikasi pribadi; rahasia dan hanya diketahui nasabah |
| **OTP** | *One Time Password* — kode sekali pakai untuk verifikasi transaksi |
| **Device Binding** | Pengikatan akun *mobile banking* ke satu perangkat terdaftar |
| **Social Engineering** | Teknik manipulasi psikologis untuk memperdaya nasabah agar memberikan data rahasia |
| **Skimming** | Pencurian data kartu menggunakan alat yang dipasang di mesin ATM/EDC |
| **Dispute** | Sanggahan nasabah atas transaksi yang tidak diakui atau bermasalah |

---

## 4. Pihak yang Terlibat

| Peran | Tanggung Jawab Utama |
|---|---|
| **Customer Service** | Penerbitan/penggantian kartu, reset PIN, registrasi dan reset *mobile banking* |
| **Contact Center** | Menerima laporan 24 jam dan melakukan blokir darurat kartu/akun |
| **Unit Kartu & E-Channel** | Personalisasi kartu, pengelolaan limit, dan penanganan *dispute* |
| **Unit Anti-Fraud** | Analisa transaksi mencurigakan dan indikasi pembobolan akun |

---

## 5. Prinsip Keamanan Wajib

1. Petugas **dilarang** menanyakan, mencatat, atau menerima PIN, password, dan OTP nasabah dalam kondisi apa pun.
2. PIN dibuat sendiri oleh nasabah melalui PIN pad atau aplikasi.
3. Bank tidak pernah meminta data rahasia melalui telepon, pesan singkat, media sosial, atau tautan; petugas wajib mengedukasi nasabah mengenai hal ini.
4. Setiap perubahan data kontak (nomor ponsel/e-mail) wajib diverifikasi dengan identitas asli, karena merupakan titik rawan pengambilalihan akun (*account takeover*).

---

## 6. Layanan Kartu Debit

### 6.1 Penerbitan Kartu

1. Kartu diterbitkan bersamaan dengan pembukaan rekening atau atas permintaan nasabah.
2. Nasabah membuat PIN melalui PIN pad; petugas memastikan tidak ada pihak lain yang melihat.
3. Kartu instan langsung aktif; kartu personalisasi dikirim/diambil di cabang dan diaktifkan setelah verifikasi.

### 6.2 Blokir Kartu

1. Nasabah dapat memblokir kartu secara mandiri melalui aplikasi *mobile banking*, atau menghubungi Contact Center 24 jam.
2. Contact Center memverifikasi identitas penelepon menggunakan data yang tidak bersifat rahasia transaksi (misalnya data profil), lalu memblokir kartu **segera**.
3. Blokir karena hilang/dicuri bersifat permanen; kartu yang ditemukan kembali tidak dapat diaktifkan ulang.

### 6.3 Penggantian Kartu

| Kondisi | Persyaratan |
|---|---|
| **Hilang / dicuri** | Identitas asli dan buku tabungan (jika ada); surat kehilangan dari kepolisian bila disyaratkan kebijakan |
| **Rusak** | Identitas asli dan kartu yang rusak |
| **Tertelan di ATM bank sendiri** | Identitas asli; kartu yang tertelan dimusnahkan sesuai prosedur |
| **Kedaluwarsa** | Identitas asli; kartu lama ditarik |

---

## 7. Layanan Mobile Banking

### 7.1 Registrasi dan Aktivasi

1. Nasabah mengunduh aplikasi resmi dari *app store* resmi.
2. Registrasi menggunakan nomor kartu/rekening, data diri, dan OTP yang dikirim ke nomor ponsel terdaftar di bank.
3. Akun diikat ke satu perangkat (*device binding*).
4. Nasabah membuat password/PIN aplikasi sendiri.

### 7.2 Pergantian Perangkat dan Reset Akses

1. Pergantian perangkat memerlukan verifikasi ulang (OTP ke nomor terdaftar dan/atau verifikasi biometrik wajah).
2. Jika nomor ponsel terdaftar sudah tidak aktif, nasabah wajib datang ke cabang untuk perubahan nomor dengan identitas asli.
3. Reset password setelah beberapa kali salah input (ilustratif: 3 kali) dilakukan melalui fitur lupa password atau di cabang.

### 7.3 Blokir Mobile Banking

1. Nasabah dapat meminta blokir melalui Contact Center bila ponsel hilang atau curiga akun diakses pihak lain.
2. Blokir memutus seluruh sesi aktif dan *device binding*.

---

## 8. Sanggahan Transaksi dan Indikasi Fraud

### 8.1 Penerimaan Sanggahan

1. Nasabah melaporkan transaksi yang tidak diakui melalui cabang, Contact Center, atau aplikasi.
2. Petugas **segera memblokir** kartu/akun untuk mencegah kerugian lanjutan.
3. Petugas mencatat kronologi, termasuk apakah nasabah pernah memberikan OTP/PIN atau mengeklik tautan mencurigakan.
4. Laporan dicatat sebagai pengaduan dan ditangani sesuai SOP-LYN-004.

### 8.2 Investigasi

1. Unit Kartu & E-Channel memeriksa log transaksi, perangkat, lokasi, dan rekaman CCTV ATM bila relevan.
2. Unit Anti-Fraud menganalisa indikasi *skimming*, *social engineering*, atau pembobolan sistem.
3. Hasil investigasi menentukan penyelesaian sesuai perjanjian layanan dan ketentuan pelindungan konsumen.

---

## 9. Ringkasan SLA (Ilustratif)

| Tahapan | SLA |
|---|---|
| Blokir darurat kartu/akun melalui Contact Center | Segera, maksimal 5 menit |
| Penggantian kartu instan di cabang | Maksimal 15 menit |
| Reset akses *mobile banking* di cabang | Maksimal 15 menit |
| Penyelesaian sanggahan transaksi | Mengikuti SLA pengaduan (SOP-LYN-004) |

---

## 10. Pengendalian Internal

1. Stok kartu kosong disimpan dengan *dual control* dan direkonsiliasi harian.
2. Kartu tertelan di ATM diambil oleh dua petugas, dicatat, dan dimusnahkan dengan berita acara jika tidak diklaim dalam jangka waktu tertentu.
3. Perubahan nomor ponsel/e-mail nasabah dilaporkan harian dan diuji petik oleh Supervisor.
4. Limit transaksi harian kartu dan *mobile banking* ditetapkan sesuai profil risiko dan dapat diturunkan sementara bila ada indikasi *fraud*.

---

## 11. Pertanyaan yang Sering Diajukan

### Nasabah ditelepon "petugas bank" yang meminta kode OTP, apa yang harus disampaikan?
Jangan berikan OTP kepada siapa pun. Bank tidak pernah meminta OTP, PIN, atau password. Segera hubungi Contact Center resmi dan blokir akun bila OTP sudah terlanjur diberikan.

### Apakah kartu yang hilang lalu ditemukan bisa dipakai lagi?
Tidak. Kartu yang diblokir karena hilang/dicuri diblokir permanen; nasabah perlu mengajukan kartu pengganti.

### Kenapa mobile banking tidak bisa dipakai di ponsel baru?
Karena akun terikat ke perangkat lama. Lakukan verifikasi pergantian perangkat melalui aplikasi atau datang ke cabang bila nomor ponsel lama sudah tidak aktif.

---

## 12. Referensi

- Ketentuan Bank Indonesia tentang penyelenggaraan pemrosesan transaksi pembayaran dan alat pembayaran menggunakan kartu.
- Ketentuan OJK tentang penyelenggaraan teknologi informasi dan layanan perbankan digital oleh bank umum.
- Ketentuan OJK tentang pelindungan konsumen dan masyarakat di sektor jasa keuangan.
- SOP-SMP-001 Pembukaan Rekening Tabungan; SOP-LYN-004 Penanganan Pengaduan Nasabah.

---

## 13. Riwayat Revisi

| Versi | Tanggal | Keterangan |
|---|---|---|
| 1.0 | 2026-09-23 | Penerbitan awal |
