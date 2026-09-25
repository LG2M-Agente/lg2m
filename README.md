# LG2M — Ecossistema Agêntico de Estudos Seriado

> **Piloto Oficial:** Vestibulares Seriados do Amazonas — **PSC (UFAM)** & **SIS (UEA)**  
> **Hackathon:** AKCIT Camp 2026 • 24 e 25 de Setembro de 2026  

---

## 🎯 Sobre o Projeto

A **LG2M** é uma plataforma agêntica de preparação inteligente voltada para os vestibulares seriados do Amazonas (PSC/UFAM e SIS/UEA). Apoiando-se em um acervo canônico de **5.771 questões oficiais homologadas dos últimos 20 anos**, o sistema resolve o isolamento e a desestruturação do vestibulando por meio de:

1. **Arquitetura Multiagente (LangGraph):** 5 agentes especializados (Router, Retriever RAG, Mentor Didático, Guardrail e Profiler Cognitivo).
2. **Efeito Flywheel de Dados Cross-Banca:** Sugere questões análogas entre PSC e SIS que avaliam o mesmo princípio cognitivo, ampliando o repertório e a retenção do aluno.
3. **Heatmap Cognitivo & Detecção de Pontos Cegos:** Rastreia o índice de domínio em tempo real por assunto, orientando estudos anti-procrastinação.
4. **Mentor Socrático com 3 Estilos Didáticos:** Auxilia na resolução com explicações nos estilos *Direto*, *Socrático* e *Teórico*.
5. **Simulados Oficiais Cronometrados:** Ambiente de prova fiel com diagnóstico IA pós-simulado.

---

## 🏗️ Arquitetura Técnica

- **Backend:** FastAPI, Python 3.14, SQLAlchemy, LangGraph, Pydantic v2, SQLite / PostgreSQL + pgvector.
- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS, KaTeX (renderização de fórmulas matemáticas).
- **Dados:** 5.771 questões históricas certificadas com gabaritos oficiais homologados e taxonomia curricular BNCC.

---

## 🚀 Como Executar

### 1. Backend
```bash
cd lg2m/backend
/home/marcos/Projetos/LG2M/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Acesse a documentação interativa em: `http://localhost:8000/docs`

### 2. Frontend
```bash
cd lg2m/frontend
npm run dev
```
Acesse a aplicação web em: `http://localhost:3000`

---

## 📚 Documentação Completa

Toda a engenharia de dados, decisões arquiteturais (ADRs), contratos de API e relatórios experimentais estão fartamente documentados no diretório [`docs/`](../docs/):

- [`docs/plano_execucao_mvp.md`](../docs/plano_execucao_mvp.md): Plano de execução mestre do MVP em 7 fases.
- [`docs/api_contracts.md`](../docs/api_contracts.md): Especificação completa dos contratos de API REST e SSE.
- [`docs/arquitetura_multiagente.md`](../docs/arquitetura_multiagente.md): Grafo de estados e nós do LangGraph.
- [`docs/data_pipeline.md`](../docs/data_pipeline.md): Engenharia de dados e schema canônico.
- [`docs/reports/experimento_flywheel.md`](../docs/reports/experimento_flywheel.md): Validação científica do Efeito Flywheel Cross-Banca.
- [`docs/reports/auditoria_dataset_mvp.md`](../docs/reports/auditoria_dataset_mvp.md): Certificação formal do dataset de 5.771 questões.
- [`docs/roteiro_demo_pitch.md`](../docs/roteiro_demo_pitch.md): Roteiro cronometrado para apresentação do pitch.
