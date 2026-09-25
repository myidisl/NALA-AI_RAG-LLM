# app/evaluation.py
# Metrik evaluasi retrieval: precision@k, hit rate@k, dan reciprocal rank (dasar MRR).
# Relevansi ditentukan secara heuristik lewat kata kunci wajib (must_contain), bukan
# ground truth _id, sehingga satu pertanyaan uji bisa dicocokkan ke chunk dari dokumen mana pun.
# Semua fungsi murni: tidak memanggil OpenSearch, Ollama, maupun jaringan apa pun.


def is_relevant(chunk_text: str, must_contain: list[str]) -> bool:
    """Return True if at least half (minimum 1) of the must_contain terms appear in chunk_text, case-insensitive."""
    text = chunk_text.lower()
    # Dicocokkan sebagai substring, jadi istilah multi-kata (mis. "default deny") juga bisa dipakai.
    matches = sum(1 for term in must_contain if term.lower() in text)
    # Ambang separuh istilah (dibulatkan ke bawah, minimal 1) agar chunk yang hanya memuat
    # sebagian kata kunci tetap dianggap relevan, tapi satu kata kebetulan tidak cukup.
    return matches >= max(1, len(must_contain) // 2)


def precision_at_k(retrieved: list[dict], must_contain: list[str], k: int) -> float:
    """Return the fraction of the top-k retrieved chunks that are relevant (0.0 if there are none)."""
    top = retrieved[:k]
    if not top:
        return 0.0
    # Penyebut = jumlah hasil yang benar-benar ada, bukan k, bila hasil lebih sedikit dari k.
    return sum(1 for r in top if is_relevant(r["text"], must_contain)) / len(top)


def hit_rate_at_k(retrieved: list[dict], must_contain: list[str], k: int) -> float:
    """Return 1.0 if at least one of the top-k retrieved chunks is relevant, else 0.0."""
    return 1.0 if any(is_relevant(r["text"], must_contain) for r in retrieved[:k]) else 0.0


def reciprocal_rank(retrieved: list[dict], must_contain: list[str]) -> float:
    """Return 1/rank of the first relevant chunk (rank starts at 1), or 0.0 if none is relevant; average over queries for MRR."""
    for i, r in enumerate(retrieved):
        if is_relevant(r["text"], must_contain):
            return 1.0 / (i + 1)
    return 0.0
