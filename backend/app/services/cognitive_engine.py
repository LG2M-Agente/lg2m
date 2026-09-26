"""
lg2m/backend/app/services/cognitive_engine.py
Motor de Modelagem e Atualização do Perfil Cognitivo Temporal do Estudante (Pt).

Formalização:
1. Atualização Epistêmica: Pt+1 = g(Pt, Tentativa_t)
2. Explicação Hiperpersonalizada: Y_t = f(Questao, Alternativas, Marcada, Gabarito, Pt, Estilo)
3. Snapshot de Baixo Overhead (< 300 tokens) para injeção rápida em prompts de LLMs.
"""

from datetime import datetime
import json
import os
import re
from typing import Dict, Any, List, Optional, Tuple


class CognitiveProfileEngine:
    """
    Gerencia a evolução temporal do modelo mental do vestibulando,
    identificando vícios conceituais, calculando proficiência ponderada
    e gerando diretrizes pedagógicas individualizadas para os agentes de IA.
    """

    CATALOGO_VICIOS = {
        "IGNORA_CONVERSAO_UNIDADES": {
            "nome": "Desatenção na Conversão de Unidades",
            "descricao": "Tende a utilizar grandezas em unidades incompatíveis (ex: km/h vs m/s, cm vs m) sem converter para o SI.",
        },
        "PRECIPITACAO_COMANDO_NEGATIVO": {
            "nome": "Precipitação em Enunciados de Negação",
            "descricao": "Assinala a primeira opção verdadeira ao se deparar com comandos que pedem a alternativa 'INCORRETA', 'FALSA' ou 'EXCETO'.",
        },
        "CONFUSAO_VETORIAL_ESCALAR": {
            "nome": "Confusão entre Grandezas Escalares e Vetoriais",
            "descricao": "Trata deslocamento/velocidade vetorial como distância percorrida/escalar, desconsiderando orientação e sentido.",
        },
        "VULNERABILIDADE_REGIONAL_AMAZONICA": {
            "nome": "Lacuna em Tópicos Regionais do Amazonas",
            "descricao": "Dificuldade na fixação de especificidades da Amazônia cobradas com alto rigor pela COMPEC (UFAM) e UEA.",
        },
        "FALHA_INTERPRETACAO_GRAFICA": {
            "nome": "Interpretação Imprecisa de Gráficos e Curvas",
            "descricao": "Dificuldade na extração de coeficientes angulares, áreas sob curvas ou vértices em gráficos cartesianos.",
        },
        "CONFUSAO_TERMINOLOGIA_CIENTIFICA": {
            "nome": "Confusão em Nomenclatura e Processos Correlatos",
            "descricao": "Troca de conceitos taxonômicos ou organelas celulares de nomes parecidos por impulsividade.",
        },
        "LACUNA_CONCEITUAL_PREMISSA": {
            "nome": "Lacuna na Premissa Teórica Fundamental",
            "descricao": "Incompreensão do axioma básico que rege o tópico, levando à escolha de distratores de senso comum.",
        },
    }

    @classmethod
    def init_empty_profile(cls, student_name: str = "Lucas Eduardo", certame_foco: str = "PSC") -> Dict[str, Any]:
        """Cria uma estrutura inicial canônica e compacta de perfil cognitivo."""
        return {
            "estudante": student_name,
            "certame_foco": certame_foco,
            "versao_epistemica": 1,
            "proficiencia_global": 0.0,
            "total_tentativas": 0,
            "total_acertos": 0,
            "tempo_medio_segundos": 0.0,
            "topicos": {},
            "vicios_cognitivos_ativos": {},
            "historico_recente": [],
            "ultima_atualizacao": datetime.utcnow().isoformat(),
        }

    @classmethod
    def detect_misconceptions(
        cls,
        question_data: Dict[str, Any],
        selected_alt: str,
        correct_alt: str
    ) -> List[str]:
        """
        Analisa a questão e a alternativa marcada para inferir a causa pedagógica raiz do erro.
        """
        if selected_alt.upper() == correct_alt.upper():
            return []

        enunciado = (question_data.get("enunciado") or "").lower()
        disciplina = (question_data.get("disciplina") or "").lower()
        assunto = (question_data.get("assunto") or "").lower()
        banca = str(question_data.get("certame") or "").lower()

        vicios_detectados = []

        # 1. Checagem de comando negativo
        if any(neg in enunciado for neg in ["incorreta", "falsa", "não é", "nao e", "exceto", "errada", "desconforme"]):
            vicios_detectados.append("PRECIPITACAO_COMANDO_NEGATIVO")

        # 2. Checagem de grandezas e conversão de unidades (Exatas)
        if any(d in disciplina for d in ["física", "fisica", "química", "quimica", "matemática", "matematica"]):
            if any(u in enunciado for u in ["km/h", "m/s", "cm", "mm", "litros", "gramas", "kg", "caloria", "joule", "minutos"]):
                vicios_detectados.append("IGNORA_CONVERSAO_UNIDADES")

        # 3. Checagem de especificidades do Amazonas (Humanas / Biologia COMPEC e SIS)
        if any(reg in enunciado or reg in assunto for reg in ["amazonas", "manaus", "uea", "ufam", "borracha", "cabanagem", "igarapé", "várzea", "bacia amazônica", "teatro amazonas"]):
            vicios_detectados.append("VULNERABILIDADE_REGIONAL_AMAZONICA")

        # 4. Checagem de gráficos e geometria
        if any(g in enunciado for g in ["gráfico", "grafico", "figura", "vértice", "vertice", "área sob", "inclinada"]):
            vicios_detectados.append("FALHA_INTERPRETACAO_GRAFICA")

        # 5. Checagem de grandezas vetoriais vs escalares
        if any(v in enunciado or v in assunto for v in ["vetor", "vetorial", "módulo", "modulo", "sentido", "direção", "deslocamento", "trajetória"]):
            vicios_detectados.append("CONFUSAO_VETORIAL_ESCALAR")

        # 6. Biologia / Química terminológica
        if any(b in disciplina for b in ["biologia", "química", "quimica"]):
            if any(t in enunciado for t in ["mitocôndria", "cloroplasto", "enzima", "ph", "ácido", "base", "isômero", "óxido", "ligação"]):
                vicios_detectados.append("CONFUSAO_TERMINOLOGIA_CIENTIFICA")

        # Se nenhum específico for identificado, recai na premissa conceitual
        if not vicios_detectados:
            vicios_detectados.append("LACUNA_CONCEITUAL_PREMISSA")

        return vicios_detectados

    @classmethod
    def update_profile_step(
        cls,
        current_profile: Optional[Dict[str, Any]],
        question_data: Dict[str, Any],
        selected_alt: str,
        is_correct: bool,
        timing_seconds: int = 45,
        student_name: str = "Lucas Eduardo",
        certame_foco: str = "PSC"
    ) -> Tuple[Dict[str, Any], str, bool, List[str]]:
        """
        Executa a função de transição de estado cognitivo:
        Pt+1 = g(Pt, Tentativa_t)
        
        Retorna:
        - profile_atualizado (JSON)
        - dossie_markdown (sintético e formatado)
        - ponto_cego_detectado (bool)
        - vicios_detectados (list de chaves)
        """
        profile = dict(current_profile) if current_profile and isinstance(current_profile, dict) and "topicos" in current_profile else cls.init_empty_profile(student_name, certame_foco)

        q_id = question_data.get("id", "QUESTAO")
        disciplina = question_data.get("disciplina", "Gerais")
        assunto = question_data.get("assunto") or question_data.get("topico_especifico") or disciplina
        gabarito = (question_data.get("gabarito_oficial") or "A").upper()

        # 1. Atualiza métricas globais
        profile["total_tentativas"] = profile.get("total_tentativas", 0) + 1
        if is_correct:
            profile["total_acertos"] = profile.get("total_acertos", 0) + 1

        total_t = profile["total_tentativas"]
        total_a = profile["total_acertos"]
        profile["proficiencia_global"] = round((total_a / total_t) * 100.0, 1)

        # Média móvel do tempo gasto
        tempo_antigo = profile.get("tempo_medio_segundos", 45.0)
        profile["tempo_medio_segundos"] = round(((tempo_antigo * (total_t - 1)) + timing_seconds) / total_t, 1)

        # 2. Diagnóstico de vícios pedagógicos
        vicios_detectados = []
        if not is_correct:
            vicios_detectados = cls.detect_misconceptions(question_data, selected_alt, gabarito)
            vicios_dict = profile.setdefault("vicios_cognitivos_ativos", {})
            for v_key in vicios_detectados:
                meta = cls.CATALOGO_VICIOS.get(v_key, {"nome": v_key, "descricao": "Vício cognitivo identificado."})
                if v_key not in vicios_dict:
                    vicios_dict[v_key] = {
                        "nome": meta["nome"],
                        "descricao": meta["descricao"],
                        "incidencias": 1,
                        "ultimo_topico": assunto,
                        "ultimo_registro": datetime.utcnow().strftime("%d/%m/%Y %H:%M"),
                    }
                else:
                    vicios_dict[v_key]["incidencias"] += 1
                    vicios_dict[v_key]["ultimo_topico"] = assunto
                    vicios_dict[v_key]["ultimo_registro"] = datetime.utcnow().strftime("%d/%m/%Y %H:%M")

        # 3. Atualização Epistêmica por Tópico (Knowledge Tracing Ponderado)
        topicos = profile.setdefault("topicos", {})
        topico_entry = topicos.setdefault(assunto, {
            "nome": assunto,
            "disciplina": disciplina,
            "score_dominio": 100.0 if is_correct else 0.0,
            "status": "EM_CALIBRACAO",
            "total_tentativas": 0,
            "total_erros": 0,
            "erros_consecutivos": 0,
            "tendencia": "ESTAVEL",
            "vicios_especificos": [],
            "historico_recente": [],
            "ultima_atualizacao": datetime.utcnow().isoformat(),
        })

        topico_entry["total_tentativas"] += 1
        if not is_correct:
            topico_entry["total_erros"] += 1
            topico_entry["erros_consecutivos"] += 1
            for v in vicios_detectados:
                if v not in topico_entry["vicios_especificos"]:
                    topico_entry["vicios_especificos"].append(v)
        else:
            topico_entry["erros_consecutivos"] = 0

        # Atualiza histórico binário recente do tópico (janela de 5)
        hist_topico = topico_entry.setdefault("historico_recente", [])
        hist_topico.append(is_correct)
        if len(hist_topico) > 5:
            hist_topico.pop(0)

        # Atualização ponderada com taxa de aprendizado adaptativa
        score_antigo = topico_entry["score_dominio"]
        alpha = 0.35  # peso para a tentativa mais recente
        impacto_atual = 100.0 if is_correct else 0.0
        if topico_entry["total_tentativas"] == 1:
            novo_score = impacto_atual
        else:
            novo_score = (1.0 - alpha) * score_antigo + alpha * impacto_atual
        topico_entry["score_dominio"] = round(novo_score, 1)

        # Avaliação de tendência
        if len(hist_topico) >= 3:
            if hist_topico[-2:] == [True, True]:
                topico_entry["tendencia"] = "EVOLUINDO"
            elif hist_topico[-2:] == [False, False]:
                topico_entry["tendencia"] = "QUEDANDO"
            else:
                topico_entry["tendencia"] = "ESTAVEL"

        # Classificação do status
        ponto_cego = False
        if topico_entry["score_dominio"] < 50.0 and topico_entry["total_tentativas"] >= 2:
            topico_entry["status"] = "PONTO_CEGO_CRITICO"
            ponto_cego = True
        elif topico_entry["score_dominio"] >= 70.0:
            topico_entry["status"] = "DOMINADO"
        else:
            topico_entry["status"] = "EM_CALIBRACAO"

        topico_entry["ultima_atualizacao"] = datetime.utcnow().isoformat()

        # 4. Histórico de sessão conciso (últimas 8 tentativas)
        hist_sessao = profile.setdefault("historico_recente", [])
        hist_sessao.append({
            "id": q_id,
            "assunto": assunto,
            "disciplina": disciplina,
            "acertou": is_correct,
            "marcada": selected_alt,
            "gabarito": gabarito,
            "hora": datetime.utcnow().strftime("%H:%M"),
        })
        if len(hist_sessao) > 8:
            hist_sessao.pop(0)

        profile["versao_epistemica"] = profile.get("versao_epistemica", 1) + 1
        profile["ultima_atualizacao"] = datetime.utcnow().isoformat()

        # 5. Geração do Dossiê Cognitivo Markdown Sintético
        dossie_md = cls._formatar_dossie_markdown(profile)

        return profile, dossie_md, ponto_cego, vicios_detectados

    @classmethod
    def get_active_cognitive_snapshot(
        cls,
        profile: Optional[Dict[str, Any]],
        question_data: Dict[str, Any],
        estilo_didatico: str = "SOCRATICO"
    ) -> Dict[str, Any]:
        """
        Extrai um snapshot ultra-compacto (< 200 tokens) do perfil cognitivo
        focado na questão ativa, pronto para guiar o Mentor Didático.
        """
        if not profile or not isinstance(profile, dict):
            profile = cls.init_empty_profile()

        assunto = question_data.get("assunto") or question_data.get("topico_especifico") or question_data.get("disciplina", "Gerais")
        topicos = profile.get("topicos", {})
        topico_info = topicos.get(assunto)

        vicios_globais = profile.get("vicios_cognitivos_ativos", {})
        vicios_ativos_nomes = [v["nome"] for v in vicios_globais.values() if v.get("incidencias", 0) >= 1]

        # Se houver histórico do tópico
        if topico_info:
            score = topico_info.get("score_dominio", 50.0)
            status = topico_info.get("status", "EM_CALIBRACAO")
            tendencia = topico_info.get("tendencia", "ESTAVEL")
            vicios_topico = [
                cls.CATALOGO_VICIOS.get(v, {}).get("nome", v)
                for v in topico_info.get("vicios_especificos", [])
            ]
            tentativas_t = topico_info.get("total_tentativas", 0)
            erros_t = topico_info.get("total_erros", 0)
            resumo_topico = f"{tentativas_t - erros_t}/{tentativas_t} acertos prévios ({score}% de retenção)."
        else:
            score = 50.0
            status = "PRIMEIRO_CONTATO"
            tendencia = "ESTAVEL"
            vicios_topico = []
            resumo_topico = "Primeiro contato registrado com este assunto."

        # Formula a diretriz pedagógica precisa para o Mentor
        diretriz = cls._formular_diretriz_pedagogica(
            status=status,
            vicios=vicios_topico or vicios_ativos_nomes,
            estilo=estilo_didatico,
            assunto=assunto
        )

        return {
            "estudante": profile.get("estudante", "Estudante"),
            "certame_foco": profile.get("certame_foco", "PSC"),
            "versao_perfil": profile.get("versao_epistemica", 1),
            "proficiencia_global": profile.get("proficiencia_global", 0.0),
            "topico_ativo": assunto,
            "dominio_no_topico": score,
            "status_topico": status,
            "tendencia_topico": tendencia,
            "vicios_cognitivos_relevantes": vicios_topico[:2] or vicios_ativos_nomes[:2],
            "resumo_historico_topico": resumo_topico,
            "estilo_didatico_aplicado": estilo_didatico.upper(),
            "diretriz_pedagogica": diretriz,
        }

    @classmethod
    def _formular_diretriz_pedagogica(
        cls,
        status: str,
        vicios: List[str],
        estilo: str,
        assunto: str
    ) -> str:
        """Gera a instrução precisa que modula o raciocínio do Mentor Didático."""
        vicio_destaque = vicios[0] if vicios else "análise rápida de enunciado"
        estilo = estilo.upper()

        if estilo == "SOCRATICO":
            if status == "PONTO_CEGO_CRITICO":
                return (
                    f"ALERTA DE PONTO CEGO: O aluno tem histórico de vulnerabilidade em '{assunto}' "
                    f"com incidência de '{vicio_destaque}'. Não revele a resposta. "
                    f"Formule UMA pergunta reflexiva que o force a perceber a inconsistência antes de calcular."
                )
            else:
                return (
                    f"Conduza a reflexão confrontando a alternativa marcada com o comando da banca. "
                    f"Instigue o estudante a justificar por que o distrator que escolheu viola a premissa."
                )
        elif estilo == "DIRETO":
            return (
                f"Foco pragmático em prova de vestibular. Aponte o erro em menos de 100 palavras. "
                f"Se relevante, dê o macete imediato para contornar '{vicio_destaque}'."
            )
        else:  # TEORICO
            return (
                f"Fundamentação conceitual formal passo a passo. Demonstre a alternativa correta "
                f"a partir dos axiomas da disciplina e desmonte formalmente o distrator marcado."
            )

    @classmethod
    def _formatar_dossie_markdown(cls, profile: Dict[str, Any]) -> str:
        """Gera o Dossiê Epistêmico em Markdown compacto e elegante."""
        nome = profile.get("estudante", "Lucas Eduardo")
        certame = profile.get("certame_foco", "PSC")
        versao = profile.get("versao_epistemica", 1)
        prof_geral = profile.get("proficiencia_global", 0.0)
        tot_t = profile.get("total_tentativas", 0)
        tot_a = profile.get("total_acertos", 0)

        # Extrai pontos cegos e tópicos dominados
        topicos = profile.get("topicos", {})
        pontos_cegos = [f"`{k}` ({v['score_dominio']}%)" for k, v in topicos.items() if v.get("status") == "PONTO_CEGO_CRITICO"]
        dominados = [f"`{k}` ({v['score_dominio']}%)" for k, v in topicos.items() if v.get("status") == "DOMINADO"]

        # Vícios
        vicios = profile.get("vicios_cognitivos_ativos", {})
        vicios_linhas = []
        for k, v in list(vicios.items())[:3]:
            vicios_linhas.append(f"- ⚠️ **{v['nome']}**: {v['descricao']} *(Incidências: {v['incidencias']})*")

        # Histórico recente
        hist = profile.get("historico_recente", [])
        hist_linhas = []
        for h in reversed(hist[-4:]):
            st = "✅ Acertou" if h["acertou"] else f"❌ Marcou ({h['marcada']}) / Gab: ({h['gabarito']})"
            hist_linhas.append(f"- `{h['hora']}` **{h['assunto']}**: {st}")

        return f"""# Dossiê Cognitivo & Modelo Mental — {nome}
**Certame-Alvo:** {certame} | **Versão Epistêmica:** v{versao} | **Taxa Global:** {prof_geral}% ({tot_a}/{tot_t} acertos)

### 1. Mapa Dinâmico de Pontos Cegos e Fortalezas
- **Pontos Cegos Críticos (<50%):** {', '.join(pontos_cegos) if pontos_cegos else 'Nenhum ponto cego crítico ativo.'}
- **Conteúdos Dominados (≥70%):** {', '.join(dominados) if dominados else 'Em calibração ativa de retenção.'}

### 2. Vícios Cognitivos & Armadilhas Mapeadas
{chr(10).join(vicios_linhas) if vicios_linhas else '*Nenhum vício cognitivo recorrente consolidado.*'}

### 3. Registro Cronológico Recente
{chr(10).join(hist_linhas) if hist_linhas else '*Aguardando resolução de itens.*'}
"""
