"""
lg2m/backend/app/schemas/api_schemas.py
Modelos Pydantic v2 para requisições e respostas das APIs REST e SSE.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class QuestionSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Texto de busca livre em linguagem natural")
    certame: Optional[str] = Field(None, description="PSC, SIS ou ALL")
    etapa: Optional[str] = Field(None, description="1, 2, 3")
    disciplina: Optional[str] = Field(None, description="Física, Química, etc.")
    ano: Optional[int] = Field(None, description="Ano específico")
    limit: int = Field(10, ge=1, le=50)


class QuestionDetailResponse(BaseModel):
    id: str
    codigo_referencia: str
    certame: str
    ano: int
    etapa: str
    numero_questao: int
    disciplina: str
    area_conhecimento: str
    assunto: str
    texto_base: Optional[str] = None
    enunciado: str
    alternativas: Dict[str, str]
    tem_imagem: bool
    imagens: List[Dict[str, Any]] = []
    possui_formula_matematica: bool = False
    descricao_detalhada: Optional[str] = None
    curadoria: Optional[str] = "MODELO_LOCAL"
    tags: List[str] = []


class QuestionAttemptRequest(BaseModel):
    alternativa_marcada: str = Field(..., pattern=r"^[A-Ea-e]$")
    tempo_gasto_segundos: int = Field(45, ge=1)
    estilo_didatico: str = Field("DIRETO", description="DIRETO, SOCRATICO ou TEORICO")
    perfil_id: Optional[str] = None


class QuestionAttemptResponse(BaseModel):
    acertou: bool
    gabarito_oficial: str
    alternativa_marcada: str
    explicacao_mentor: str
    estilo_didatico: str
    causa_erro: Optional[str] = None
    novo_score_assunto: Optional[float] = None
    ponto_cego_detectado: bool = False
    cognitive_snapshot: Optional[Dict[str, Any]] = None
    identified_misconceptions: Optional[List[str]] = None


class MentorChatRequest(BaseModel):
    questao_id: str
    mensagem: str
    estilo_didatico: str = Field("DIRETO", description="DIRETO, SOCRATICO ou TEORICO")
    perfil_id: Optional[str] = None


class SimuladoCreateRequest(BaseModel):
    certame_sigla: str = Field("PSC", description="PSC ou SIS")
    etapa: str = Field("1", description="1, 2 ou 3")
    tipo: str = Field("GERAL", description="GERAL ou TEMATICO")
    disciplina_foco: Optional[str] = None
    quantidade_questoes: int = Field(15, ge=5, le=60)
    perfil_id: Optional[str] = None


class SimuladoSubmitRequest(BaseModel):
    respostas: Dict[str, str] = Field(..., description="Mapeamento de questao_id para letra marcada")
    tempo_utilizado_segundos: int = Field(3600, ge=1)


class HeatmapItem(BaseModel):
    assunto: str
    disciplina: str
    area: str
    total_tentativas: int
    total_erros: int
    indice_dominio: float
    eh_ponto_cego: bool


class StudentProfileResponse(BaseModel):
    usuario_id: str
    perfil_id: str
    nome: str
    email: str
    certame_foco: str
    estilo_didatico_padrao: str
    total_tentativas: int
    total_acertos: int
    taxa_acerto_geral: float
    pontos_cegos_count: int
    tempo_medio_segundos: float
    dossie_cognitivo_markdown: Optional[str] = None
    perfil_cognitivo_json: Optional[Dict[str, Any]] = None
    versao_perfil: int = 1


class StudentProfileUpdateRequest(BaseModel):
    certame_foco: Optional[str] = None
    estilo_didatico_padrao: Optional[str] = None


class StudentHeatmapResponse(BaseModel):
    perfil_id: str
    total_assuntos_avaliados: int
    pontos_cegos_count: int
    pontos_cegos: List[HeatmapItem]
    heatmap: List[HeatmapItem]

