"""
lg2m/backend/app/agents/router_agent.py
Agente 1 — Orquestrador & Triagem Cognitiva.
Ponto de entrada do grafo LangGraph responsável por sanitização, análise de sessão e despacho de intenções.
"""

import re
from typing import Dict, Any
from app.agents.state import AgentState


def router_node(state: AgentState) -> Dict[str, Any]:
    """
    Nó do Orquestrador: sanitiza a entrada, identifica o objetivo da requisição
    e define a rota especializada no grafo.
    """
    intent_existente = state.get("intent_detected")
    if intent_existente and intent_existente != "INDEFINIDO":
        return {"intent_detected": intent_existente}

    # Sanitização básica contra prompt injection ou desvios de persona
    forbidden_terms = ["ignore all previous instructions", "system prompt", "jailbreak", "dan mode"]
    if any(term in user_msg.lower() for term in forbidden_terms):
        return {
            "intent_detected": "OUT_OF_SCOPE",
            "verified_response": "Como Mentor do LG2M, estou focado exclusivamente em auxiliar nos seus estudos para vestibulares e concursos. Como posso ajudar com a questão atual?"
        }

    # Se uma alternativa acabou de ser marcada pelo aluno
    if selected_alt is not None and current_q is not None:
        return {
            "intent_detected": "DISSECAR_RESPOSTA"
        }

    msg_lower = user_msg.lower()

    # Intenção de simulado
    if any(w in msg_lower for w in ["simulado", "montar prova", "gerar caderno", "treino cronometrado"]):
        return {
            "intent_detected": "MONTAR_SIMULADO"
        }

    # Intenção de busca semântica de questões
    if any(w in msg_lower for w in ["buscar", "procurar", "questões sobre", "questoes sobre", "questão de", "exercício de", "me mostre questões"]):
        return {
            "intent_detected": "BUSCAR_QUESTAO"
        }

    # Intenção de busca de semelhantes do conceito ativo
    if any(w in msg_lower for w in ["semelhante", "parecida", "mesmo conceito", "outra banca", "reforço"]):
        return {
            "intent_detected": "BUSCAR_SEMELHANTES"
        }

    # Dúvida conversacional sobre a questão ativa
    if current_q is not None and user_msg:
        return {
            "intent_detected": "DUVIDA_CHAT"
        }

    # Default
    return {
        "intent_detected": "BUSCAR_QUESTAO"
    }
