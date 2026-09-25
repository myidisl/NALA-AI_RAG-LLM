# app/jobs.py
# Fungsi job yang dijalankan worker RQ (antrian "ingest", lihat app/queue.py).
# Sengaja TIDAK mengimpor app.main: worker tidak boleh ikut menyalakan FastAPI,
# membuat client Langfuse, atau memuat model reranker.
from app.cache import invalidate_answer_cache
from app.ingest import ingest_document


def ingest_document_job(file_path: str) -> dict:
    """Ingest one knowledge base file into OpenSearch, then clear the answer cache so stale answers are not served."""
    chunks = ingest_document(file_path)
    # Dokumen baru bisa mengubah jawaban, jadi cache dikosongkan SETELAH ingest selesai.
    cache_invalidated = invalidate_answer_cache()
    return {"file": file_path, "chunks": chunks, "cache_invalidated": cache_invalidated}
