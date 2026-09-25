# Business Requirements Document (BRD) — NALA

**Nama Proyek:** NALA (*Not Another Lowkey Assistant*)
**Versi Dokumen:** 2.1
**Tanggal:** 2026-09-24
**Status:** Draft — beberapa bagian berisi asumsi yang perlu dikonfirmasi *business owner* (ditandai ⚠)

**Riwayat Perubahan:**

| Versi | Tanggal | Ringkasan |
|---|---|---|
| 1.0 | 2026-09-23 | MVP asisten tanya-jawab teknologi umum |
| 2.0 | 2026-09-24 | Fokus ke pegawai perbankan; tanya-jawab berbasis dokumen SOP internal (RAG); upload knowledge base; pipeline ingest |
| 2.1 | 2026-09-24 | FR-02, FR-18, NFR-02, NFR-10 terpenuhi (streaming real-time, folder knowledge base persisten & seragam) |

---

## 1. Latar Belakang

Pegawai bank setiap hari membutuhkan jawaban cepat atas dua jenis pertanyaan: **pertanyaan teknologi** (aplikasi kantor, perangkat, sistem perbankan digital, keamanan informasi) dan **pertanyaan prosedur** yang tersebar di banyak dokumen SOP internal. Mencari prosedur secara manual di banyak dokumen memakan waktu, sementara asisten AI berbasis cloud menimbulkan dua hambatan: **biaya berlangganan per token** dan **risiko kerahasiaan data**, karena pertanyaan dan dokumen internal dikirim ke server pihak ketiga.

NALA dibangun untuk menjawab keduanya: asisten AI untuk pegawai perbankan yang berjalan **sepenuhnya di infrastruktur sendiri** (Ollama sebagai runtime model lokal, OpenSearch sebagai penyimpan dokumen) dan mampu menjawab **berdasarkan isi dokumen SOP internal** yang diunggah ke knowledge base.

---

## 2. Tujuan Bisnis

| No | Tujuan | Indikator Keberhasilan ⚠ |
|---|---|---|
| B-1 | Menyediakan akses tanya-jawab teknologi yang cepat dan mudah dipahami lintas peran pegawai bank | Pegawai memperoleh jawaban relevan tanpa perlu berpindah ke mesin pencari |
| B-2 | Mempercepat akses ke prosedur internal (SOP) | Pertanyaan prosedur dijawab dengan merujuk dokumen SOP sumbernya |
| B-3 | Menjaga kerahasiaan data percakapan dan dokumen internal | 0% data percakapan maupun dokumen keluar dari jaringan internal |
| B-4 | Menekan biaya operasional asisten AI | Tidak ada biaya per-token; biaya terbatas pada infrastruktur server |
| B-5 | Knowledge base dapat diperbarui tanpa melibatkan tim pengembang | Dokumen SOP baru dapat diunggah lewat antarmuka web dan langsung dapat ditanyakan |
| B-6 | Menyediakan fondasi teknis yang dapat dikembangkan untuk kebutuhan internal lain | Arsitektur modular; penggantian model cukup lewat *environment variable* |

---

## 3. Ruang Lingkup

### 3.1 Termasuk dalam Lingkup (In Scope)

- Antarmuka web chat berbasis browser
- Tanya-jawab seputar teknologi dan teknologi perbankan
- Tanya-jawab berbasis dokumen SOP internal (RAG), dengan opsi mematikan pencarian dokumen per pertanyaan
- Halaman Knowledge Base: upload dokumen `.md`, `.txt`, `.pdf` dan daftar dokumen tersimpan
- Pipeline ingest dokumen (otomatis saat upload, dan manual melalui Airflow)
- Balasan streaming
- Konteks percakapan multi-giliran (10 pesan terakhir)
- Reset percakapan
- Deployment melalui Docker Compose
- Health check endpoint untuk monitoring

### 3.2 Tidak Termasuk dalam Lingkup (Out of Scope)

- Autentikasi dan manajemen pengguna/hak akses
- Penyimpanan permanen riwayat percakapan
- Pertanyaan di luar topik teknologi dan SOP (secara eksplisit ditolak oleh sistem)
- Pemrosesan data nasabah atau kredensial (nomor rekening, PIN, password, OTP)
- OCR untuk dokumen hasil scan
- Pengelolaan dokumen lanjutan (hapus, versi, persetujuan dokumen)
- Aplikasi mobile native
- Integrasi dengan sistem internal lain (core banking, ticketing, dsb.)
- Dukungan suara (*voice input/output*)

---

## 4. Pemangku Kepentingan ⚠

| Peran | Tanggung Jawab |
|---|---|
| *Business Owner* | Menetapkan tujuan, cakupan, dan prioritas pengembangan |
| Pemilik Dokumen SOP / Unit Kepatuhan | Menyediakan dan memastikan dokumen SOP di knowledge base valid dan terbaru |
| Tim Pengembang | Implementasi, pemeliharaan, dan deployment aplikasi |
| Tim Infrastruktur / IT Ops | Penyediaan server, kapasitas komputasi, OpenSearch, Airflow, dan monitoring |
| Tim Keamanan Informasi | Menilai risiko akses, kerahasiaan dokumen, dan kepatuhan |
| Pengguna Akhir | Pegawai bank: frontliner, staf operasional, marketing/sales, analis, manajemen, tim IT |

---

## 5. Persona Pengguna

| Persona | Karakteristik | Kebutuhan Utama |
|---|---|---|
| **Frontliner** (teller, customer service) | Berinteraksi langsung dengan nasabah, butuh jawaban cepat | Langkah prosedur layanan yang ringkas dan merujuk SOP |
| **Staf Operasional / Back Office** | Menjalankan proses rutin sesuai SOP | Rincian prosedur, syarat dokumen, dan alur persetujuan |
| **Marketing / Sales & Analis** | Mengolah data dan menyiapkan materi | Bantuan aplikasi kantor, pengolahan data, otomasi pekerjaan |
| **Manajemen** | Perlu gambaran ringkas | Penjelasan konsep teknologi perbankan dengan bahasa sederhana |
| **Tim IT Bank** | Mengelola infrastruktur (mis. firewall) | Referensi SOP teknis dan jawaban akurat dengan pengakuan jujur saat model tidak yakin |

---

## 6. Kebutuhan Fungsional

| ID | Kebutuhan | Prioritas | Status |
|---|---|---|---|
| FR-01 | Pengguna dapat mengirim pertanyaan melalui antarmuka web | Wajib | ✅ Selesai |
| FR-02 | Sistem menampilkan jawaban secara bertahap (streaming) tanpa menunggu balasan penuh | Wajib | ✅ Selesai |
| FR-03 | Sistem mempertahankan konteks percakapan sebelumnya saat menjawab | Wajib | ✅ Selesai |
| FR-04 | Sistem membatasi konteks pada 10 pesan terakhir demi menjaga performa | Wajib | ✅ Selesai |
| FR-05 | Pengguna mendapat informasi jumlah pesan dan pemberitahuan saat konteks mulai dipangkas | Sedang | ✅ Selesai |
| FR-06 | Pengguna dapat mereset percakapan dengan konfirmasi terlebih dahulu | Sedang | ✅ Selesai |
| FR-07 | Sistem menolak request yang tidak valid dengan pesan error yang jelas | Wajib | ✅ Selesai (sisi API) |
| FR-08 | Sistem menyediakan endpoint health check | Sedang | ✅ Selesai |
| FR-09 | Jawaban mengikuti persona yang ditetapkan (ramah, gaya Gen-Z, ditutup pantun) | Sedang | ✅ Selesai |
| FR-10 | Sistem menolak menjawab pertanyaan di luar lingkup teknologi dan SOP | Wajib | ✅ Selesai |
| FR-11 | Model dan alamat server dapat dikonfigurasi tanpa mengubah kode | Wajib | ✅ Selesai |
| FR-12 | Sistem menampilkan pesan error yang ramah di UI saat backend gagal merespons | Wajib | ⚠ Sebagian — error HTTP/jaringan sudah tampil; error dari Ollama (mis. model belum di-*pull*) masih menghasilkan balasan kosong |
| FR-13 | Sistem menjawab pertanyaan prosedur berdasarkan dokumen SOP di knowledge base (RAG) | Wajib | ✅ Selesai |
| FR-14 | Pengguna dapat mengaktifkan/menonaktifkan pencarian dokumen per pertanyaan | Sedang | ✅ Selesai |
| FR-15 | Pengguna dapat mengunggah dokumen `.md`, `.txt`, `.pdf` ke knowledge base dan dokumen langsung dapat ditanyakan | Wajib | ✅ Selesai |
| FR-16 | Pengguna dapat melihat daftar dokumen yang ada di knowledge base | Sedang | ✅ Selesai |
| FR-17 | Chat tetap berfungsi (tanpa konteks dokumen) bila layanan pencarian dokumen tidak tersedia | Wajib | ✅ Selesai |
| FR-18 | Seluruh folder knowledge base dapat di-*ingest* ulang melalui pipeline terjadwal/manual | Sedang | ✅ Selesai (manual via DAG Airflow; belum terjadwal) |
| FR-19 | Sistem mengingatkan pengguna untuk tidak membagikan data rahasia nasabah/kredensial | Wajib | ✅ Selesai (melalui system prompt) |
| FR-20 | Jawaban mencantumkan dokumen sumber yang dirujuk | Sedang | ❌ Belum — label sumber hanya dikirim ke model, tidak ditampilkan di UI |
| FR-21 | Pengguna dapat menghapus/memperbarui dokumen di knowledge base | Sedang | ❌ Belum |
| FR-22 | Riwayat percakapan tersimpan dan dapat dibuka kembali setelah halaman ditutup | Rendah | ❌ Belum |
| FR-23 | Pengguna dapat memilih model yang digunakan dari antarmuka | Rendah | ❌ Belum |

---

## 7. Kebutuhan Non-Fungsional

| ID | Kategori | Kebutuhan | Status |
|---|---|---|---|
| NFR-01 | Privasi | Seluruh pemrosesan (LLM, embedding, penyimpanan dokumen) berjalan di infrastruktur internal | ✅ Terpenuhi |
| NFR-02 | Responsivitas | Token pertama jawaban mulai tampil sesegera mungkin melalui mekanisme streaming | ✅ Terpenuhi |
| NFR-03 | Keamanan | Seluruh input pengguna dan output model di-*escape* sebelum ditampilkan untuk mencegah XSS | ✅ Terpenuhi |
| NFR-04 | Keamanan Upload | Nama file disanitasi dan ekstensi divalidasi di server | ✅ Terpenuhi |
| NFR-05 | Portabilitas | Aplikasi dapat dijalankan di lingkungan mana pun melalui Docker Compose | ✅ Terpenuhi |
| NFR-06 | Skalabilitas | Backend chat bersifat *stateless* sehingga dapat di-*scale* horizontal | ✅ Terpenuhi (folder dokumen berupa bind mount; multi-host perlu penyimpanan bersama) |
| NFR-07 | Kemudahan Konfigurasi | Perubahan model/endpoint cukup melalui *environment variable* | ✅ Terpenuhi |
| NFR-08 | Ketersediaan | Endpoint health check tersedia untuk pemantauan otomatis | ✅ Terpenuhi (belum memeriksa Ollama/OpenSearch) |
| NFR-09 | Aksesibilitas | Tampilan responsif di layar sempit dan menghormati preferensi animasi minimal | ✅ Terpenuhi |
| NFR-10 | Persistensi Dokumen | Dokumen yang diunggah tetap tersimpan setelah container dibuat ulang | ✅ Terpenuhi (bind mount `./app/knowledge-base`) |
| NFR-11 | Keamanan Akses | Pembatasan akses aplikasi, halaman upload, dan OpenSearch melalui autentikasi | ❌ Belum |
| NFR-12 | Observabilitas | Logging terstruktur dan metrik penggunaan | ❌ Belum |
| NFR-13 | Ketahanan | Mekanisme retry saat koneksi ke Ollama/OpenSearch gagal | ❌ Belum |

---

## 8. Alur Proses Bisnis

### 8.1 Tanya-Jawab

1. Pengguna membuka halaman NALA di browser.
2. Pengguna mengetik pertanyaan, memilih apakah **Pakai RAG** aktif (default aktif), lalu menekan **Kirim**.
3. Pertanyaan langsung tampil di area percakapan dan disimpan ke riwayat sisi browser; NALA menampilkan indikator "sedang mengetik".
4. Browser mengirim seluruh riwayat percakapan ke backend.
5. Backend memvalidasi request dan memangkas riwayat menjadi 10 pesan terakhir.
6. Jika RAG aktif, backend mencari potongan dokumen SOP yang paling relevan dengan pertanyaan terakhir dan menyisipkannya sebagai konteks. Jika tidak ada dokumen relevan atau layanan pencarian tidak tersedia, model diminta menjawab dari pengetahuan umum dan menyarankan pengunggahan SOP.
7. Backend meneruskan permintaan ke server Ollama.
8. Jawaban dirender bertahap di layar.
9. Setelah jawaban selesai, balasan disimpan ke riwayat sebagai konteks pertanyaan berikutnya.
10. Pengguna dapat melanjutkan percakapan atau menekan **Reset** untuk memulai dari awal.

### 8.2 Pembaruan Knowledge Base

1. Pengguna membuka halaman **Knowledge Base**.
2. Pengguna memilih dokumen SOP (`.md`, `.txt`, `.pdf`) dan menekan **Upload**.
3. Sistem menyimpan dokumen, memecahnya menjadi potongan, membuat embedding, dan menyimpannya ke OpenSearch.
4. Sistem menampilkan jumlah potongan yang ter-index dan memperbarui daftar dokumen. Bila layanan pencarian tidak tersedia, dokumen tetap tersimpan namun belum dapat ditanyakan.
5. Secara terpisah, tim IT dapat menjalankan DAG `ingest_documents` di Airflow untuk meng-*ingest* ulang seluruh folder knowledge base.

---

## 9. Asumsi

| No | Asumsi |
|---|---|
| A-1 | Server Ollama tersedia dan model `llama3.2:3b` serta `nomic-embed-text` telah diunduh sebelum aplikasi digunakan |
| A-2 | Infrastruktur memiliki kapasitas komputasi memadai untuk menjalankan model chat, embedding, OpenSearch, dan Airflow secara lokal |
| A-3 | Aplikasi diakses dari jaringan tepercaya (internal), sehingga autentikasi belum menjadi prioritas |
| A-4 | Pengguna memahami bahwa riwayat percakapan akan hilang saat halaman ditutup |
| A-5 | Dokumen SOP yang diunggah sudah valid, terbaru, dan boleh diakses seluruh pengguna NALA ⚠ |
| A-6 | Jawaban NALA bersifat bantuan; untuk keputusan resmi pengguna tetap merujuk SOP asli atau unit terkait |

---

## 10. Ketergantungan

| No | Ketergantungan | Dampak Bila Tidak Tersedia |
|---|---|---|
| D-1 | Server Ollama aktif dan dapat dijangkau | Aplikasi tidak dapat menghasilkan jawaban maupun meng-*index* dokumen |
| D-2 | Model chat dan model embedding telah di-*pull* ke server Ollama | Chat menghasilkan balasan kosong; RAG dan upload tidak berfungsi |
| D-3 | OpenSearch aktif dan dapat dijangkau | Chat tetap berjalan tanpa konteks dokumen; dokumen upload tersimpan tapi belum ter-index |
| D-4 | Docker & Docker Compose terpasang pada server | Deployment harus dilakukan manual |
| D-5 | Kapasitas RAM/CPU (atau GPU) yang memadai | Latensi jawaban meningkat hingga melewati timeout (120 detik chat, 60 detik embedding) |
| D-6 | Ketersediaan dokumen SOP dalam format teks (bukan hasil scan) | Isi PDF hasil scan tidak dapat dibaca sehingga tidak dapat ditanyakan |

---

## 11. Risiko & Mitigasi

| No | Risiko | Dampak | Mitigasi |
|---|---|---|---|
| R-1 | Model kecil menghasilkan jawaban kurang akurat atau salah mengutip SOP | Tinggi | Konteks diberi label sumber; *system prompt* melarang mengarang fakta; disclaimer di UI untuk mengecek SOP resmi; opsi upgrade model lewat konfigurasi |
| R-2 | Server Ollama mati atau kelebihan beban | Tinggi | Pesan error di UI; perlu retry, deteksi error Ollama, dan health check yang memeriksa dependensi |
| R-3 | Aplikasi, halaman upload, dan OpenSearch tanpa autentikasi diakses/diubah pihak tak berwenang | Tinggi | Batasi akses pada jaringan internal; tambahkan autentikasi dan aktifkan security plugin OpenSearch sebelum rilis |
| R-4 | Dokumen SOP kedaluwarsa atau tidak valid diunggah sehingga jawaban menyesatkan | Tinggi | Tetapkan pemilik dokumen; tambahkan fitur hapus/perbarui dokumen dan alur persetujuan |
| R-5 | Pengguna membagikan data nasabah/kredensial di chat | Tinggi | *System prompt* menolak dan mengingatkan; sosialisasi kepada pengguna; data tidak disimpan di server |
| R-6 | Dokumen upload hilang saat container API dibuat ulang | Rendah | Sudah dimitigasi: folder knowledge base di-bind mount dari host dan dipakai bersama oleh API & Airflow; tetap perlu backup folder `./app/knowledge-base` |
| R-7 | Percakapan panjang menyebabkan konteks awal terpotong | Rendah | Windowing 10 pesan sudah diterapkan dan diinformasikan ke pengguna melalui UI |
| R-8 | Lonjakan pengguna bersamaan menurunkan performa | Sedang | Backend stateless memungkinkan penambahan instance; perlu perencanaan kapasitas Ollama |

---

## 12. Rencana Pengembangan Lanjutan ⚠

| Fase | Fokus | Cakupan |
|---|---|---|
| **Fase 1 — Selesai** | MVP | Chat streaming, windowing konteks, reset, deployment Docker |
| **Fase 2 — Selesai** | Knowledge Base & RAG | Upload dokumen, ingest ke OpenSearch, RAG dengan switch on/off, persona pegawai perbankan, indikator loading, pesan error di UI, redesain tampilan |
| **Fase 3 — Berjalan** | Stabilitas Pipeline | Selesai: streaming real-time dari Ollama, folder knowledge base persisten & seragam untuk API dan Airflow. Sisa: deteksi error Ollama, hapus/perbarui dokumen, retry |
| **Fase 4** | Keamanan & Observabilitas | Autentikasi (termasuk pembatasan halaman upload), security plugin OpenSearch, rate limiting, batas ukuran upload, logging terstruktur, metrik penggunaan |
| **Fase 5** | Pengayaan Fitur | Tampilan sumber dokumen pada jawaban, penyimpanan riwayat, pemilihan model dari UI, OCR untuk PDF hasil scan, jadwal ingest otomatis |

---

## 13. Kriteria Penerimaan

| No | Kriteria | Status |
|---|---|---|
| AC-1 | Pengguna dapat mengirim pertanyaan dan menerima jawaban dari model lokal | ✅ |
| AC-2 | Jawaban tampil secara bertahap, bukan sekaligus setelah selesai | ✅ |
| AC-3 | Pertanyaan lanjutan dijawab dengan mempertimbangkan konteks percakapan sebelumnya | ✅ |
| AC-4 | Request tidak valid ditolak dengan kode status yang tepat | ✅ |
| AC-5 | Aplikasi dapat dijalankan melalui satu perintah `docker compose up` | ✅ |
| AC-6 | Tidak ada data percakapan maupun dokumen yang dikirim ke layanan eksternal | ✅ |
| AC-7 | Dokumen SOP yang diunggah dapat langsung dijadikan rujukan jawaban | ✅ |
| AC-8 | Chat tetap berfungsi saat OpenSearch tidak tersedia | ✅ |
| AC-9 | Pengguna dapat memperoleh jawaban tanpa pencarian dokumen dengan mematikan switch RAG | ✅ |

---

## 14. Dokumen Terkait

- [`spesifikasi.md`](./spesifikasi.md) — spesifikasi teknis, arsitektur, detail API, dan batasan implementasi
