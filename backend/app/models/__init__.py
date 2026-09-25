"""
lg2m/backend/app/models/__init__.py
Exportação de todas as entidades do domínio LG2M.
"""

from app.models.entities import (
    Banca,
    Certame,
    Disciplina,
    Assunto,
    Questao,
    Alternativa,
    Usuario,
    PerfilEstudante,
    TentativaQuestao,
    RegistroDificuldade,
    Simulado,
    ItemSimulado,
    SessaoMentoria,
    MensagemMentoria,
)

__all__ = [
    "Banca",
    "Certame",
    "Disciplina",
    "Assunto",
    "Questao",
    "Alternativa",
    "Usuario",
    "PerfilEstudante",
    "TentativaQuestao",
    "RegistroDificuldade",
    "Simulado",
    "ItemSimulado",
    "SessaoMentoria",
    "MensagemMentoria",
]
