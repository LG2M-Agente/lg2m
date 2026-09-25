#!/usr/bin/env python3
"""
lg2m/backend/scripts/build_vector_index.py
Script de indexação vetorial densa das 5.771 questões do LG2M utilizando FastEmbed (ONNX CPU).
Gera embeddings sobre o bloco semântico enriquecido ([Disciplina] [Assunto] [Tópico] [Enunciado])
e persiste em matriz NumPy binária de alta velocidade (data/vector_index.npz).
"""

import os
import sys
import time
from pathlib import Path
import numpy as np

backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from app.core.database import SessionLocal
from app.models.entities import Questao
from fastembed import TextEmbedding


def build_vector_index():
    print("=" * 70)
    print("  INICIANDO CONSTRUÇÃO DO ÍNDICE VETORIAL DENSO (LG2M)")
    print("=" * 70)

    db = SessionLocal()
    try:
        questoes = db.query(Questao).all()
        total = len(questoes)
        print(f"Total de questões carregadas do banco: {total}")

        ids = []
        textos_enriquecidos = []

        print("\n1. Montando blocos semânticos enriquecidos...")
        for q in questoes:
            ids.append(q.id)
            assunto = q.assunto_rel.nome if q.assunto_rel else q.disciplina_nome
            topico = q.topico_especifico or ""
            # Bloco semântico estruturado para máxima densidade conceitual com Document Expansion
            desc = q.descricao_detalhada or ""
            bloco = f"[{q.disciplina_nome}] [{assunto}] {topico} | {desc} | {q.enunciado[:350]}"
            textos_enriquecidos.append(bloco)

        print(f"   [OK] {len(textos_enriquecidos)} blocos gerados.")

        print("\n2. Inicializando modelo de embeddings FastEmbed (ONNX CPU)...")
        t0 = time.perf_counter()
        model = TextEmbedding()

        print("3. Gerando vetores densos em lote (batch_size=128)...")
        embeddings_list = []
        batch_size = 128
        
        for i in range(0, total, batch_size):
            batch_texts = textos_enriquecidos[i:i + batch_size]
            batch_embs = list(model.embed(batch_texts, batch_size=batch_size))
            embeddings_list.extend(batch_embs)
            print(f"   Processados {min(i + batch_size, total)}/{total} vetores...", end="\r")

        t1 = time.perf_counter()
        total_time = t1 - t0
        print(f"\n   [OK] {len(embeddings_list)} vetores calculados em {total_time:.2f}s ({total_time/total*1000:.2f}ms/item).")

        embeddings_matrix = np.array(embeddings_list, dtype=np.float32)
        # Normalização L2 para que similaridade de cosseno seja um simples produto escalar (dot product)
        norms = np.linalg.norm(embeddings_matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1e-10
        embeddings_normalized = embeddings_matrix / norms

        out_path = backend_dir / "data" / "vector_index.npz"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            out_path,
            ids=np.array(ids),
            embeddings=embeddings_normalized
        )
        file_size_mb = out_path.stat().st_size / (1024 * 1024)
        print(f"\n4. Índice vetorial salvo com sucesso em:")
        print(f"   -> {out_path} ({file_size_mb:.2f} MB)")

        # Teste de validação rápida com query real
        print("\n5. Testando busca vetorial imediata com query de teste...")
        test_query = "cálculo de velocidade e aceleração em física"
        q_emb = np.array(list(model.embed([test_query]))[0], dtype=np.float32)
        q_norm = np.linalg.norm(q_emb)
        if q_norm > 0:
            q_emb = q_emb / q_norm

        scores = np.dot(embeddings_normalized, q_emb)
        top_indices = np.argsort(scores)[::-1][:3]

        print(f"   Query: '{test_query}'")
        for rank, idx in enumerate(top_indices, 1):
            q_id = ids[idx]
            q_match = db.query(Questao).filter_by(id=q_id).first()
            print(f"   Top-{rank}: [{q_id}] Score: {scores[idx]:.4f} | {q_match.disciplina_nome} - {q_match.enunciado[:75]}...")

        print("\n" + "=" * 70)
        print("  ÍNDICE VETORIAL CONCLUÍDO COM 100% DE SUCESSO!")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    build_vector_index()
