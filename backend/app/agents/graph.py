"""
lg2m/backend/app/agents/graph.py
Orquestração da máquina de estados do sistema multiagente LG2M utilizando LangGraph.
Instrumentado com AgentTracer para observabilidade em tempo real via WebSocket.
"""

import time
from typing import Literal
from langgraph.graph import StateGraph, START, END

from app.agents.state import AgentState
from app.agents.router_agent import router_node
from app.agents.retriever_agent import retriever_node
from app.agents.mentor_agent import mentor_node
from app.agents.guardrail_agent import guardrail_node
from app.agents.profiler_agent import profiler_node
from app.core.agent_tracer import tracer

# ── Metadados dos agentes (para o tracer) ──────────────────────────────────
_NODE_META = {
    "router": {
        "label": "Agente 1 — Orquestrador & Triagem",
        "tools": ["sanitize_input()", "detect_intent()", "cognitive_snapshot()"],
    },
    "retriever": {
        "label": "Agente 2 — Curador RAG Semântico",
        "tools": ["search_semantic_questions()", "fetch_isomorphic_similar()", "cosine_similarity()"],
    },
    "mentor": {
        "label": "Agente 3 — Mentor Didático",
        "tools": ["build_didactic_explanation()", "classify_error_type()", "apply_teaching_style()"],
    },
    "guardrail": {
        "label": "Agente 5 — Guardrail & Verificador",
        "tools": ["verify_gabarito_alignment()", "execute_python_math_sandbox()", "record_audit_log()"],
    },
    "profiler": {
        "label": "Agente 4 — Profiler Cognitivo",
        "tools": ["update_cognitive_profile()", "recalculate_domain_score()", "detect_blindspot()"],
    },
}


def _safe_state_snapshot(state: AgentState) -> dict:
    """Extrai campos relevantes do estado para exibição no visualizador."""
    return {
        "intent_detected": state.get("intent_detected"),
        "guardrail_status": state.get("guardrail_status"),
        "is_correct": state.get("is_correct"),
        "verification_attempts": state.get("verification_attempts", 0),
        "error_classification": state.get("error_classification"),
        "estilo_didatico": state.get("estilo_didatico"),
        "certame_foco": state.get("certame_foco"),
        "critical_blindspot_detected": state.get("critical_blindspot_detected"),
        "subject_score_updated": state.get("subject_score_updated"),
        "current_question_id": state.get("current_question_id"),
    }


def _make_traced_node(node_name: str, original_fn):
    """Wrapper que envolve um nó do LangGraph com emissão de eventos de trace."""
    meta = _NODE_META.get(node_name, {"label": node_name, "tools": []})

    def traced(state: AgentState) -> dict:
        t0 = time.perf_counter()
        # Limpa objetos não serializáveis (tipo classes de mensagens do LangChain) do input/output
        def _clean_dict(d: dict) -> dict:
            return {k: (str(v) if k == "messages" else v) for k, v in d.items()}

        tracer.emit_node_start(
            node=node_name,
            label=meta["label"],
            state_snapshot=_safe_state_snapshot(state),
            tools=meta["tools"],
            inputs=_clean_dict(state),
        )

        result = original_fn(state)

        duration_ms = (time.perf_counter() - t0) * 1000

        # Monta snapshot pós-execução mesclando estado + resultado
        post_state = {**state, **result}
        guardrail_status = post_state.get("guardrail_status", "APPROVED")
        is_rejected = node_name == "guardrail" and guardrail_status == "REJECTED"

        # Resumo amigável do output
        summaries = {
            "router":    f"intent → {post_state.get('intent_detected', '?')}",
            "retriever": f"{len(post_state.get('similar_questions_found') or [])} questões recuperadas",
            "mentor":    "rascunho pedagógico gerado",
            "guardrail": f"guardrail → {guardrail_status}",
            "profiler":  f"score={post_state.get('subject_score_updated', '?')} · blindspot={post_state.get('critical_blindspot_detected', False)}",
        }

        tracer.emit_node_end(
            node=node_name,
            label=meta["label"],
            duration_ms=duration_ms,
            output_summary=summaries.get(node_name, ""),
            state_snapshot=_safe_state_snapshot(post_state),
            status="rejected" if is_rejected else "done",
            outputs=_clean_dict(result),
        )

        # Evento especial para o Guardrail
        if node_name == "guardrail":
            tracer.emit_guardrail_event(
                status=guardrail_status,
                reason=post_state.get("guardrail_feedback", ""),
                attempt=post_state.get("verification_attempts", 1),
            )

        return result

    traced.__name__ = f"traced_{node_name}"
    return traced


def route_after_router(state: AgentState) -> Literal["retriever", "mentor", "__end__"]:
    intent = state.get("intent_detected", "BUSCAR_QUESTAO")
    dest = "retriever" if intent in ("BUSCAR_QUESTAO", "BUSCAR_SEMELHANTES", "MONTAR_SIMULADO") \
        else "mentor" if intent in ("DISSECAR_RESPOSTA", "DUVIDA_CHAT") \
        else "__end__"
    tracer.emit_edge("router", dest, label=intent)
    return dest


def route_after_guardrail(state: AgentState) -> Literal["profiler", "mentor"]:
    status = state.get("guardrail_status", "APPROVED")
    attempts = state.get("verification_attempts", 1)
    if status == "REJECTED" and attempts < 2:
        tracer.emit_edge("guardrail", "mentor", label="REJECTED → re-gerar")
        return "mentor"
    tracer.emit_edge("guardrail", "profiler", label="APPROVED")
    return "profiler"


def build_lg2m_graph():
    """Constrói e compila o grafo multiagente de estados da LG2M."""
    builder = StateGraph(AgentState)

    # 1. Adiciona os nós instrumentados com tracer
    builder.add_node("router",    _make_traced_node("router",    router_node))
    builder.add_node("retriever", _make_traced_node("retriever", retriever_node))
    builder.add_node("mentor",    _make_traced_node("mentor",    mentor_node))
    builder.add_node("guardrail", _make_traced_node("guardrail", guardrail_node))
    builder.add_node("profiler",  _make_traced_node("profiler",  profiler_node))

    # 2. Conecta ponto de entrada
    builder.add_edge(START, "router")

    # 3. Transições condicionais a partir do Router
    builder.add_conditional_edges(
        "router",
        route_after_router,
        {
            "retriever": "retriever",
            "mentor": "mentor",
            "__end__": END,
        }
    )

    # 4. Transições do Retriever
    builder.add_edge("retriever", END)

    # 5. Fluxo de Mentoria e Guardrails
    builder.add_edge("mentor", "guardrail")

    builder.add_conditional_edges(
        "guardrail",
        route_after_guardrail,
        {
            "profiler": "profiler",
            "mentor": "mentor",
        }
    )

    # 6. Conclusão da Profilagem Cognitiva
    builder.add_edge("profiler", END)

    return builder.compile()


# Grafo compilado singleton
multiagent_engine = build_lg2m_graph()
