# app/vector_store.py
# Penyimpanan vektor berbasis OpenSearch: menyimpan potongan teks knowledge base
# beserta embedding-nya, lalu mencari dokumen paling mirip lewat k-NN search.
# Diakses langsung via REST API OpenSearch memakai httpx (tanpa opensearch-py).
from urllib.parse import quote

import httpx


class VectorStore:
    """Wrapper REST API OpenSearch untuk satu index: buat index, simpan chunk, dan k-NN search."""

    def __init__(self, base_url: str, index_name: str):
        """Initialize the store with the OpenSearch base URL (e.g. OPENSEARCH_BASE_URL) and the target index name."""
        # Buang trailing slash agar penggabungan URL tidak menghasilkan "//".
        self.base_url = base_url.rstrip("/")
        self.index_name = index_name

    def ensure_index(self, dims: int = 768) -> None:
        """HEAD /{index} - create the index with a knn_vector mapping of the given dimension if it does not exist yet."""
        index_url = f"{self.base_url}/{self.index_name}"
        with httpx.Client() as client:
            # HEAD mengembalikan 200 jika index sudah ada, 404 jika belum.
            response = client.head(index_url, timeout=30.0)
            if response.status_code == 200:
                return
            if response.status_code != 404:
                response.raise_for_status()  # status lain berarti ada masalah di server

            body = {
                # index.knn wajib true agar field knn_vector bisa dipakai untuk k-NN search.
                "settings": {"index": {"knn": True}},
                "mappings": {
                    "properties": {
                        "text": {"type": "text"},  # isi potongan teks (full-text)
                        "embedding": {
                            "type": "knn_vector",
                            # Harus sama dengan panjang vektor dari model embedding
                            # (nomic-embed-text menghasilkan 768 dimensi).
                            "dimension": dims,
                            "method": {
                                "name": "hnsw",  # algoritma approximate nearest neighbor berbasis graf
                                "space_type": "cosinesimil",  # kemiripan kosinus, cocok untuk embedding teks
                                "engine": "nmslib",  # library k-NN yang dipakai OpenSearch
                            },
                        },
                        "metadata": {"type": "object"},  # info tambahan, mis. {"source": nama file}
                    }
                },
            }
            # PUT /{index} membuat index baru dengan settings & mapping di atas.
            response = client.put(index_url, json=body, timeout=30.0)
            response.raise_for_status()

    def index_document(self, doc_id: str, text: str, embedding: list[float], metadata: dict) -> None:
        """PUT /{index}/_doc/{doc_id} - store (or overwrite) a text chunk with its embedding and metadata."""
        # doc_id di-quote (termasuk "/") karena bisa berisi nama file/path yang merusak URL.
        url = f"{self.base_url}/{self.index_name}/_doc/{quote(doc_id, safe='')}"
        with httpx.Client() as client:
            response = client.put(
                url,
                json={"text": text, "embedding": embedding, "metadata": metadata},
                # refresh=true agar dokumen langsung bisa dicari tanpa menunggu refresh interval.
                params={"refresh": "true"},
                timeout=30.0,
            )
            response.raise_for_status()

    def search(self, query_embedding: list[float], top_k: int = 3) -> list[dict]:
        """POST /{index}/_search - run a k-NN query and return the top_k hits as {_id, text, score, metadata}."""
        # "k" = jumlah tetangga terdekat yang dicari di index k-NN,
        # "size" = jumlah hit yang dikembalikan di response.
        body = {
            "size": top_k,
            "query": {"knn": {"embedding": {"vector": query_embedding, "k": top_k}}},
        }
        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/{self.index_name}/_search",
                json=body,
                timeout=30.0,
            )
            response.raise_for_status()
            hits = response.json()["hits"]["hits"]  # sudah terurut dari skor kemiripan tertinggi
        # Ratakan struktur hit OpenSearch menjadi dict sederhana untuk pemanggil.
        # _id disertakan (sama seperti search_bm25()) agar chunk yang sama bisa dicocokkan
        # antar daftar hasil vector dan BM25.
        return [
            {
                "_id": hit["_id"],
                "text": hit["_source"].get("text", ""),
                "score": hit["_score"],
                "metadata": hit["_source"].get("metadata", {}),
            }
            for hit in hits
        ]

    def search_bm25(self, query_text: str, top_k: int = 10) -> list[dict]:
        """POST /{index}/_search - run a BM25 full-text match query on "text" and return the top_k hits as {_id, text, score, metadata}."""
        # Query "match" memakai skor BM25 bawaan OpenSearch pada field "text" (tipe text
        # di mapping ensure_index()), jadi tidak butuh embedding maupun reindex.
        body = {
            "size": top_k,
            "query": {"match": {"text": query_text}},
        }
        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/{self.index_name}/_search",
                json=body,
                timeout=30.0,
            )
            response.raise_for_status()
            hits = response.json()["hits"]["hits"]  # sudah terurut dari skor BM25 tertinggi
        # _id ikut dikembalikan sebagai identitas unik chunk ("<nama file>-<urutan>"),
        # untuk mencocokkan hasil yang sama antar daftar hasil pencarian yang berbeda.
        return [
            {
                "_id": hit["_id"],
                "text": hit["_source"].get("text", ""),
                "score": hit["_score"],
                "metadata": hit["_source"].get("metadata", {}),
            }
            for hit in hits
        ]

    def search_hybrid(
        self,
        query_text: str,
        query_embedding: list[float],
        top_k: int = 3,
        candidate_pool: int = 20,
        rrf_k: int = 60,
    ) -> list[dict]:
        """Combine BM25 and k-NN results with Reciprocal Rank Fusion; return the top_k hits as {_id, text, score, metadata, rrf_score}."""
        # Ambil kandidat lebih banyak dari top_k di kedua metode, supaya dokumen yang
        # peringkatnya sedang di salah satu daftar tetap berkesempatan naik setelah fusion.
        bm25_results = self.search_bm25(query_text, top_k=candidate_pool)
        vector_results = self.search(query_embedding, top_k=candidate_pool)

        # RRF hanya memakai peringkat, bukan skor mentah, karena skor BM25 (tak terbatas)
        # dan cosine similarity (0..1) tidak sebanding. Tiap daftar menyumbang
        # 1 / (rrf_k + peringkat), peringkat mulai dari 1; rrf_k meredam dominasi peringkat teratas.
        fused_scores: dict[str, float] = {}
        for results in (bm25_results, vector_results):
            for rank, hit in enumerate(results):
                fused_scores[hit["_id"]] = fused_scores.get(hit["_id"], 0.0) + 1.0 / (rrf_k + rank + 1)

        # Simpan satu versi hit per _id; versi BM25 diutamakan, hasil vector hanya
        # mengisi _id yang belum ada (setdefault tidak menimpa).
        doc_lookup: dict[str, dict] = {}
        for hit in bm25_results:
            doc_lookup.setdefault(hit["_id"], hit)
        for hit in vector_results:
            doc_lookup.setdefault(hit["_id"], hit)

        # Urutkan menurun berdasarkan skor gabungan; jumlah hasil bisa kurang dari top_k
        # bila kandidat unik dari kedua daftar lebih sedikit.
        top_ids = sorted(fused_scores, key=fused_scores.get, reverse=True)[:top_k]
        # "score" tetap skor asli dari metode sumber hit; "rrf_score" adalah skor gabungan.
        return [{**doc_lookup[doc_id], "rrf_score": fused_scores[doc_id]} for doc_id in top_ids]
