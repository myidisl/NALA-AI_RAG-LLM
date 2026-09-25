# Image dasar Python untuk menjalankan service FastAPI (NALA API).
FROM python:3.12-slim

# Kode ditaruh di /code/app agar import "app.xxx" dan path relatif "app/static"
# di main.py berjalan dengan working directory /code.
WORKDIR /code

# Salin & install dependency lebih dulu agar layer ini bisa di-cache
# selama requirements.txt tidak berubah (mempercepat rebuild).
COPY requirements.txt app/requirements.txt
RUN pip install --no-cache-dir -r app/requirements.txt

# itsdangerous (dibutuhkan SessionMiddleware untuk cookie sesi login) dipasang sebagai layer
# terpisah, bukan lewat requirements.txt, agar layer dependency besar di atas tetap ter-cache.
RUN pip install --no-cache-dir --timeout 120 --retries 10 itsdangerous==2.2.0

# redis (client cache/antrian) dan rq (worker antrian job, dipakai Module 28 Tahap B) juga layer
# terpisah di luar requirements.txt, agar layer dependency besar (torch, dll.) tetap ter-cache.
RUN pip install --no-cache-dir --timeout 120 --retries 10 redis==5.0.8 rq==1.16.2

# Salin sisa source code aplikasi setelah dependency terpasang.
COPY . app/

# Jalankan server FastAPI dengan uvicorn, listen di semua interface port 8000.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
