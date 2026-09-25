# app/tools/sql_tool.py
# Tool query data operasional (Postgres nala_operasional) untuk agent — SENGAJA dibatasi:
# LLM hanya memilih dari pilihan tetap (tabel, mode, status, nasabah_id), tidak pernah
# menulis SQL sendiri. Koneksi memakai role nala_readonly (hanya SELECT, lihat app/db.py).
from datetime import date
from decimal import Decimal

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from app.db import get_connection

# Whitelist: nama tabel/kolom di SQL hanya boleh berasal dari sini, bukan dari input LLM.
_ALLOWED_TABLES = {"pengajuan_kredit", "klaim_asuransi"}
_ALLOWED_MODES = {"hitung_per_status", "detail_nasabah"}
# Gabungan status kedua tabel (sesuai CHECK constraint di db/seed.sql):
# pencairan hanya ada di pengajuan_kredit, diproses hanya ada di klaim_asuransi.
_ALLOWED_STATUS = {"pending", "disetujui", "ditolak", "pencairan", "diproses"}
# Batas baris untuk mode detail_nasabah agar hasil tool tidak membanjiri konteks model.
_MAX_ROWS = 20

SQL_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "query_data_operasional",
        "description": (
            "Mengambil DATA operasional dari database: jumlah pengajuan kredit atau klaim "
            "asuransi per status, atau detail transaksi milik satu nasabah (berdasarkan ID "
            "nasabah, mis. NSB0003). Gunakan untuk pertanyaan tentang ANGKA, STATUS, atau DATA "
            "transaksi — bukan untuk aturan/prosedur (untuk itu pakai cari_dokumen_sop)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "tabel": {
                    "type": "string",
                    "enum": ["pengajuan_kredit", "klaim_asuransi"],
                    "description": "Tabel yang ditanyakan: pengajuan_kredit atau klaim_asuransi",
                },
                "mode": {
                    "type": "string",
                    "enum": ["hitung_per_status", "detail_nasabah"],
                    "description": (
                        "hitung_per_status = jumlah data per status (bisa difilter satu status); "
                        "detail_nasabah = daftar data milik satu nasabah (wajib isi nasabah_id)"
                    ),
                },
                "status": {
                    "type": "string",
                    "enum": ["pending", "disetujui", "ditolak", "pencairan", "diproses"],
                    "description": (
                        "Opsional, filter status untuk mode hitung_per_status. pencairan hanya untuk "
                        "pengajuan_kredit; diproses hanya untuk klaim_asuransi"
                    ),
                },
                "nasabah_id": {
                    "type": "string",
                    "description": "ID nasabah, mis. NSB0003. Wajib diisi untuk mode detail_nasabah",
                },
            },
            "required": ["tabel", "mode"],
        },
    },
}


def _format_value(value) -> str:
    """Human-readable cell value: Rupiah with dot thousands separators, ISO dates, '-' for NULL."""
    if value is None:
        return "-"
    if isinstance(value, Decimal):
        return "Rp " + f"{value:,.0f}".replace(",", ".")
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def query_data_operasional(tabel: str, mode: str, status: str | None = None, nasabah_id: str | None = None) -> str:
    """Run one of the fixed, parameterized read-only queries and return the result as readable text (errors are returned as text, never raised)."""
    # Validasi input LLM terhadap whitelist sebelum menyentuh database.
    if tabel not in _ALLOWED_TABLES:
        return f"Tabel '{tabel}' tidak diizinkan. Pilihan: {', '.join(sorted(_ALLOWED_TABLES))}."
    if mode not in _ALLOWED_MODES:
        return f"Mode '{mode}' tidak dikenal. Pilihan: {', '.join(sorted(_ALLOWED_MODES))}."
    if status is not None and status not in _ALLOWED_STATUS:
        return f"Status '{status}' tidak valid. Pilihan: {', '.join(sorted(_ALLOWED_STATUS))}."
    if mode == "detail_nasabah":
        # Model kadang menulis id huruf kecil/berspasi; dinormalkan agar tetap cocok (mis. nsb0003 -> NSB0003).
        nasabah_id = (nasabah_id or "").strip().upper()
        if not nasabah_id:
            return "Parameter nasabah_id wajib diisi untuk mode detail_nasabah (contoh: NSB0003)."

    # Nama tabel sudah lolos whitelist; tetap disisipkan lewat sql.Identifier (di-quote dengan
    # benar), sedangkan semua NILAI dikirim sebagai parameter %s terpisah.
    table = sql.Identifier(tabel)
    try:
        with get_connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            if mode == "hitung_per_status":
                if status:
                    cur.execute(
                        sql.SQL("SELECT status, COUNT(*) AS jumlah FROM {} WHERE status = %s GROUP BY status").format(table),
                        (status,),
                    )
                else:
                    cur.execute(
                        sql.SQL("SELECT status, COUNT(*) AS jumlah FROM {} GROUP BY status ORDER BY jumlah DESC").format(table)
                    )
                rows = cur.fetchall()
                if not rows:
                    return f"Tidak ada data {tabel}" + (f" dengan status '{status}'." if status else ".")
                lines = [f"Jumlah data {tabel} per status:"]
                lines += [f"- {r['status']}: {r['jumlah']}" for r in rows]
                if not status:
                    lines.append(f"Total: {sum(r['jumlah'] for r in rows)}")
                return "\n".join(lines)

            # mode == "detail_nasabah": data terbaru lebih dulu, maksimal _MAX_ROWS baris.
            cur.execute(
                sql.SQL("SELECT * FROM {} WHERE nasabah_id = %s ORDER BY id DESC LIMIT %s").format(table),
                (nasabah_id, _MAX_ROWS),
            )
            rows = cur.fetchall()
    except psycopg.OperationalError:
        return "Database data operasional tidak dapat diakses saat ini. Coba lagi nanti."
    except psycopg.Error as e:
        return f"Query data operasional gagal: {e.diag.message_primary or type(e).__name__}."

    if not rows:
        return f"Tidak ada data {tabel} untuk nasabah {nasabah_id}."
    blocks = [f"Data {tabel} untuk nasabah {nasabah_id} ({len(rows)} baris, maksimal {_MAX_ROWS}):"]
    for r in rows:
        blocks.append("\n".join(f"  {col}: {_format_value(val)}" for col, val in r.items()))
    return "\n\n".join(blocks)
