# Pipeline de Engenharia de Dados & Schema Canônico — LG2M

> **Módulo:** Engenharia de Dados & Ingestão  
> **Status:** Documentação Técnica Oficial  
> **Versão:** 1.0  
> **Implementação:** `parsingScripts/common/schema.py`

---

## 1. Visão Geral

O pipeline de dados da plataforma LG2M tem como objetivo converter acervos brutos de provas e gabaritos em formato PDF (de qualquer certame brasileiro) em objetos de dados tipados, validados e enriquecidos com taxonomia pedagógica, representação científica KaTeX e matriz preliminar de distratores.

---

## 2. Contrato de Dados Canônico (`QuestionCanonicalSchema`)

Implementado com **Pydantic v2**, o contrato unificado exige consistência de tipos e impede a entrada de dados incompletos ou gabaritos corrompidos na base vetorial e relacional.

### 2.1. Dicionário de Campos

| Campo | Tipo | Obrigatório | Descrição / Exemplo |
| :--- | :--- | :---: | :--- |
| `id` | `string` | **Sim** | Identificador único global determinístico (ex: `PSC_2025_E1_LP_01`, `SIS_2024_E2_MAT_15`). |
| `codigo_referencia` | `string` | **Sim** | Código amigável para exibição em UI (ex: `PSC_2025_E1_01`). |
| `certame` | `CertameInfo` | **Sim** | Objeto contendo `sigla`, `nome`, `instituicao`, `banca`, `tipo` e `esfera`. |
| `ano` | `int` | **Sim** | Ano de aplicação oficial da prova (entre 1990 e 2030). |
| `etapa_edicao` | `string` | **Sim** | Etapa seriada (`"1"`, `"2"`, `"3"`) ou edição (`"UNICA"`). |
| `numero_questao` | `int` | **Sim** | Número do item no caderno oficial (ex: `1` a `60`). |
| `disciplina` | `string` | **Sim** | Disciplina oficial (ex: `"Língua Portuguesa"`, `"Física"`, `"História"`). |
| `area_conhecimento` | `AreaConhecimento` | **Sim** | `LINGUAGENS`, `MATEMATICA`, `CIENCIAS_NATUREZA`, `CIENCIAS_HUMANAS`, `JURIDICAS`, `GERAIS`. |
| `assunto` | `string` | **Sim** | Assunto curricular macro (ex: `"Cinemática"`, `"Sintaxe"`, `"Termologia"`). |
| `topico_especifico` | `string` (opcional) | Não | Subtópico refinado (ex: `"Movimento Uniformemente Variado com Gráficos"`). |
| `texto_base` | `string` (opcional) | Não | Texto de apoio ou crônica compartilhada por múltiplas questões. |
| `enunciado` | `string` | **Sim** | Comando da questão com equações convertidas para notação KaTeX. |
| `alternativas` | `dict[str, str]` | **Sim** | Dicionário com chaves normalizadas em maiúsculo (`"A"`, `"B"`, `"C"`, `"D"`, `"E"`). |
| `gabarito_oficial` | `string` | **Sim** | Letra homologada pela banca (`"A"` a `"E"`) ou `"ANULADA"`. |
| `descricao_detalhada` | `string` | **Sim** | Síntese pedagógica de alta densidade semântica para Document Expansion e busca vetorial densa. |
| `curadoria` | `string` | **Sim** | Estrato de curadoria do registro (`"AGENTE_ANTIGRAVITY"` para 100% da base homologada). |
| `tem_imagem` | `bool` | **Sim** | Sinalizador booleano indicando presença de figuras/gráficos. |
| `imagens` | `list[ImagemDetail]` | **Sim** | Lista de metadados das imagens associadas (caminho, bbox, tipo, texto interno). |
| `possui_formula_matematica` | `bool` | **Sim** | Indica se a questão contém formulações KaTeX que demandam renderizador matemático. |
| `tags` | `list[str]` | **Sim** | Marcadores conceituais para auxílio na busca e filtragem. |

> **Nota sobre Distratores:** Campos legados de distratores estáticos (`distratores_info`, `tipo_pegadinha`, `explicacao_distrator`) foram descontinuados e removidos da base canônica. A dissecação de alternativas incorretas agora é realizada dinamicamente em tempo de execução pela arquitetura multiagente (`MentorAgent`), garantindo explicações contextuais adaptadas à resposta e à causa do erro do candidato.

---

## 3. Regras de Validação Estrita

1. **Blindagem do Gabarito Oficial:**  
   O campo `gabarito_oficial` rejeita valores nulos ou diferentes de `{"A", "B", "C", "D", "E", "ANULADA"}`.
2. **Normalização de Alternativas:**  
   Chaves de alternativas minúsculas (`a`, `b`, `c`, `d`, `e`) são automaticamente sanitizadas e convertidas para letras maiúsculas.
3. **Certificação de Curadoria e Document Expansion:**  
   Todo item do acervo canônico deve conter `descricao_detalhada` obrigatória de alta densidade semântica e chancela de homologação `curadoria = "AGENTE_ANTIGRAVITY"`.
