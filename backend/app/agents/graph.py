"""
lg2m/backend/app/agents/graph.py
Orquestração da máquina de estados do sistema multiagente LG2M utilizando LangGraph.
"""

from typing import Literal
from langgraph.graph import StateGraph, START, END

from app.agents.state import AgentState
from app.agents.router_agent import router_node
from app.agents.retriever_agent import retriever_node
from app.agents.mentor_agent import mentor_node
from app.agents.guardrail_agent import guardrail_node
from app.agents.profiler_agent import profiler_node


def route_after_router(state: AgentState) -> Literal["retriever", "mentor", "__end__"]:
    intent = state.get("intent_detected", "BUSCAR_QUESTAO")
    if intent in ("BUSCAR_QUESTAO", "BUSCAR_SEMELHANTES", "MONTAR_SIMULADO"):
        return "retriever"
    elif intent in ("DISSECAR_RESPOSTA", "DUVIDA_CHAT"):
        return "mentor"
    return "__end__"


def route_after_guardrail(state: AgentState) -> Literal["profiler", "mentor"]:
    status = state.get("guardrail_status", "APPROVED")
    attempts = state.get("verification_attempts", 1)
    if status == "REJECTED" and attempts < 2:
        return "mentor"
    return "profiler"


def build_lg2m_graph():
    """Constrói e compila o grafo multiagente de estados da LG2M."""
    builder = StateGraph(AgentState)

    # 1. Adiciona os nós de agentes autônomos
    builder.add_node("router", router_node)
    builder.add_node("retriever", retriever_node)
    builder.add_node("mentor", mentor_node)
    builder.add_node("guardrail", guardrail_node)
    builder.add_node("profiler", profiler_node)

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
