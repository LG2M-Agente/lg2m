#!/usr/bin/env python3
"""
inspect_canonical.py — Utilitário CLI para visualização e busca na base canônica de questões do LG2M.

Uso:
  python inspect_canonical.py                          # Mostra estatísticas e 3 questões aleatórias
  python inspect_canonical.py --id PSC_2025_E1_LP_01   # Inspeciona uma questão específica detalhadamente
  python inspect_canonical.py --disciplina Física      # Lista 5 questões da disciplina
  python inspect_canonical.py --query "leis de newton" # Realiza busca vetorial/semântica instantânea
"""

import argparse
import json
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from app.core.database import SessionLocal
from app.models.entities import Questao, Alternativa, Assunto, Certame


def exibir_questao(q: Questao, db):
    print("=" * 75)
    print(f" ID: {q.id}  |  Código: {q.codigo_referencia}")
    cert_sigla = q.certame.sigla if q.certame else "N/A"
    print(f" Certame: {cert_sigla} ({q.ano} - Etapa {q.etapa_edicao})  |  Questão nº: {q.numero_questao}")
    print(f" Disciplina: {q.disciplina_nome} ({q.area_conhecimento})")
    assunto_nome = q.assunto_rel.nome if q.assunto_rel else "N/A"
    print(f" Assunto: {assunto_nome}")
    print(f" Tópico: {q.topico_especifico or 'N/A'}")
    print(f" Dificuldade Estimada: {q.tags[-1] if q.tags and 'dificuldade_' in q.tags[-1] else 'MEDIO'}")
    print(f" Fórmulas: {'Sim' if q.possui_formula_matematica else 'Não'}  |  Imagens: {'Sim' if q.tem_imagem else 'Não'}")
    print("-" * 75)

    if q.texto_base:
        print("\n[TEXTO-BASE]:")
        print(f"  {q.texto_base[:300]}...")

    print("\n[ENUNCIADO]:")
    print(f"  {q.enunciado}")

    print("\n[ALTERNATIVAS]:")
    alts = db.query(Alternativa).filter_by(questao_id=q.id).order_by(Alternativa.letra).all()
    for alt in alts:
        correta_tag = " [GABARITO OFICIAL]" if alt.eh_correta else f" (Distrator: {alt.tipo_pegadinha})"
        print(f"  ({alt.letra}) {alt.texto}{correta_tag}")

    print("=" * 75 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Visualizador da Base Canônica LG2M")
    parser.add_argument("--id", type=str, help="ID canônico da questão")
    parser.add_argument("--disciplina", type=str, help="Filtrar por disciplina")
    parser.add_argument("--query", type=str, help="Buscar por termo semântico")
    parser.add_argument("--limite", type=int, default=3, help="Número de questões a exibir")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        total = db.query(Questao).count()
        if not args.id and not args.disciplina and not args.query:
            print("=" * 75)
            print(f"  BASE CANÔNICA LG2M — TOTAL DE {total} QUESTÕES CERTIFICADAS")
            print("=" * 75)
            print("Exibindo uma amostra de questões enriquecidas:\n")
            amostra = db.query(Questao).order_by(Questao.ano.desc()).limit(args.limite).all()
            for q in amostra:
                exibir_questao(q, db)
            print("Dica: Use --query 'termo' para buscar ou --id 'ID' para ver uma questão específica.")
            return

        if args.id:
            q = db.query(Questao).filter_by(id=args.id).first()
            if not q:
                print(f"[ERRO] Questão com ID '{args.id}' não encontrada.")
            else:
                exibir_questao(q, db)
            return

        if args.disciplina:
            qs = db.query(Questao).filter(Questao.disciplina_nome.ilike(f"%{args.disciplina}%")).limit(args.limite).all()
            print(f"Encontradas {len(qs)} questões para a disciplina '{args.disciplina}':\n")
            for q in qs:
                exibir_questao(q, db)
            return

        if args.query:
            # Usa o VectorSearchService para buscar pelo vetor semântico
            from app.services.vector_search import vector_search_service
            resultados = vector_search_service.search(args.query, top_k=args.limite)
            print(f"Busca Semântica Vetorial por: '{args.query}'\n")
            for qid, score in resultados:
                q = db.query(Questao).filter_by(id=qid).first()
                if q:
                    print(f">>> Similaridade por Cosseno: {score:.4f} <<<")
                    exibir_questao(q, db)

    finally:
        db.close()


if __name__ == "__main__":
    main()
