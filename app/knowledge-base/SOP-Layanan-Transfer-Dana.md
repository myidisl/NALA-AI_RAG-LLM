# SOP Layanan Transfer Dana

**Nomor Dokumen:** SOP-LYN-001
**Versi:** 1.0
**Tanggal Berlaku:** 2026-09-23
**Unit Pemilik:** Divisi Operasional dan Sistem Pembayaran
**Status:** Dokumen contoh untuk basis pengetahuan (knowledge base) NALA

> **Catatan:** Dokumen ini merupakan **template acuan umum**, bukan salinan kebijakan resmi institusi tertentu. Batas nominal, jam layanan (*cut-off*), biaya, dan SLA bersifat ilustratif dan wajib diverifikasi terhadap ketentuan Bank Indonesia serta kebijakan internal terbaru sebelum digunakan secara operasional.

---

## 1. Tujuan

1. Menyediakan panduan baku pemrosesan transfer dana keluar dan masuk melalui berbagai kanal.
2. Memastikan pemilihan sarana transfer yang tepat sesuai nominal dan urgensi nasabah.
3. Memastikan setiap transfer diverifikasi dengan benar untuk mencegah salah kirim dan penipuan.
4. Menetapkan penanganan transfer gagal, salah kirim, dan retur.

---

## 2. Ruang Lingkup

Dokumen ini berlaku untuk transfer dana Rupiah yang dilakukan melalui kantor cabang dan kanal elektronik, meliputi:

- Transfer antar-rekening di bank yang sama (pemindahbukuan)
- Transfer antarbank melalui BI-FAST, SKNBI, dan BI-RTGS
- Transfer antarbank *online* melalui jaringan switching (ATM Bersama/Prima dan sejenisnya)
- Penanganan transfer masuk (*incoming*), retur, dan salah transfer

**Tidak termasuk:** pengiriman uang ke/dari luar negeri (remitansi internasional/SWIFT) yang diatur dalam SOP tersendiri.

---

## 3. Definisi

| Istilah | Penjelasan |
|---|---|
| **BI-FAST** | Infrastruktur sistem pembayaran ritel Bank Indonesia yang memproses transfer secara *real time* 24/7 |
| **SKNBI** | Sistem Kliring Nasional Bank Indonesia, diproses per *batch* pada jadwal tertentu |
| **BI-RTGS** | Sistem transfer dana bernilai besar secara *real time* per transaksi |
| **Cut-off** | Batas waktu penerimaan instruksi agar diproses pada hari yang sama |
| **Retur** | Pengembalian dana transfer karena gagal dikreditkan ke rekening tujuan |
| **Proxy Address** | Alias rekening, misalnya nomor ponsel atau e-mail, yang terhubung ke nomor rekening di BI-FAST |
| **Call Back** | Konfirmasi ulang kepada nasabah melalui kontak terdaftar sebelum transaksi diproses |

---

## 4. Pilihan Sarana Transfer Antarbank (Ilustratif)

| Sarana | Batas Nominal per Transaksi | Waktu Dana Diterima | Keterangan |
|---|---|---|---|
| **BI-FAST** | Maksimal Rp250 juta | *Real time* | Beroperasi 24/7, mendukung *proxy address* |
| **SKNBI** | Maksimal Rp1 miliar | Sesuai jadwal *batch* kliring pada hari kerja | Cocok untuk transfer terjadwal/massal |
| **BI-RTGS** | Di atas Rp100 juta | *Real time* pada jam operasional RTGS | Untuk nominal besar dan mendesak |
| **Transfer online (switching)** | Sesuai limit kanal | *Real time* | Umumnya melalui ATM/mobile banking |

> Batas nominal dan jam operasional mengikuti ketentuan Bank Indonesia terbaru dan dapat berubah.

---

## 5. Pihak yang Terlibat

| Peran | Tanggung Jawab Utama |
|---|---|
| **Customer Service / Teller** | Menerima dan memverifikasi formulir transfer di cabang |
| **Supervisor Layanan** | Otorisasi transfer di atas limit petugas dan pelaksanaan *call back* |
| **Unit Operasional Sistem Pembayaran** | Memproses transfer keluar/masuk, retur, dan rekonsiliasi |
| **Unit Anti-Fraud** | Menganalisa transaksi transfer yang terindikasi penipuan |

---

## 6. Alur Transfer Dana Keluar melalui Cabang

### Tahap 1 — Penerimaan Instruksi

1. Nasabah mengisi formulir transfer dengan lengkap: rekening sumber, nama dan nomor rekening penerima, bank tujuan, nominal, dan berita transfer.
2. Petugas mencocokkan tanda tangan dengan spesimen dan identitas nasabah.
3. Petugas membantu memilih sarana transfer yang sesuai nominal dan urgensi.

### Tahap 2 — Verifikasi

1. Untuk BI-FAST/transfer *online*, petugas melakukan pengecekan nama pemilik rekening tujuan (*account inquiry*) dan meminta nasabah memastikan kecocokan nama.
2. Transfer bernilai besar (ilustratif: di atas Rp500 juta) atau tidak sesuai profil nasabah wajib dilakukan *call back* dan dicatat.
3. Petugas mewaspadai indikasi penipuan, misalnya nasabah lanjut usia yang diarahkan pihak lain melalui telepon untuk mentransfer dana; bila ada indikasi, petugas memberikan edukasi dan meminta persetujuan Supervisor sebelum memproses.

### Tahap 3 — Pemrosesan

1. Petugas menginput transaksi; Supervisor melakukan otorisasi sesuai limit.
2. Instruksi yang diterima setelah *cut-off* SKNBI/RTGS diproses pada hari kerja berikutnya, kecuali nasabah memilih BI-FAST.
3. Nasabah menerima bukti transaksi berisi nomor referensi.

---

## 7. Penanganan Transfer Masuk dan Retur

1. Transfer masuk dikreditkan otomatis bila nomor dan nama rekening sesuai.
2. Transfer masuk yang nomor rekeningnya tidak ditemukan, rekening tutup, atau nama sangat berbeda ditahan di rekening penampungan dan diretur ke bank pengirim sesuai ketentuan sistem terkait.
3. Retur transfer keluar dikreditkan kembali ke rekening nasabah pengirim dan nasabah diberi notifikasi.

---

## 8. Penanganan Salah Transfer

1. Nasabah melapor dengan bukti transaksi.
2. Jika rekening tujuan berada di bank yang sama, bank menghubungi penerima dan meminta persetujuan pengembalian dana; bank **tidak boleh** mendebit rekening penerima tanpa persetujuan atau dasar hukum yang sah.
3. Jika rekening tujuan di bank lain, bank mengirim surat permohonan pengembalian dana ke bank penerima.
4. Nasabah diinformasikan bahwa penerima yang sengaja menguasai dana salah transfer dapat dikenakan sanksi pidana sesuai peraturan tentang transfer dana.
5. Laporan salah transfer terkait penipuan ditangani Unit Anti-Fraud dan dapat dilakukan pemblokiran sementara sesuai ketentuan.

---

## 9. Ringkasan SLA (Ilustratif)

| Tahapan | SLA |
|---|---|
| Pemrosesan transfer di cabang (dokumen lengkap) | Maksimal 15 menit |
| Pengkreditan retur transfer keluar | Maksimal 1 hari kerja setelah retur diterima |
| Pengiriman surat permohonan pengembalian salah transfer | Maksimal 1 hari kerja setelah laporan |
| Tanggapan awal atas laporan salah transfer | Maksimal 2 hari kerja |

---

## 10. Pengendalian Internal

1. Limit otorisasi transfer diatur berjenjang sesuai jabatan.
2. Rekonsiliasi harian antara transaksi di *core banking* dan laporan settlement BI-FAST/SKNBI/RTGS.
3. Instruksi transfer melalui faksimili atau e-mail hanya dapat diproses untuk nasabah yang memiliki perjanjian khusus dan wajib *call back*.
4. Transfer dari rekening nasabah berisiko tinggi dipantau sesuai SOP-KPT-001.

---

## 11. Pertanyaan yang Sering Diajukan

### Mengapa transfer lewat SKN belum masuk padahal sudah ditransfer pagi hari?
SKNBI diproses per jadwal *batch* pada hari kerja, sehingga dana diterima sesuai jadwal kliring, tidak *real time*. Untuk dana cepat gunakan BI-FAST atau RTGS.

### Apakah bank bisa langsung menarik kembali dana yang salah transfer?
Tidak secara sepihak. Pengembalian memerlukan persetujuan penerima atau dasar hukum yang sah; bank membantu melalui mekanisme permohonan pengembalian dana.

### Apa itu proxy address pada BI-FAST?
Alias seperti nomor ponsel atau e-mail yang didaftarkan nasabah dan terhubung ke nomor rekening, sehingga pengirim cukup memasukkan alias tersebut.

---

## 12. Referensi

- Undang-Undang tentang Transfer Dana.
- Ketentuan Bank Indonesia tentang BI-FAST, SKNBI, dan BI-RTGS.
- Ketentuan OJK tentang pelindungan konsumen dan masyarakat di sektor jasa keuangan.
- SOP-KPT-001 Penerapan APU-PPT; SOP-LYN-004 Penanganan Pengaduan Nasabah.

---

## 13. Riwayat Revisi

| Versi | Tanggal | Keterangan |
|---|---|---|
| 1.0 | 2026-09-23 | Penerbitan awal |
