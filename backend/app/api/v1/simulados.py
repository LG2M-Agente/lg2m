"""
lg2m/backend/app/api/v1/simulados.py
Endpoints para criação, resolução e diagnóstico de Simulados Gerais Oficiais e Temáticos.
"""

from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func

from app.core.database import get_db
from app.models.entities import Simulado, ItemSimulado, Questao, PerfilEstudante, TentativaQuestao
from app.schemas.api_schemas import SimuladoCreateRequest, SimuladoSubmitRequest
from app.agents.profiler_agent import diagnose_simulado_battery

router = APIRouter(prefix="/simulados", tags=["Simulados Gerais & Temáticos"])


@router.post("")
@router.post("/")
@router.post("/create")
def create_simulado(req: SimuladoCreateRequest, db: Session = Depends(get_db)):
    """
    Gera um novo simulado:
    - GERAL: Seleciona bloco balanceado de questões respeitando o certame (PSC/SIS) e etapa.
    - TEMATICO: Bloco focado em uma disciplina específica com quantidade configurável (5, 10 ou 15 questões).
    """
    perfil_id = req.perfil_id
    if not perfil_id:
        p_demo = db.query(PerfilEstudante).first()
        perfil_id = p_demo.id if p_demo else None

    # Consulta questões elegíveis
    query = db.query(Questao).join(Questao.certame).filter(
        Questao.etapa_edicao == req.etapa
    )

    if req.certame_sigla and req.certame_sigla != "ALL":
        query = query.filter(Questao.certame.has(sigla=req.certame_sigla))

    if req.tipo == "TEMATICO" and req.disciplina_foco:
        query = query.filter(Questao.disciplina_nome.ilike(f"%{req.disciplina_foco}%"))

    # Sorteia as questões
    candidatas = query.order_by(func.random()).limit(req.quantidade_questoes).all()
    if not candidatas:
        raise HTTPException(status_code=400, detail="Não foram encontradas questões suficientes para os critérios selecionados.")

    # Cria registro do simulado
    novo_simulado = Simulado(
        perfil_id=perfil_id,
        certame_sigla=req.certame_sigla,
        etapa=req.etapa,
        tipo=req.tipo,
        disciplina_foco=req.disciplina_foco if req.tipo == "TEMATICO" else None,
        total_questoes=len(candidatas),
        total_acertos=0,
        tempo_limite_minutos=180 if req.tipo == "GERAL" else len(candidatas) * 3,
        status="EM_ANDAMENTO",
    )
    db.add(novo_simulado)
    db.flush()

    for idx, q in enumerate(candidatas, 1):
        item = ItemSimulado(
            simulado_id=novo_simulado.id,
            questao_id=q.id,
            ordem=idx,
        )
        db.add(item)

    db.commit()

    itens_caderno = []
    for idx, q in enumerate(candidatas, 1):
        itens_caderno.append({
            "ordem": idx,
            "questao_id": q.id,
            "disciplina": q.disciplina_nome,
            "assunto": q.assunto_rel.nome if q.assunto_rel else q.disciplina_nome,
            "enunciado": q.enunciado,
            "texto_base": q.texto_base,
            "alternativas": {a.letra: a.texto for a in q.alternativas},
            "tem_imagem": q.tem_imagem,
        })

    return {
        "simulado_id": novo_simulado.id,
        "certame": req.certame_sigla,
        "etapa": req.etapa,
        "tipo": req.tipo,
        "total_questoes": len(candidatas),
        "tempo_limite_minutos": novo_simulado.tempo_limite_minutos,
        "status": "EM_ANDAMENTO",
        "questoes": itens_caderno,
        "itens": itens_caderno,
    }


@router.get("/{simulado_id}")
def get_simulado(simulado_id: str, db: Session = Depends(get_db)):
    """Carrega o caderno completo do simulado para resolução (gabarito oculto)."""
    sim = db.query(Simulado).filter_by(id=simulado_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulado não encontrado.")

    itens_formatados = []
    for item in sim.itens:
        q = db.query(Questao).filter_by(id=item.questao_id).first()
        if q:
            itens_formatados.append({
                "ordem": item.ordem,
                "questao_id": q.id,
                "disciplina": q.disciplina_nome,
                "assunto": q.assunto_rel.nome if q.assunto_rel else q.disciplina_nome,
                "enunciado": q.enunciado,
                "texto_base": q.texto_base,
                "alternativas": {a.letra: a.texto for a in q.alternativas},
                "tem_imagem": q.tem_imagem,
                "resposta_submetida": item.alternativa_marcada,
            })

    itens_formatados.sort(key=lambda x: x["ordem"])

    return {
        "simulado_id": sim.id,
        "certame": sim.certame_sigla,
        "etapa": sim.etapa,
        "tipo": sim.tipo,
        "total_questoes": sim.total_questoes,
        "tempo_limite_minutos": sim.tempo_limite_minutos,
        "status": sim.status,
        "questoes": itens_formatados,
    }


@router.post("/{simulado_id}/submit")
def submit_simulado(
    simulado_id: str,
    req: SimuladoSubmitRequest,
    db: Session = Depends(get_db)
):
    """
    Envia as respostas finais do simulado, calcula pontuação e gera Relatório Diagnóstico.
    """
    sim = db.query(Simulado).filter_by(id=simulado_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulado não encontrado.")

    total_acertos = 0
    relatorio_itens = []
    desempenho_por_disciplina = {}

    for item in sim.itens:
        q = db.query(Questao).filter_by(id=item.questao_id).first()
        marcada = req.respostas.get(q.id, "").upper()
        gab_real = q.gabarito_oficial.upper()
        acertou = (marcada == gab_real and marcada != "")

        if acertou:
            total_acertos += 1

        item.alternativa_marcada = marcada or None
        item.acertou = acertou

        disc = q.disciplina_nome
        if disc not in desempenho_por_disciplina:
            desempenho_por_disciplina[disc] = {"total": 0, "acertos": 0}
        desempenho_por_disciplina[disc]["total"] += 1
        if acertou:
            desempenho_por_disciplina[disc]["acertos"] += 1

        relatorio_itens.append({
            "ordem": item.ordem,
            "questao_id": q.id,
            "disciplina": disc,
            "assunto": q.assunto_rel.nome if q.assunto_rel else disc,
            "alternativa_marcada": marcada,
            "gabarito_oficial": gab_real,
            "acertou": acertou,
            "dissecar_link": f"/api/v1/attempts/{q.id}",
        })

    sim.total_acertos = total_acertos
    sim.tempo_utilizado_segundos = req.tempo_utilizado_segundos
    sim.status = "FINALIZADO"
    db.commit()

    taxa_aproveitamento = round((total_acertos / max(1, sim.total_questoes)) * 100.0, 1)

    # Aciona o Agente Profiler para diagnóstico pedagógico reflexivo e atualização do dossiê cognitivo
    diagnostico_ia = diagnose_simulado_battery(sim.id, db)

    return {
        "simulado_id": sim.id,
        "total_questoes": sim.total_questoes,
        "total_acertos": total_acertos,
        "acertos": total_acertos,
        "aproveitamento_percentual": taxa_aproveitamento,
        "tempo_gasto_segundos": req.tempo_utilizado_segundos,
        "desempenho_por_disciplina": desempenho_por_disciplina,
        "diagnostico_ia": diagnostico_ia,
        "itens": relatorio_itens,
    }
