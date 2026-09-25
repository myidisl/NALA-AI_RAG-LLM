# app/agent.py
# Agent NALA berbasis LangGraph: model memutuskan sendiri kapan memanggil tool (pencarian
# dokumen SOP / RAG dan query data operasional terbatas), lalu menjawab setelah melihat hasil tool.
#
#   call_model ──(ada tool_calls)──> call_tool ──> call_model ──(tanpa tool_calls)──> END
#
# Instrumentasi Langfuse bersifat opsional: tanpa trace, graph tetap berjalan normal.
import json
import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, StateGraph

from app.tools.rag_tool import RAG_TOOL_SCHEMA, rag_search
from app.tools.sql_tool import SQL_TOOL_SCHEMA, query_data_operasional

# Tool yang ditawarkan ke model: pencarian dokumen SOP (aturan/prosedur) dan query data
# operasional terbatas (angka/status transaksi). SEMUA role ditawari SEMUA tool; RBAC ditegakkan
# saat eksekusi di call_tool. Menyembunyikan tool per role membuat model mengarang data dan
# membuat percobaan akses tidak tercatat di audit log.
ALL_TOOLS = [RAG_TOOL_SCHEMA, SQL_TOOL_SCHEMA]

# Role yang boleh MENJALANKAN query_data_operasional; role lain ditolak di call_tool.
SQL_ALLOWED_ROLES = {"staff_finance", "supervisor"}


class AgentState(TypedDict):
    """Graph state: the running chat history in Ollama message format, the user's role, and the tools called so far."""

    # operator.add: pesan yang dikembalikan tiap node DITAMBAHKAN ke riwayat, bukan menimpanya.
    messages: Annotated[list[dict], operator.add]
    # Role user dari sesi login (app/auth.py), diisi pemanggil di initial state; bukan dari body request.
    role: str
    # Jejak tool yang diminta model beserta keputusan RBAC-nya ({"tool", "diizinkan"}), untuk audit log.
    called_tools: Annotated[list[dict], operator.add]


def build_agent(ollama_client, vector_store, ollama_base_url: str, reranker=None, trace=None, model_name: str = "llama3.2:3b"):
    """Build and compile the tool-calling agent graph; trace (Langfuse) is optional and used for per-node observability."""

    def call_model(state: AgentState) -> dict:
        """Ask the model for the next step; it either answers or requests tool calls."""
        generation = trace.generation(name="agent_call_model", model=model_name, input=state["messages"]) if trace else None
        response_message = ollama_client.chat(state["messages"], tools=ALL_TOOLS)
        if generation:
            generation.end(output=response_message)
        return {"messages": [response_message]}

    def call_tool(state: AgentState) -> dict:
        """Run every tool call requested in the last model message, enforcing RBAC, and return the results as tool messages."""
        last_message = state["messages"][-1]
        # Role yang tidak ada di state diperlakukan sebagai tidak berwenang (default aman).
        role = state.get("role")
        tool_messages = []
        called = []
        for call in last_message.get("tool_calls", []):
            function = call.get("function") or {}
            name = function.get("name", "")
            args = function.get("arguments") or {}
            # Ollama mengirim arguments sebagai dict; format OpenAI-style mengirim string JSON.
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            span = trace.span(name=f"agent_tool:{name}", input=args) if trace else None
            try:
                if name == "query_data_operasional" and role not in SQL_ALLOWED_ROLES:
                    # RBAC: tool TIDAK dieksekusi sama sekali untuk role yang tidak berwenang.
                    called.append({"tool": name, "diizinkan": False})
                    result = (
                        f"Akses ditolak: role '{role}' tidak berwenang mengakses data operasional "
                        "(pengajuan kredit / klaim asuransi). Sampaikan penolakan ini ke user apa adanya "
                        "dan jangan mengarang data pengganti."
                    )
                elif name == "cari_dokumen_sop":
                    # Entry dicatat dulu (seperti tool lain), lalu "sumber" diisi setelah pencarian:
                    # daftar nama file dokumen yang dipakai, untuk lampiran sumber di UI mode Agent.
                    entry = {"tool": name, "diizinkan": True, "sumber": []}
                    called.append(entry)
                    query = args.get("query")
                    # Model kecil kadang lupa mengisi argumen wajib; dikembalikan sebagai hasil tool
                    # agar model bisa mencoba lagi, bukan menghentikan graph.
                    if query:
                        result, entry["sumber"] = rag_search(query, vector_store, ollama_base_url, reranker=reranker)
                    else:
                        result = "Argumen 'query' wajib diisi untuk tool cari_dokumen_sop."
                elif name == "query_data_operasional":
                    called.append({"tool": name, "diizinkan": True})
                    result = query_data_operasional(**args)
                else:
                    called.append({"tool": name, "diizinkan": False})
                    result = f"Tool '{name}' tidak dikenal."
            except (TypeError, KeyError):
                # Argumen wajib tidak ada atau ada argumen yang tidak dikenal; dikembalikan ke model
                # agar bisa memperbaiki panggilannya.
                result = (
                    f"Argumen tidak valid untuk tool '{name}'. query_data_operasional wajib: tabel, mode "
                    "(opsional: status, nasabah_id); cari_dokumen_sop wajib: query."
                )
            if span:
                span.end(output={"result": result[:300]})
            tool_messages.append({"role": "tool", "name": name, "tool_call_id": call.get("id"), "content": result})
        return {"messages": tool_messages, "called_tools": called}

    def should_continue(state: AgentState) -> str:
        """Route to call_tool while the model keeps requesting tools; otherwise finish."""
        last_message = state["messages"][-1]
        return "call_tool" if last_message.get("tool_calls") else END

    graph = StateGraph(AgentState)
    graph.add_node("call_model", call_model)
    graph.add_node("call_tool", call_tool)
    graph.set_entry_point("call_model")
    graph.add_conditional_edges("call_model", should_continue, {"call_tool": "call_tool", END: END})
    # Setelah tool dijalankan, model dipanggil lagi untuk membaca hasilnya.
    graph.add_edge("call_tool", "call_model")
    return graph.compile()
