"""
lg2m/backend/app/services/vector_search.py
Serviço de Busca Vetorial Densa e RAG Semântico Real.
Utiliza FastEmbed (ONNX CPU) para embedding da consulta e matriz NumPy normalizada
para cálculo de similaridade de cosseno em tempo sub-milissegundo.
Suporta Busca Híbrida: combina filtros determinísticos SQL com ranking vetorial contínuo.
"""

import os
import time
from pathlib import Path
from typing import List, Tuple, Optional, Set
import numpy as np
from fastembed import TextEmbedding

backend_dir = Path(__file__).resolve().parent.parent.parent


class VectorSearchService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(VectorSearchService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.index_path = backend_dir / "data" / "vector_index.npz"
        self.ids = []
        self.id_to_idx = {}
        self.embeddings = None
        self.model = None
        self._load_index()
        self._initialized = True

    def _load_index(self):
        """Carrega a matriz vetorial e inicializa o modelo de embeddings."""
        if not self.index_path.exists():
            print(f"[VectorSearchService] Aviso: Índice vetorial não encontrado em {self.index_path}. Execute build_vector_index.py.")
            return

        try:
            data = np.load(self.index_path)
            self.ids = list(data["ids"])
            self.id_to_idx = {qid: idx for idx, qid in enumerate(self.ids)}
            self.embeddings = data["embeddings"]  # Já normalizado L2
            self.model = TextEmbedding()
            print(f"[VectorSearchService] Índice vetorial carregado: {len(self.ids)} itens ({self.embeddings.shape[1]} dimensões).")
        except Exception as e:
            print(f"[VectorSearchService] Erro ao carregar índice vetorial: {e}")

    def is_ready(self) -> bool:
        return self.embeddings is not None and self.model is not None

    def embed_query(self, query: str) -> Optional[np.ndarray]:
        """Gera embedding normalizado para a consulta em linguagem natural."""
        if not self.is_ready():
            return None
        q_emb = np.array(list(self.model.embed([query]))[0], dtype=np.float32)
        norm = np.linalg.norm(q_emb)
        if norm > 0:
            q_emb = q_emb / norm
        return q_emb

    def search(
        self,
        query: str,
        top_k: int = 10,
        allowed_ids: Optional[Set[str]] = None,
        min_score: float = 0.15
    ) -> List[Tuple[str, float]]:
        """
        Busca semântica híbrida por similaridade de cosseno:
        - Calcula o produto escalar entre o vetor da consulta e os vetores do acervo.
        - Aplica máscara para permitir apenas questões que atendem aos filtros SQL (allowed_ids).
        - Retorna lista de tuplas (question_id, score_cosseno).
        """
        if not self.is_ready():
            return []

        q_vec = self.embed_query(query)
        if q_vec is None:
            return []

        # Similaridade de cosseno (como ambos são L2-normalizados, cosseno = dot product)
        scores = np.dot(self.embeddings, q_vec)

        # Se houver pré-filtro SQL, zera o score dos itens não permitidos
        if allowed_ids is not None:
            mask = np.zeros(len(self.ids), dtype=bool)
            for qid in allowed_ids:
                idx = self.id_to_idx.get(qid)
                if idx is not None:
                    mask[idx] = True
            scores = np.where(mask, scores, -1.0)

        # Ordena decrescente
        sorted_indices = np.argsort(scores)[::-1]
        results = []
        for idx in sorted_indices[:top_k]:
            score = float(scores[idx])
            if score < min_score:
                break
            results.append((self.ids[idx], round(score, 4)))

        return results

    def find_isomorphic_similar(
        self,
        question_id: str,
        target_banca_ids: Optional[Set[str]] = None,
        top_k: int = 3,
        min_similarity: float = 0.30
    ) -> List[Tuple[str, float]]:
        """
        Localiza questões irmãs (isomórficas) mais próximas no espaço vetorial.
        Pode filtrar especificamente por itens da outra banca para o efeito Flywheel.
        """
        if not self.is_ready():
            return []

        q_idx = self.id_to_idx.get(question_id)
        if q_idx is None:
            return []

        origin_vec = self.embeddings[q_idx]
        scores = np.dot(self.embeddings, origin_vec)
        # Exclui a própria questão da busca
        scores[q_idx] = -1.0

        if target_banca_ids is not None:
            mask = np.zeros(len(self.ids), dtype=bool)
            for qid in target_banca_ids:
                idx = self.id_to_idx.get(qid)
                if idx is not None:
                    mask[idx] = True
            scores = np.where(mask, scores, -1.0)

        sorted_indices = np.argsort(scores)[::-1]
        results = []
        for idx in sorted_indices[:top_k]:
            score = float(scores[idx])
            if score < min_similarity:
                break
            results.append((self.ids[idx], round(score, 4)))

        return results


# Instância singleton exportada
vector_search_service = VectorSearchService()
