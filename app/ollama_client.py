# app/ollama_client.py
# Client sederhana untuk berkomunikasi dengan server Ollama lokal via HTTP:
# chat_stream() untuk /chat/stream, chat() (dengan tools) untuk agent, generate() untuk LLM judge.
import json
import os

import httpx


class OllamaClient:
    """Wrapper HTTP untuk endpoint Ollama: /api/generate (sekali jawab) dan /api/chat (streaming maupun non-streaming dengan tools)."""

    def __init__(self, base_url: str | None = None, model: str | None = None):
        """Initialize the client with the base URL and default model of the Ollama server (env vars OLLAMA_BASE_URL / OLLAMA_MODEL)."""
        # Prioritaskan argumen yang diberikan saat instansiasi, baru jatuh ke
        # environment variable, dan terakhir ke nilai default lokal.
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2:3b")

    def generate(self, model: str, prompt: str, system: str | None = None) -> str:
        """POST /api/generate - send a prompt (with optional system prompt) to the given model and return the generated response text."""
        # stream=False supaya Ollama mengembalikan satu respons JSON utuh,
        # bukan aliran chunk seperti pada chat_stream().
        payload = {"model": model, "prompt": prompt, "stream": False}
        if system:
            # system prompt bersifat opsional, hanya disertakan jika diisi.
            payload["system"] = system
        response = httpx.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=120.0,  # timeout dilonggarkan karena model lokal bisa lambat merespons
        )
        response.raise_for_status()  # lempar exception jika status HTTP menandakan error
        # Field "response" berisi teks lengkap hasil generate model.
        return response.json()["response"]

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """POST /api/chat - non-streaming chat completion with optional tool definitions; return the full assistant message dict."""
        # Non-streaming karena pemanggil (agent) perlu pesan utuh, termasuk tool_calls, sebelum
        # memutuskan langkah berikutnya.
        payload = {"model": self.model, "messages": messages, "stream": False}
        if tools:
            # tools hanya dikirim bila ada; list kosong diperlakukan sama dengan tanpa tools.
            payload["tools"] = tools
        response = httpx.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=60.0,
        )
        response.raise_for_status()  # lempar exception jika status HTTP menandakan error
        # Kembalikan dict "message" utuh ({"role", "content", dan "tool_calls" bila model
        # memanggil tool}), bukan hanya content, agar tool_calls bisa diproses pemanggil.
        return response.json()["message"]

    def chat_stream(self, messages: list[dict]):
        """POST /api/chat - stream a chat completion, yielding message content chunks as they arrive."""
        # stream=True membuat Ollama mengirim respons secara bertahap (baris per baris)
        # sehingga bisa ditampilkan ke user secara real-time.
        # httpx.stream() (bukan httpx.post()) agar body dibaca sambil berjalan; httpx.post()
        # menunggu seluruh respons selesai sehingga token baru terkirim di akhir.
        # Context manager menutup koneksi saat stream selesai atau client memutus request.
        with httpx.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json={"model": self.model, "messages": messages, "stream": True},
            timeout=120.0,
        ) as response:
            # Ollama mengirim NDJSON: setiap baris adalah satu objek JSON berisi potongan balasan.
            for line in response.iter_lines():
                if not line:
                    # lewati baris kosong (biasanya terjadi di antara chunk)
                    continue
                chunk = json.loads(line)
                # Ambil teks dari chunk["message"]["content"]; .get() dipakai agar aman
                # jika chunk tidak memiliki field tersebut (mis. chunk penutup).
                content = chunk.get("message", {}).get("content")
                if content:
                    yield content  # kirim potongan teks ke pemanggil begitu diterima
                if chunk.get("done"):
                    # server menandai akhir stream lewat flag "done"
                    break
