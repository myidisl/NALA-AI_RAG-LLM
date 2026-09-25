# app/reranker.py
# Reranker berbasis cross-encoder: menilai ulang relevansi kandidat hasil retrieval
# (mis. dari VectorStore.search_hybrid) terhadap pertanyaan, lalu mengambil yang terbaik.
# Berbeda dari embedding (query & dokumen di-encode terpisah), cross-encoder membaca
# pasangan (query, teks) sekaligus sehingga lebih akurat, tapi lebih lambat — karena itu
# hanya dipakai untuk kandidat yang sudah disaring, bukan seluruh index.
from sentence_transformers import CrossEncoder


class Reranker:
    """Wrapper CrossEncoder untuk mengurutkan ulang kandidat berdasarkan relevansi terhadap query."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """Load the cross-encoder model (from the HuggingFace cache at HF_HOME, downloaded if not cached yet)."""
        # Model dimuat sekali saat instansiasi; buat satu instance saja dan pakai ulang.
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, candidates: list[dict], top_k: int = 3) -> list[dict]:
        """Score each candidate's text against the query and return the top_k candidates, each with an added "rerank_score"."""
        if not candidates:
            return []
        # Satu pasangan (query, teks) per kandidat; predict() menilai semuanya dalam satu batch.
        pairs = [(query, c["text"]) for c in candidates]
        scores = self.model.predict(pairs)
        # Salin dict kandidat agar key lama (_id, text, score, metadata, rrf_score) tetap utuh
        # dan hanya ditambah rerank_score; float() mengubah numpy.float32 menjadi float biasa.
        reranked = [{**c, "rerank_score": float(score)} for c, score in zip(candidates, scores)]
        # Skor lebih tinggi = lebih relevan.
        reranked.sort(key=lambda c: c["rerank_score"], reverse=True)
        return reranked[:top_k]
