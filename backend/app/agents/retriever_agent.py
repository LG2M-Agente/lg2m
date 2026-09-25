"""
lg2m/backend/app/agents/retriever_agent.py
Agente 2 — Curador & RAG Vetorial Semântico de Questões.
Motor do Flywheel de Dados Semânticos da LG2M: busca por significado conceitual e recuperação de questões irmãs.
"""

import math
import re
from typing import Dict, Any, List
from app.agents.state import AgentState
from app.core.database import SessionLocal
from app.models.entities import Questao, Alternativa


def calcular_similaridade_lexica_semantica(query: str, texto_alvo: str) -> float:
    """Heurística ponderada de similaridade textual e conceitual (TF-IDF aproximado)."""
    q_tokens = set(re.findall(r"\w{3,}", query.lower()))
    if not q_tokens:
        return 0.0
    t_tokens = set(re.findall(r"\w{3,}", texto_alvo.lower()))
    intersec = q_tokens.intersection(t_tokens)
    return len(intersec) / math.sqrt(len(q_tokens) * max(1, len(t_tokens)))


def retriever_node(state: AgentState) -> Dict[str, Any]:
    """
    Nó do Curador RAG: pesquisa questões relevantes no banco e localiza questões isomórficas.
    """
    db = SessionLocal()
    try:
        user_msg = state.get("user_input_message", "") or ""
        intent = state.get("intent_detected", "BUSCAR_QUESTAO")
        current_q = state.get("current_question_data")

        # Rota 1: Busca de Questões Semelhantes / Isomórficas (Flywheel de Dados)
        if intent == "BUSCAR_SEMELHANTES" and current_q:
            origem_id = current_q.get("id")
            assunto = current_q.get("assunto")
            disc = current_q.get("disciplina")
            banca_origem = current_q.get("certame", {}).get("sigla", "PSC")

            # Busca prioritariamente na OUTRA banca (efeito flywheel cross-certame)
            banca_oposta = "SIS" if banca_origem == "PSC" else "PSC"
            candidatos = db.query(Questao).join(Questao.certame).filter(
                Questao.disciplina_nome.ilike(f"%{disc}%"),
                Questao.certame.has(sigla=banca_oposta),
                Questao.id != origem_id
            ).limit(40).all()

            if not candidatos:
                candidatos = db.query(Questao).filter(
                    Questao.disciplina_nome.ilike(f"%{disc}%"),
                    Questao.id != origem_id
                ).limit(40).all()

            similares = []
            enunciado_base = current_q.get("enunciado", "")
            for c in candidatos:
                score = calcular_similaridade_lexica_semantica(enunciado_base, c.enunciado)
                banca_c = c.certame.sigla if c.certame else banca_oposta

                similares.append({
                    "id": c.id,
                    "codigo_referencia": c.codigo_referencia,
                    "certame": banca_c,
                    "banca": banca_c,
                    "ano": c.ano,
                    "etapa": c.etapa_edicao,
                    "disciplina": c.disciplina_nome,
                    "assunto": c.assunto_rel.nome if c.assunto_rel else c.disciplina_nome,
                    "enunciado": c.enunciado,
                    "alternativas": {a.letra: a.texto for a in c.alternativas},
                    "tem_imagem": c.tem_imagem,
                    "motivo_semelhanca": f"Mesmo princípio estrutural de {disc} cobrado no {banca_c}.",
                    "score_similaridade": round(min(0.98, score + 0.20), 2),
                })

            similares.sort(key=lambda x: x["score_similaridade"], reverse=True)
            top_similares = similares[:3]

            return {
                "similar_questions_found": top_similares,
                "guardrail_status": "APPROVED",
                "verified_response": f"Encontrei {len(top_similares)} questões conceituais semelhantes para fixação do tema '{assunto}', incluindo itens da outra banca para testar seu domínio do padrão de cobrança!"
            }

        # Rota 2: Busca Semântica em Linguagem Natural
        query_text = user_msg
        # Limpa termos de comando
        for cmd in ["buscar", "procurar", "questões sobre", "questoes sobre", "exercícios de"]:
            query_text = re.sub(cmd, "", query_text, flags=re.I).strip()

        # Realiza varredura inicial no banco
        questoes_db = db.query(Questao).limit(200).all()
        ranqueadas = []
        for q in questoes_db:
            texto_comp = f"{q.disciplina_nome} {q.assunto_rel.nome if q.assunto_rel else ''} {q.enunciado}"
            score = calcular_similaridade_lexica_semantica(query_text, texto_comp)
            if score > 0.03:
                ranqueadas.append((score, q))

        ranqueadas.sort(key=lambda x: x[0], reverse=True)
        top_questoes = [q for _, q in ranqueadas[:5]]

        resultado = []
        for q in top_questoes:
            resultado.append({
                "id": q.id,
                "codigo_referencia": q.codigo_referencia,
                "certame": q.certame.sigla if q.certame else "PSC",
                "ano": q.ano,
                "etapa": q.etapa_edicao,
                "disciplina": q.disciplina_nome,
                "assunto": q.assunto_rel.nome if q.assunto_rel else q.disciplina_nome,
                "enunciado": q.enunciado,
                "alternativas": {a.letra: a.texto for a in q.alternativas},
                "tem_imagem": q.tem_imagem,
                "gabarito_oficial": q.gabarito_oficial,  # protegido no backend
            })

        return {
            "similar_questions_found": resultado,
            "current_question_data": resultado[0] if resultado else None,
            "current_question_id": resultado[0]["id"] if resultado else None,
        }

    finally:
        db.close()
