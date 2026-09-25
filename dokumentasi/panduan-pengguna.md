# Panduan Pengguna — NALA

**Versi Dokumen:** 1.0
**Tanggal:** 2026-09-25
**Pembaca:** pegawai pengguna NALA

NALA adalah asisten AI internal PT Nusantara Finance. NALA bisa menjawab pertanyaan teknologi, menjelaskan isi SOP internal, dan (untuk role tertentu) menjawab pertanyaan data operasional seperti jumlah pengajuan kredit per status.

> NALA bisa keliru. Untuk keputusan resmi, selalu cek kembali ke SOP internal atau unit terkait.

---

## 1. Masuk ke NALA

1. Buka `http://localhost:8000` (atau alamat yang diberikan tim IT).
2. Masukkan **username** dan **password**, lalu klik **Login**.
3. Di bagian atas akan tampil *"Masuk sebagai <nama> [<role>] · Logout"*.
4. Klik **Logout** bila selesai. Sesi otomatis berakhir setelah 8 jam.

Akun demo (password `nala123`):

| Username | Role | Cocok untuk mencoba |
|---|---|---|
| `budi.umum` | Staff Umum | Pertanyaan SOP pengadaan & aset; melihat penolakan akses data |
| `sari.finance` | Staff Finance | Pertanyaan SOP kredit dan data operasional |
| `andi.super` | Supervisor | Semua pertanyaan, termasuk data operasional |
| `thoriq.netsec` | Staff NetSec | SOP firewall & keamanan siber |
| `zein.netsec` | Supervisor NetSec | SOP firewall, persetujuan perubahan |

---

## 2. Halaman Chat

### 2.1 Mengirim Pertanyaan

Ketik pertanyaan di kotak **"Tanya NALA dong.."** lalu tekan Enter atau tombol panah. Pertanyaan Anda tampil sebagai bubble di kanan; jawaban NALA muncul di kiri. Selama NALA berpikir, tampil tiga titik yang bergerak.

### 2.2 Pengaturan di Bawah Kotak Pertanyaan

| Switch | Fungsi | Kapan dipakai |
|---|---|---|
| **Pakai RAG (cari dari dokumen)** | NALA mencari jawaban di dokumen SOP | Aktifkan untuk pertanyaan prosedur/kebijakan; matikan untuk pertanyaan umum |
| **BM25 (kata kunci)** / **Vector (makna)** | Metode pencarian dokumen. Keduanya aktif = Hybrid | BM25 saja biasanya paling tepat untuk istilah spesifik (mis. nama SOP, kode dokumen) |
| **Rerank hasil (cross-encoder)** | Menilai ulang dokumen yang ditemukan agar yang paling relevan dipakai | Aktif secara default; sedikit lebih lambat |
| **Pakai Agent (RAG + SQL tool)** | NALA memilih sendiri: cari di SOP, ambil data operasional, atau keduanya | Pertanyaan data (angka, status, nasabah tertentu) atau campuran SOP + data |

Saat **Pakai Agent** aktif, switch pencarian di atasnya diredupkan karena agent mengatur pencarian sendiri.

### 2.3 Mode Agent: Badge dan Sumber

Jawaban mode agent dilengkapi:

- **Sumber dokumen** — daftar file SOP yang dipakai sebagai rujukan. Klik nama file untuk membuka dokumennya di tab baru (Markdown/teks tampil sebagai teks biasa, PDF tampil di penampil PDF browser).
- **Badge**:
  - 📄 **Dokumen SOP** — jawaban memakai pencarian dokumen.
  - 🗄️ **Data operasional** — jawaban memakai data dari database.
  - ⚡ **Dari cache** — pertanyaan yang sama pernah dijawab untuk role Anda dalam 1 jam terakhir, jadi jawabannya diambil langsung (lebih cepat). Jawaban dari cache tidak menampilkan daftar sumber.

### 2.4 Pertanyaan Data Operasional

Hanya **Staff Finance** dan **Supervisor** yang dapat memperoleh data operasional. Role lain akan menerima jawaban *"Akses ditolak: ..."* — ini bukan error, melainkan pembatasan akses. Setiap pertanyaan mode agent tercatat di audit log.

Contoh pertanyaan:
- "Berapa jumlah pengajuan kredit per status?"
- "Berapa klaim asuransi yang masih pending?"
- "Tampilkan data pengajuan kredit nasabah NSB0003."
- "Apa syarat KPR, dan berapa pengajuan kredit yang ditolak?" (campuran SOP + data)

### 2.5 Riwayat & Reset

- NALA mengingat percakapan selama halaman terbuka; hanya **10 pesan terakhir** yang dipakai sebagai konteks (akan muncul catatan bila batas tercapai).
- Tombol **Reset** menghapus percakapan (dengan konfirmasi).
- Menutup atau me-*refresh* halaman menghapus riwayat.

### 2.6 Tampilan

- **Tema gelap** aktif otomatis bila perangkat/browser Anda memakai mode gelap.
- Di ponsel, pengaturan di bawah kotak pertanyaan tersusun satu kolom.

---

## 3. Halaman Knowledge Base

1. Klik **Knowledge Base** di menu atas.
2. Pilih file `.md`, `.txt`, atau `.pdf`, lalu klik **Upload**.
3. Muncul pesan *"… sedang diproses di background (job ID: …)"*. Dokumen dapat ditanyakan setelah proses selesai (biasanya beberapa detik hingga beberapa menit, tergantung ukuran).
4. File dengan nama sama akan **menimpa** file lama.

Tips:
- PDF hasil scan (gambar) tidak bisa dibaca; gunakan PDF berisi teks.
- Dokumen Markdown dengan heading (`#`, `##`) menghasilkan jawaban yang lebih tepat karena dipotong per bagian.
- Maksimal 5 upload per menit.

---

## 4. Halaman Data Operasional

1. Klik **Data Operasional** di menu atas.
2. Isi form **Pengajuan Kredit** atau **Klaim Asuransi**, lalu simpan.
3. Data baru tampil di baris teratas tabel. Tabel menampilkan 10 baris per halaman; gunakan nomor halaman di bawah tabel.

Aturan isian:
- **Status pengajuan kredit:** pending, disetujui, ditolak, pencairan. Isi **alasan penolakan** hanya bila status *ditolak*.
- **Status klaim asuransi:** pending, diproses, disetujui, ditolak.
- ID nasabah maksimal 10 karakter (mis. `NSB0051`).
- Maksimal 10 penyimpanan per menit.

---

## 5. Pesan yang Mungkin Muncul

| Pesan | Arti | Yang perlu dilakukan |
|---|---|---|
| "Username atau password salah." | Login gagal | Periksa kembali username/password |
| "Akses ditolak: role ... tidak berwenang ..." | Role Anda tidak boleh melihat data operasional | Hubungi atasan/Staff Finance bila membutuhkan data |
| "Terlalu banyak permintaan. Batasnya ..." | Batas permintaan per menit tercapai | Tunggu sekitar 1 menit |
| "Gagal mendapatkan balasan (...). Coba lagi." | Server/koneksi bermasalah atau sesi berakhir (HTTP 401) | Coba lagi; bila 401, login ulang |
| "... belum masuk antrian proses (Redis belum terjangkau)" | File tersimpan tapi belum diproses | Upload ulang nanti atau hubungi tim IT |
| "Database data operasional tidak terjangkau" | Database sedang bermasalah | Hubungi tim IT |

---

## 6. Etika Penggunaan

- Jangan memasukkan PIN, password, OTP, atau nomor rekening ke chat.
- Gunakan data nasabah hanya untuk keperluan pekerjaan.
- Jawaban NALA adalah bantuan; untuk keputusan resmi, rujuk dokumen SOP asli.
