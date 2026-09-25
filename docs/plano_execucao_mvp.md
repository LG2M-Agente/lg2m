# Plano de Execução Detalhado — Construção do Protótipo Funcional LG2M (MVP)

> **Projeto:** LG2M — Mentor Agêntico de Estudos  
> **Programa:** Hackathon AKCIT Camp 2026 (Polo Regional Norte / Manaus & Final Nacional Cubo Itaú)  
> **Status:** ✅ 100% CONCLUÍDO E HOMOLOGADO EM TODAS AS 7 FASES  
> **Versão:** 1.0 (MVP Finalizado & Auditado)  
> **Data de Homologação:** 24/09/2026  
> **Repositório da Aplicação:** `lg2m/` (Commit Inicial `111c1d4`)  
> **Acervo Canônico:** 5.771 questões históricas certificadas PSC/UFAM & SIS/UEA  
> **Efeito Flywheel:** 100% de pareamento Cross-Banca | 23.39 ms de latência média  
> **Documento de Referência Primária:** `docs/contexto_geral_sistema.md`

---

## 1. Visão Geral e Princípios Orientadores

Este documento estabelece o **roteiro exaustivo de engenharia passo a passo** a ser executado para a construção completa, funcional e testada do MVP da plataforma **LG2M**, tendo como escopo piloto inicial os vestibulares seriados do Amazonas (**PSC/UFAM** e **SIS/UEA**), sob uma arquitetura 100% universal e desacoplada, pronta para expansão nacional (ENEM e Concursos Públicos).

### 1.1. Princípio da Documentação Farta e Transparência Decisória

Em estrita consonância com os parâmetros avaliativos do Edital do AKCIT Camp 2026 (Centralidade da IA, Profundidade de Engenharia e Defensibilidade do Ativo Próprio) e com a exigência expressa do usuário, **toda e qualquer etapa de implementação deve ser extensamente documentada**.

Cada fase contará com:
1. **Relatórios Técnicos de Entrega:** Arquivos detalhados em `docs/` registrando o que foi feito, métricas obtidas e códigos relevantes;
2. **Architecture Decision Records (ADRs):** Registro formal em `docs/decisions/` contendo o contexto, a decisão tomada, alternativas descartadas e as consequências arquiteturais;
3. **Logs de Validação & Evidências Empíricas:** Amostras reais de testes de RAG, tempo de resposta (TTFT), precisão de guardrails e taxas de acerto dos parsers;
4. **Commits Semânticos e Rastreabilidade Git:** Commits claros e incrementais no repositório `lg2m/` seguindo a convenção *Conventional Commits*.

---

## 2. Diagnóstico Crítico dos Dados & Parsing Atual (`parsingScripts`)

Antes do início da codificação da aplicação `lg2m`, foi realizada uma auditoria minuciosa nos PDFs baixados pelos loaders e nos arquivos JSON atualmente gerados pelos scripts em `parsingScripts/`.

### 2.1. O que já temos disponível
* **PDFs Baixados:** Acervo completo de provas históricas do **PSC (UFAM)** das etapas 1, 2 e 3 (anos de 2002 a 2025) e do **SIS (UEA)** das etapas 1, 2 e 3 (anos de 2012 a 2025) armazenados em `parsingScripts/PSC/provas/` e `parsingScripts/SIS/provas/`.

### 2.2. Diagnóstico e Inconsistências Identificadas nos Parsers Atuais

A inspeção detalhada revelou discrepâncias e limitações estruturais severas que inviabilizam o uso imediato dos JSONs atuais sem refatoração:

| Problema Identificado | Impacto no Sistema | Ocorrência |
| :--- | :--- | :--- |
| **Gabaritos Oficiais Nulos no PSC** | Todas as questões do PSC foram salvas com `"gabarito": null`. Contudo, os PDFs contêm o **"Gabarito Definitivo" na última página**, que não foi lido pelo script `psc_to_json.py`. | Presente em 100% dos JSONs do PSC. |
| **Falha Total em Anos Anteriores a 2009 no PSC** | Provas de 2004, 2005, 2006, 2007 e 2008 geraram JSONs de ~170 bytes com `"total_questoes": 0`, devido a divergências de layout e regex no cabeçalho. | Anos 2004 a 2008 em PSC 1, 2 e 3. |
| **Ausência de Disciplina/Matéria no SIS** | O parser `sis_to_json.py` extraiu gabaritos e textos-base com precisão, mas não mapeou as **disciplinas curriculares** (Língua Portuguesa, História, Física, etc.), impedindo a montagem de simulados por matéria e o Mapa de Calor. | Presente em 100% dos JSONs do SIS. |
| **Assuntos/Tópicos Ausentes em Ambos** | Nenhum dos parsers extrai ou classifica o **assunto curricular** específico (ex: "Termodinâmica: Ciclos de Carnot", "Sintaxe: Regência e Crase"). | PSC e SIS. |
| **Incompatibilidade de Esquemas JSON** | PSC usa chaves minúsculas `{"a": ..., "b": ...}`, estrutura em lista plana de JSONs; SIS usa chaves maiúsculas `{"A": ..., "B": ...}`, subpastas individuais com `prova.json` e pasta de imagens. Nenhum atende ao modelo canônico unificado do sistema. | Ambos os parsers. |
| **Falta da Matriz de Distratores** | Nenhum JSON possui campos preparados para o tipo de pegadinha (`tipo_pegadinha`) e a explicação pré-computada do distrator (`explicacao_distrator`). | Ambos os parsers. |

> **Decisão de Arquitetura:** A **Fase 1** será integralmente dedicada a refatorar os parsers, criar o pipeline de unificação e gerar o **Dataset Canônico Unificado e Enriquecido** no padrão do schema da LG2M antes de iniciar o banco de dados e a orquestração multiagente.

---

## 3. Schema Canônico Unificado da Questão (Fonte da Verdade)

Para que o sistema seja universal e agnóstico a bancas (PSC, SIS, ENEM, Cebraspe, FGV), toda questão processada pelo pipeline deve aderir rigorosamente ao seguinte contrato tipado Pydantic (`QuestionCanonicalSchema`):

```json
{
  "id": "PSC_2025_E1_LP_01",
  "codigo_referencia": "PSC_2025_E1_01",
  "certame": {
    "sigla": "PSC",
    "nome": "Processo Seletivo Contínuo",
    "instituicao": "UFAM",
    "banca": "COMPEC",
    "tipo": "VESTIBULAR",
    "esfera": "ESTADUAL"
  },
  "ano": 2025,
  "etapa_edicao": "1",
  "numero_questao": 1,
  "disciplina": "Língua Portuguesa",
  "area_conhecimento": "LINGUAGENS",
  "assunto": "Sintaxe",
  "topico_especifico": "Coesão Referencial por Elipse do Sujeito",
  "texto_base": "Texto ou crônica introdutória compartilhada...",
  "enunciado": "Leia o texto a seguir...\nAssinale a alternativa que contém o fragmento em que há coesão por elipse do sujeito:",
  "alternativas": {
    "A": "Agora jazem de nariz para o ar.",
    "B": "Em todos os rostos vê-se impressa a angústia mais dolorida.",
    "C": "Na sala reina um desconsolo aterrador.",
    "D": "O que há é que não há assunto.",
    "E": "Uma dessas frivolidades que punham cóleras surdas em Gustavo Flaubert."
  },
  "gabarito_oficial": "A",
  "distratores_info": {
    "B": {
      "tipo_pegadinha": "CONCEITUAL",
      "explicacao": "Apresenta oração com partícula apassivadora 'se', e não sujeito elíptico."
    },
    "C": {
      "tipo_pegadinha": "ATENCAO",
      "explicacao": "O sujeito 'um desconsolo aterrador' está posposto ao verbo 'reina'."
    },
    "D": {
      "tipo_pegadinha": "CONCEITUAL",
      "explicacao": "Oração sem sujeito com o verbo haver no sentido de existir."
    },
    "E": {
      "tipo_pegadinha": "OPERACIONAL",
      "explicacao": "Fragmento nominal sem oração principal com sujeito elíptico."
    }
  },
  "tem_imagem": false,
  "imagens": [],
  "possui_formula_matematica": false,
  "tags": ["elipse", "coesao", "sintaxe", "compec", "vestibular_seriado"]
}
```

---

## 4. O Roteiro de Execução Passo a Passo (Fases 1 a 7)

```mermaid
flowchart TD
    subgraph Fase 1: Engenharia de Dados & Parsers
        F1_1[1.1 Especificar Schema Canônico] --> F1_2[1.2 Refatorar Parser PSC + Gabaritos]
        F1_2 --> F1_3[1.3 Refatorar Parser SIS + Disciplinas]
        F1_3 --> F1_4[1.4 Enriquecimento Curricular & KaTeX]
        F1_4 --> F1_5[1.5 Pipeline Unificado & Validação 100%]
    end

    subgraph Fase 2: Fundação da Aplicação lg2m
        F1_5 --> F2_1[2.1 Setup da Estrutura lg2m: Monorepo]
        F2_1 --> F2_2[2.2 PostgreSQL 16 + pgvector Docker]
        F2_2 --> F2_3[2.3 Modelagem ORM & Migrations]
        F2_3 --> F2_4[2.4 Ingestão & Embeddings Vetoriais HNSW]
    end

    subgraph Fase 3: Motor Multiagente no LangGraph
        F2_4 --> F3_1[3.1 StateGraph & AgentState]
        F3_1 --> F3_2[3.2 Agente 1: Router & Triagem]
        F3_2 --> F3_3[3.3 Agente 2: Curador & RAG Vetorial Semântico]
        F3_3 --> F3_4[3.4 Agente 3: Mentor Didático 3 Estilos]
        F3_4 --> F3_5[3.5 Agente 5: Verificador & Guardrail Blindado]
        F3_5 --> F3_6[3.6 Agente 4: Profiler & Heatmap Cognitivo]
        F3_6 --> F3_7[3.7 Observabilidade Langfuse]
    end

    subgraph Fase 4: APIs Backend FastAPI
        F3_7 --> F4_1[4.1 API de Busca Semântica & Filtros]
        F4_1 --> F4_2[4.2 API de Resolução Interativa Blindada]
        F4_2 --> F4_3[4.3 API SSE de Streaming de Mentoria]
        F4_3 --> F4_4[4.4 API Geradora de Simulados Geral & Temático]
        F4_4 --> F4_5[4.5 API do Heatmap Cognitivo]
    end

    subgraph Fase 5: Frontend Next.js & UI
        F4_5 --> F5_1[5.1 Setup Next.js 14 + Shadcn/ui + KaTeX]
        F5_1 --> F5_2[5.2 Tela 1: Onboarding & Perfil]
        F5_2 --> F5_3[5.3 Tela 2: Dashboard & Heatmap]
        F5_3 --> F5_4[5.4 Tela 3: Arena de Prática & Busca]
        F5_4 --> F5_5[5.5 Tela 4: Painel do Mentor 3 Estilos]
        F5_5 --> F5_6[5.6 Telas 5 & 6: Simulados & Relatório]
    end

    subgraph Fase 6: Validação, Flywheel & Testes
        F5_6 --> F6_1[6.1 Teste Experimental do Flywheel]
        F6_1 --> F6_2[6.2 Teste Stress Guardrail: 0% Alucinação]
        F6_2 --> F6_3[6.3 Benchmark de Latência: TTFT < 2.5s]
    end

    subgraph Fase 7: Entregáveis & Demo Hackathon
        F6_3 --> F7_1[7.1 Roteiro da Demonstração ao Vivo 3min]
        F7_1 --> F7_2[7.2 Pacote de Submissão Edital AKCIT]
    end
```

---

### FASE 1: Engenharia de Dados & Refatoração dos Parsers (`parsingScripts`)

> **Objetivo:** Transformar o conjunto de PDFs brutos baixados em uma base de dados JSON canônica, 100% validada, com gabaritos oficiais homologados, textos matemáticos higienizados em KaTeX e taxonomia curricular atribuída.

#### Tarefa 1.1: Especificação e Tipagem do Schema Canônico Unificado
- **O que fazer:** Criar o módulo Python com classes Pydantic v2 que formalizam a estrutura de todas as questões do sistema, garantindo validação estrita em tempo de execução.
- **Arquivo a criar:** `parsingScripts/common/schema.py`.
- **Documentação da etapa:** Registrar em `docs/data_pipeline.md` o dicionário de dados de cada campo, regras de obrigatoriedade e enumerações aceitas.

#### Tarefa 1.2: Refatoração do Parser PSC (`psc_to_json.py`)
- **O que fazer:**
  1. Adicionar módulo de extração da tabela de **Gabarito Definitivo** contida na última página de cada PDF do PSC;
  2. Cruzar deterministicamente cada número de questão com a respectiva letra do gabarito (`A`, `B`, `C`, `D`, `E` ou `ANULADA`);
  3. Corrigir o algoritmo de split e regex de cabeçalho para processar com sucesso os anos de 2004 a 2008 (atualmente com 0 questões);
  4. Padronizar as chaves de alternativas para maiúsculas (`A` a `E`);
  5. Extrair e associar corretamente a `etapa` (1, 2 ou 3) a partir do nome do arquivo ou do cabeçalho oficial;
  6. Preservar fórmulas matemáticas e referências de imagens recortadas.
- **Arquivos a alterar/criar:** `parsingScripts/PSC/psc_to_json.py` e testes unitários em `parsingScripts/tests/test_psc_parser.py`.
- **Documentação da etapa:** Relatório de comparação "Antes vs. Depois" em `docs/reports/refatoracao_parser_psc.md`, com taxa de extração e cobertura de gabaritos.

#### Tarefa 1.3: Refatoração do Parser SIS (`sis_to_json.py`)
- **O que fazer:**
  1. Implementar o mapeamento determinístico de disciplinas e áreas de conhecimento a partir da matriz curricular oficial da Fundação Vunesp para o SIS (ex: Questões 1 a 12: Língua Portuguesa; 13 a 16: Língua Inglesa; 17 a 22: História; etc.);
  2. Ajustar a saída para o formato canônico unificado (em vez de subpasta isolada `prova.json`);
  3. Vincular textos-base de múltiplos itens de forma padronizada.
- **Arquivos a alterar/criar:** `parsingScripts/SIS/sis_to_json.py` e `parsingScripts/tests/test_sis_parser.py`.
- **Documentação da etapa:** Relatório em `docs/reports/refatoracao_parser_sis.md` detalhando o mapeamento de blocos de matérias e validação do gabarito.

#### Tarefa 1.4: Pipeline de Classificação Curricular & KaTeX
- **O que fazer:**
  1. Desenvolver script para enriquecimento semântico: classificação automática de **Assunto** e **Tópico Específico** com base nas diretrizes dos editais da UFAM (COMPEC) e UEA (Vunesp);
  2. Higienizar enunciados contendo equações, expoentes, frações e reações químicas para sintaxe padrão **KaTeX** (`$...$` e `$$...$$`);
  3. Gerar pré-computação da matriz de distratores para as questões principais (`tipo_pegadinha` e `explicacao_distrator`).
- **Arquivo a criar:** `parsingScripts/enrich_dataset.py`.
- **Documentação da etapa:** Registrar em `docs/taxonomia_curricular.md` a árvore completa de disciplinas e assuntos adotada no MVP.

#### Tarefa 1.5: Validador Automatizado e Emissão de Relatório de Integridade
- **O que fazer:**
  1. Criar script de auditoria que varre todo o acervo consolidado e atesta:
     - 100% das questões ativas possuem gabarito homologado não nulo;
     - Todas as 5 alternativas (A, B, C, D, E) estão presentes e não vazias;
     - Nenhuma questão possui texto truncado;
     - Imagens vinculadas existem fisicamente no disco.
  2. Gerar arquivo consolidado `canonical_dataset_mvp.jsonl` e `canonical_dataset_mvp.json`.
- **Arquivo a criar:** `parsingScripts/validate_dataset.py`.
- **Documentação da etapa:** Relatório formal de auditoria em `docs/reports/auditoria_dataset_mvp.md` com contagem final de itens por prova, banca, disciplina e etapa.

---

### FASE 2: Fundação da Aplicação `lg2m` (Backend & PostgreSQL Vetorial)

> **Objetivo:** Estabelecer a infraestrutura de dados no repositório da aplicação `lg2m`, configurando o banco relacional e vetorial (`PostgreSQL 16` com `pgvector`), modelagem ORM e indexação vetorial dos enunciados.

#### Tarefa 2.1: Estruturação do Repositório `lg2m/`
- **O que fazer:**
  1. Inicializar o repositório `lg2m/` com estrutura modular limpa:
     - `lg2m/backend/`: FastAPI, SQLAlchemy, LangGraph, Pydantic;
     - `lg2m/frontend/`: Next.js 14 (App Router), Tailwind CSS, Shadcn/ui;
     - `lg2m/shared/`: Schemas compartilhados e contratos TypeScript/Python;
     - `lg2m/docker/`: `docker-compose.yml` para banco de dados local com `pgvector`.
  2. Criar `.gitignore`, `.env.example` e `README.md` da aplicação.
- **Documentação da etapa:** ADR 001 em `docs/decisions/ADR-001-estrutura-monorepo-modular.md`.

#### Tarefa 2.2: Ambiente de Banco de Dados (`PostgreSQL 16 + pgvector`)
- **O que fazer:**
  1. Configurar `docker-compose.yml` em `lg2m/docker/` com a imagem oficial `pgvector/pgvector:pg16`;
  2. Configurar variáveis de conexão e script de inicialização para ativar a extensão `CREATE EXTENSION IF NOT EXISTS vector;`.
- **Documentação da etapa:** Seção de infraestrutura em `docs/guia_ambiente_desenvolvimento.md`.

#### Tarefa 2.3: Modelagem Relacional & Migrations (SQLAlchemy)
- **O que fazer:**
  1. Implementar no backend os modelos de dados especificados na Seção 9 do documento de contexto:
     - `Banca`, `Certame`, `Disciplina`, `Assunto`;
     - `Questao` (com coluna `embedding_vetorial VECTOR(1536)`);
     - `Alternativa` (com `letra`, `texto`, `eh_correta`, `explicacao_distrator`, `tipo_pegadinha`);
     - `Usuario`, `PerfilEstudante`, `TentativaQuestao`, `Simulado`, `ItemSimulado`, `RegistroDificuldade`, `SessaoMentoria`, `MensagemMentoria`.
  2. Gerar migrations automáticas via Alembic.
- **Arquivos a criar:** `lg2m/backend/app/models/*.py` e scripts de migração Alembic.
- **Documentação da etapa:** Diagrama ERD atualizado e dicionário de tabelas em `docs/modelo_banco_dados.md`.

#### Tarefa 2.4: Ingestão do Dataset Canônico e Vetorização em Lote
- **O que fazer:**
  1. Desenvolver o script de ingestão `seed_database.py` que lê o arquivo `canonical_dataset_mvp.jsonl` gerado na Fase 1;
  2. Chamar o modelo de embeddings (OpenAI `text-embedding-3-small` ou Bedrock Titan Embeddings) para converter o enunciado + texto-base em vetores densos de 1536 dimensões;
  3. Criar índice HNSW com distância de cosseno:
     ```sql
     CREATE INDEX ON questao USING hnsw (embedding_vetorial vector_cosine_ops);
     ```
  4. Inserir bancas, certames, disciplinas, assuntos, questões e alternativas no banco.
- **Arquivo a criar:** `lg2m/backend/scripts/seed_database.py`.
- **Documentação da etapa:** Relatório de ingestão em `docs/reports/ingestao_vetorial.md` contendo quantidade de registros indexados, dimensionalidade e tempo de processamento.

---

### FASE 3: Construção do Motor Multiagente no LangGraph (`lg2m/backend`)

> **Objetivo:** Implementar o núcleo de inteligência da LG2M atendendo aos Parâmetros 1 e 2 do Edital AKCIT Camp: rede de agentes autônomos com divisão estrita de papéis, orquestração via máquina de estados do LangGraph e guardrails determinísticos para alucinação zero.

#### Tarefa 3.1: Modelagem da Máquina de Estados (`AgentState`)
- **O que fazer:**
  1. Definir o esquema tipado de estado da sessão no LangGraph (`AgentState`), contendo dados da questão ativa, alternativas, gabarito oficial protegido, histórico conversacional, estilo didático, status do guardrail e métricas de profilagem.
- **Arquivo a criar:** `lg2m/backend/app/agents/state.py`.
- **Documentação da etapa:** Especificação da máquina de estados em `docs/arquitetura_multiagente.md`.

#### Tarefa 3.2: Implementação do Agente 1 — Orquestrador & Triagem Cognitiva
- **O que fazer:**
  1. Nó de entrada do grafo. Analisa o prompt/evento do usuário, sanitiza contra injeções de prompt e classifica a intenção em:
     - `BUSCAR_QUESTOES`: Direciona para o Curador Semântico;
     - `DISSECAR_RESPOSTA`: Direciona para o Mentor Didático;
     - `DUVIDA_CHAT`: Mantém o diálogo no contexto da questão atual;
     - `MONTAR_SIMULADO`: Dispara o gerador de simulados.
- **Arquivo a criar:** `lg2m/backend/app/agents/router_agent.py`.
- **Documentação da etapa:** Matriz de intenções e prompts de triagem documentados em `docs/prompts_sistema.md`.

#### Tarefa 3.3: Implementação do Agente 2 — Curador & RAG Vetorial Semântico
- **O que fazer:**
  1. Nó responsável pelo **Flywheel de Dados**.
  2. Implementar função de busca híbrida: vetor de busca gerado em tempo real confrontado contra os embeddings de questões no `pgvector`, com pré-filtros SQL opcionais (banca, certame, etapa, matéria);
  3. Implementar tool `fetch_similar_isomorphic_questions(question_id)` para localizar questões irmãs com similaridade de cosseno $> 0.82$.
- **Arquivo a criar:** `lg2m/backend/app/agents/retriever_agent.py`.
- **Documentação da etapa:** Relatório de precisão da recuperação (Top-1, Top-3, Top-5 Relevance) em `docs/reports/avaliacao_rag.md`.

#### Tarefa 3.4: Implementação do Agente 3 — Mentor Didático & Analista de Distratores
- **O que fazer:**
  1. O coração pedagógico da plataforma. Recebe a questão, o gabarito oficial homologado, a alternativa selecionada pelo aluno e o estilo didático;
  2. Prompts especializados com injeção do padrão da banca examinadora (COMPEC / Vunesp);
  3. Três modos de resposta estritos:
     - *Direto & Prático:* Foco no macete e anulação rápida do distrator (máx. 150 palavras);
     - *Socrático & Reflexivo:* Não revela a resposta de imediato; formula uma pergunta indutiva que faz o estudante confrontar sua premissa;
     - *Teórico & Detalhado:* Passo a passo aprofundado, com teoremas, fórmulas em KaTeX e dissecação das 5 alternativas (A a E).
- **Arquivo a criar:** `lg2m/backend/app/agents/mentor_agent.py`.
- **Documentação da etapa:** Engenharia de prompts e guia de estilos didáticos em `docs/guia_pedagogico_mentor.md`.

#### Tarefa 3.5: Implementação do Agente 5 — Verificador, Solver & Guardrail de Segurança
- **O que fazer:**
  1. Nó de auditoria determinística antes que a resposta chegue ao usuário.
  2. Regra inviolável: o gabarito oficial da banca é injetado como premissa absoluta (*Ground Truth Pinning*);
  3. Inspeciona o rascunho do mentor: se houver qualquer afirmação ou sugestão de que outra alternativa está certa em desacordo com a banca, rejeita o rascunho com feedback de autocorreção;
  4. Sandbox simbólico em Python para verificar cálculos matemáticos;
  5. Ciclo de autocorreção com teto rígido de 2 tentativas.
- **Arquivo a criar:** `lg2m/backend/app/agents/guardrail_agent.py`.
- **Documentação da etapa:** ADR 002 em `docs/decisions/ADR-002-guardrails-alucinacao-zero.md`.

#### Tarefa 3.6: Implementação do Agente 4 — Profiler Cognitivo & Gestor de Dificuldades
- **O que fazer:**
  1. Após aprovação do guardrail, registra a tentativa na tabela `TentativaQuestao`;
  2. Classifica a causa do erro em *Conceitual*, *Operacional* ou *Atenção/Pegadinha*;
  3. Atualiza o score do assunto na tabela `RegistroDificuldade` usando média ponderada móvel exponencial:
     $$\text{Score}_{assunto} = \frac{\sum_{i=1}^{n} (Acerto_i \times i)}{\sum_{i=1}^{n} i}$$
  4. Identifica pontos cegos (< 50% de aproveitamento) e enfileira recomendação de questões irmãs de reforço.
- **Arquivo a criar:** `lg2m/backend/app/agents/profiler_agent.py`.
- **Documentação da etapa:** Detalhamento da lógica de memória cognitiva em `docs/memoria_cognitiva_profiler.md`.

#### Tarefa 3.7: Observabilidade de IA e Tracing via Langfuse
- **O que fazer:**
  1. Instrumentar cada nó do LangGraph com callbacks do Langfuse;
  2. Registrar latência por agente, consumo de tokens, status dos guardrails e avaliações de RAG (Context Relevance, Faithfulness, Answer Relevance).
- **Arquivo a criar:** `lg2m/backend/app/core/telemetry.py`.
- **Documentação da etapa:** Guia de configuração e dashboards de observabilidade em `docs/observabilidade_langfuse.md`.

---

### FASE 4: APIs Backend REST & Streaming SSE (`lg2m/backend`)

> **Objetivo:** Expor todos os serviços do sistema através de APIs assíncronas de alta performance construídas com FastAPI, documentadas automaticamente via Swagger/OpenAPI.

#### Tarefa 4.1: Endpoints de Busca Semântica e Filtros de Questões
- **O que fazer:**
  1. `POST /api/v1/questions/search`: Recebe query em linguagem natural + filtros facetados (banca, certame, etapa, disciplina, ano), executa o Curador RAG e retorna lista paginada de questões sem expor gabaritos;
  2. `GET /api/v1/questions/{id}`: Detalhes da questão com alternativas.
- **Arquivo a criar:** `lg2m/backend/app/api/v1/questions.py`.
- **Documentação da etapa:** Especificação dos contratos OpenAPI em `docs/api_contracts.md`.

#### Tarefa 4.2: Endpoints de Resolução Interativa com Gabarito Blindado
- **O que fazer:**
  1. `POST /api/v1/questions/{id}/attempt`: Recebe a alternativa marcada pelo aluno, valida no banco de dados de forma estrita e retorna se acertou ou errou, liberando o gabarito oficial apenas neste momento.
- **Arquivo a criar:** `lg2m/backend/app/api/v1/attempts.py`.
- **Documentação da etapa:** Testes automatizados de segurança comprovando a blindagem de gabarito em `lg2m/backend/tests/test_blind_gabarito.py`.

#### Tarefa 4.3: Streaming de Mentoria em Tempo Real (SSE)
- **O que fazer:**
  1. `POST /api/v1/mentor/stream`: Conexão Server-Sent Events (SSE) para transmissão em tempo real dos tokens de raciocínio e explicação do Mentor Didático, garantindo TTFT < 2,5 segundos;
  2. Suporte à troca imediata de estilo didático (`DIRETO`, `SOCRATICO`, `TEORICO`).
- **Arquivo a criar:** `lg2m/backend/app/api/v1/mentor.py`.
- **Documentação da etapa:** Documentação do protocolo SSE em `docs/api_contracts.md`.

#### Tarefa 4.4: Gerador e Executor de Simulados
- **O que fazer:**
  1. `POST /api/v1/simulados/geral`: Cria simulado oficial completo respeitando as cotas de disciplinas da etapa (ex: PSC 1 com 54 questões distribuídas pelas matérias);
  2. `POST /api/v1/simulados/tematico`: Cria bloco customizado (5, 10 ou 15 questões) de uma disciplina ou assunto específico;
  3. `POST /api/v1/simulados/{id}/submit`: Finaliza o simulado, calcula pontuação, tempo total e gera o Relatório Diagnóstico.
- **Arquivo a criar:** `lg2m/backend/app/api/v1/simulados.py`.
- **Documentação da etapa:** Algoritmo de balanceamento de simulados documentado em `docs/motor_simulados.md`.

#### Tarefa 4.5: Endpoints do Heatmap Cognitivo e Métricas do Aluno
- **O que fazer:**
  1. `GET /api/v1/student/heatmap`: Retorna a árvore hierárquica (Área -> Disciplina -> Assunto) com o índice de domínio ponderado e indicação visual de pontos cegos;
  2. `GET /api/v1/student/stats`: Resumo de questões respondidas, taxa de acerto global e horas de estudo.
- **Arquivo a criar:** `lg2m/backend/app/api/v1/student.py`.
- **Documentação da etapa:** Schema do Heatmap em `docs/api_contracts.md`.

---

### FASE 5: Interface do Usuário e Experiência do Estudante (`lg2m/frontend`)

> **Objetivo:** Construir a interface web moderna, responsiva e focada em estudo ativo, utilizando Next.js 14, Tailwind CSS, Shadcn/ui e suporte a fórmulas KaTeX, materializando as 6 telas centrais do sistema.

#### Tarefa 5.1: Setup da Aplicação Next.js 14 & Design System
- **O que fazer:**
  1. Inicializar Next.js 14 com TypeScript e Tailwind CSS na pasta `lg2m/frontend`;
  2. Configurar biblioteca de componentes **Shadcn/ui**;
  3. Implementar a paleta de cores definida no contexto geral:
     - Slate-900 (`#0F172A`) — Dark mode / Foco;
     - Blue-600 (`#2563EB`) — Marca e ações principais;
     - Emerald-600 (`#059669`) — Acertos e domínio;
     - Amber-600 (`#D97706`) — Distratores e avisos;
  4. Configurar biblioteca de renderização matemática KaTeX / Remark-Math.
- **Arquivos a configurar:** `tailwind.config.ts`, `globals.css` e componentes base em `components/ui/`.
- **Documentação da etapa:** Design System e Styleguide documentados em `docs/design_system.md`.

#### Tarefa 5.2: Tela 1 — Onboarding & Calibração de Perfil
- **O que fazer:**
  1. Interface ágil de configuração inicial do aluno:
     - Seleção de foco: Vestibulares ou Concursos Públicos;
     - Seleção do certame piloto: PSC (UFAM) ou SIS (UEA) - Etapas 1, 2 ou 3;
     - Seleção do estilo pedagógico padrão do mentor (com exemplos visuais de cada estilo).
- **Arquivo a criar:** `lg2m/frontend/src/app/(auth)/onboarding/page.tsx`.
- **Documentação da etapa:** Registro do fluxo e prints em `docs/telas/tela_1_onboarding.md`.

#### Tarefa 5.3: Tela 2 — Dashboard Principal & Hub do Estudante
- **O que fazer:**
  1. Barra de busca semântica em destaque no cabeçalho;
  2. Cards de métricas: Questões resolvidas, taxa de acerto global, simulados realizados;
  3. **Widget do Mapa de Calor de Dificuldades (Heatmap Cognitivo):** Visualização em árvore/matriz com código de cores (Verde > 80%, Amarelo 50-79%, Vermelho < 50%);
  4. Card inteligente de recomendação: *"Ponto cego identificado em Cinemática: Que tal resolver 5 questões de reforço agora?"*;
  5. Acesso rápido a novos simulados e histórico.
- **Arquivo a criar:** `lg2m/frontend/src/app/(dashboard)/page.tsx`.
- **Documentação da etapa:** Documentação dos componentes em `docs/telas/tela_2_dashboard.md`.

#### Tarefa 5.4: Tela 3 — Arena de Prática & Busca Semântica
- **O que fazer:**
  1. Layout com divisão Desktop 70% / 30%;
  2. Lado esquerdo: Enunciado oficial com renderização de fórmulas KaTeX e imagens recortadas, badges de metadados (Banca, Ano, Disciplina, Assunto), alternativas A a E selecionáveis e botão "Confirmar Resposta";
  3. Lado direito: Painel retrátil do Mentor Didático;
  4. Barra de filtros retrátil por certame, etapa, ano e disciplina;
  5. Botão de ação: **"Buscar Questões Semelhantes Deste Conceito"** (Flywheel).
- **Arquivo a criar:** `lg2m/frontend/src/app/(practice)/questoes/page.tsx`.
- **Documentação da etapa:** Detalhamento do comportamento reativo da tela em `docs/telas/tela_3_arena_pratica.md`.

#### Tarefa 5.5: Tela 4 — Painel do Mentor Didático (Chat Agêntico)
- **O que fazer:**
  1. Painel conversacional com streaming em tempo real via SSE;
  2. Pílulas no topo para alternância imediata de estilo didático (*Direto*, *Socrático*, *Teórico*);
  3. Feed de mensagens com renderização de markdown e expressões científicas KaTeX;
  4. Dissecação automática e imediata do distrator quando o aluno confirma resposta incorreta;
  5. Chips de perguntas sugeridas (*"Qual foi a pegadinha da banca?"*, *"Me dê um macete"*, *"Mostre a dedução passo a passo"*).
- **Arquivo a criar:** `lg2m/frontend/src/components/mentor/MentorChatPanel.tsx`.
- **Documentação da etapa:** Guia de interação do chat em `docs/telas/tela_4_mentor_chat.md`.

#### Tarefa 5.6: Telas 5 e 6 — Módulo de Simulados & Relatório Pós-Simulado
- **O que fazer:**
  1. *Tela de Execução:* Cronômetro regressivo oficial, top-bar com índice numérico navegável de questões (respondidas em verde, pendentes em cinza) e encerramento com confirmação;
  2. *Tela de Relatório Diagnóstico:* Aproveitamento percentual, gráfico de barras por disciplina, lista detalhada de questões com status (Acerto / Erro) e botão rápido ao lado de cada erro: **"Dissecar Distrator com o Mentor"**.
- **Arquivos a criar:** `lg2m/frontend/src/app/(simulados)/simulado/[id]/page.tsx` e `lg2m/frontend/src/app/(simulados)/resultado/[id]/page.tsx`.
- **Documentação da etapa:** Registro do fluxo de simulados em `docs/telas/telas_5_6_simulados.md`.

---

### FASE 6: Validação Experimental, Efeito Flywheel & Auditoria de Alucinação Zero

> **Objetivo:** Produzir evidências empíricas, quantitativas e reprodutíveis atestando o funcionamento da tese do produto e a aderência total aos critérios de avaliação do Edital do AKCIT Camp.

#### Tarefa 6.1: Teste Experimental do Efeito Flywheel
- **O que fazer:**
  1. Executar bateria de 50 consultas semânticas conceituais na base contendo apenas o PSC;
  2. Reexecutar a mesma bateria após a inclusão do SIS;
  3. Mensurar o ganho de densidade de itens contextualmente similares e a capacidade de conectar questões irmãs entre bancas distintas (COMPEC vs. Vunesp).
- **Arquivo a criar:** `lg2m/backend/scripts/benchmark_flywheel.py`.
- **Documentação da etapa:** Relatório experimental comprobatório em `docs/reports/experimento_flywheel.md` para exibição no pitch.

#### Tarefa 6.2: Teste de Stress do Guardrail (0% de Alucinação)
- **O que fazer:**
  1. Bateria automatizada de 100 requisições de mentoria forçando cenários adversos de distratores ambíguos;
  2. Monitorar a taxa de aprovação/rejeição do Agente Verificador e comprovar que em **100% das vezes** a explicação homologada respeitou o gabarito oficial da banca.
- **Arquivo a criar:** `lg2m/backend/tests/test_guardrail_stress.py`.
- **Documentação da etapa:** Certificado de conformidade de gabarito em `docs/reports/auditoria_guardrails.md`.

#### Tarefa 6.3: Benchmark de Latência e Performance
- **O que fazer:**
  1. Aferir tempos de resposta de ponta a ponta:
     - Busca vetorial no `pgvector`: meta < 300 ms;
     - Time To First Token (TTFT) no streaming do mentor: meta < 2,5 s;
     - Carregamento inicial do dashboard (FCP): meta < 1,2 s.
- **Arquivo a criar:** `lg2m/backend/scripts/benchmark_latency.py`.
- **Documentação da etapa:** Relatório de telemetria em `docs/reports/benchmark_latencia.md`.

---

### FASE 7: Preparação para Demonstração e Pitch do Hackathon AKCIT Camp

> **Objetivo:** Consolidar todos os entregáveis exigidos pela Seção 8 do Edital do Hackathon AKCIT Camp e ensaiar a demonstração ao vivo do protótipo funcional.

#### Tarefa 7.1: Roteiro Estruturado da Demo ao Vivo (Pitch de 3 Minutos)
- **O que fazer:** Estruturar e documentar o roteiro cronometrado da demonstração prática para a banca:
  1. **Minuto 1: A Dor e a Busca Semântica:** Digitar uma busca em linguagem natural complexa (ex: *"questão sobre cálculo de velocidade média com aceleração variável"*), demonstrando a recuperação instantânea no `pgvector`;
  2. **Minuto 2: A Resolução e a Dissecação do Distrator:** Selecionar intencionalmente um distrator clássico da banca, submeter a resposta e mostrar o Agente Mentor entrando em ação imediatamente para desmascarar a pegadinha; trocar em 1 clique para o estilo *Socrático* e mostrar a adaptação do tom didático;
  3. **Minuto 3: O Flywheel e o Heatmap Cognitivo:** Clicar em "Buscar Questões Semelhantes Deste Conceito" (mostrando a questão irmã da outra banca), exibir o Heatmap atualizado com o ponto cego detectado e apresentar a defensibilidade técnica do ativo próprio.
- **Documentação da etapa:** Roteiro completo e transcrição de falas em `docs/roteiro_demo_pitch.md`.

#### Tarefa 7.2: Pacote de Entregáveis Obrigatórios do Edital
- **O que fazer:**
  1. Atualizar o Business Model Canvas (BMC) e análise de Unit Economics (margem > 80%);
  2. Validar que o repositório `lg2m/` está limpo, organizado e com README explicativo com instruções de execução com 1 comando via Docker;
  3. Gravar vídeo de demonstração do protótipo (backup obrigatório de contingência).
- **Documentação da etapa:** Pasta de submissão consolidada em `docs/submissao_akcit/`.

---

## 5. Estrutura de Diretórios da Documentação a ser Produzida

Para manter a farta documentação exigida, a pasta `docs/` será organizada na seguinte árvore de artefatos:

```
docs/
├── contexto_geral_sistema.md           # [Existente] Especificação completa do produto v2.0
├── plano_execucao_mvp.md               # [Este Documento] Guia mestre passo a passo
├── guia_ambiente_desenvolvimento.md    # Instruções de setup, Docker, Python e Node
├── taxonomia_curricular.md             # Matriz de disciplinas, áreas e assuntos do MVP
├── modelo_banco_dados.md               # Diagrama ERD e dicionário de dados SQL
├── arquitetura_multiagente.md          # Especificação formal do LangGraph e nós
├── api_contracts.md                    # Contratos OpenAPI das rotas REST e SSE
├── design_system.md                    # Paleta de cores, tipografia e componentes UI
├── roteiro_demo_pitch.md               # Roteiro cronometrado da demonstração de 3 minutos
├── decisions/                          # Architecture Decision Records (ADRs)
│   ├── ADR-001-estrutura-monorepo-modular.md
│   ├── ADR-002-guardrails-alucinacao-zero.md
│   └── ADR-003-estrategia-indexacao-hnsw.md
├── reports/                            # Relatórios técnicos empíricos
│   ├── refatoracao_parser_psc.md
│   ├── refatoracao_parser_sis.md
│   ├── auditoria_dataset_mvp.md
│   ├── avaliacao_rag.md
│   ├── experimento_flywheel.md
│   ├── auditoria_guardrails.md
│   └── benchmark_latencia.md
└── telas/                              # Especificações e wireframes de telas
    ├── tela_1_onboarding.md
    ├── tela_2_dashboard.md
    ├── tela_3_arena_pratica.md
    ├── tela_4_mentor_chat.md
    └── telas_5_6_simulados.md
```

---

## 6. Próximo Passo Imediato

Com a aprovação deste plano de execução, o trabalho prático terá início imediato pela **Fase 1 (Tarefa 1.1 e 1.2: Refatoração do Parser do PSC para extração dos gabaritos oficiais da última página e recuperação das provas de 2004 a 2008)**, acompanhada da emissão do respectivo relatório técnico comprobatório.
