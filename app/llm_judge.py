# app/llm_judge.py
# LLM-as-judge lokal: model Ollama menilai jawaban RAG pada dua aspek, masing-masing skor 1-5:
# - FAITHFULNESS: seberapa setia jawaban pada konteks (tidak mengarang di luar konteks);
# - RELEVANCE: seberapa tepat jawaban menjawab pertanyaan.
import re

from app.ollama_client import OllamaClient

# CATATAN: teks ini disusun mengikuti spesifikasi Module 21 Langkah 4 (skor 1-5, format keluaran
# persis dua baris), BUKAN salinan teks materi Module 21 Bagian 6 yang tidak tersedia saat
# file ini dibuat. Ganti dengan teks materi bila ingin hasil yang sebanding dengan materi.
JUDGE_SYSTEM_PROMPT = """
Kamu adalah penilai (judge) kualitas jawaban sistem tanya-jawab berbasis dokumen.
Kamu akan menerima KONTEKS (potongan dokumen), PERTANYAAN, dan JAWABAN.

Nilai JAWABAN pada dua aspek, masing-masing dengan skor bilangan bulat 1 sampai 5:

FAITHFULNESS — apakah seluruh isi JAWABAN didukung oleh KONTEKS?
5 = semua pernyataan didukung konteks; 3 = sebagian didukung, sebagian tidak;
1 = sebagian besar tidak ada di konteks atau bertentangan dengan konteks.

RELEVANCE — apakah JAWABAN benar-benar menjawab PERTANYAAN?
5 = menjawab langsung dan lengkap; 3 = menjawab sebagian atau kurang fokus;
1 = tidak menjawab pertanyaan sama sekali.

Jawab HANYA dengan format persis berikut, tanpa penjelasan, teks, atau tanda baca lain:
FAITHFULNESS: <angka>
RELEVANCE: <angka>
""".strip()


def judge_answer(judge_client: OllamaClient, context: str, question: str, answer: str) -> dict:
    """Ask the judge model to score faithfulness and relevance (1-5); return {"faithfulness", "relevance", "raw"} with None for scores that could not be parsed."""
    prompt = f"KONTEKS:\n{context}\n\nPERTANYAAN:\n{question}\n\nJAWABAN:\n{answer}"
    # OllamaClient.generate() memakai signature (model, prompt, system); model judge mengikuti
    # model default client (OLLAMA_MODEL, mis. llama3.2:3b).
    raw = judge_client.generate(model=judge_client.model, prompt=prompt, system=JUDGE_SYSTEM_PROMPT)
    # Model kecil tidak selalu patuh format, jadi setiap skor diparse terpisah dan
    # bernilai None bila tidak ditemukan, bukan diasumsikan selalu ada.
    faithfulness = re.search(r"FAITHFULNESS:\s*(\d)", raw)
    relevance = re.search(r"RELEVANCE:\s*(\d)", raw)
    return {
        "faithfulness": int(faithfulness.group(1)) if faithfulness else None,
        "relevance": int(relevance.group(1)) if relevance else None,
        "raw": raw,
    }
