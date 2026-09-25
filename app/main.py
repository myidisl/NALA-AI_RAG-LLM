# app/main.py
# Entry point FastAPI aplikasi NALA. Berisi:
# - Login/sesi (SessionMiddleware + app/auth.py): semua halaman & endpoint wajib login;
#   user_id dan role SELALU dibaca dari sesi, tidak pernah dari body request.
# - POST /chat/stream : chat streaming dengan RAG (vector/BM25/hybrid + reranking opsional).
# - POST /chat        : mode agent (LangGraph, app/agent.py) dengan tool SOP & SQL, RBAC per role,
#                       audit log (app/audit.py), cache jawaban Redis (app/cache.py), badge tool,
#                       dan lampiran dokumen sumber.
# - GET/POST /upload  : knowledge base; ingest dijalankan worker RQ di background (app/queue.py).
# - /data-operasional : input & daftar data pengajuan kredit / klaim asuransi (Postgres).
# - Rate limiting per IP berbasis Redis (app/rate_limit.py) di endpoint chat, upload, dan tulis data.
# - Observability: setiap request chat dicatat sebagai trace Langfuse.
import os
from datetime import date
from decimal import Decimal
from typing import Literal

import httpx
import psycopg
import redis
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from langfuse import Langfuse
from psycopg.rows import dict_row
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from app.agent import build_agent
from app.audit import log_audit
from app.cache import get_cached_answer, set_cached_answer
from app.auth import get_current_user, verify_user
from app.db import get_connection, get_write_connection
from app.embeddings import embed_text
from app.ollama_client import OllamaClient
from app.queue import ingest_queue
from app.rate_limit import check_rate_limit
from app.reranker import Reranker
from app.system_prompt import (
    NALA_SYSTEM_PROMPT_AGENT,
    NALA_SYSTEM_PROMPT_NO_CONTEXT,
    NALA_SYSTEM_PROMPT_RAG_OFF,
    SYSTEM_PROMPT,
)
from app.vector_store import VectorStore

app = FastAPI(title="NALA")
# Sesi login disimpan di cookie yang ditandatangani (butuh paket itsdangerous, lihat Dockerfile).
# Secret dibaca dari env var SESSION_SECRET; fallback hanya untuk development. Sesi berlaku 8 jam.
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET", "nala-dev-session-secret-change-me"),
    max_age=8 * 60 * 60,
)
# Sajikan file statis (CSS, logo) di URL /static/...; path relatif terhadap
# working directory, sehingga server harus dijalankan dari root project (lihat Dockerfile).
app.mount("/static", StaticFiles(directory="app/static"), name="static")
# Engine template Jinja2 untuk me-render halaman HTML di app/templates.
templates = Jinja2Templates(directory="app/templates")
# Alamat server Ollama; disimpan sebagai konstanta modul karena dipakai ulang
# oleh ollama_client dan oleh retrieval (embed_text) untuk knowledge base.
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
ollama_client = OllamaClient(base_url=OLLAMA_BASE_URL)  # model tetap diambil dari env var (lihat OllamaClient)

# Vector store OpenSearch berisi dokumen knowledge base hasil ingest (lihat ingest.py).
# Instansiasi tidak melakukan request, jadi aman walau OpenSearch belum siap saat startup.
OPENSEARCH_BASE_URL = os.environ.get("OPENSEARCH_BASE_URL", "http://localhost:9200")
vector_store = VectorStore(base_url=OPENSEARCH_BASE_URL, index_name="nala-docs")

# Reranker cross-encoder untuk mengurutkan ulang kandidat retrieval (lihat reranker.py).
# Bisa dimatikan tanpa ubah kode lewat env var RERANK_ENABLED=false; saat mati, model
# tidak dimuat sama sekali. Saat aktif, model dimuat sekali di startup (cache di HF_HOME).
RERANK_ENABLED = os.environ.get("RERANK_ENABLED", "true").lower() == "true"
reranker = Reranker() if RERANK_ENABLED else None

# Client Langfuse untuk observability (trace retrieval & generate). Kredensial dibaca dari
# env var yang di-set di docker-compose.yml; instansiasi tidak melakukan request, dan data
# trace dikirim di background thread sehingga tidak memblokir request chat.
langfuse_client = Langfuse(
    public_key=os.environ.get("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.environ.get("LANGFUSE_SECRET_KEY"),
    host=os.environ.get("LANGFUSE_HOST", "http://localhost:3000"),
)

# Folder dokumen knowledge base (.md/.txt/.pdf). Di docker compose diisi lewat env var
# KNOWLEDGE_BASE_DIR; default relatif terhadap working directory, seperti app/static.
KNOWLEDGE_BASE_PATH = os.environ.get("KNOWLEDGE_BASE_DIR", "app/knowledge-base")


def list_knowledge_base_documents() -> list[str]:
    """Return the sorted names of .md/.txt/.pdf files directly inside KNOWLEDGE_BASE_PATH ([] if the folder does not exist)."""
    if not os.path.isdir(KNOWLEDGE_BASE_PATH):
        return []
    # Hanya file langsung di folder ini (tanpa subfolder) dengan ekstensi yang didukung ingest.
    return sorted(
        name
        for name in os.listdir(KNOWLEDGE_BASE_PATH)
        if os.path.isfile(os.path.join(KNOWLEDGE_BASE_PATH, name))
        and name.lower().endswith((".md", ".txt", ".pdf"))
    )


# Skema request/response body, divalidasi otomatis oleh pydantic/FastAPI.
class ChatMessage(BaseModel):
    """Satu pesan dalam percakapan."""
    role: str  # "user" atau "assistant" (system prompt ditambahkan di server)
    content: str  # isi teks pesan


class ChatStreamRequest(BaseModel):
    """Body request POST /chat/stream."""
    # Seluruh riwayat percakapan dari frontend, urut dari yang terlama.
    messages: list[ChatMessage]
    # Default True agar client lama (tanpa field ini) tetap memakai RAG seperti sebelumnya.
    use_rag: bool = True
    # Metode retrieval saat use_rag=True: "vector" (k-NN embedding), "bm25" (full-text),
    # atau "hybrid" (gabungan keduanya lewat RRF). Default "hybrid"; nilai lain ditolak 422.
    search_method: Literal["vector", "bm25", "hybrid"] = "hybrid"
    # Urutkan ulang kandidat dengan cross-encoder sebelum dijadikan konteks; bisa dikombinasikan
    # dengan search_method mana pun. Diabaikan bila reranker dimatikan server (RERANK_ENABLED=false).
    use_reranking: bool = True


class ChatRequest(BaseModel):
    """Body request POST /chat (mode agent): pertanyaan baru plus riwayat percakapan opsional."""
    message: str
    # Riwayat percakapan sebelumnya (urut dari yang terlama), tanpa pesan baru di atas.
    # Default [] agar client lama yang hanya mengirim message tetap valid.
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    """Body response POST /chat: jawaban akhir agent (non-streaming)."""
    reply: str
    # Tool yang dipakai untuk badge di UI: "rag", "sql", "mixed" (keduanya), "none", atau "cache"
    # (jawaban dari cache Redis, agent tidak dijalankan). Opsional agar client lama tetap kompatibel.
    tool_used: str | None = None
    # Nama file dokumen SOP yang diambil tool cari_dokumen_sop (lampiran sumber di UI mode Agent).
    # Kosong untuk jawaban dari cache: cache hanya menyimpan teks jawaban.
    sources: list[str] = []


# Jumlah pesan terakhir yang ikut dikirim sebagai konteks ke model,
# supaya prompt tidak membengkak seiring panjangnya percakapan.
HISTORY_WINDOW = 10


def _summarize_hits(hits: list[dict]) -> list[dict]:
    """Compact view of retrieval hits for Langfuse (id, source, scores, text preview) instead of full chunk text."""
    return [
        {
            "_id": h.get("_id"),
            "source": h.get("metadata", {}).get("source"),
            "score": h.get("score"),
            "rrf_score": h.get("rrf_score"),
            "rerank_score": h.get("rerank_score"),
            "text": h.get("text", "")[:200],
        }
        for h in hits
    ]


def traced_chat_stream(trace, ollama_messages: list[dict]):
    """Wrap ollama_client.chat_stream() in a Langfuse generation; close the generation and trace once streaming ends."""
    generation = trace.generation(name="llm_generate_stream", model=ollama_client.model, input=ollama_messages)
    accumulated = ""
    try:
        for token in ollama_client.chat_stream(ollama_messages):
            accumulated += token
            yield token
    finally:
        # Dijalankan setelah token terakhir, saat stream error, maupun saat client memutus koneksi
        # (GeneratorExit), sehingga trace selalu tertutup dengan balasan yang sempat terkirim.
        # Tidak bisa ditaruh di chat_stream() karena endpoint sudah return sebelum stream berjalan.
        generation.end(output=accumulated)
        trace.update(output={"reply": accumulated})
        langfuse_client.flush()


@app.get("/health")
def health():
    """GET /health - health check endpoint, returns service status."""
    return {"status": "ok"}


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """GET /login - render the login form; redirect to / if already logged in."""
    if get_current_user(request):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request, "login.html", {"error": None})


@app.post("/login", response_class=HTMLResponse)
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """POST /login - verify credentials; on success store user_id/role/nama in the session and redirect to /."""
    user = verify_user(username.strip(), password)
    if user is None:
        return templates.TemplateResponse(
            request, "login.html", {"error": "Username atau password salah."}, status_code=401
        )
    # Identitas (user_id & role) hanya ditulis ke sesi di sini; endpoint lain membacanya
    # lewat get_current_user(), bukan dari body request.
    request.session["user_id"] = user["user_id"]
    request.session["role"] = user["role"]
    request.session["nama"] = user["nama"]
    return RedirectResponse("/", status_code=303)


@app.get("/logout")
def logout(request: Request):
    """GET /logout - clear the session and redirect to the login page."""
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@app.post("/chat/stream")
def chat_stream(request: ChatStreamRequest, http_request: Request) -> StreamingResponse:
    """POST /chat/stream - stream a chat reply from Ollama, grounded on knowledge base documents retrieved for the last user message."""
    check_rate_limit(http_request, "chat")
    if not get_current_user(http_request):
        raise HTTPException(status_code=401, detail="login required")
    # Percakapan harus diakhiri pesan user, karena Ollama diminta membalas giliran user tersebut.
    if not request.messages or request.messages[-1].role != "user":
        raise HTTPException(status_code=400, detail="messages must be non-empty and end with a user message")

    # Ambil hanya HISTORY_WINDOW pesan terakhir agar konteks tetap ringkas.
    windowed = request.messages[-HISTORY_WINDOW:]
    last_user_message = windowed[-1].content

    # Satu trace Langfuse per request chat; ditutup di traced_chat_stream() setelah streaming selesai.
    trace = langfuse_client.trace(
        name="chat_stream",
        input={"message": last_user_message},
        metadata={
            "use_rag": request.use_rag,
            "search_method": request.search_method,
            "use_reranking": request.use_reranking,
        },
    )

    # Retrieval: cari dokumen knowledge base yang paling mirip dengan pertanyaan terakhir.
    # Jika Ollama/OpenSearch gagal (mati, index belum ada, dsb.), chat tetap jalan tanpa konteks.
    # Jika user mematikan RAG, embedding & pencarian dilewati sama sekali.
    results = []
    if request.use_rag:
        # Reranking hanya jalan bila diminta client DAN reranker aktif di server.
        do_rerank = request.use_reranking and reranker is not None
        # Dengan reranking: ambil 20 kandidat agar cross-encoder punya pilihan lebih luas, lalu
        # disaring jadi 3. Tanpa reranking: jumlah konteks sama seperti sebelumnya (hybrid 3, lainnya 6).
        pool_size = 20 if do_rerank else (3 if request.search_method == "hybrid" else 6)
        # Span yang sedang terbuka, agar bisa ditutup dengan status ERROR bila retrieval/rerank gagal.
        open_span = None
        try:
            # Span retrieval mencakup embedding + pencarian untuk ketiga search_method.
            open_span = trace.span(
                name="retrieval",
                input={"query": last_user_message, "search_method": request.search_method, "top_k": pool_size},
            )
            if request.search_method == "bm25":
                # BM25 mencocokkan kata langsung di field "text", jadi tidak perlu embedding (Ollama).
                candidates = vector_store.search_bm25(last_user_message, top_k=pool_size)
            elif request.search_method == "hybrid":
                # search_hybrid() menjalankan BM25 dan k-NN sekaligus lalu menggabungkannya (RRF),
                # jadi cukup satu panggilan; embedding tetap dibutuhkan untuk sisi k-NN.
                query_embedding = embed_text(last_user_message, base_url=OLLAMA_BASE_URL)
                candidates = vector_store.search_hybrid(
                    query_text=last_user_message, query_embedding=query_embedding, top_k=pool_size
                )
            else:
                query_embedding = embed_text(last_user_message, base_url=OLLAMA_BASE_URL)
                candidates = vector_store.search(query_embedding, top_k=pool_size)
            open_span.end(output=_summarize_hits(candidates))
            open_span = None
            if do_rerank:
                open_span = trace.span(
                    name="rerank",
                    input={"query": last_user_message, "candidates": len(candidates), "top_k": 3},
                )
                results = reranker.rerank(last_user_message, candidates, top_k=3)
                open_span.end(output=_summarize_hits(results))
                open_span = None
            else:
                results = candidates
        except httpx.HTTPError as e:
            if open_span is not None:
                open_span.end(level="ERROR", status_message=str(e))
            results = []

    # Pilih system prompt dan isi pesan terakhir sesuai 3 kondisi:
    # RAG dimatikan user, ada konteks dokumen, atau RAG aktif tapi tidak ada hasil.
    if not request.use_rag:
        system_prompt = NALA_SYSTEM_PROMPT_RAG_OFF
        grounded_content = last_user_message
    elif results:
        # Tiap potongan diberi label sumber agar model bisa membedakan asal informasinya
        # dan tidak mencampur angka/ketentuan antar-dokumen.
        context = "\n\n".join(f"[{r['metadata']['source']}]\n{r['text']}" for r in results)
        system_prompt = SYSTEM_PROMPT
        grounded_content = f"Konteks:\n{context}\n\nPertanyaan: {last_user_message}"
    else:
        system_prompt = NALA_SYSTEM_PROMPT_NO_CONTEXT
        grounded_content = last_user_message

    # Susun pesan: system prompt, riwayat sebelum pesan terakhir, lalu pesan terakhir
    # user yang sudah diperkaya konteks (konteks hanya disisipkan di giliran terakhir).
    ollama_messages = (
        [{"role": "system", "content": system_prompt}]
        + [{"role": m.role, "content": m.content} for m in windowed[:-1]]
        + [{"role": "user", "content": grounded_content}]
    )
    # Balasan diteruskan langsung sebagai stream teks agar frontend bisa render bertahap;
    # traced_chat_stream() mencatat generation dan menutup trace setelah token terakhir.
    return StreamingResponse(traced_chat_stream(trace, ollama_messages), media_type="text/plain")


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, http_request: Request) -> ChatResponse:
    """POST /chat - answer a question (with optional chat history) using the LangGraph agent, which decides by itself when to call its tools."""
    check_rate_limit(http_request, "chat")
    # Identitas (user_id & role) HANYA dari sesi login, bukan dari body request.
    user = get_current_user(http_request)
    if user is None:
        raise HTTPException(status_code=401, detail="login required")
    # Cache jawaban hanya untuk pertanyaan tanpa riwayat: bila ada history, jawabannya bergantung
    # pada percakapan sebelumnya, bukan cuma pesan terakhir. Role dari SESI masuk ke key cache,
    # sehingga jawaban satu role tidak pernah disajikan ke role lain (RBAC Module 27).
    use_cache = not request.history
    if use_cache:
        cached_reply = get_cached_answer(request.message, user["role"], "hybrid", True)
        if cached_reply is not None:
            # Request yang kena cache tetap dicatat di audit log (tool_dipanggil="cache").
            log_audit(
                user_id=user["user_id"],
                role=user["role"],
                pertanyaan=request.message,
                tool_dipanggil="cache",
                akses_diizinkan=True,
            )
            return ChatResponse(reply=cached_reply, tool_used="cache")
    # Satu trace Langfuse per request; node agent mencatat generation/span di dalamnya.
    trace = langfuse_client.trace(
        name="chat_agent",
        input={"message": request.message},
        metadata={"history_count": len(request.history)},
    )
    # Agent dibangun per request (bukan sekali di level modul) karena trace di atas
    # dioper ke closure node-node graph lewat build_agent().
    agent = build_agent(
        ollama_client=ollama_client,
        vector_store=vector_store,
        ollama_base_url=OLLAMA_BASE_URL,
        reranker=reranker,
        trace=trace,
        model_name=os.environ.get("OLLAMA_MODEL", "llama3.2:3b"),
    )
    # Riwayat dari client hanya boleh berisi giliran user/assistant: pesan "system"/"tool" dari
    # client dibuang agar tidak bisa menimpa system prompt atau memalsukan hasil tool.
    history_messages = [
        {"role": m.role, "content": m.content} for m in request.history if m.role in ("user", "assistant")
    ]
    # Sama seperti /chat/stream: hanya HISTORY_WINDOW pesan terakhir (termasuk pesan baru)
    # yang dikirim ke model agar prompt tidak membengkak seiring panjangnya percakapan.
    windowed = (history_messages + [{"role": "user", "content": request.message}])[-HISTORY_WINDOW:]
    # role dipakai call_tool untuk menegakkan RBAC (lihat SQL_ALLOWED_ROLES di agent.py).
    initial_state = {
        "messages": [{"role": "system", "content": NALA_SYSTEM_PROMPT_AGENT}] + windowed,
        "role": user["role"],
        "called_tools": [],
    }
    # invoke() menjalankan loop call_model -> call_tool -> call_model hingga model berhenti
    # meminta tool; pesan terakhir adalah jawaban akhir untuk user.
    final_state = agent.invoke(initial_state)
    reply = final_state["messages"][-1]["content"]
    trace.update(output={"reply": reply, "message_count": len(final_state["messages"])})
    langfuse_client.flush()
    # Audit log dicatat SETELAH reply didapat; log_audit() menangani error database-nya sendiri,
    # jadi kegagalan pencatatan tidak menggagalkan response. Satu baris per tool yang diminta
    # model (termasuk yang ditolak RBAC), atau satu baris tanpa tool bila agent tidak memanggil tool.
    called_tools = final_state.get("called_tools", [])
    if called_tools:
        for entry in called_tools:
            log_audit(
                user_id=user["user_id"],
                role=user["role"],
                pertanyaan=request.message,
                tool_dipanggil=entry["tool"],
                akses_diizinkan=entry["diizinkan"],
            )
    else:
        log_audit(
            user_id=user["user_id"],
            role=user["role"],
            pertanyaan=request.message,
            tool_dipanggil=None,
            akses_diizinkan=True,
        )
    if use_cache:
        set_cached_answer(request.message, user["role"], "hybrid", True, reply)
    # Badge tool di UI: hanya tool yang BENAR-BENAR dijalankan (diizinkan=True) yang dihitung;
    # tool yang ditolak RBAC bukan tool yang dipakai.
    used = {entry["tool"] for entry in called_tools if entry["diizinkan"]}
    rag_used = "cari_dokumen_sop" in used
    sql_used = "query_data_operasional" in used
    if rag_used and sql_used:
        tool_used = "mixed"
    elif sql_used:
        tool_used = "sql"
    elif rag_used:
        tool_used = "rag"
    else:
        tool_used = "none"
    # Lampiran sumber lewat kanal yang sama (called_tools): gabungan "sumber" dari tool yang
    # diizinkan, tanpa duplikat, urutan pertama kali muncul tetap terjaga.
    sources = list(
        dict.fromkeys(src for entry in called_tools if entry["diizinkan"] for src in entry.get("sumber", []))
    )
    return ChatResponse(reply=reply, tool_used=tool_used, sources=sources)


@app.get("/", response_class=HTMLResponse)
def chat_page(request: Request):
    """GET / - render halaman chat utama."""
    user = get_current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(request, "chat.html", {"user": user})


# Tipe konten saat dokumen knowledge base dibuka di browser. .md dan .txt sengaja disajikan sebagai
# text/plain (bukan text/html/markdown yang dirender) agar isi file hasil upload tidak pernah
# dijalankan sebagai HTML/script oleh browser.
KNOWLEDGE_BASE_MEDIA_TYPES = {
    ".md": "text/plain; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".pdf": "application/pdf",
}


@app.get("/knowledge-base/{filename}")
def knowledge_base_document(request: Request, filename: str):
    """GET /knowledge-base/{filename} - open one knowledge base document in the browser (login required); used by the source links in agent answers."""
    user = get_current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    # Hanya nama file (tanpa komponen path) dengan ekstensi yang didukung, dan path akhirnya harus
    # tetap berada di dalam folder knowledge base (mencegah path traversal seperti "../").
    name = os.path.basename(filename)
    media_type = KNOWLEDGE_BASE_MEDIA_TYPES.get(os.path.splitext(name)[1].lower())
    base_dir = os.path.realpath(KNOWLEDGE_BASE_PATH)
    path = os.path.realpath(os.path.join(base_dir, name))
    if name != filename or media_type is None or os.path.dirname(path) != base_dir or not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan di knowledge base.")
    # content_disposition_type="inline": dibuka di tab browser, bukan diunduh. nosniff mencegah
    # browser menebak tipe konten lain (mis. menafsirkan .txt sebagai HTML).
    return FileResponse(
        path,
        media_type=media_type,
        filename=name,
        content_disposition_type="inline",
        headers={"X-Content-Type-Options": "nosniff"},
    )


@app.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    """GET /upload - render the knowledge base page with the upload form and the list of stored documents."""
    user = get_current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(
        request,
        "upload.html",
        {"message": None, "documents": list_knowledge_base_documents(), "user": user},
    )


@app.post("/upload", response_class=HTMLResponse)
def upload_document(request: Request, file: UploadFile = File(...)):
    """POST /upload - save an uploaded .md/.txt/.pdf file into the knowledge base folder and enqueue a background job (RQ worker) to ingest it into OpenSearch."""
    check_rate_limit(request, "upload", max_requests=5)
    user = get_current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    # Ambil nama file saja (buang komponen path seperti "../") agar upload tidak bisa
    # menulis ke luar folder knowledge base.
    filename = os.path.basename(file.filename or "")
    # Atribut accept di form hanya filter di sisi browser, jadi ekstensi dicek ulang di server.
    if not filename.lower().endswith((".md", ".txt", ".pdf")):
        raise HTTPException(status_code=400, detail="only .md, .txt, or .pdf files are allowed")

    # Buat folder knowledge base bila belum ada, lalu simpan file (menimpa file
    # bernama sama) dalam mode biner agar PDF tidak rusak.
    os.makedirs(KNOWLEDGE_BASE_PATH, exist_ok=True)
    dest_path = os.path.join(KNOWLEDGE_BASE_PATH, filename)
    with open(dest_path, "wb") as f:
        f.write(file.file.read())

    # Ingest (embedding + index ke OpenSearch) dijalankan worker RQ di background (service worker,
    # app/jobs.py), jadi response tidak menunggu proses yang bisa lama. Fungsi job dirujuk lewat
    # string path agar main.py tidak perlu mengimpor app/jobs.py.
    try:
        job = ingest_queue.enqueue("app.jobs.ingest_document_job", dest_path)
        message = (
            f"Dokumen '{filename}' berhasil diunggah dan sedang diproses di background "
            f"(job ID: {job.id}). Dokumen bisa dipakai NALA setelah proses selesai."
        )
    except redis.RedisError:
        # File tetap tersimpan walau antrian tidak terjangkau, supaya bisa di-index ulang nanti.
        message = (
            f"Dokumen '{filename}' berhasil disimpan, tapi belum masuk antrian proses "
            "(Redis belum terjangkau) — unggah ulang atau jalankan DAG ingest_documents "
            "di Airflow setelah layanan aktif."
        )
    # Render ulang halaman upload dengan pesan status dan daftar dokumen terbaru.
    return templates.TemplateResponse(
        request,
        "upload.html",
        {"message": message, "documents": list_knowledge_base_documents(), "user": user},
    )


# ---------- Data operasional (Postgres nala_operasional, lihat app/db.py & db/seed.sql) ----------
# Pembacaan SELALU lewat get_connection() (role nala_readonly, hanya SELECT) dan penulisan
# SELALU lewat get_write_connection() (role nala_writer, hanya INSERT); role writer tidak bisa
# SELECT, jadi daftar data setelah simpan dibaca ulang dengan koneksi readonly terpisah.


# Jumlah baris per halaman pada tabel daftar data.
PAGE_SIZE = 10


def build_pagination(page: int, total: int) -> dict:
    """Clamp page to the valid range and describe it for the template: page, pages, total, start/end row numbers, offset, and page links (None = ellipsis)."""
    pages = max(1, -(-total // PAGE_SIZE))  # pembagian dibulatkan ke atas; minimal 1 halaman
    page = min(max(page, 1), pages)  # nomor halaman di luar rentang dikoreksi, bukan error
    # Tautan halaman: halaman pertama, terakhir, dan 1 halaman di kiri-kanan halaman aktif;
    # celah di antaranya ditandai None (ditampilkan sebagai "…").
    shown = sorted({1, pages, page - 1, page, page + 1} & set(range(1, pages + 1)))
    links: list[int | None] = []
    for n in shown:
        if links and n - links[-1] > 1:
            links.append(None)
        links.append(n)
    return {
        "page": page,
        "pages": pages,
        "total": total,
        "start": (page - 1) * PAGE_SIZE + 1 if total else 0,
        "end": min(page * PAGE_SIZE, total),
        "offset": (page - 1) * PAGE_SIZE,
        "links": links,
    }


def _fetch_page(count_sql: str, select_sql: str, page: int) -> tuple[list[dict], dict]:
    """Count rows, clamp the page, then SELECT one page (LIMIT/OFFSET) with the read-only role."""
    with get_connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(count_sql)
        pagination = build_pagination(page, cur.fetchone()["count"])
        cur.execute(select_sql + " LIMIT %s OFFSET %s", (PAGE_SIZE, pagination["offset"]))
        return cur.fetchall(), pagination


def fetch_pengajuan_kredit(page: int = 1) -> tuple[list[dict], dict]:
    """Return one page of pengajuan_kredit rows (newest first) and its pagination info."""
    # Terbaru di atas agar data yang baru disimpan langsung terlihat di halaman 1.
    return _fetch_page(
        "SELECT count(*) FROM pengajuan_kredit",
        "SELECT id, nasabah_id, nama_nasabah, jumlah_pengajuan, status, tanggal_pengajuan, alasan_penolakan "
        "FROM pengajuan_kredit ORDER BY id DESC",
        page,
    )


def fetch_klaim_asuransi(page: int = 1) -> tuple[list[dict], dict]:
    """Return one page of klaim_asuransi rows (newest first) and its pagination info."""
    return _fetch_page(
        "SELECT count(*) FROM klaim_asuransi",
        "SELECT id, nasabah_id, nama_nasabah, jenis_klaim, jumlah_klaim, status, tanggal_klaim "
        "FROM klaim_asuransi ORDER BY id DESC",
        page,
    )


def render_data_operasional(
    request: Request,
    user: dict,
    message: str | None = None,
    error: str | None = None,
    status_code: int = 200,
    kredit_page: int = 1,
    klaim_page: int = 1,
):
    """Render data_operasional.html with one page of each table; show an error instead of failing if the database is unreachable."""
    try:
        pengajuan_kredit, kredit_pagination = fetch_pengajuan_kredit(kredit_page)
        klaim_asuransi, klaim_pagination = fetch_klaim_asuransi(klaim_page)
    except psycopg.OperationalError:
        pengajuan_kredit, klaim_asuransi = [], []
        kredit_pagination = klaim_pagination = build_pagination(1, 0)
        # Pesan error simpan yang sudah menyebut database tidak terjangkau dipertahankan apa adanya
        # agar tidak dobel; selain itu ganti/lengkapi dengan info database tidak terjangkau.
        if not error or "tidak terjangkau" not in error:
            error = " ".join(filter(None, [error, "Database data operasional tidak terjangkau, daftar data tidak bisa ditampilkan."]))
        status_code = 503
    return templates.TemplateResponse(
        request,
        "data_operasional.html",
        {
            "pengajuan_kredit": pengajuan_kredit,
            "klaim_asuransi": klaim_asuransi,
            "kredit_pagination": kredit_pagination,
            "klaim_pagination": klaim_pagination,
            "message": message,
            "error": error,
            "user": user,
        },
        status_code=status_code,
    )


def insert_row(sql: str, params: tuple) -> tuple[str | None, int]:
    """Run one INSERT with the write-only role and commit; return (error message or None, HTTP status)."""
    try:
        # Hanya INSERT di dalam blok ini: error apa pun di transaksi yang sama akan membatalkan INSERT.
        with get_write_connection() as conn:
            conn.execute(sql, params)
            conn.commit()
    except psycopg.OperationalError:
        return "Gagal menyimpan: database data operasional tidak terjangkau.", 503
    except (psycopg.errors.IntegrityError, psycopg.errors.DataError) as e:
        # Mis. status di luar CHECK constraint atau teks melebihi panjang kolom.
        return f"Gagal menyimpan: data tidak valid ({e.diag.message_primary}).", 400
    return None, 200


@app.get("/data-operasional", response_class=HTMLResponse)
def data_operasional_page(request: Request, kredit_page: int = 1, klaim_page: int = 1):
    """GET /data-operasional - render the operational data page; ?kredit_page= and ?klaim_page= select each table's page independently."""
    user = get_current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    return render_data_operasional(request, user, kredit_page=kredit_page, klaim_page=klaim_page)


@app.post("/data-operasional/pengajuan-kredit", response_class=HTMLResponse)
def create_pengajuan_kredit(
    request: Request,
    nasabah_id: str = Form(...),
    nama_nasabah: str = Form(...),
    jumlah_pengajuan: Decimal = Form(...),
    status: str = Form(...),
    tanggal_pengajuan: date = Form(...),
    alasan_penolakan: str = Form(""),
):
    """POST /data-operasional/pengajuan-kredit - insert a new pengajuan_kredit row, then re-render the page with the latest data."""
    # Endpoint TULIS: batas paling ketat (defense-in-depth, belum ada pembatasan per role).
    check_rate_limit(request, "data-operasional", max_requests=10)
    user = get_current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    # Parameter %s (bukan f-string) agar input form tidak bisa menyisipkan SQL.
    error, status_code = insert_row(
        "INSERT INTO pengajuan_kredit "
        "(nasabah_id, nama_nasabah, jumlah_pengajuan, status, tanggal_pengajuan, alasan_penolakan) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (
            nasabah_id.strip(),
            nama_nasabah.strip(),
            jumlah_pengajuan,
            status,
            tanggal_pengajuan,
            # Textarea kosong disimpan NULL (bukan string kosong), konsisten dengan data seed.
            alasan_penolakan.strip() or None,
        ),
    )
    message = None if error else f"Pengajuan kredit {nasabah_id.strip()} berhasil disimpan."
    return render_data_operasional(request, user, message=message, error=error, status_code=status_code)


@app.post("/data-operasional/klaim-asuransi", response_class=HTMLResponse)
def create_klaim_asuransi(
    request: Request,
    nasabah_id: str = Form(...),
    nama_nasabah: str = Form(...),
    jenis_klaim: str = Form(...),
    jumlah_klaim: Decimal = Form(...),
    status: str = Form(...),
    tanggal_klaim: date = Form(...),
):
    """POST /data-operasional/klaim-asuransi - insert a new klaim_asuransi row, then re-render the page with the latest data."""
    check_rate_limit(request, "data-operasional", max_requests=10)
    user = get_current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    error, status_code = insert_row(
        "INSERT INTO klaim_asuransi "
        "(nasabah_id, nama_nasabah, jenis_klaim, jumlah_klaim, status, tanggal_klaim) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (nasabah_id.strip(), nama_nasabah.strip(), jenis_klaim.strip(), jumlah_klaim, status, tanggal_klaim),
    )
    message = None if error else f"Klaim asuransi {nasabah_id.strip()} berhasil disimpan."
    return render_data_operasional(request, user, message=message, error=error, status_code=status_code)
