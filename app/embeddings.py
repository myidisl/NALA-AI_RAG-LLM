# app/embeddings.py
# Pembuat embedding teks: mengubah teks menjadi vektor angka melalui model
# embedding di server Ollama, untuk pencarian kemiripan dokumen knowledge base.
import httpx


def embed_text(text: str, base_url: str, model: str = "nomic-embed-text") -> list[float]:
    """POST /api/embed - send text to the Ollama embedding model and return its embedding vector."""
    # Context manager memastikan koneksi HTTP ditutup setelah request selesai.
    with httpx.Client() as client:
        response = client.post(
            f"{base_url}/api/embed",
            json={"model": model, "input": text},
            timeout=60.0,  # timeout dilonggarkan karena model lokal bisa lambat, terutama saat pertama dimuat
        )
        response.raise_for_status()  # lempar exception jika status HTTP menandakan error
        # /api/embed mengembalikan daftar embedding (satu per input);
        # karena input berupa satu teks, ambil vektor pertama.
        return response.json()["embeddings"][0]
