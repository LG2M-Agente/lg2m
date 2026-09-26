"""
lg2m/backend/app/api/v1/questions.py
Endpoints REST para pesquisa semântica, catálogo e recuperação de questões semelhantes.
"""

import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.models.entities import Questao, Certame, Assunto
from app.schemas.api_schemas import QuestionSearchRequest, QuestionDetailResponse
from app.agents.graph import multiagent_engine
from app.services.vector_search import vector_search_service
from app.services.image_resolver import ImageResolver

router = APIRouter(prefix="/questions", tags=["Questões & Busca Semântica"])


@router.get("/search", response_model=List[QuestionDetailResponse])
def search_questions_get(
    query: str = Query(..., min_length=2, description="Texto de busca livre"),
    certame: str = Query(None, description="PSC, SIS ou ALL"),
    etapa: str = Query(None, description="1, 2, 3"),
    disciplina: str = Query(None, description="Disciplina"),
    ano: int = Query(None, description="Ano"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    req = QuestionSearchRequest(
        query=query, certame=certame, etapa=etapa, disciplina=disciplina, ano=ano, limit=limit
    )
    return search_questions(req, db)


@router.post("/search", response_model=List[QuestionDetailResponse])
def search_questions(req: QuestionSearchRequest, db: Session = Depends(get_db)):
    """
    Busca semântica híbrida: combina filtros relacionais SQL (certame, etapa, disciplina, ano)
    com relevância vetorial densa por similaridade de cosseno em linguagem natural.
    O gabarito oficial é rigorosamente blindado no backend.
    """
    query_builder = db.query(Questao)

    # Filtros relacionais
    tem_filtro_relacional = False
    if req.certame and req.certame != "ALL":
        query_builder = query_builder.join(Questao.certame).filter(Certame.sigla == req.certame)
        tem_filtro_relacional = True

    if req.etapa and req.etapa != "ALL":
        query_builder = query_builder.filter(Questao.etapa_edicao == req.etapa)
        tem_filtro_relacional = True

    if req.disciplina and req.disciplina != "ALL":
        query_builder = query_builder.filter(Questao.disciplina_nome.ilike(f"%{req.disciplina}%"))
        tem_filtro_relacional = True

    if req.ano:
        query_builder = query_builder.filter(Questao.ano == req.ano)
        tem_filtro_relacional = True

    resultados = []

    # 1. Tenta Busca Vetorial Densa Real com FastEmbed
    if vector_search_service.is_ready() and req.query and req.query.strip():
        allowed_ids = None
        if tem_filtro_relacional:
            candidatos_rel = query_builder.with_entities(Questao.id).all()
            allowed_ids = {row[0] for row in candidatos_rel}

        vector_matches = vector_search_service.search(
            query=req.query,
            top_k=req.limit,
            allowed_ids=allowed_ids,
            min_score=0.10
        )
        if vector_matches:
            ids_em_ordem = [qid for qid, _ in vector_matches]
            # Recupera objetos do banco mantendo a ordem vetorial
            questoes_map = {q.id: q for q in db.query(Questao).filter(Questao.id.in_(ids_em_ordem)).all()}
            resultados = [questoes_map[qid] for qid in ids_em_ordem if qid in questoes_map]

    # 2. Fallback por termos-chave se o índice não retornou itens
    if not resultados:
        termos = [t.strip() for t in req.query.split() if len(t.strip()) >= 3]
        if termos:
            condicoes = []
            for t in termos:
                condicoes.append(Questao.enunciado.ilike(f"%{t}%"))
                condicoes.append(Questao.disciplina_nome.ilike(f"%{t}%"))
                condicoes.append(Questao.topico_especifico.ilike(f"%{t}%"))
            query_builder = query_builder.filter(or_(*condicoes))
        resultados = query_builder.limit(req.limit).all()

    # Formata resposta sem expor gabarito
    response_items = []
    for q in resultados:
        response_items.append(QuestionDetailResponse(
            id=q.id,
            codigo_referencia=q.codigo_referencia,
            certame=q.certame.sigla if q.certame else "PSC",
            ano=q.ano,
            etapa=q.etapa_edicao,
            numero_questao=q.numero_questao,
            disciplina=q.disciplina_nome,
            area_conhecimento=q.area_conhecimento,
            assunto=q.assunto_rel.nome if q.assunto_rel else q.disciplina_nome,
            texto_base=q.texto_base,
            enunciado=q.enunciado,
            alternativas={a.letra: a.texto for a in q.alternativas},
            tem_imagem=q.tem_imagem,
            imagens=q.imagens or [],
            possui_formula_matematica=q.possui_formula_matematica,
            descricao_detalhada=q.descricao_detalhada,
            curadoria=q.curadoria,
            tags=q.tags or [],
        ))

    return response_items


@router.get("/{question_id}", response_model=QuestionDetailResponse)
def get_question_detail(question_id: str, db: Session = Depends(get_db)):
    """Retorna detalhes da questão sem expor o gabarito antes da resolução."""
    q = db.query(Questao).filter_by(id=question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Questão não encontrada no acervo oficial.")

    return QuestionDetailResponse(
        id=q.id,
        codigo_referencia=q.codigo_referencia,
        certame=q.certame.sigla if q.certame else "PSC",
        ano=q.ano,
        etapa=q.etapa_edicao,
        numero_questao=q.numero_questao,
        disciplina=q.disciplina_nome,
        area_conhecimento=q.area_conhecimento,
        assunto=q.assunto_rel.nome if q.assunto_rel else q.disciplina_nome,
        texto_base=q.texto_base,
        enunciado=q.enunciado,
        alternativas={a.letra: a.texto for a in q.alternativas},
        tem_imagem=q.tem_imagem,
        imagens=q.imagens or [],
        possui_formula_matematica=q.possui_formula_matematica,
        descricao_detalhada=q.descricao_detalhada,
        curadoria=q.curadoria,
        tags=q.tags or [],
    )


@router.get("/{question_id}/similar", response_model=List[dict])
def get_similar_questions(question_id: str, db: Session = Depends(get_db)):
    """
    Ativa o Flywheel de Dados Semânticos: localiza itens análogos de outras bancas ou anos
    que compartilham a mesma estrutura de raciocínio.
    """
    q = db.query(Questao).filter_by(id=question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Questão de referência não encontrada.")

    # Aciona o motor multiagente via nó retriever
    state_input = {
        "intent_detected": "BUSCAR_SEMELHANTES",
        "current_question_id": q.id,
        "current_question_data": {
            "id": q.id,
            "disciplina": q.disciplina_nome,
            "assunto": q.assunto_rel.nome if q.assunto_rel else q.disciplina_nome,
            "certame": {"sigla": q.certame.sigla if q.certame else "PSC"},
            "enunciado": q.enunciado,
        },
        "messages": [],
    }

    result = multiagent_engine.invoke(state_input)
    return result.get("similar_questions_found", [])


@router.get("/{question_id}/image", response_class=FileResponse)
def get_question_image(question_id: str, img_index: int = 0, db: Session = Depends(get_db)):
    """
    Retorna o arquivo de figura/gráfico original da questão em formato PNG.
    """
    q = db.query(Questao).filter_by(id=question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Questão não encontrada.")

    img_path = ImageResolver.resolve_image(
        question_id=q.id,
        numero_questao=q.numero_questao,
        ano=q.ano,
        imagens_data=q.imagens,
        img_index=img_index
    )
    if not img_path or not os.path.exists(img_path):
        raise HTTPException(status_code=404, detail="Imagem não encontrada no acervo para este item.")

    return FileResponse(img_path, media_type="image/png")

