"""
lg2m/backend/app/models/entities.py
Modelagem completa do banco de dados relacional e vetorial da LG2M via SQLAlchemy.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class Banca(Base):
    __tablename__ = "bancas"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = Column(String(255), nullable=False)
    sigla = Column(String(50), nullable=False, unique=True, index=True)
    descricao = Column(Text, nullable=True)

    certames = relationship("Certame", back_populates="banca", cascade="all, delete-orphan")


class Certame(Base):
    __tablename__ = "certames"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    banca_id = Column(String(36), ForeignKey("bancas.id"), nullable=False)
    nome = Column(String(255), nullable=False)
    sigla = Column(String(50), nullable=False, index=True)
    instituicao = Column(String(100), nullable=False)
    tipo_certame = Column(String(50), default="VESTIBULAR")
    esfera = Column(String(50), default="ESTADUAL")

    banca = relationship("Banca", back_populates="certames")
    questoes = relationship("Questao", back_populates="certame")


class Disciplina(Base):
    __tablename__ = "disciplinas"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = Column(String(100), nullable=False, unique=True, index=True)
    area_conhecimento = Column(String(50), nullable=False, index=True)

    assuntos = relationship("Assunto", back_populates="disciplina", cascade="all, delete-orphan")


class Assunto(Base):
    __tablename__ = "assuntos"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    disciplina_id = Column(String(36), ForeignKey("disciplinas.id"), nullable=False)
    nome = Column(String(150), nullable=False, index=True)

    disciplina = relationship("Disciplina", back_populates="assuntos")
    questoes = relationship("Questao", back_populates="assunto_rel")
    registros_dificuldade = relationship("RegistroDificuldade", back_populates="assunto")


class Questao(Base):
    __tablename__ = "questoes"

    id = Column(String(100), primary_key=True)  # ID canônico, ex: PSC_2025_E1_LP_01
    codigo_referencia = Column(String(100), nullable=False, index=True)
    certame_id = Column(String(36), ForeignKey("certames.id"), nullable=False)
    assunto_id = Column(String(36), ForeignKey("assuntos.id"), nullable=True)

    ano = Column(Integer, nullable=False, index=True)
    etapa_edicao = Column(String(20), nullable=False, index=True)
    numero_questao = Column(Integer, nullable=False)

    disciplina_nome = Column(String(100), nullable=False, index=True)
    area_conhecimento = Column(String(50), nullable=False, index=True)
    topico_especifico = Column(String(200), nullable=True)

    texto_base = Column(Text, nullable=True)
    enunciado = Column(Text, nullable=False)
    gabarito_oficial = Column(String(10), nullable=False)  # A, B, C, D, E ou ANULADA

    tem_imagem = Column(Boolean, default=False)
    imagens = Column(JSON, default=list)
    possui_formula_matematica = Column(Boolean, default=False)
    tags = Column(JSON, default=list)

    descricao_detalhada = Column(Text, nullable=True)
    curadoria = Column(String(50), default="MODELO_LOCAL", index=True)

    # Armazena embedding como lista JSON (ou Vector em pgvector)
    embedding_json = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    certame = relationship("Certame", back_populates="questoes")
    assunto_rel = relationship("Assunto", back_populates="questoes")
    alternativas = relationship("Alternativa", back_populates="questao", cascade="all, delete-orphan")
    tentativas = relationship("TentativaQuestao", back_populates="questao")


class Alternativa(Base):
    __tablename__ = "alternativas"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    questao_id = Column(String(100), ForeignKey("questoes.id"), nullable=False, index=True)
    letra = Column(String(5), nullable=False)  # A, B, C, D, E
    texto = Column(Text, nullable=False)
    eh_correta = Column(Boolean, nullable=False)

    questao = relationship("Questao", back_populates="alternativas")


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    nome = Column(String(255), nullable=False)
    senha_hash = Column(String(255), nullable=True)
    tipo_plano = Column(String(50), default="FREE")
    created_at = Column(DateTime, default=datetime.utcnow)

    perfis = relationship("PerfilEstudante", back_populates="usuario", cascade="all, delete-orphan")


class PerfilEstudante(Base):
    __tablename__ = "perfis_estudante"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    usuario_id = Column(String(36), ForeignKey("usuarios.id"), nullable=False)
    certame_foco = Column(String(50), default="PSC")
    estilo_didatico_padrao = Column(String(50), default="DIRETO")  # DIRETO, SOCRATICO, TEORICO

    # Dossiê Epistêmico & Memória de Longo Prazo gerada e atualizada pelo Profiler Agent
    dossie_cognitivo_markdown = Column(Text, nullable=True)
    versao_perfil = Column(Integer, default=1)

    created_at = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario", back_populates="perfis")
    tentativas = relationship("TentativaQuestao", back_populates="perfil")
    simulados = relationship("Simulado", back_populates="perfil")
    registros_dificuldade = relationship("RegistroDificuldade", back_populates="perfil")
    sessoes_mentoria = relationship("SessaoMentoria", back_populates="perfil")


class TentativaQuestao(Base):
    __tablename__ = "tentativas_questao"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    perfil_id = Column(String(36), ForeignKey("perfis_estudante.id"), nullable=False, index=True)
    questao_id = Column(String(100), ForeignKey("questoes.id"), nullable=False, index=True)
    alternativa_marcada = Column(String(5), nullable=False)
    acertou = Column(Boolean, nullable=False)
    tempo_gasto_segundos = Column(Integer, default=0)
    causa_erro = Column(String(50), nullable=True)  # CONCEITUAL, OPERACIONAL, PEGADINHA
    created_at = Column(DateTime, default=datetime.utcnow)

    perfil = relationship("PerfilEstudante", back_populates="tentativas")
    questao = relationship("Questao", back_populates="tentativas")


class RegistroDificuldade(Base):
    __tablename__ = "registros_dificuldade"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    perfil_id = Column(String(36), ForeignKey("perfis_estudante.id"), nullable=False, index=True)
    assunto_id = Column(String(36), ForeignKey("assuntos.id"), nullable=False, index=True)
    total_tentativas = Column(Integer, default=0)
    total_erros = Column(Integer, default=0)
    indice_dominio = Column(Float, default=100.0)  # 0 a 100%
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    perfil = relationship("PerfilEstudante", back_populates="registros_dificuldade")
    assunto = relationship("Assunto", back_populates="registros_dificuldade")


class Simulado(Base):
    __tablename__ = "simulados"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    perfil_id = Column(String(36), ForeignKey("perfis_estudante.id"), nullable=False, index=True)
    certame_sigla = Column(String(50), nullable=False)
    etapa = Column(String(20), nullable=False)
    tipo = Column(String(50), default="GERAL")  # GERAL ou TEMATICO
    disciplina_foco = Column(String(100), nullable=True)
    total_questoes = Column(Integer, default=0)
    total_acertos = Column(Integer, default=0)
    tempo_limite_minutos = Column(Integer, default=180)
    tempo_utilizado_segundos = Column(Integer, default=0)
    status = Column(String(50), default="EM_ANDAMENTO")  # EM_ANDAMENTO, FINALIZADO
    diagnostico_profiler = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    perfil = relationship("PerfilEstudante", back_populates="simulados")
    itens = relationship("ItemSimulado", back_populates="simulado", cascade="all, delete-orphan")


class ItemSimulado(Base):
    __tablename__ = "itens_simulado"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    simulado_id = Column(String(36), ForeignKey("simulados.id"), nullable=False, index=True)
    questao_id = Column(String(100), ForeignKey("questoes.id"), nullable=False)
    ordem = Column(Integer, nullable=False)
    alternativa_marcada = Column(String(5), nullable=True)
    acertou = Column(Boolean, nullable=True)

    simulado = relationship("Simulado", back_populates="itens")


class SessaoMentoria(Base):
    __tablename__ = "sessoes_mentoria"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    perfil_id = Column(String(36), ForeignKey("perfis_estudante.id"), nullable=False, index=True)
    questao_id = Column(String(100), ForeignKey("questoes.id"), nullable=False, index=True)
    estilo_utilizado = Column(String(50), default="DIRETO")
    created_at = Column(DateTime, default=datetime.utcnow)

    perfil = relationship("PerfilEstudante", back_populates="sessoes_mentoria")
    mensagens = relationship("MensagemMentoria", back_populates="sessao", cascade="all, delete-orphan")


class MensagemMentoria(Base):
    __tablename__ = "mensagens_mentoria"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sessao_id = Column(String(36), ForeignKey("sessoes_mentoria.id"), nullable=False, index=True)
    remetente = Column(String(20), nullable=False)  # USUARIO ou AGENTE
    conteudo = Column(Text, nullable=False)
    tipo_agente = Column(String(50), nullable=True)  # MENTOR, VERIFICADOR
    created_at = Column(DateTime, default=datetime.utcnow)

    sessao = relationship("SessaoMentoria", back_populates="mensagens")
