# Keamanan, RBAC & Audit — NALA

**Versi Dokumen:** 1.0
**Tanggal:** 2026-09-25
**Pembaca:** tim pengembang, tim keamanan informasi, audit intern

Dokumen ini menjelaskan lapisan keamanan yang ada di NALA, alasan desainnya, dan celah yang masih terbuka. Semua kontrol di bawah ini sudah diimplementasikan dan diuji kecuali yang ditandai **Belum**.

---

## 1. Prinsip Desain

1. **Identitas hanya dari sesi terautentikasi.** `user_id` dan `role` tidak pernah dibaca dari body request, sehingga pengguna tidak bisa "mengaku" sebagai role lain.
2. **RBAC ditegakkan saat eksekusi, bukan saat menawarkan tool.** Semua role melihat semua tool; pembatasan terjadi ketika tool akan dijalankan.
3. **Least privilege di database.** Setiap kebutuhan akses memakai role Postgres sendiri dengan hak seminimal mungkin.
4. **Model tidak pernah menulis SQL.** LLM hanya memilih parameter dari daftar tetap.
5. **Jejak audit append-only.** Aplikasi bisa menambah dan membaca log, tetapi tidak bisa mengubah atau menghapusnya.
6. **Fitur optimasi bersifat fail-open.** Cache dan rate limit tidak boleh membuat NALA berhenti menjawab saat Redis mati.

---

## 2. Autentikasi & Sesi

| Aspek | Implementasi |
|---|---|
| Mekanisme | Starlette `SessionMiddleware` — sesi disimpan di cookie yang ditandatangani (itsdangerous) |
| Secret | `SESSION_SECRET` (env var); fallback `nala-dev-session-secret-change-me` hanya untuk development |
| Masa berlaku | 8 jam (`max_age=8*60*60`) |
| Isi sesi | `user_id`, `role`, `nama` |
| Akun | 5 akun demo di `app/auth.py`, password plaintext `nala123` (**khusus development**) |
| Halaman tanpa sesi | Redirect 303 ke `/login` |
| API tanpa sesi | `401` (`/chat`, `/chat/stream`) |
| Logout | `session.clear()` |

**Catatan:** isi cookie ditandatangani tetapi tidak dienkripsi — jangan menyimpan data rahasia di sesi. Cookie belum diset `https_only` karena lingkungan pengembangan memakai HTTP.

---

## 3. RBAC (Role-Based Access Control)

### 3.1 Matriks Akses

| Kemampuan | staff_umum | staff_finance | supervisor | staff_netsec | spv_netsec |
|---|---|---|---|---|---|
| Login & chat (RAG) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Mode agent — tool dokumen SOP | ✅ | ✅ | ✅ | ✅ | ✅ |
| Mode agent — tool data operasional (SQL) | ❌ | ✅ | ✅ | ❌ | ❌ |
| Upload knowledge base | ✅ | ✅ | ✅ | ✅ | ✅ |
| Halaman data operasional (lihat & tambah) | ✅ | ✅ | ✅ | ✅ | ✅ |

Konstanta: `SQL_ALLOWED_ROLES = {"staff_finance", "supervisor"}` di `app/agent.py`.

> ⚠ Halaman Data Operasional dan halaman upload saat ini hanya mensyaratkan login, belum dibatasi per role. Pembatasan per role baru diterapkan pada tool SQL di mode agent.

### 3.2 Mengapa Semua Role Ditawari Semua Tool

Desain awal menyembunyikan tool SQL dari role yang tidak berwenang. Hasilnya buruk:

- **Halusinasi** — model yang tidak punya tool data tetap "menjawab" pertanyaan data dengan angka karangan.
- **Celah audit** — karena tool tidak pernah dipanggil, percobaan akses data tidak tercatat.

Desain sekarang: tool SQL tetap ditawarkan, tetapi `call_tool` **menolak mengeksekusinya** untuk role tidak berwenang. Model menerima hasil tool:

```
Akses ditolak: role 'staff_umum' tidak berwenang mengakses data operasional (pengajuan kredit /
klaim asuransi). Sampaikan penolakan ini ke user apa adanya dan jangan mengarang data pengganti.
```

Percobaan tersebut dicatat `diizinkan=False` dan masuk audit log. System prompt agent juga mewajibkan pesan penolakan diteruskan apa adanya dan melarang mengarang nama/ID/status/jumlah nasabah.

### 3.3 Aturan Eksekusi di `call_tool`

| Tool diminta | Role | Tindakan | Dicatat |
|---|---|---|---|
| `query_data_operasional` | tidak berwenang / role kosong | Tidak dieksekusi; hasil "Akses ditolak" | `diizinkan: False` |
| `query_data_operasional` | berwenang | Dieksekusi | `diizinkan: True` |
| `cari_dokumen_sop` | semua | Dieksekusi | `diizinkan: True`, `sumber: [...]` |
| Tool tidak dikenal | semua | Tidak dieksekusi | `diizinkan: False` |

Role yang tidak ada di state diperlakukan sebagai tidak berwenang (default aman).

---

## 4. Keamanan Query Data (Tool SQL)

- Tabel hanya dari whitelist `{"pengajuan_kredit", "klaim_asuransi"}`, mode dari `{"hitung_per_status", "detail_nasabah"}`, status dari daftar tetap.
- Nama tabel disisipkan lewat `psycopg.sql.Identifier`; semua nilai lewat parameter `%s`.
- Koneksi memakai role `nala_readonly` (hanya SELECT).
- `detail_nasabah` dibatasi 20 baris.
- Error database dikembalikan sebagai teks ke model, tidak menjatuhkan request.

Form Data Operasional memakai role `nala_writer` (hanya INSERT) dengan parameter `%s`; CHECK constraint di database menolak status di luar daftar.

---

## 5. Role Database

| Role | Hak | Tidak bisa |
|---|---|---|
| `nala_admin` | Pemilik database | – (tidak dipakai aplikasi) |
| `nala_readonly` | SELECT `pengajuan_kredit`, `klaim_asuransi` | INSERT/UPDATE/DELETE; akses `audit_log` |
| `nala_writer` | INSERT kedua tabel (+ sequence) | SELECT, UPDATE, DELETE |
| `nala_app` | INSERT + SELECT `audit_log` (+ sequence) | UPDATE/DELETE `audit_log`; akses tabel data operasional |

Hak `nala_app` sudah diuji: INSERT/SELECT `audit_log` berhasil; UPDATE/DELETE `audit_log`, SELECT `pengajuan_kredit`, dan INSERT `klaim_asuransi` ditolak (`permission denied`).

---

## 6. Audit Log

### 6.1 Apa yang Dicatat

Setiap request `POST /chat` (mode agent) menghasilkan baris di tabel `audit_log`:

| Situasi | Baris yang ditulis |
|---|---|
| Agent memanggil satu atau lebih tool | Satu baris per tool: `tool_dipanggil=<nama>`, `akses_diizinkan=<True/False>` |
| Agent menjawab tanpa tool | Satu baris: `tool_dipanggil=NULL`, `akses_diizinkan=True` |
| Jawaban dari cache | Satu baris: `tool_dipanggil='cache'`, `akses_diizinkan=True` |

`user_id` dan `role` selalu dari sesi. Log ditulis **setelah** jawaban didapat.

### 6.2 Ketahanan

`log_audit()` menangkap `psycopg.Error` dan hanya mencatat ke log aplikasi (`nala.audit`), sehingga kegagalan audit tidak membuat `/chat` gagal. Kekurangannya: baris audit yang gagal ditulis (mis. database mati, nama tool karangan model > 50 karakter) **tidak tersimpan** di tabel.

### 6.3 Yang Belum Tercatat

- `/chat/stream` (mode chat RAG) tidak diaudit — jalur ini tidak mengakses data operasional.
- Kolom `ringkasan_data_diakses` belum diisi.
- Cache hit atas jawaban yang sebelumnya ditolak tercatat `akses_diizinkan = true`. **Keputusan terbuka:** simpan `called_tools` bersama jawaban di cache, atau jangan meng-cache jawaban penolakan.

---

## 7. Cache & Isolasi antar Role

Key cache: `nala:answer:sha256(pertanyaan | role | metode | rerank)`. Role **wajib** menjadi bagian key agar jawaban yang berisi data untuk `staff_finance` tidak pernah disajikan ke `staff_umum` yang menanyakan hal sama. Hal ini sudah diuji: pertanyaan identik dari role berbeda tidak berbagi cache.

Cache hanya dipakai untuk pertanyaan tanpa riwayat (`history` kosong), karena jawaban dengan riwayat bergantung pada percakapan sebelumnya.

---

## 8. Rate Limiting

| Bucket | Endpoint | Batas default |
|---|---|---|
| `chat` | `/chat`, `/chat/stream` (berbagi) | 20 request / 60 detik |
| `upload` | `POST /upload` | 5 / 60 detik |
| `data-operasional` | kedua POST data operasional (berbagi) | 10 / 60 detik (paling ketat karena endpoint tulis) |

- Fixed window per (bucket, IP); `EXPIRE` hanya dipasang saat counter pertama kali dibuat.
- Dihitung sebelum pemeriksaan login (request tanpa login juga menghabiskan kuota).
- **Fail-open** (keputusan sadar): Redis mati → request tetap dilayani.
- ⚠ Di balik Docker/proxy, IP yang terlihat adalah IP gateway (mis. `172.18.0.1`), sehingga semua pengguna berbagi satu kuota. Perbaikan yang disarankan: kunci per `user_id` sesi.

---

## 9. Keamanan Frontend & Upload

| Ancaman | Kontrol |
|---|---|
| XSS dari pesan user | Dirender dengan `textContent` |
| XSS dari jawaban model | Markdown dirender `marked`, lalu disanitasi `DOMPurify` (whitelist tag/atribut) |
| XSS dari nama file sumber | `escapeHtml()` per nama file (diuji dengan nama file `<img src=x onerror=...>`) |
| Library dari CDN | `marked` dan `DOMPurify` disajikan lokal dari `/static/vendor` |
| Path traversal saat upload | `os.path.basename()` pada nama file |
| Tipe file berbahaya | Validasi ekstensi di server (`.md`, `.txt`, `.pdf`) |
| Ukuran upload | **Belum** dibatasi |

---

## 10. Data Sensitif & Privasi

- Semua inferensi, embedding, reranking, dan penyimpanan berjalan lokal.
- Riwayat percakapan hanya di memori browser; server tidak menyimpannya (kecuali pertanyaan mode agent di `audit_log` dan trace di Langfuse lokal).
- System prompt menolak meminta/memproses PIN, password, OTP, nomor rekening.
- Data operasional di lingkungan pengembangan adalah data fiktif.

---

## 11. Celah yang Diketahui & Rekomendasi Sebelum Produksi

| No | Celah | Rekomendasi |
|---|---|---|
| 1 | Akun demo dengan password plaintext | Manajemen pengguna nyata (hash password) atau SSO/LDAP |
| 2 | Secret di `docker-compose.yml` (kunci Langfuse, password role DB, fallback `SESSION_SECRET`) | Pindahkan ke `.env`/secret manager; rotasi kunci |
| 3 | OpenSearch & Dashboards tanpa autentikasi (security plugin dimatikan) | Aktifkan security plugin, TLS |
| 4 | Adminer, RedisInsight, Airflow, Langfuse terbuka di port host | Jangan publikasikan port; batasi lewat jaringan/VPN |
| 5 | Halaman upload & data operasional belum dibatasi per role | Tambahkan pengecekan role di endpoint |
| 6 | Dokumen SOP dapat dibaca semua role | Metadata role per chunk + filter saat retrieval |
| 7 | Rate limit per IP | Kunci per `user_id` |
| 8 | Cookie sesi tanpa `https_only` | Aktifkan HTTPS dan `https_only=True` |
| 9 | Audit cache hit tidak mencerminkan penolakan awal | Simpan `called_tools` di cache atau jangan cache penolakan |
| 10 | Batas ukuran upload belum ada | Batasi di reverse proxy dan di endpoint |
