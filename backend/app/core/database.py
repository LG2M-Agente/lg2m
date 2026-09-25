"""
lg2m/backend/app/core/database.py
Gerenciamento de conexões com banco de dados SQLAlchemy (PostgreSQL/pgvector ou SQLite Fallback).
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# Determina URL do banco com suporte a fallback gracioso
db_url = settings.DATABASE_URL

# Tenta verificar se PostgreSQL está acessível; caso contrário, ativa SQLite
if settings.USE_SQLITE_FALLBACK:
    try:
        # Teste rápido de string ou conexão
        if "postgresql" in db_url:
            test_engine = create_engine(db_url, connect_args={"connect_timeout": 2})
            with test_engine.connect():
                pass
            engine = test_engine
    except Exception:
        # Fallback para SQLite local
        sqlite_file = os.path.join(os.path.dirname(__file__), "..", "..", settings.SQLITE_DB_PATH)
        db_url = f"sqlite:///{os.path.abspath(sqlite_file)}"
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
else:
    engine = create_engine(db_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency para injeção de sessão de banco de dados nos endpoints FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
