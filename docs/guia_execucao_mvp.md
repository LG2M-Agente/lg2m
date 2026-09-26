# Guia de Execução & Inicialização do MVP — Ecossistema LG2M

**Projeto:** LG2M — Ecossistema Agêntico Seriado (PSC/UFAM & SIS/UEA)  
**Hackathon:** AKCIT Camp 2026  
**Repositório da Aplicação:** `lg2m/`  

---

## 1. Pré-Requisitos do Ambiente

- **Python:** 3.11+ (compatível com 3.11, 3.12, 3.13 e 3.14).
- **Node.js:** 18+ (testado no Node.js v20+ / v24 e npm 10+).

### Instalação das Dependências (Para novos usuários / avaliadores)

1. **Backend (Python):**
```bash
# Na raiz do projeto ou em lg2m/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r lg2m/backend/requirements.txt
```

2. **Frontend (Node.js):**
```bash
cd lg2m/frontend
npm install
```

3. **Variáveis de Ambiente:**
```bash
cp lg2m/backend/.env.example lg2m/backend/.env
# Edite o arquivo .env e configure sua chave GEMINI_API_KEY
```

---

## 2. Inicialização dos Serviços

### Passo 1: Iniciar o Servidor Backend (FastAPI + LangGraph)

Em um terminal com o ambiente ativado:
```bash
cd lg2m/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Swagger Interativo:** Acesse [`http://localhost:8000/docs`](http://localhost:8000/docs)
- **Health Check:** Acesse [`http://localhost:8000/health`](http://localhost:8000/health)

---

### Passo 2: Iniciar a Aplicação Frontend (Next.js 14)

Em outro terminal, execute:
```bash
cd /home/marcos/Projetos/LG2M/lg2m/frontend
npm run dev
```

- **Aplicação Web:** Acesse [`http://localhost:3000`](http://localhost:3000)

---

## 3. Testes Automatizados e Benchmarks

### Executar Testes de Integração da API
```bash
/home/marcos/Projetos/LG2M/.venv/bin/python lg2m/backend/tests/test_api_endpoints.py
```
> Executa a validação de todas as rotas de saúde, perfil, busca semântica, tentativas blindadas, criação e correção de simulados e chat com o Mentor.

### Executar Testes do Motor Multiagente LangGraph
```bash
/home/marcos/Projetos/LG2M/.venv/bin/python lg2m/backend/tests/test_multiagent_flow.py
```
> Valida as transições de estado entre Router, Retriever, Mentor, Guardrail e Profiler.

### Executar Benchmark do Efeito Flywheel Cross-Banca
```bash
/home/marcos/Projetos/LG2M/.venv/bin/python lg2m/backend/scripts/benchmark_flywheel.py
```
> Mede a taxa de pareamento de questões equivalentes entre PSC (UFAM) e SIS (UEA) e afere as métricas de latência.

---

## 4. Estrutura de Arquivos Principais

```text
lg2m/
├── backend/
│   ├── app/
│   │   ├── agents/          # Agentes autônomos e grafo LangGraph
│   │   ├── api/v1/          # Endpoints REST e SSE
│   │   ├── core/            # Configurações e conexões SQLAlchemy
│   │   ├── models/          # Entidades ORM (Questões, Usuários, Perfis, Simulados)
│   │   ├── schemas/         # Schemas Pydantic de validação
│   │   └── main.py          # Aplicação FastAPI principal
│   ├── scripts/             # Ingestão em lote e benchmarks
│   ├── tests/               # Baterias de testes automatizados
│   └── lg2m_local.db        # Banco local populado com 5.771 questões
│
├── frontend/
│   ├── src/
│   │   ├── app/             # Rotas do Next.js 14 App Router
│   │   ├── components/      # Componentes (Navbar, MathRenderer KaTeX, etc.)
│   │   └── lib/             # Cliente de API e tipagens TypeScript
│   └── package.json
│
└── data/
    └── canonical_dataset_mvp.jsonl  # Dataset canônico oficial homologado
```
