-- Habilita a extensão pgvector para busca semântica em alta dimensão
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Cria schema principal
CREATE SCHEMA IF NOT EXISTS lg2m;
