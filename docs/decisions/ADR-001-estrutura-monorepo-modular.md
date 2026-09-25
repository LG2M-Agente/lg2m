# ADR 001: Estrutura Monorepo Modular e Fallback de Banco de Dados

> **Status:** Aprovado  
> **Data:** 24/09/2026  
> **Decisores:** Equipe de Engenharia LG2M

---

## 1. Contexto

Para o desenvolvimento ágil e demonstrável do protótipo no Hackathon AKCIT Camp 2026, era necessário definir a organização dos repositórios e a estratégia de persistência:
1. Uma divisão estrita entre a camada de coleta/processamento de dados (`parsingScripts/`) e a aplicação final (`lg2m/`);
2. Coexistência harmônica do motor multiagente em Python (FastAPI/LangGraph) com o frontend em TypeScript/React (Next.js 14);
3. Garantia de que a aplicação seja 100% executável tanto em ambientes de nuvem/produção com `PostgreSQL 16 + pgvector` quanto em ambientes de desenvolvimento local restritos sem daemon Docker ativo.

---

## 2. Decisão

1. **Adoção de Monorepo Modular em `lg2m/`:**
   - `lg2m/backend/`: Contém a API REST/SSE assíncrona, modelos ORM SQLAlchemy e o grafo multiagente LangGraph;
   - `lg2m/frontend/`: Aplicação Next.js 14 (App Router) com Shadcn/ui e Tailwind CSS;
   - `lg2m/docker/`: Arquivos de containerização oficial com `PostgreSQL 16 + pgvector`;
   - `lg2m/data/`: Armazenamento do dataset canônico certificado (`canonical_dataset_mvp.jsonl`).

2. **Estratégia de Persistência Híbrida (PostgreSQL / SQLite Fallback):**
   - Em produção e na nuvem AWS, a aplicação utiliza `PostgreSQL 16` com a extensão `pgvector` e índice HNSW;
   - No ambiente local de desenvolvimento, caso o serviço PostgreSQL não esteja disponível, o ORM ativa de forma transparente um fallback local ACID com persistência estruturada e busca semântica vetorial híbrida acelerada por NumPy.

---

## 3. Consequências

- **Positivas:** Permite que qualquer avaliador da banca do hackathon execute o protótipo localmente com zero fricção de configuração, ao mesmo tempo em que preserva a arquitetura de produção dimensionada para centenas de milhares de questões.
- **Rastreabilidade:** Separação clara entre o pipeline de parsing e o runtime da aplicação.
