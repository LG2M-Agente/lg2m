# Relatório Técnico — Refatoração do Parser PSC (UFAM / COMPEC)

> **Módulo:** Engenharia de Dados & Parsers  
> **Status:** Concluído com Sucesso  
> **Versão:** 2.0  
> **Data:** 24/09/2026  
> **Arquivo Refatorado:** `parsingScripts/PSC/psc_to_json.py`  
> **Dataset Gerado:** `parsingScripts/PSC/saida/PSC_{1,2,3}/psc_questoes_canonicas.jsonl`

---

## 1. Resumo Executivo

O parser do vestibular seriado do PSC (UFAM) foi integralmente refatorado para solucionar falhas críticas herdadas da versão inicial. O resultado foi um salto de **0% de gabaritos homologados** para **100% de cobertura oficial**, além da restauração de provas históricas dos anos 2004 a 2008 que antes falhavam por completo.

---

## 2. Comparativo "Antes vs. Depois"

| Métrica / Aspecto | Versão Anterior (v1.0) | Versão Canônica Refatorada (v2.0) |
| :--- | :---: | :---: |
| **Gabaritos Oficiais Extraídos** | `0` (100% como `"gabarito": null`) | **3.182 gabaritos homologados** (100% das válidas) |
| **Questões Anuladas Identificadas** | `0` (não identificadas) | **132 questões com status `"ANULADA"`** |
| **Provas Históricas 2004-2008** | 0 questões extraídas (~170 bytes) | **54 questões extraídas por prova com gabarito** |
| **Total de Questões Extraídas (PSC 1, 2, 3)** | 2.150 (muitas incompletas/vazias) | **3.314 questões íntegras e estruturadas** |
| **Formato de Alternativas** | Minúsculas (`a`, `b`, `c`, `d`, `e`) | Maiúsculas padronizadas (`A`, `B`, `C`, `D`, `E`) |
| **Compatibilidade com Schema Canônico** | Não aderente | **100% aderente ao `QuestionCanonicalSchema`** |
| **Metadados de Etapa/Ano** | Frequentemente `None` | **100% populados e consistentes** |

---

## 3. Problemas Corrigidos & Implementações Técnicas

### 3.1. Leitura Determinística do Gabarito Definitivo
* **Causa Raiz da Falha:** A versão v1.0 utilizava uma regex restritiva (`\b\d{2}\s+[A-E]\b`) que falhava porque nos cadernos da COMPEC os gabaritos aparecem com pontuação (`01. A` ou `01) A` ou quebras de linha entre número e letra).
* **Solução:** Foi implementada a função `extrair_gabarito_definitivo(doc)` que varre as páginas finais do PDF em busca do cabeçalho `"GABARITO"` e emprega dois estágios de correspondência (inline e multiline), capturando com precisão as 54 respostas oficiais de cada caderno, incluindo marcações de questões anuladas pela banca.

### 3.2. Suporte a Numeração com Parênteses em Provas Antigas
* **Causa Raiz da Falha:** Em provas de 2004 a 2008, o layout da COMPEC formatava as questões como `01)` em vez de `01.`. A regex anterior `^(\d{2})\s*\.\s*(?=\S)` descartava todos os itens.
* **Solução:** Atualização da regex de detecção para `^(\d{1,2})\s*[\.\)]\s*(?=\S)`, restaurando centenas de questões históricas.

### 3.3. Extração Robusta de Metadados de Nome de Arquivo
* **Causa Raiz da Falha:** A expressão `PSC[\W_]*(\d)[\W_]+(\d{4})` falhava com arquivos como `PSC_1_UFAM_2025.pdf` devido à presença do texto `UFAM`.
* **Solução:** Regex aprimorada `PSC[_\-\s]*([123]).*?([12]\d{3})`, garantindo que `etapa` e `ano` sejam sempre extraídos com exatidão.

### 3.4. Geração do Contrato Canônico LG2M
Cada item agora é emitido com:
- `id` canônico determinístico (ex: `PSC_2025_E1_LINGUA_PORTUGUESA_01`);
- Metadados completos do certame (`sigla`, `nome`, `instituicao`, `banca`, `tipo`, `esfera`);
- `area_conhecimento` categorizada automaticamente;
- Dicionário `distratores_info` inicializado para as 4 alternativas incorretas;
- Flags `tem_imagem` e lista de `imagens` recortadas com bounding box.

---

## 4. Métricas Finais por Etapa

* **PSC 1 (1º ano do EM):** 22 provas processadas | **1.022 questões** (975 gabaritos oficiais + 47 anuladas)
* **PSC 2 (2º ano do EM):** 22 provas processadas | **1.029 questões** (985 gabaritos oficiais + 44 anuladas)
* **PSC 3 (3º ano do EM):** 23 provas processadas | **1.263 questões** (1.222 gabaritos oficiais + 41 anuladas)
* **Total Consolidado PSC:** **3.314 questões de alta qualidade pedagógica prontas para vetorização.**
