# Business Model Canvas (BMC) — LG2M
**Projeto:** LG2M — Mentor Agêntico de Estudos  
**Hackathon:** AKCIT Camp Multicêntrico 2026 (Polo Regional Norte / Manaus)  
**Versão:** 1.0 — Atualizado para Congelamento da Etapa Regional  
**Data:** 25 de Setembro de 2026  

---

## Matriz Visual do Business Model Canvas (9 Blocos)

```
┌─────────────────────────┬─────────────────────────┬─────────────────────────┬─────────────────────────┬─────────────────────────┐
│ 8. PARCERIAS-CHAVE      │ 7. ATIVIDADES-CHAVE     │ 2. PROPOSTAS DE VALOR   │ 4. RELACIONAMENTO       │ 1. SEGMENTOS DE         │
│                         │                         │                         │    COM CLIENTES         │    CLIENTES             │
│ • Programa AKCIT Camp   │ • Ingestão contínua de  │ • Mentoria Agêntica com │ • Diálogo Socrático     │ • Estudantes do EM      │
│   e EMBRAPII            │   provas e gabaritos    │   Dissecação Forense    │   empático 24/7 sem     │   e vestibulandos do    │
│ • AWS (Amazon Web       │ • Calibração de prompts │   de Distratores da     │   julgamento de erros   │   Amazonas (PSC UFAM    │
│   Services)             │   e guardrails anti-    │   banca (COMPEC/Vunesp) │ • Acompanhamento visual │   e SIS UEA)            │
│ • Escolas Públicas e    │   alucinação            │ • Efeito Flywheel       │   de pontos cegos       │ • Concurseiros em fase  │
│   Privadas de Manaus    │ • Treinamento do motor  │   Cross-Banca (questões │   (Heatmap Cognitivo)   │   de transição de       │
│ • Professores e         │   vetorial semântico    │   irmãs PSC <-> SIS)    │ • Suporte interativo    │   carreira              │
│   Cursinhos Parceiros   │ • Desenvolvimento e     │ • Alucinação Zero com   │   e comunidade de       │ • Escolas e cursinhos   │
│   do Polo Norte         │   otimização de UX web  │   Ground Truth Pinning  │   estudos seriados      │   preparatórios (B2B)   │
├─────────────────────────┼─────────────────────────┤ • Dossiê Cognitivo vivo ├─────────────────────────┼─────────────────────────┤
│ 6. RECURSOS-CHAVE       │                         │   que evolui no tempo   │ 3. CANAIS               │                         │
│                         │                         │                         │                         │                         │
│ • Acervo proprietário   │                         │                         │ • Web App responsivo    │                         │
│   de 5.771 questões     │                         │                         │   (PWA mobile-first)    │                         │
│   certificadas PSC/SIS  │                         │                         │ • Parcerias com grêmios │                         │
│ • Grafo multiagente no  │                         │                         │   e colégios de Manaus  │                         │
│   LangGraph             │                         │                         │ • Redes sociais         │                         │
│ • Índice vetorial denso │                         │                         │   (Instagram/TikTok)    │                         │
│ • Infraestrutura Cloud  │                         │                         │   com pílulas didáticas │                         │
├─────────────────────────┴─────────────────────────┴─────────────────────────┴─────────────────────────┴─────────────────────────┤
│ 9. ESTRUTURA DE CUSTOS                                                      │ 5. FONTES DE RECEITA                              │
│                                                                             │                                                   │
│ • Servidores de computação em nuvem (AWS ECS / RDS)                         │ • Plano B2C Pro: R$ 29,90/mês ou R$ 199,00/ano   │
│ • Custo de inferência de IA (< R$ 4,80 por usuário ativo/mês com cache)     │   (buscas vetoriais ilimitadas e simulados extras)│
│ • Custos de domínio, CDN e armazenamento de imagens                         │ • Plano B2C Freemium: Grátis com cota diária      │
│ • Marketing digital de atração regional e suporte pedagógico                │ • Licenciamento B2B Cursinhos: R$ 9,90/aluno/mês  │
└─────────────────────────────────────────────────────────────────────────────┴───────────────────────────────────────────────────┘
```

---

## Detalhamento Estratégico dos 9 Blocos

### 1. Segmentos de Clientes (Customer Segments)
* **B2C Primário (Foco MVP):** Estudantes do 1º, 2º e 3º ano do Ensino Médio de Manaus e do interior do Amazonas preparando-se para o PSC (UFAM) e SIS (UEA).
* **B2C Secundário (Expansão):** Concurseiros e vestibulandos nacionais que demandam estudo ativo por questões com explicações adaptativas.
* **B2B (Roadmap 1–2 anos):** Redes privadas de ensino e cursinhos preparatórios de Manaus que necessitam de diagnósticos de turma e montagem automatizada de cadernos.

### 2. Propostas de Valor (Value Propositions)
* **Aprender com o Erro:** Em vez de gabaritos binários secos, o estudante entende exatamente por que o distrator que marcou está incorreto.
* **Efeito Flywheel de Questões Irmãs:** Recuperação semântica de questões do SIS que cobram o mesmo princípio do PSC, duplicando as possibilidades de treino.
* **Gabarito Blindado & Alucinação Zero:** Verificação determinística que impede que a IA contradiga o gabarito oficial homologado.
* **Dossiê Cognitivo Evolutivo:** O sistema lembra as fraquezas conceituais do aluno ao longo das semanas e adapta as explicações futuras aos seus pontos cegos.

### 3. Canais de Distribuição (Channels)
* **Plataforma Web (PWA):** Acesso instantâneo sem necessidade de download em lojas de apps, otimizado para celulares modestos.
* **Canais Institucionais:** Demonstrações diretas em escolas de Ensino Médio do Amazonas.
* **Marketing Orgânico Viral:** Publicação de vídeos curtos dissecando "as maiores pegadinhas históricas da COMPEC/UFAM".

### 4. Relacionamento com o Cliente (Customer Relationship)
* **Mentoria Socrática Personalizada:** Abordagem empática que conduz o estudante à dedução sem respostas punitivas.
* **Autonomia e Transparência:** Visualização clara do Mapa de Calor (verde/amarelo/vermelho) dando previsibilidade do desempenho.

### 5. Fontes de Receita (Revenue Streams)
* **Modelo Freemium B2C:**
  - *Free:* Acesso a 30 resoluções diárias, 2 simulados por dia e histórico básico.
  - *Pro (R$ 29,90/mês ou R$ 199/ano):* Consultas ilimitadas, diagnósticos profundos do Dossiê Cognitivo e cadernos de revisão de erros.
* **SaaS B2B para Cursinhos:** Assinatura corporativa com painel do professor a R$ 9,90/aluno/mês.

### 6. Recursos-Chave (Key Resources)
* **Ativo Próprio de Dados:** Base certificada de 5.771 questões históricas oficiais com gabaritos definitivos (2004–2025).
* **Tecnologia Agêntica:** Grafo de estados no LangGraph, motor de embeddings densos e guardrail determinístico.

### 7. Atividades-Chave (Key Activities)
* Manutenção e atualização anual do acervo de exames oficiais.
* Calibração contínua dos agentes pedagógicos e redução de latência de inferência.
* Engenharia de prompts e testes automatizados de regressão pedagógica.

### 8. Parcerias-Chave (Key Partnerships)
* **AKCIT e EMBRAPII:** Fomento, credibilidade institucional e rede de mentoria de negócios.
* **Amazon AWS:** Parceria de infraestrutura e créditos de nuvem.
* **Comunidade Educacional do Amazonas:** Professores das bancas e coordenadores pedagógicos locais.

### 9. Estrutura de Custos (Cost Structure)
* **Inferência de LLM e Embeddings:** Estimada em R$ 4,80/mês por usuário ativo na versão em nuvem (margem bruta de ~84% no Plano Pro).
* **Infraestrutura Cloud:** Hospedagem de banco de dados e APIs.
* **Desenvolvimento e Suporte.**
