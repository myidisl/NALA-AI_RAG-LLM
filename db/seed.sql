-- db/seed.sql
-- Skema awal database data operasional NALA (nala_operasional) + dua role akses terpisah.
-- Dijalankan otomatis oleh image Postgres dari /docker-entrypoint-initdb.d/ HANYA sekali,
-- saat volume postgres_data masih kosong. Perubahan file ini setelahnya tidak berlaku
-- sampai volume dihapus (docker volume rm nala_postgres_data).

-- ---------------------------------------------------------------------------
-- Tabel
-- ---------------------------------------------------------------------------

-- Pengajuan kredit nasabah beserta status prosesnya.
CREATE TABLE pengajuan_kredit (
    id                SERIAL PRIMARY KEY,
    nasabah_id        VARCHAR(10),
    nama_nasabah      VARCHAR(100),
    jumlah_pengajuan  NUMERIC(15, 2),
    status            VARCHAR(20) CHECK (status IN ('pending', 'disetujui', 'ditolak', 'pencairan')),
    tanggal_pengajuan DATE,
    alasan_penolakan  TEXT  -- hanya diisi bila status = 'ditolak'
);

-- Klaim asuransi nasabah beserta status prosesnya.
CREATE TABLE klaim_asuransi (
    id            SERIAL PRIMARY KEY,
    nasabah_id    VARCHAR(10),
    nama_nasabah  VARCHAR(100),
    jenis_klaim   VARCHAR(50),
    jumlah_klaim  NUMERIC(15, 2),
    status        VARCHAR(20) CHECK (status IN ('pending', 'diproses', 'disetujui', 'ditolak')),
    tanggal_klaim DATE
);

-- ---------------------------------------------------------------------------
-- Data contoh: FIKTIF dan sengaja minimal (bukan data nasabah sungguhan).
-- Data lain ditambahkan lewat UI.
-- ---------------------------------------------------------------------------

INSERT INTO pengajuan_kredit (nasabah_id, nama_nasabah, jumlah_pengajuan, status, tanggal_pengajuan, alasan_penolakan)
VALUES
    ('NSB0001', 'Contoh Nasabah Satu', 50000000.00,  'pending', '2026-09-01', NULL),
    ('NSB0002', 'Contoh Nasabah Dua',  150000000.00, 'ditolak', '2026-08-20', 'Rasio utang terhadap pendapatan melebihi batas');

INSERT INTO klaim_asuransi (nasabah_id, nama_nasabah, jenis_klaim, jumlah_klaim, status, tanggal_klaim)
VALUES
    ('NSB0001', 'Contoh Nasabah Satu', 'Kesehatan', 7500000.00, 'diproses', '2026-09-10');

-- ---------------------------------------------------------------------------
-- Role akses (prinsip least privilege)
-- Password di bawah HANYA untuk development lokal; ganti sebelum dipakai di luar laptop:
--   ALTER ROLE nala_readonly PASSWORD '<password baru>';
-- ---------------------------------------------------------------------------

-- Hanya bisa MEMBACA kedua tabel (untuk SQL tool / query analitik).
CREATE ROLE nala_readonly LOGIN PASSWORD 'readonly_dev_only';
GRANT CONNECT ON DATABASE nala_operasional TO nala_readonly;
GRANT USAGE ON SCHEMA public TO nala_readonly;
GRANT SELECT ON pengajuan_kredit, klaim_asuransi TO nala_readonly;

-- Hanya bisa MENAMBAH baris baru (untuk input dari UI); tidak bisa membaca, mengubah, atau menghapus.
CREATE ROLE nala_writer LOGIN PASSWORD 'writer_dev_only';
GRANT CONNECT ON DATABASE nala_operasional TO nala_writer;
GRANT USAGE ON SCHEMA public TO nala_writer;
GRANT INSERT ON pengajuan_kredit, klaim_asuransi TO nala_writer;
-- Kolom id SERIAL mengambil nilai dari sequence, jadi INSERT butuh akses ke sequence-nya.
GRANT USAGE, SELECT ON SEQUENCE pengajuan_kredit_id_seq, klaim_asuransi_id_seq TO nala_writer;

-- ---------------------------------------------------------------------------
-- Audit log (Module 27): jejak setiap pertanyaan ke NALA, tool yang dipanggil,
-- dan apakah akses diizinkan RBAC. Append-only dari sisi aplikasi.
-- ---------------------------------------------------------------------------

CREATE TABLE audit_log (
    id                     SERIAL PRIMARY KEY,
    waktu                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    user_id                VARCHAR(50) NOT NULL,  -- dari sesi login (app/auth.py), bukan body request
    role                   VARCHAR(20) NOT NULL,
    pertanyaan             TEXT NOT NULL,
    tool_dipanggil         VARCHAR(50),           -- NULL bila agent tidak memanggil tool
    akses_diizinkan        BOOLEAN NOT NULL,
    ringkasan_data_diakses TEXT                   -- NULL bila tidak ada data yang diakses
);

-- Role aplikasi untuk MENULIS & MEMBACA audit_log saja; sengaja tanpa UPDATE/DELETE agar log
-- tidak bisa diubah/dihapus aplikasi, dan tanpa akses ke pengajuan_kredit/klaim_asuransi.
CREATE ROLE nala_app WITH LOGIN PASSWORD 'app_dev_only';
GRANT CONNECT ON DATABASE nala_operasional TO nala_app;
GRANT USAGE ON SCHEMA public TO nala_app;
GRANT INSERT, SELECT ON audit_log TO nala_app;
GRANT USAGE, SELECT ON SEQUENCE audit_log_id_seq TO nala_app;
