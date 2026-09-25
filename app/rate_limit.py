# app/rate_limit.py
# Rate limiting per IP berbasis Redis dengan fixed window: tiap jendela RATE_LIMIT_WINDOW detik
# punya satu counter per (bucket, IP). Keputusan sadar: FAIL-OPEN — bila Redis tidak terjangkau,
# request tetap dilayani (rate limit adalah perlindungan tambahan, bukan syarat NALA berjalan).
import os
import time

import redis
from fastapi import HTTPException, Request

# Memakai client yang sama dengan cache jawaban (tanpa koneksi baru).
from app.cache import redis_client

# Batas default per IP per jendela, untuk bucket yang tidak memberi max_requests sendiri.
RATE_LIMIT_MAX = int(os.environ.get("RATE_LIMIT_MAX", "20"))
# Panjang jendela (detik).
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", "60"))


def check_rate_limit(request: Request, bucket: str, max_requests: int | None = None) -> None:
    """Count this request in the (bucket, client IP) window; raise HTTP 429 once the limit is exceeded. Fail-open if Redis is unreachable."""
    limit = max_requests if max_requests is not None else RATE_LIMIT_MAX
    client_ip = request.client.host if request.client else "unknown"
    # Nomor jendela berganti tiap RATE_LIMIT_WINDOW detik, sehingga counter otomatis mulai dari 0.
    window = int(time.time()) // RATE_LIMIT_WINDOW
    key = f"nala:ratelimit:{bucket}:{client_ip}:{window}"
    try:
        count = redis_client.incr(key)
        # TTL hanya dipasang saat key baru dibuat; memasangnya di tiap request akan terus
        # memperpanjang umur key. Key kedaluwarsa sendiri setelah jendelanya lewat.
        if count == 1:
            redis_client.expire(key, RATE_LIMIT_WINDOW)
    except redis.RedisError:
        return
    if count > limit:
        raise HTTPException(
            status_code=429,
            detail=f"Terlalu banyak permintaan. Batasnya {limit} permintaan per {RATE_LIMIT_WINDOW} detik; coba lagi sebentar lagi.",
        )
