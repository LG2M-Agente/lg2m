"""
lg2m/backend/app/api/v1/student.py
Endpoints para Perfil Cognitivo, Heatmap de Domínio e Recomendações Pedagógicas.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.core.database import get_db
from app.models.entities import Usuario, PerfilEstudante, RegistroDificuldade, TentativaQuestao, Assunto, Questao, Disciplina
from app.schemas.api_schemas import (
    StudentProfileResponse,
    StudentProfileUpdateRequest,
    StudentHeatmapResponse,
    HeatmapItem,
    QuestionDetailResponse
)

router = APIRouter(prefix="/student", tags=["Estudante & Heatmap"])


def _obter_ou_criar_perfil_demo(db: Session, perfil_id: Optional[str] = None) -> PerfilEstudante:
    """Recupera o perfil solicitado ou o perfil demo ativo."""
    if perfil_id:
        perfil = db.query(PerfilEstudante).filter(PerfilEstudante.id == perfil_id).first()
        if perfil:
            return perfil

    # Busca o primeiro perfil existente ou cria um novo
    perfil = db.query(PerfilEstudante).first()
    if not perfil:
        usuario = db.query(Usuario).first()
        if not usuario:
            usuario = Usuario(
                email="estudante.demo@lg2m.edu.br",
                nome="Lucas Eduardo",
                tipo_plano="PREMIUM"
            )
            db.add(usuario)
            db.commit()
            db.refresh(usuario)

        perfil = PerfilEstudante(
            usuario_id=usuario.id,
            certame_foco="PSC",
            estilo_didatico_padrao="DIRETO"
        )
        db.add(perfil)
        db.commit()
        db.refresh(perfil)

    return perfil


@router.get("/profile", response_model=StudentProfileResponse)
def get_student_profile(
    perfil_id: Optional[str] = Query(None, description="ID do perfil"),
    db: Session = Depends(get_db)
):
    """
    Retorna o perfil do estudante, incluindo taxa de acerto acumulada e tempo médio por questão.
    """
    perfil = _obter_ou_criar_perfil_demo(db, perfil_id)
    usuario = perfil.usuario

    tentativas = db.query(TentativaQuestao).filter(TentativaQuestao.perfil_id == perfil.id).all()
    total_tentativas = len(tentativas)
    total_acertos = sum(1 for t in tentativas if t.acertou)
    taxa_acerto = (total_acertos / total_tentativas * 100.0) if total_tentativas > 0 else 0.0
    tempo_medio = (sum(t.tempo_gasto_segundos for t in tentativas) / total_tentativas) if total_tentativas > 0 else 0.0

    pontos_cegos_count = db.query(RegistroDificuldade).filter(
        RegistroDificuldade.perfil_id == perfil.id,
        RegistroDificuldade.indice_dominio < 50.0,
        RegistroDificuldade.total_erros >= 2
    ).count()

    return StudentProfileResponse(
        usuario_id=usuario.id,
        perfil_id=perfil.id,
        nome=usuario.nome,
        email=usuario.email,
        certame_foco=perfil.certame_foco,
        estilo_didatico_padrao=perfil.estilo_didatico_padrao,
        total_tentativas=total_tentativas,
        total_acertos=total_acertos,
        taxa_acerto_geral=round(taxa_acerto, 1),
        pontos_cegos_count=pontos_cegos_count,
        tempo_medio_segundos=round(tempo_medio, 1)
    )


@router.patch("/profile", response_model=StudentProfileResponse)
def update_student_profile(
    req: StudentProfileUpdateRequest,
    perfil_id: Optional[str] = Query(None, description="ID do perfil"),
    db: Session = Depends(get_db)
):
    """
    Atualiza as preferências do perfil (certame foco ou estilo didático preferido).
    """
    perfil = _obter_ou_criar_perfil_demo(db, perfil_id)

    if req.certame_foco:
        perfil.certame_foco = req.certame_foco.upper()
    if req.estilo_didatico_padrao:
        perfil.estilo_didatico_padrao = req.estilo_didatico_padrao.upper()

    db.commit()
    db.refresh(perfil)

    return get_student_profile(perfil_id=perfil.id, db=db)


@router.get("/heatmap", response_model=StudentHeatmapResponse)
def get_student_heatmap(
    perfil_id: Optional[str] = Query(None, description="ID do perfil"),
    db: Session = Depends(get_db)
):
    """
    Retorna o Heatmap Cognitivo completo do estudante:
    Mapeamento de domínio por assunto, destacando pontos cegos críticos.
    """
    perfil = _obter_ou_criar_perfil_demo(db, perfil_id)

    registros = db.query(RegistroDificuldade).filter(
        RegistroDificuldade.perfil_id == perfil.id
    ).order_by(RegistroDificuldade.indice_dominio.asc()).all()

    heatmap_itens: List[HeatmapItem] = []
    pontos_cegos: List[HeatmapItem] = []

    for reg in registros:
        assunto = reg.assunto
        disciplina_nome = assunto.disciplina.nome if assunto and assunto.disciplina else "Geral"
        area_nome = assunto.disciplina.area_conhecimento if assunto and assunto.disciplina else "Geral"
        eh_cego = (reg.indice_dominio < 50.0 and reg.total_erros >= 2)

        item = HeatmapItem(
            assunto=assunto.nome if assunto else "Geral",
            disciplina=disciplina_nome,
            area=area_nome,
            total_tentativas=reg.total_tentativas,
            total_erros=reg.total_erros,
            indice_dominio=round(reg.indice_dominio, 1),
            eh_ponto_cego=eh_cego
        )
        heatmap_itens.append(item)
        if eh_cego:
            pontos_cegos.append(item)

    return StudentHeatmapResponse(
        perfil_id=perfil.id,
        total_assuntos_avaliados=len(heatmap_itens),
        pontos_cegos_count=len(pontos_cegos),
        pontos_cegos=pontos_cegos,
        heatmap=heatmap_itens
    )


@router.get("/recommendations", response_model=List[QuestionDetailResponse])
def get_recommended_questions(
    perfil_id: Optional[str] = Query(None, description="ID do perfil"),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Recomenda questões prioritárias para o estudante treinar, priorizando seus pontos cegos
    mais urgentes no certame de seu foco.
    """
    perfil = _obter_ou_criar_perfil_demo(db, perfil_id)

    # Identifica assuntos com menor domínio
    registros_criticos = db.query(RegistroDificuldade).filter(
        RegistroDificuldade.perfil_id == perfil.id
    ).order_by(RegistroDificuldade.indice_dominio.asc()).limit(3).all()

    assuntos_ids = [r.assunto_id for r in registros_criticos if r.assunto_id]

    # Busca questões do certame foco nesses assuntos
    query = db.query(Questao)
    if assuntos_ids:
        query = query.filter(Questao.assunto_id.in_(assuntos_ids))

    if perfil.certame_foco in ["PSC", "SIS"]:
        query = query.filter(Questao.certame.has(sigla=perfil.certame_foco))

    questoes = query.limit(limit).all()

    # Se não houver questões suficientes nos pontos cegos, completa com questões recentes
    if len(questoes) < limit:
        ids_ja_inclusos = [q.id for q in questoes]
        complemento = db.query(Questao).filter(
            Questao.id.notin_(ids_ja_inclusos)
        ).order_by(Questao.ano.desc()).limit(limit - len(questoes)).all()
        questoes.extend(complemento)

    res = []
    for q in questoes:
        alts = {alt.letra: alt.texto for alt in q.alternativas}
        res.append(QuestionDetailResponse(
            id=q.id,
            codigo_referencia=q.codigo_referencia,
            certame=q.certame.sigla if q.certame else "OUTRO",
            ano=q.ano,
            etapa=q.etapa,
            numero_questao=q.numero_questao,
            disciplina=q.disciplina.nome if q.disciplina else "Geral",
            area_conhecimento=q.disciplina.area_conhecimento if q.disciplina else "Geral",
            assunto=q.assunto.nome if q.assunto else "Geral",
            texto_base=q.texto_base,
            enunciado=q.enunciado,
            alternativas=alts,
            tem_imagem=q.tem_imagem,
            possui_formula_matematica=q.possui_formula_matematica,
            tags=[q.certame.sigla, f"Etapa {q.etapa}", q.disciplina.nome if q.disciplina else ""]
        ))

    return res
