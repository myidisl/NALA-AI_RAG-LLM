# app/queue.py
# Antrian job RQ di Redis (Module 28). Job di antrian "ingest" dijalankan oleh service worker
# (docker-compose.yml, `rq worker ingest`), bukan oleh proses FastAPI.
import os

from redis import Redis
from rq import Queue

# Koneksi terpisah dari app/cache.py: RQ menyimpan payload job ter-pickle (bytes), jadi tidak
# boleh memakai decode_responses=True seperti client cache.
redis_conn = Redis.from_url(os.environ.get("REDIS_URL", "redis://redis:6379/0"))

# default_timeout 1800 detik (30 menit): ingest PDF besar (embedding per chunk via Ollama) bisa lama.
ingest_queue = Queue("ingest", connection=redis_conn, default_timeout=1800)
