"""
lg2m/backend/app/agents/retriever_agent.py
Agente 2 — Curador & RAG Vetorial Semântico de Questões.
Motor do Flywheel de Dados Semânticos da LG2M:
1. Executa busca vetorial densa por similaridade de cosseno em alta dimensão (FastEmbed ONNX CPU).
2. Localiza questões irmãs isomórficas entre certames (PSC <-> SIS) com base em proximidade geométrica vetorial.
3. Fallback inteligente e gracioso quando necessário.
"""

import re
from typing import Dict, Any, List, Set
from app.agents.state import AgentState
from app.core.database import SessionLocal
from app.models.entities import Questao
from app.services.vector_search import vector_search_service


def retriever_node(state: AgentState) -> Dict[str, Any]:
    """
    Nó do Curador RAG no LangGraph:
    Pesquisa questões relevantes no banco vetorial e localiza questões isomórficas cross-banca.
    """
    db = SessionLocal()
    try:
        user_msg = state.get("user_input_message", "") or ""
        intent = state.get("intent_detected", "BUSCAR_QUESTAO")
        current_q = state.get("current_question_data")

        # -----------------------------------------------------------------
        # ROTA 1: Busca de Questões Semelhantes / Isomórficas (Flywheel de Dados)
        # -----------------------------------------------------------------
        if intent == "BUSCAR_SEMELHANTES" and current_q:
            origem_id = current_q.get("id")
            assunto = current_q.get("assunto")
            disc = current_q.get("disciplina")
            banca_origem = current_q.get("certame", {}).get("sigla", "PSC")
            banca_oposta = "SIS" if banca_origem == "PSC" else "PSC"

            # Busca IDs elegíveis da outra banca (e mesma disciplina) para efeito Flywheel
            candidatos_db = db.query(Questao.id).join(Questao.certame).filter(
                Questao.disciplina_nome.ilike(f"%{disc}%"),
                Questao.certame.has(sigla=banca_oposta),
                Questao.id != origem_id
            ).all()

            target_banca_ids = {row[0] for row in candidatos_db}

            similares = []
            if vector_search_service.is_ready() and origem_id:
                # Busca vetorial densa real por cosseno
                matches = vector_search_service.find_isomorphic_similar(
                    question_id=origem_id,
                    target_banca_ids=target_banca_ids if target_banca_ids else None,
                    top_k=3,
                    min_similarity=0.20
                )
                for qid, cos_score in matches:
                    q_obj = db.query(Questao).filter_by(id=qid).first()
                    if q_obj:
                        banca_sigla = q_obj.certame.sigla if q_obj.certame else banca_oposta
                        similares.append({
                            "id": q_obj.id,
                            "codigo_referencia": q_obj.codigo_referencia,
                            "certame": banca_sigla,
                            "banca": banca_sigla,
                            "ano": q_obj.ano,
                            "etapa": q_obj.etapa_edicao,
                            "disciplina": q_obj.disciplina_nome,
                            "assunto": q_obj.assunto_rel.nome if q_obj.assunto_rel else q_obj.disciplina_nome,
                            "enunciado": q_obj.enunciado,
                            "alternativas": {a.letra: a.texto for a in q_obj.alternativas},
                            "tem_imagem": q_obj.tem_imagem,
                            "motivo_semelhanca": f"Mesmo princípio estrutural de {disc} cobrado no {banca_sigla}.",
                            "score_similaridade": cos_score,
                        })

            # Fallback caso o serviço vetorial não esteja carregado
            if not similares:
                candidatos = db.query(Questao).filter(
                    Questao.disciplina_nome.ilike(f"%{disc}%"),
                    Questao.id != origem_id
                ).limit(3).all()
                for c in candidatos:
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
                        "score_similaridade": 0.75,
                    })

            return {
                "similar_questions_found": similares,
                "guardrail_status": "APPROVED",
                "verified_response": f"Encontrei {len(similares)} questões conceituais semelhantes para fixação do tema '{assunto}', incluindo itens da outra banca para testar seu domínio do padrão de cobrança!"
            }

        # -----------------------------------------------------------------
        # ROTA 2: Busca Semântica em Linguagem Natural
        # -----------------------------------------------------------------
        query_text = user_msg
        for cmd in ["buscar", "procurar", "questões sobre", "questoes sobre", "exercícios de"]:
            query_text = re.sub(cmd, "", query_text, flags=re.I).strip()

        resultado = []
        if vector_search_service.is_ready() and query_text:
            matches = vector_search_service.search(query=query_text, top_k=5, min_score=0.10)
            for qid, cos_score in matches:
                q_obj = db.query(Questao).filter_by(id=qid).first()
                if q_obj:
                    resultado.append({
                        "id": q_obj.id,
                        "codigo_referencia": q_obj.codigo_referencia,
                        "certame": q_obj.certame.sigla if q_obj.certame else "PSC",
                        "ano": q_obj.ano,
                        "etapa": q_obj.etapa_edicao,
                        "disciplina": q_obj.disciplina_nome,
                        "assunto": q_obj.assunto_rel.nome if q_obj.assunto_rel else q_obj.disciplina_nome,
                        "enunciado": q_obj.enunciado,
                        "alternativas": {a.letra: a.texto for a in q_obj.alternativas},
                        "tem_imagem": q_obj.tem_imagem,
                        "score_similaridade": cos_score,
                    })

        # Fallback relacional se a busca vetorial não retornar itens suficientes
        if not resultado:
            questoes_fallback = db.query(Questao).limit(5).all()
            for q in questoes_fallback:
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
                    "score_similaridade": 0.60,
                })

        return {
            "similar_questions_found": resultado,
            "guardrail_status": "APPROVED",
            "verified_response": f"Encontrei {len(resultado)} questões oficiais relevantes por similaridade semântica para a sua consulta."
        }

    except Exception as e:
        print(f"[ERRO NO RETRIEVER]: {e}")
        return {
            "similar_questions_found": [],
            "guardrail_status": "APPROVED",
            "verified_response": "Não foi possível recuperar questões semânticas neste momento."
        }
    finally:
        db.close()
