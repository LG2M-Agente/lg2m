"""
lg2m/backend/app/agents/guardrail_agent.py
Agente 5 — Verificador, Solver & Guardrail de Segurança.
Auditor independente determinístico responsável por garantir Alucinação Zero em relação ao gabarito oficial.
"""

import re
from typing import Dict, Any
from app.agents.state import AgentState


def guardrail_node(state: AgentState) -> Dict[str, Any]:
    """
    Nó do Guardrail: audita deterministicamente a resposta do mentor contra o gabarito oficial.
    """
    draft = state.get("mentor_draft_response", "") or ""
    current_q = state.get("current_question_data") or {}
    gabarito_oficial = current_q.get("gabarito_oficial", "A").upper()

    # 1. Checagem de Ground Truth Pinning
    # Verifica se o texto do mentor menciona explicitamente outra letra como sendo o gabarito correto
    letras_erradas = [l for l in ["A", "B", "C", "D", "E"] if l != gabarito_oficial]
    
    incoerencia_detectada = False
    motivo_rejeicao = None

    for letra in letras_erradas:
        padroes_contradicao = [
            rf"gabarito\s+(?:oficial\s+)?(?:é|e)\s+a\s+(?:alternativa\s+)?\({letra}\)",
            rf"resposta\s+correta\s+(?:é|e)\s+\({letra}\)",
            rf"a\s+opção\s+correta\s+é\s+a\s+\({letra}\)",
            rf"o\s+correto\s+é\s+a\s+letra\s+{letra}\b",
        ]
        for pat in padroes_contradicao:
            if re.search(pat, draft, re.I):
                incoerencia_detectada = True
                motivo_rejeicao = f"Contradição detectada: mentor indicou ({letra}) quando o gabarito oficial é ({gabarito_oficial})."
                break
        if incoerencia_detectada:
            break

    # 2. Avaliação do Limite de Tentativas de Autocorreção
    attempts = state.get("verification_attempts", 1)
    if incoerencia_detectada:
        if attempts < 2:
            return {
                "guardrail_status": "REJECTED",
                "guardrail_feedback": f"RETIFICAÇÃO OBRIGATÓRIA: O gabarito oficial inviolável é ({gabarito_oficial}). Ajuste imediatamente a explicação para concordar com a banca.",
            }
        else:
            # Fallback seguro determinístico após 2 tentativas
            safe_explanation = (
                f"📌 **Gabarito Homologado pela Banca:** Alternativa **({gabarito_oficial})**.\n\n"
                f"Conforme o gabarito oficial definitivo, a alternativa correta é a **({gabarito_oficial})**. "
                f"As demais alternativas funcionam como distratores conceituais formulados pela comissão examinadora."
            )
            return {
                "guardrail_status": "APPROVED",
                "verified_response": safe_explanation,
                "guardrail_feedback": "Aprovado via fallback determinístico com Ground Truth Pinning."
            }

    # 3. Aprovado com Louvor
    return {
        "guardrail_status": "APPROVED",
        "verified_response": draft,
        "guardrail_feedback": "Auditoria de gabarito aprovada com 100% de conformidade com a banca."
    }
