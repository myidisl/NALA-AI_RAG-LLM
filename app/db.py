# app/db.py
# Koneksi ke database data operasional NALA (Postgres nala_operasional, lihat db/seed.sql).
# Dua fungsi terpisah sesuai prinsip least privilege:
# - get_connection()       -> role nala_readonly: hanya SELECT (untuk membaca/menjawab pertanyaan);
# - get_write_connection() -> role nala_writer  : hanya INSERT (untuk input data baru).
# Pemanggil bertanggung jawab menutup koneksi, mis. `with get_connection() as conn: ...`.
import os

import psycopg

# Default memakai localhost agar mudah diakses dari luar container saat debugging;
# di docker compose, service api meng-override ke hostname service "postgres".
# Password default hanya untuk development lokal (sama dengan db/seed.sql).
POSTGRES_READONLY_DSN = os.environ.get(
    "POSTGRES_READONLY_DSN",
    "postgresql://nala_readonly:readonly_dev_only@localhost:5432/nala_operasional",
)
POSTGRES_WRITER_DSN = os.environ.get(
    "POSTGRES_WRITER_DSN",
    "postgresql://nala_writer:writer_dev_only@localhost:5432/nala_operasional",
)


def get_connection() -> psycopg.Connection:
    """Open a read-only connection as role nala_readonly (SELECT only)."""
    # connect_timeout agar request tidak menggantung lama bila Postgres mati/tidak terjangkau.
    return psycopg.connect(POSTGRES_READONLY_DSN, connect_timeout=5)


def get_write_connection() -> psycopg.Connection:
    """Open a write connection as role nala_writer (INSERT only; commit is the caller's responsibility)."""
    return psycopg.connect(POSTGRES_WRITER_DSN, connect_timeout=5)
