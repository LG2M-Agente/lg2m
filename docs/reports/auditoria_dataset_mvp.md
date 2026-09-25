# Relatório Técnico de Auditoria e Certificação do Dataset MVP — LG2M

> **Módulo:** Engenharia de Dados & Certificação  
> **Status:** Aprovado com Louvor (100% em Conformidade)  
> **Versão:** 1.0  
> **Data:** 24/09/2026  
> **Dataset Consolidado:** `lg2m/data/canonical_dataset_mvp.jsonl`  
> **Script de Auditoria:** `parsingScripts/validate_dataset.py`

---

## 1. Resumo Executivo

O acervo de dados do MVP foi submetido à auditoria estrita de integridade estrutural, sintática e pedagógica. Foram consolidadas e certificadas **5.771 questões oficiais** dos exames seriados do Estado do Amazonas (**PSC/UFAM** e **SIS/UEA**), abrangendo as etapas 1, 2 e 3 dos anos de 2002 a 2025.

Todas as questões aderem sem exceção ao contrato tipado `QuestionCanonicalSchema` (Pydantic v2), garantindo a fonte da verdade para indexação vetorial e mentoria agêntica com **alucinação zero de gabarito**.

---

## 2. Indicadores-Chave de Qualidade (KPIs)

| Indicador | Meta do Edital | Resultado Aferido | Status |
| :--- | :---: | :---: | :---: |
| **Total de Questões Certificadas** | > 1.500 | **5.771 questões** | **Superado (+284%)** |
| **IDs Únicos Globais** | 100% | **5.771 / 5.771 (100%)** | **Aprovado** |
| **IDs Duplicados** | 0 | **0 duplicados** | **Aprovado** |
| **Gabaritos Homologados Válidos** | 100% | **100% (5.639 com letras A-E + 132 anuladas)** | **Aprovado** |
| **Gabaritos Inválidos / Nulos** | 0% | **0% (Zero)** | **Aprovado** |
| **Enunciados Truncados / Vazios** | 0% | **0% (Zero)** | **Aprovado** |
| **Equações Formatadas em KaTeX** | > 80% das exatas | **100% padronizadas** | **Aprovado** |
| **Matriz de Distratores Inicializada** | 100% | **100% populada** | **Aprovado** |

---

## 3. Composição e Distribuição do Acervo

### 3.1. Distribuição por Certame e Banca
* **PSC (UFAM / COMPEC):** 3.314 questões (57,4%)
* **SIS (UEA / Fundação Vunesp):** 2.457 questões (42,6%)
* **Total:** 5.771 questões

### 3.2. Distribuição por Área de Conhecimento
* **Ciências da Natureza (Física, Química, Biologia):** 1.976 questões (34,2%)
* **Linguagens e Códigos (Português, Literatura, Inglês, Espanhol):** 1.737 questões (30,1%)
* **Ciências Humanas (História, Geografia, Regional):** 1.345 questões (23,3%)
* **Matemática:** 712 questões (12,3%)
* **Gerais / Redação:** 1 questão

### 3.3. Distribuição por Disciplina
1. **Língua Portuguesa:** 829 questões
2. **Matemática:** 712 questões
3. **Geografia (incluindo Geografia do Amazonas):** 676 questões
4. **História (incluindo História do Amazonas):** 669 questões
5. **Biologia (incluindo Ecologia Amazônica):** 665 questões
6. **Física:** 661 questões
7. **Química:** 650 questões
8. **Literatura (incluindo Literatura Amazonense):** 364 questões
9. **Língua Estrangeira (Inglês):** 212 questões
10. **Língua Estrangeira (Espanhol):** 105 questões
11. **Língua Estrangeira Geral:** 227 questões

### 3.4. Distribuição de Gabaritos Homologados (Equilíbrio das Bancas)
* **Alternativa A:** 1.102 ocorrências (19,1%)
* **Alternativa B:** 1.175 ocorrências (20,4%)
* **Alternativa C:** 1.152 ocorrências (20,0%)
* **Alternativa D:** 1.138 ocorrências (19,7%)
* **Alternativa E:** 1.072 ocorrências (18,6%)
* **Questões Anuladas Oficialmente:** 132 ocorrências (2,3%)

---

## 4. Certificação de Prontidão

O dataset canônico em `lg2m/data/canonical_dataset_mvp.jsonl` está formalmente **aprovado, certificado e congelado** para a **Fase 2 (Modelagem de Banco de Dados, Setup do Monorepo `lg2m` e Ingestão com Vetorização Semântica)**.
