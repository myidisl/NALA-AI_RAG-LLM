# app/cache.py
# Cache jawaban NALA di Redis (service redis di docker-compose.yml). Cache hanya optimasi:
# setiap error Redis ditelan di sini agar Redis mati tidak membuat NALA gagal menjawab.
import hashlib
import os

import redis

# Default memakai hostname service "redis" dalam network compose.
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
# Umur jawaban di cache (detik); setelah itu key kedaluwarsa otomatis.
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "3600"))

# decode_responses=True: nilai dikembalikan sebagai str, bukan bytes.
# Instansiasi tidak membuka koneksi, jadi aman walau Redis belum siap saat startup.
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def _answer_key(question: str, role: str, search_method: str, use_reranking: bool) -> str:
    """Build the cache key from everything that changes the answer; role is included so answers never leak across roles (RBAC)."""
    raw = "|".join([question, role, search_method, str(use_reranking)])
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"nala:answer:{digest}"


def get_cached_answer(question: str, role: str, search_method: str, use_reranking: bool) -> str | None:
    """Return the cached answer, or None on a miss or if Redis is unreachable."""
    try:
        return redis_client.get(_answer_key(question, role, search_method, use_reranking))
    except redis.RedisError:
        return None


def set_cached_answer(question: str, role: str, search_method: str, use_reranking: bool, answer: str) -> None:
    """Store the answer with a TTL of CACHE_TTL_SECONDS; silently skipped if Redis is unreachable."""
    try:
        # setex menyimpan nilai dan TTL secara atomik (bukan set() lalu expire()).
        redis_client.setex(_answer_key(question, role, search_method, use_reranking), CACHE_TTL_SECONDS, answer)
    except redis.RedisError:
        pass


def invalidate_answer_cache() -> int:
    """Delete every cached answer and return how many keys were removed (0 if none or Redis is unreachable)."""
    try:
        # scan_iter menelusuri key bertahap; KEYS akan memblokir Redis selama pencarian.
        keys = list(redis_client.scan_iter(match="nala:answer:*", count=100))
        if not keys:
            return 0
        return redis_client.delete(*keys)
    except redis.RedisError:
        return 0
