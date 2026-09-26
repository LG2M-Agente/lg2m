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

    user_msg = state.get("user_input_message") or ""
    selected_alt = state.get("selected_alternative")
    current_q = state.get("current_question_data")

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
    intent = "BUSCAR_QUESTAO"
    if any(w in msg_lower for w in ["simulado", "montar prova", "gerar caderno", "treino cronometrado"]):
        intent = "MONTAR_SIMULADO"
    elif any(w in msg_lower for w in ["buscar", "procurar", "questões sobre", "questoes sobre", "questão de", "exercício de", "me mostre questões"]):
        intent = "BUSCAR_QUESTAO"
    elif any(w in msg_lower for w in ["semelhante", "parecida", "mesmo conceito", "outra banca", "reforço"]):
        intent = "BUSCAR_SEMELHANTES"
    elif current_q is not None and user_msg:
        intent = "DUVIDA_CHAT"

    # Carrega snapshot cognitivo compacto se houver questão ativa
    cognitive_snapshot = state.get("cognitive_profile_summary")
    if not cognitive_snapshot and current_q:
        from app.core.database import SessionLocal
        from app.models.entities import PerfilEstudante
        from app.services.cognitive_engine import CognitiveProfileEngine
        
        db = SessionLocal()
        try:
            p_id = state.get("perfil_id")
            perfil = db.query(PerfilEstudante).filter_by(id=p_id).first() if p_id else db.query(PerfilEstudante).first()
            if perfil:
                cognitive_snapshot = CognitiveProfileEngine.get_active_cognitive_snapshot(
                    profile=perfil.perfil_cognitivo_json or {},
                    question_data=current_q,
                    estilo_didatico=state.get("estilo_didatico", "SOCRATICO")
                )
        except Exception as e:
            print(f"[Router Cognitive Snapshot Error]: {e}")
        finally:
            db.close()

    result_payload: Dict[str, Any] = {"intent_detected": intent}
    if cognitive_snapshot:
        result_payload["cognitive_profile_summary"] = cognitive_snapshot
        result_payload["identified_misconceptions"] = cognitive_snapshot.get("vicios_cognitivos_relevantes", [])
        result_payload["didactic_guidance"] = cognitive_snapshot.get("diretriz_pedagogica")

    return result_payload
