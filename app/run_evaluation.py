# app/run_evaluation.py
# Skrip evaluasi retrieval: membandingkan hybrid search sebelum dan sesudah reranking
# terhadap test set berlabel (QA_TESTSET) dengan metrik precision@3, hit rate@3, dan MRR.
# Dijalankan manual di container api: docker compose exec api python -m app.run_evaluation
import os

from app.embeddings import embed_text
from app.eval_testset import QA_TESTSET
from app.evaluation import hit_rate_at_k, precision_at_k, reciprocal_rank
from app.reranker import Reranker
from app.vector_store import VectorStore

# Konfigurasi sama dengan main.py agar hasil evaluasi mencerminkan perilaku /chat/stream.
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OPENSEARCH_BASE_URL = os.environ.get("OPENSEARCH_BASE_URL", "http://localhost:9200")
K = 3
# Jumlah kandidat BM25 & k-NN yang digabung RRF; WAJIB sama di kedua skenario agar
# selisih hasil murni berasal dari reranking, bukan dari jumlah kandidat yang berbeda.
CANDIDATE_POOL = 20
# Jumlah kandidat hasil fusion yang diberikan ke reranker (sama seperti pool_size di main.py).
RERANK_POOL = 20


def evaluate(retrieved_fn, label: str) -> dict:
    """Run retrieved_fn on every QA_TESTSET question, print and return the average precision@3, hit_rate@3, and MRR."""
    precisions, hit_rates, rrs = [], [], []
    for item in QA_TESTSET:
        retrieved = retrieved_fn(item["question"])
        precisions.append(precision_at_k(retrieved, item["must_contain"], K))
        hit_rates.append(hit_rate_at_k(retrieved, item["must_contain"], K))
        # reciprocal_rank() tidak punya parameter k, jadi dibatasi manual ke top-K
        # agar ketiga metrik dihitung atas konteks yang sama (yang dikirim ke LLM).
        rrs.append(reciprocal_rank(retrieved[:K], item["must_contain"]))

    n = len(QA_TESTSET)
    result = {
        f"precision@{K}": sum(precisions) / n,
        f"hit_rate@{K}": sum(hit_rates) / n,
        "mrr": sum(rrs) / n,
    }
    print(f"\n== {label} ({n} pertanyaan)")
    for name, value in result.items():
        print(f"  {name:<13} {value:.3f}")
    return result


if __name__ == "__main__":
    vector_store = VectorStore(base_url=OPENSEARCH_BASE_URL, index_name="nala-docs")
    # Model cross-encoder dimuat sekali di sini (dari cache HF_HOME bila sudah di-pre-pull).
    reranker = Reranker()

    def before_rerank(question: str) -> list[dict]:
        """Hybrid search (RRF) top-3 without reranking."""
        embedding = embed_text(question, base_url=OLLAMA_BASE_URL)
        return vector_store.search_hybrid(
            query_text=question, query_embedding=embedding, top_k=K, candidate_pool=CANDIDATE_POOL
        )

    def after_rerank(question: str) -> list[dict]:
        """Hybrid search (RRF) top-20, then cross-encoder reranking down to top-3."""
        embedding = embed_text(question, base_url=OLLAMA_BASE_URL)
        candidates = vector_store.search_hybrid(
            query_text=question, query_embedding=embedding, top_k=RERANK_POOL, candidate_pool=CANDIDATE_POOL
        )
        return reranker.rerank(question, candidates, top_k=K)

    before = evaluate(before_rerank, "Sebelum reranking (hybrid top-3)")
    after = evaluate(after_rerank, "Sesudah reranking (hybrid top-20 -> rerank top-3)")

    # Tabel delta: nilai positif berarti reranking memperbaiki metrik tersebut.
    print(f"\n{'Metrik':<14}{'Sebelum':>10}{'Sesudah':>10}{'Delta':>10}")
    for name in before:
        delta = after[name] - before[name]
        print(f"{name:<14}{before[name]:>10.3f}{after[name]:>10.3f}{delta:>+10.3f}")
