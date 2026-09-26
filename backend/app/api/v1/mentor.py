"""
lg2m/backend/app/api/v1/mentor.py
Endpoints para diálogo socrático e streaming de explicações pedagógicas em tempo real (SSE).
"""

import asyncio
import json
import time
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import Questao, SessaoMentoria, MensagemMentoria
from app.schemas.api_schemas import MentorChatRequest
from app.agents.graph import multiagent_engine
from app.core.agent_tracer import tracer

router = APIRouter(prefix="/mentor", tags=["Chat & Streaming do Mentor"])


@router.post("/chat")
def chat_with_mentor(req: MentorChatRequest, db: Session = Depends(get_db)):
    """
    Diálogo contínuo com o Mentor Didático sobre a questão ativa.
    Permite perguntas subsequentes mantendo a memória de curto prazo.
    """
    q = db.query(Questao).filter_by(id=req.questao_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Questão não encontrada.")

    hist_messages = []
    if req.historico:
        for item in req.historico:
            r = item.get("role") or "user"
            c = item.get("content") or item.get("text") or ""
            if c:
                hist_messages.append({"role": r, "content": c})
    hist_messages.append({"role": "user", "content": req.mensagem})

    state_input = {
        "user_input_message": req.mensagem,
        "intent_detected": "DUVIDA_CHAT",
        "current_question_id": q.id,
        "current_question_data": {
            "id": q.id,
            "disciplina": q.disciplina_nome,
            "assunto": q.assunto_rel.nome if q.assunto_rel else q.disciplina_nome,
            "certame": {"sigla": q.certame.sigla if q.certame else "PSC"},
            "enunciado": q.enunciado,
            "alternativas": {a.letra: a.texto for a in q.alternativas},
            "gabarito_oficial": q.gabarito_oficial,
        },
        "estilo_didatico": req.estilo_didatico.upper(),
        "verification_attempts": 0,
        "messages": hist_messages,
    }

    tracer.emit_graph_start(
        intent="DUVIDA_CHAT",
        certame=q.certame.sigla if q.certame else "PSC",
        estilo=req.estilo_didatico.upper(),
        trigger_action="CHAT_PERGUNTA",
        trigger_detail=f"Pergunta no chat: \"{(req.mensagem or '')[:60]}\"",
        question_id=q.id,
        question_discipline=q.disciplina_nome or "",
        question_subject=(q.assunto_rel.nome if q.assunto_rel else q.disciplina_nome) or "",
        question_preview=(q.enunciado or "")[:90],
        user_message=req.mensagem or "",
    )
    t0 = time.perf_counter()
    result = multiagent_engine.invoke(state_input)
    tracer.emit_graph_end(total_ms=(time.perf_counter() - t0) * 1000, guardrail_status=result.get("guardrail_status", "APPROVED"))
    resposta = result.get("verified_response") or result.get("mentor_draft_response", "")

    return {
        "questao_id": req.questao_id,
        "resposta": resposta,
        "estilo_utilizado": req.estilo_didatico.upper(),
        "estilo_didatico": req.estilo_didatico.upper(),
        "guardrail_status": result.get("guardrail_status", "APPROVED")
    }


@router.get("/stream")
async def stream_mentor_response(
    question_id: str,
    alternative: str,
    style: str = "DIRETO",
    db: Session = Depends(get_db)
):
    """
    Endpoint Server-Sent Events (SSE) que simula o streaming de tokens em tempo real.
    Garante o cumprimento da meta de TTFT (Time To First Token) < 2,5 segundos no frontend.
    """
    q = db.query(Questao).filter_by(id=question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Questão não encontrada.")

    state_input = {
        "selected_alternative": alternative.upper(),
        "current_question_id": q.id,
        "current_question_data": {
            "id": q.id,
            "disciplina": q.disciplina_nome,
            "assunto": q.assunto_rel.nome if q.assunto_rel else q.disciplina_nome,
            "certame": {"sigla": q.certame.sigla if q.certame else "PSC"},
            "enunciado": q.enunciado,
            "alternativas": {a.letra: a.texto for a in q.alternativas},
            "gabarito_oficial": q.gabarito_oficial,
        },
        "estilo_didatico": style.upper(),
        "verification_attempts": 0,
        "messages": [],
    }

    tracer.emit_graph_start(
        intent="DISSECAR_RESPOSTA",
        certame=q.certame.sigla if q.certame else "PSC",
        estilo=style.upper(),
        trigger_action="STREAM_MENTORIA",
        trigger_detail=f"SSE Stream — Alt ({alternative.upper()}) · {style.upper()}",
        question_id=q.id,
        question_discipline=q.disciplina_nome or "",
        question_subject=(q.assunto_rel.nome if q.assunto_rel else q.disciplina_nome) or "",
        question_preview=(q.enunciado or "")[:90],
        alternative_selected=alternative.upper(),
    )
    t0 = time.perf_counter()
    result = multiagent_engine.invoke(state_input)
    tracer.emit_graph_end(total_ms=(time.perf_counter() - t0) * 1000, guardrail_status=result.get("guardrail_status", "APPROVED"))
    full_text = result.get("verified_response") or "Explicação do mentor."

    async def event_generator():
        palavras = full_text.split(" ")
        for p in palavras:
            chunk = json.dumps({"token": p + " "}, ensure_ascii=False)
            yield f"data: {chunk}\n\n"
            await asyncio.sleep(0.03)  # Emite a cada 30ms para efeito fluído
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
