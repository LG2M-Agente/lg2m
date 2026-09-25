"""
lg2m/backend/app/api/v1/attempts.py
Endpoints REST para submissão de respostas com Gabarito Blindado e acionamento do fluxo multiagente.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import Questao, PerfilEstudante
from app.schemas.api_schemas import QuestionAttemptRequest, QuestionAttemptResponse
from app.agents.graph import multiagent_engine

router = APIRouter(prefix="/attempts", tags=["Resolução Interativa & Mentoria"])


@router.post("/{question_id}", response_model=QuestionAttemptResponse)
def submit_question_attempt(
    question_id: str,
    req: QuestionAttemptRequest,
    db: Session = Depends(get_db)
):
    """
    Submete a resposta do estudante.
    O gabarito oficial só é revelado após a confirmação.
    Aciona a rede multiagente para dissecar o distrator no estilo didático selecionado.
    """
    q = db.query(Questao).filter_by(id=question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Questão não encontrada.")

    letra_marcada = req.alternativa_marcada.upper()
    gabarito_real = q.gabarito_oficial.upper()
    acertou = (letra_marcada == gabarito_real)

    # Identifica ou cria perfil padrão para demonstração
    perfil_id = req.perfil_id
    if not perfil_id:
        p_demo = db.query(PerfilEstudante).first()
        perfil_id = p_demo.id if p_demo else None

    # Monta estado para o grafo LangGraph
    state_input = {
        "user_input_message": f"Submeti alternativa ({letra_marcada})",
        "selected_alternative": letra_marcada,
        "perfil_id": perfil_id,
        "current_question_id": q.id,
        "current_question_data": {
            "id": q.id,
            "disciplina": q.disciplina_nome,
            "assunto": q.assunto_rel.nome if q.assunto_rel else q.disciplina_nome,
            "assunto_id": q.assunto_id,
            "certame": {"sigla": q.certame.sigla if q.certame else "PSC"},
            "enunciado": q.enunciado,
            "alternativas": {a.letra: a.texto for a in q.alternativas},
            "gabarito_oficial": gabarito_real,
        },
        "estilo_didatico": req.estilo_didatico.upper(),
        "tempo_resolucao_segundos": req.tempo_gasto_segundos,
        "verification_attempts": 0,
        "messages": [],
    }

    # Executa a máquina de estados do LangGraph (Router -> Mentor -> Guardrail -> Profiler)
    result = multiagent_engine.invoke(state_input)

    return QuestionAttemptResponse(
        acertou=acertou,
        gabarito_oficial=gabarito_real,
        alternativa_marcada=letra_marcada,
        explicacao_mentor=result.get("verified_response", "Explicação gerada pelo mentor."),
        estilo_didatico=req.estilo_didatico.upper(),
        causa_erro=result.get("error_classification"),
        novo_score_assunto=result.get("subject_score_updated"),
        ponto_cego_detectado=result.get("critical_blindspot_detected", False),
    )
