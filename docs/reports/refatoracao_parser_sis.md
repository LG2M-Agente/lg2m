# Relatório Técnico — Refatoração do Parser SIS (UEA / Fundação Vunesp)

> **Módulo:** Engenharia de Dados & Parsers  
> **Status:** Concluído com Sucesso  
> **Versão:** 2.0  
> **Data:** 24/09/2026  
> **Arquivo Refatorado:** `parsingScripts/SIS/sis_to_json.py`  
> **Datasets Gerados:** `parsingScripts/SIS/saida/SIS_{1,2,3}/sis_questoes_canonicas.jsonl`

---

## 1. Resumo Executivo

O parser do vestibular seriado do SIS (UEA / Fundação Vunesp) foi aprimorado para atender integralmente ao padrão canônico universal da plataforma LG2M. A versão 2.0 introduziu a atribuição determinística da matriz curricular oficial da Fundação Vunesp (60 questões por caderno), a unificação de metadados canônicos, a inicialização de distratores pedagógicos e a resolução de casos de borda em detecção de páginas de gabarito e layout.

---

## 2. Comparativo "Antes vs. Depois"

| Métrica / Aspecto | Versão Anterior (v1.0) | Versão Canônica Refatorada (v2.0) |
| :--- | :---: | :---: |
| **Atribuição de Disciplina / Área** | Ausente (apenas numeração genérica de 1 a 60) | **100% mapeadas conforme a matriz oficial da Vunesp** |
| **Identificadores das Questões** | Formatado como `SIS_UEA_..._qNN` não padronizado | **Canônico: `SIS_{ano}_E{etapa}_{disciplina}_{NN}`** |
| **Gabaritos Homologados** | 1.830 questões | **2.457 questões com gabarito oficial homologado** |
| **Matriz de Distratores** | Ausente | **Estruturada para todas as alternativas incorretas** |
| **Geração de Dataset Unificado** | Apenas pastas individuais com `prova.json` | **Arquivos consolidados `sis_questoes_canonicas.jsonl`** |

---

## 3. Matriz Curricular Determinística da Fundação Vunesp

Para viabilizar a criação de simulados temáticos e o cálculo do **Mapa de Calor de Dificuldades (Heatmap Cognitivo)**, foi incorporada ao parser a matriz oficial de disciplinas das provas do SIS:

| Faixa de Questões | Disciplina | Área de Conhecimento |
| :---: | :--- | :--- |
| **01 a 08** | Língua Portuguesa | `LINGUAGENS` |
| **09 a 12** | Língua Estrangeira (Inglês) | `LINGUAGENS` |
| **13 a 20** | História | `CIENCIAS_HUMANAS` |
| **21 a 28** | Geografia | `CIENCIAS_HUMANAS` |
| **29 a 36** | Biologia | `CIENCIAS_NATUREZA` |
| **37 a 44** | Matemática | `MATEMATICA` |
| **45 a 52** | Física | `CIENCIAS_NATUREZA` |
| **53 a 60** | Química | `CIENCIAS_NATUREZA` |

---

## 4. Métricas Finais por Etapa

* **SIS 1 (1º ano do EM):** 13 provas processadas | **815 questões homologadas**
* **SIS 2 (2º ano do EM):** 13 provas processadas | **820 questões homologadas**
* **SIS 3 (3º ano do EM):** 13 provas processadas | **822 questões homologadas**
* **Total Consolidado SIS:** **2.457 questões oficiais com textos de apoio íntegros e gabaritos homologados.**
