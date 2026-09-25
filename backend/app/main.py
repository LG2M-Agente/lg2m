"""
lg2m/backend/app/main.py
Aplicação FastAPI Principal do Ecossistema LG2M (PSC/UFAM & SIS/UEA).
Hackathon AKCIT Camp 2026.
"""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.models.entities import Base, Questao
from app.api.v1.questions import router as questions_router
from app.api.v1.attempts import router as attempts_router
from app.api.v1.mentor import router as mentor_router
from app.api.v1.simulados import router as simulados_router
from app.api.v1.student import router as student_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("lg2m")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: garante que as tabelas existem e checa contagem de questões
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        count = db.query(Questao).count()
        logger.info(f"LG2M Backend iniciado com sucesso! Total de questoes carregadas no banco: {count}")
    except Exception as e:
        logger.warning(f"Aviso ao verificar questoes no startup: {e}")
    finally:
        db.close()
    yield
    # Shutdown
    logger.info("LG2M Backend finalizado.")


app = FastAPI(
    title="LG2M API - Ecossistema Agêntico de Estudos Seriado",
    description=(
        "Backend inteligente com arquitetura multiagente (LangGraph + RAG Semântico) "
        "para preparação personalizada e de alta performance nos certames PSC/UFAM e SIS/UEA. "
        "Desenvolvido para o Hackathon AKCIT Camp 2026."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configuração de CORS para permitir acesso do frontend Next.js 14
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro dos roteadores da API v1
api_v1_prefix = "/api/v1"
app.include_router(questions_router, prefix=api_v1_prefix)
app.include_router(attempts_router, prefix=api_v1_prefix)
app.include_router(mentor_router, prefix=api_v1_prefix)
app.include_router(simulados_router, prefix=api_v1_prefix)
app.include_router(student_router, prefix=api_v1_prefix)


@app.get("/health", tags=["Infraestrutura"])
@app.get(f"{api_v1_prefix}/health", tags=["Infraestrutura"])
def health_check():
    """Verifica a integridade do serviço e da conexão com o banco de dados."""
    db = SessionLocal()
    try:
        total_questoes = db.query(Questao).count()
        return {
            "status": "healthy",
            "version": "1.0.0",
            "total_questoes_banco": total_questoes,
            "engine": "FastAPI + LangGraph + PostgreSQL/SQLite",
            "certames_suportados": ["PSC", "SIS"]
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.get("/", tags=["Infraestrutura"])
def root():
    return {
        "message": "Bem-vindo à API do LG2M - Ecossistema Agêntico para PSC/UFAM e SIS/UEA",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }
