# app/audit.py
# Pencatatan audit log ke tabel audit_log (Postgres nala_operasional, lihat db/seed.sql).
# Memakai role nala_app yang hanya bisa INSERT+SELECT di audit_log (tanpa UPDATE/DELETE,
# tanpa akses ke tabel data operasional), jadi log bersifat append-only dari sisi aplikasi.
import logging
import os

import psycopg

# Default memakai localhost seperti app/db.py; di docker compose, service api perlu
# meng-override ke hostname service "postgres". Password default hanya untuk development lokal.
POSTGRES_APP_DSN = os.environ.get(
    "POSTGRES_APP_DSN",
    "postgresql://nala_app:app_dev_only@localhost:5432/nala_operasional",
)

logger = logging.getLogger("nala.audit")


def log_audit(
    user_id: str,
    role: str,
    pertanyaan: str,
    tool_dipanggil: str | None,
    akses_diizinkan: bool,
    ringkasan_data_diakses: str | None = None,
) -> None:
    """Insert one row into audit_log as role nala_app; a database connection failure is logged, never raised to the caller."""
    try:
        # Keluar dari blok `with` tanpa error otomatis meng-commit transaksi (perilaku psycopg 3).
        with psycopg.connect(POSTGRES_APP_DSN, connect_timeout=5) as conn:
            # Parameter %s (bukan f-string) agar isi pertanyaan user tidak bisa menyisipkan SQL.
            conn.execute(
                "INSERT INTO audit_log "
                "(user_id, role, pertanyaan, tool_dipanggil, akses_diizinkan, ringkasan_data_diakses) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (user_id, role, pertanyaan, tool_dipanggil, akses_diizinkan, ringkasan_data_diakses),
            )
    # psycopg.Error mencakup OperationalError (DB tidak terjangkau) dan juga DataError, mis. nama
    # tool hasil karangan model yang melebihi VARCHAR(50) kolom tool_dipanggil.
    except psycopg.Error as e:
        # Audit log gagal tidak boleh menggagalkan request chat; cukup dicatat di log aplikasi.
        logger.error("Gagal menulis audit_log (user_id=%s, tool=%s): %s", user_id, tool_dipanggil, e)
