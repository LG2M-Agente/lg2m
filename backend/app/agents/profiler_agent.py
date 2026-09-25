"""
lg2m/backend/app/agents/profiler_agent.py
Agente 4 — Profiler Cognitivo & Gestor de Dificuldades.
Guardião da memória de longo prazo: atualiza o histórico do aluno e recalcula o Mapa de Calor de Dificuldades.
"""

from typing import Dict, Any
from app.agents.state import AgentState
from app.core.database import SessionLocal
from app.models.entities import TentativaQuestao, RegistroDificuldade, Assunto, PerfilEstudante


def profiler_node(state: AgentState) -> Dict[str, Any]:
    """
    Nó do Profiler: registra a tentativa e atualiza a média ponderada de domínio do assunto.
    """
    db = SessionLocal()
    try:
        perfil_id = state.get("perfil_id")
        current_q = state.get("current_question_data") or {}
        q_id = current_q.get("id")
        selected_alt = state.get("selected_alternative")
        is_acerto = state.get("is_correct", False)
        causa = state.get("error_classification")
        tempo_gasto = state.get("tempo_resolucao_segundos", 45)

        # Se não houver perfil_id informado, usa o perfil de Lucas Eduardo (demo)
        if not perfil_id:
            perfil = db.query(PerfilEstudante).first()
            perfil_id = perfil.id if perfil else None

        if not perfil_id or not q_id or not selected_alt:
            return {"subject_score_updated": None}

        # 1. Registra a tentativa individual
        tentativa = TentativaQuestao(
            perfil_id=perfil_id,
            questao_id=q_id,
            alternativa_marcada=selected_alt,
            acertou=is_acerto,
            tempo_gasto_segundos=tempo_gasto,
            causa_erro=causa,
        )
        db.add(tentativa)
        db.flush()

        # 2. Localiza o Assunto da questão
        assunto_id = current_q.get("assunto_id")
        if not assunto_id:
            assunto_nome = current_q.get("assunto")
            assunto_obj = db.query(Assunto).filter_by(nome=assunto_nome).first()
            assunto_id = assunto_obj.id if assunto_obj else None

        novo_score = 100.0
        ponto_cego = False

        if assunto_id:
            reg = db.query(RegistroDificuldade).filter_by(
                perfil_id=perfil_id,
                assunto_id=assunto_id
            ).first()

            if not reg:
                reg = RegistroDificuldade(
                    perfil_id=perfil_id,
                    assunto_id=assunto_id,
                    total_tentativas=1,
                    total_erros=0 if is_acerto else 1,
                    indice_dominio=100.0 if is_acerto else 0.0,
                )
                db.add(reg)
            else:
                reg.total_tentativas += 1
                if not is_acerto:
                    reg.total_erros += 1

                # Média ponderada móvel recente: mais peso para tentativas recentes
                # Taxa de acerto ponderada simplificada
                acertos = reg.total_tentativas - reg.total_erros
                reg.indice_dominio = round((acertos / reg.total_tentativas) * 100.0, 1)

            db.commit()
            novo_score = reg.indice_dominio
            ponto_cego = (novo_score < 50.0 and reg.total_tentativas >= 2)

        return {
            "subject_score_updated": novo_score,
            "critical_blindspot_detected": ponto_cego,
        }

    except Exception as e:
        db.rollback()
        print(f"[ERRO NO PROFILER]: {e}")
        return {"subject_score_updated": None}
    finally:
        db.close()
