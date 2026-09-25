# app/ingest.py
# Ingest dokumen knowledge base: mengekstrak isi file dokumen
# (misalnya dari folder app/knowledge-base) menjadi teks polos, membuat
# embedding-nya, lalu menyimpannya ke OpenSearch untuk pencarian kemiripan.
import os
import re

from pypdf import PdfReader

from app.embeddings import embed_text
from app.vector_store import VectorStore

# Alamat server Ollama (embedding) dan OpenSearch (vector store); di docker compose
# diisi hostname service, default ke localhost saat dijalankan di luar container.
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OPENSEARCH_BASE_URL = os.environ.get("OPENSEARCH_BASE_URL", "http://localhost:9200")


def extract_text(file_path: str) -> str:
    """Extract the plain-text content of a single document: .pdf via pypdf, any other file read as text."""
    if file_path.endswith(".pdf"):
        # PDF diekstrak per halaman lalu digabung dengan baris baru;
        # halaman tanpa lapisan teks (mis. hasil scan) menghasilkan None,
        # sehingga diganti string kosong. pypdf tidak melakukan OCR.
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    # Selain PDF (mis. .md, .txt) dibaca apa adanya sebagai teks;
    # encoding mengikuti default sistem (UTF-8 di container Linux).
    with open(file_path, "r") as f:
        return f.read()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into fixed-size character chunks, each overlapping the previous one by `overlap` characters."""
    # overlap >= chunk_size membuat posisi awal tidak pernah maju (infinite loop).
    if chunk_size <= 0 or not 0 <= overlap < chunk_size:
        raise ValueError("chunk_size must be > 0 and 0 <= overlap < chunk_size")

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        if end >= len(text):
            # Potongan ini sudah mencakup sisa teks, tidak perlu potongan lagi.
            break
        # Mundur `overlap` karakter dari akhir potongan agar kalimat yang terpotong
        # di batas chunk tetap utuh di salah satu chunk.
        start = end - overlap
    return chunks


def chunk_markdown(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split Markdown text per heading section; sections longer than chunk_size are split further with chunk_text()."""
    chunks = []
    # Pecah tepat sebelum baris heading (# s.d. ######) sehingga tiap section
    # diawali heading-nya sendiri; lookahead membuat heading tidak ikut terbuang.
    for section in re.split(r"\n(?=#{1,6} )", text):
        section = section.strip()
        if not section:
            continue
        if len(section) <= chunk_size:
            chunks.append(section)
        else:
            # Section terlalu panjang: fallback ke fixed-size chunking dengan overlap.
            chunks.extend(chunk_text(section, chunk_size=chunk_size, overlap=overlap))
    return chunks


def ingest_document(file_path: str) -> int:
    """Ingest a single document: extract its text, split it into chunks, embed and index each chunk into OpenSearch (index "nala-docs"); return the number of chunks."""
    store = VectorStore(base_url=OPENSEARCH_BASE_URL, index_name="nala-docs")
    # Aman dipanggil berulang: index hanya dibuat jika belum ada.
    store.ensure_index()
    filename = os.path.basename(file_path)
    content = extract_text(file_path)
    # Markdown dipecah per heading (structure-aware); format lain (.txt, .pdf)
    # dipecah per ukuran tetap karena tidak punya struktur heading yang bisa diandalkan.
    chunks = chunk_markdown(content) if filename.endswith(".md") else chunk_text(content)
    for i, chunk in enumerate(chunks):
        embedding = embed_text(chunk, base_url=OLLAMA_BASE_URL)
        # doc_id = "<nama file>-<urutan chunk>", sehingga ingest ulang file yang sama
        # menimpa chunk lama alih-alih membuat duplikat; metadata.source tetap nama file
        # agar label sumber di konteks chat menunjuk ke dokumen asalnya.
        store.index_document(
            doc_id=f"{filename}-{i}",
            text=chunk,
            embedding=embedding,
            metadata={"source": filename},
        )
    return len(chunks)


def ingest_documents(folder_path: str) -> int:
    """Ingest every .md/.txt/.pdf file in a folder (alphabetical order) and return the number of documents indexed."""
    count = 0
    # sorted() agar urutan ingest konsisten (alfabetis) di semua OS.
    for name in sorted(os.listdir(folder_path)):
        path = os.path.join(folder_path, name)
        # Lewati subfolder dan file dengan ekstensi yang tidak didukung.
        if not os.path.isfile(path) or not name.lower().endswith((".md", ".txt", ".pdf")):
            continue
        ingest_document(path)
        count += 1
    return count
