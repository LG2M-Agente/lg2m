"""
lg2m/backend/app/agents/state.py
Definição do esquema de estado compartilhado (StateGraph) para a rede multiagente da LG2M.
"""

from typing import TypedDict, List, Optional, Dict, Any


class AgentState(TypedDict, total=False):
    # Metadados de Sessão e Usuário
    session_id: str
    user_id: str
    perfil_id: str
    certame_foco: str              # ex: "PSC", "SIS", "ENEM"
    estilo_didatico: str           # "DIRETO", "SOCRATICO" ou "TEORICO"

    # Contexto da Questão Ativa
    current_question_id: Optional[str]
    current_question_data: Optional[Dict[str, Any]]
    selected_alternative: Optional[str]  # "A", "B", "C", "D", "E"
    is_correct: Optional[bool]
    tempo_resolucao_segundos: Optional[int]

    # Mensagens e Interações
    user_input_message: Optional[str]
    intent_detected: Optional[str]       # "BUSCAR_QUESTAO", "DISSECAR_RESPOSTA", "DUVIDA_CHAT", "MONTAR_SIMULADO"
    
    # Raciocínio Pedagógico e Respostas
    mentor_draft_response: Optional[str]
    verified_response: Optional[str]
    similar_questions_found: Optional[List[Dict[str, Any]]]
    error_classification: Optional[str] # "CONCEITUAL", "OPERACIONAL", "PEGADINHA"

    # Guardrails e Auditoria Determinística
    verification_attempts: int
    guardrail_status: str               # "PENDING", "APPROVED", "REJECTED"
    guardrail_feedback: Optional[str]

    # Histórico de Conversação (Short-Term Memory)
    messages: List[Dict[str, str]]

    # Atualizações Cognitivas (Profiler)
    subject_score_updated: Optional[float]
    critical_blindspot_detected: Optional[bool]
