"""
lg2m/backend/app/agents/mentor_agent.py
Agente 3 — Mentor Didático & Analista Forense de Bancas.

Implementa a função epistêmica de mentoria:
Y_t = f(Questao, Alternativas, Alternativa Marcada, Gabarito Oficial, Pt, Estilo Didatico)

1. Condiciona a didática rigorosamente ao Perfil Cognitivo Temporal (Pt) do estudante.
2. Disseca o distrator marcado, apontando os vícios conceituais mapeados no perfil.
3. Tenta inferência em LLM de ponta (Gemini / Groq / OpenAI) com fallback determinístico ultracontextualizado.
4. Modula a intervenção nos 3 estilos (Direto & Prático, Socrático & Reflexivo, Teórico & Detalhado).
"""

from typing import Dict, Any, Optional
from app.agents.state import AgentState
from app.core.database import SessionLocal
from app.models.entities import PerfilEstudante
from app.services.cognitive_engine import CognitiveProfileEngine
from app.services.llm_client import call_llm


def _obter_ou_gerar_snapshot_cognitivo(state: AgentState, current_q: Dict[str, Any], estilo: str) -> Dict[str, Any]:
    """Recupera ou gera sob demanda o snapshot cognitivo Pt para a questão ativa."""
    snapshot = state.get("cognitive_profile_summary")
    if snapshot and isinstance(snapshot, dict):
        return snapshot

    perfil_id = state.get("perfil_id")
    db = SessionLocal()
    try:
        perfil = db.query(PerfilEstudante).filter_by(id=perfil_id).first() if perfil_id else db.query(PerfilEstudante).first()
        if perfil:
            return CognitiveProfileEngine.get_active_cognitive_snapshot(
                profile=perfil.perfil_cognitivo_json or {},
                question_data=current_q,
                estilo_didatico=estilo
            )
        return CognitiveProfileEngine.get_active_cognitive_snapshot(
            profile=None,
            question_data=current_q,
            estilo_didatico=estilo
        )
    finally:
        db.close()


def mentor_node(state: AgentState) -> Dict[str, Any]:
    """
    Nó do Mentor Didático no LangGraph:
    Interpreta o erro do estudante condicionando a explicação ao seu perfil cognitivo temporal Pt.
    """
    current_q = state.get("current_question_data") or {}
    selected_alt = (state.get("selected_alternative") or "A").upper()
    gabarito = (current_q.get("gabarito_oficial") or "A").upper()
    estilo = (state.get("estilo_didatico") or "SOCRATICO").upper()
    disciplina = current_q.get("disciplina", "Gerais")
    assunto = current_q.get("assunto") or current_q.get("topico_especifico") or disciplina
    banca = current_q.get("certame", "COMPEC")
    if isinstance(banca, dict):
        banca = banca.get("sigla", "COMPEC")

    enunciado = current_q.get("enunciado", "")
    alternativas = current_q.get("alternativas", {})
    texto_marcado = alternativas.get(selected_alt, "")
    texto_correto = alternativas.get(gabarito, "")

    intent = state.get("intent_detected", "DISSECAR_RESPOSTA")
    user_msg = state.get("user_input_message") or ""

    # Recupera o Perfil Cognitivo Temporal Pt do estudante
    snapshot = _obter_ou_gerar_snapshot_cognitivo(state, current_q, estilo)
    dominio = snapshot.get("dominio_no_topico", 50.0)
    status_topico = snapshot.get("status_topico", "EM_CALIBRACAO")
    vicios = snapshot.get("vicios_cognitivos_relevantes", [])
    diretriz = snapshot.get("diretriz_pedagogica", "")
    nome_aluno = snapshot.get("estudante", "Estudante")

    is_acerto = (selected_alt == gabarito)

    # -------------------------------------------------------------
    # 1. TENTATIVA DE INFERÊNCIA COM LLM REAL CONDICIONADA A Pt
    # -------------------------------------------------------------
    system_prompt = f"""Você é o Mentor Didático de IA do LG2M, especialista nos certames vestibulares seriados do Amazonas (PSC da UFAM e SIS da UEA).
Sua missão é acompanhar o estudante {nome_aluno} em sua preparação ativa.

DIRETRIZES DO ESTILO DIDÁTICO ({estilo}):
- SOCRATICO: Não dê a resposta nem a fórmula de mão beijada. Formule perguntas provocativas e reflexivas que conduzam o aluno a identificar a incoerência da opção marcada perante o enunciado da banca {banca}.
- DIRETO: Seja conciso, cirúrgico (< 90 palavras). Destaque o macete de prova, a armadilha do distrator e como ganhar tempo na prova da {banca}.
- TEORICO: Apresente demonstração conceitual formal, notação científica e análise axiomática das premissas.

PERFIL COGNITIVO VIVO DO ESTUDANTE (Pt):
- Assunto em foco: {assunto} ({disciplina})
- Nível de Domínio no tópico: {dominio}% ({status_topico})
- Vícios cognitivos mapeados no histórico: {', '.join(vicios) if vicios else 'Em fase de mapeamento inicial.'}
- Diretriz Pedagógica Individual: {diretriz}

REGRA INVIOLÁVEL DE CONFIABILIDADE (GROUND TRUTH):
O gabarito oficial homologado pela comissão examinadora é a alternativa ({gabarito}).
Você NUNCA deve contradizer ou alterar a letra do gabarito oficial.
"""

    if intent == "DUVIDA_CHAT" and user_msg:
        user_prompt = f"""Questão ({banca} - {disciplina}):
{enunciado}

Alternativas:
{alternativas}
Gabarito Oficial: ({gabarito})

Dúvida ou colocação enviada pelo estudante:
"{user_msg}"

Responda mantendo rigorosamente a persona no estilo {estilo}, considerando as dificuldades prévias de {nome_aluno} em {assunto}."""
    elif is_acerto:
        user_prompt = f"""O estudante acertou a questão marcando a alternativa ({selected_alt}).
Questão: {enunciado}
Parabenize-o no estilo {estilo}, reforçando o domínio da premissa de {assunto} perante o padrão da banca {banca}."""
    else:
        user_prompt = f"""O estudante errou a questão!
Questão da banca {banca}:
{enunciado}

Alternativas:
{alternativas}
Alternativa marcada pelo estudante: ({selected_alt}) -> "{texto_marcado}"
Gabarito oficial inviolável da banca: ({gabarito}) -> "{texto_correto}"

Disseque o distrator ({selected_alt}) de forma altamente pedagógica no estilo {estilo}, considerando o vício cognitivo mapeado ({vicios[0] if vicios else 'geral'})."""

    # Tenta chamada real de LLM
    llm_response = call_llm(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.25)
    if llm_response and len(llm_response) > 40:
        return {
            "mentor_draft_response": llm_response,
            "is_correct": is_acerto,
            "error_classification": "CONCEITUAL" if not is_acerto else None,
            "cognitive_profile_summary": snapshot,
            "verification_attempts": state.get("verification_attempts", 0) + 1,
        }

    # -------------------------------------------------------------
    # 2. FALLBACK COGNITIVO DETERMINÍSTICO HIPERCONTEXTUALIZADO
    # -------------------------------------------------------------
    # Se offline ou sem API key, gera explicação rica baseada em Pt
    prefixo_vicio = ""
    if vicios:
        prefixo_vicio = f"*(Diagnóstico do seu Perfil Cognitivo: identificamos histórico recente de **{vicios[0]}** em {assunto}.)*\n\n"
    elif status_topico == "PONTO_CEGO_CRITICO":
        prefixo_vicio = f"*(Atenção: o tema **{assunto}** está classificado como Ponto Cego Crítico no seu plano de estudos.)*\n\n"

    # Caso Dúvida no Chat
    if intent == "DUVIDA_CHAT" and user_msg:
        if estilo == "SOCRATICO":
            draft = (
                f"🤔 **Excelente reflexão sobre {assunto}!**\n\n"
                f"{prefixo_vicio}"
                f"Para te ajudar a desatar esse nó: releia a premissa central da questão da banca **{banca}**:\n"
                f"> *\"{enunciado[:140]}...\"*\n\n"
                f"Se aplicarmos os axiomas de {assunto} sob a condição que você questionou, "
                f"qual seria a consequência direta sobre a alternativa correta **({gabarito})**? "
                f"Percebe como o comando impõe uma restrição que invalida as outras opções?"
            )
        elif estilo == "DIRETO":
            draft = (
                f"⚡ **Direto ao ponto para a banca {banca}:**\n\n"
                f"{prefixo_vicio}"
                f"Em relação a *\"{user_msg}\"*: em questões de *{assunto}*, a banca testa se você cai na pegadinha conceitual. "
                f"A alternativa **({gabarito})** é a única que atende estritamente à definição formal. "
                f"Macete: verifique sempre as unidades e condições de contorno antes de marcar!"
            )
        else:  # TEORICO
            draft = (
                f"📖 **Fundamentação Teórica Detalhada — {disciplina}:**\n\n"
                f"{prefixo_vicio}"
                f"Analisando sua pergunta sob os princípios canônicos de *{assunto}*:\n"
                f"1. **Definição Axiomática:** O comando exige a aplicação estrita das propriedades formais da matéria;\n"
                f"2. **Análise de Incoerência:** A dúvida decorre frequentemente da sobreposição entre grandezas escalares e vetoriais;\n"
                f"3. **Conclusão:** A alternativa oficial homologada **({gabarito})** permanece como a única analiticamente válida."
            )

        return {
            "mentor_draft_response": draft,
            "verified_response": draft,
            "guardrail_status": "APPROVED",
            "cognitive_profile_summary": snapshot,
            "verification_attempts": state.get("verification_attempts", 0) + 1,
        }

    # Caso Acerto
    if is_acerto:
        if estilo == "DIRETO":
            draft = (
                f"🎯 **Excelente raciocínio! Resposta Correta: Alternativa ({gabarito})**.\n\n"
                f"Você dominou com precisão o padrão da banca **{banca}** para {disciplina} (*{assunto}*). "
                f"Seu domínio no tópico subiu para **{min(100.0, dominio + 10.0)}%**. Pronto para a próxima?"
            )
        elif estilo == "SOCRATICO":
            draft = (
                f"💡 **Muito bem! A alternativa ({gabarito}) é a correta.**\n\n"
                f"Para consolidar a retenção a longo prazo: o que na estrutura do comando te permitiu eliminar de imediato o distrator mais plausível? "
                f"Percebeu como a comissão da {banca} tentou armar uma pegadinha de leitura rápida?"
            )
        else:  # TEORICO
            draft = (
                f"📚 **Gabarito Homologado Confirmado: Alternativa ({gabarito})**.\n\n"
                f"**Demonstração Conceitual:** Sua dedução preenche todos os requisitos teóricos em {disciplina}. "
                f"A alternativa **({gabarito})** é rigorosamente consistente com os axiomas da matéria (*{assunto}*)."
            )

        return {
            "mentor_draft_response": draft,
            "is_correct": True,
            "error_classification": None,
            "cognitive_profile_summary": snapshot,
            "verification_attempts": state.get("verification_attempts", 0) + 1,
        }

    # Caso Erro (Dissecação do Distrator)
    causa_erro = "CONCEITUAL"
    if any(k in disciplina.lower() for k in ["física", "química", "matemática"]):
        causa_erro = "OPERACIONAL" if "cálculo" in enunciado.lower() else "CONCEITUAL"
    elif "assinale a incorreta" in enunciado.lower() or "falsa" in enunciado.lower():
        causa_erro = "PEGADINHA"

    if estilo == "DIRETO":
        draft = (
            f"⚠️ **Atenção à armadilha da banca {banca}! O gabarito oficial homologado é ({gabarito})**.\n\n"
            f"{prefixo_vicio}"
            f"**Por que a alternativa ({selected_alt}) é um distrator?**\n"
            f"Você marcou: *\"{texto_marcado}\"*. A comissão desenhou intencionalmente essa opção para capturar quem se descuida da restrição central do comando. "
            f"O macete para a prova é: isole a condição de contorno antes de marcar!\n\n"
            f"👉 A opção correta é a **({gabarito})**: *\"{texto_correto}\"*, que satisfaz com exatidão o que foi solicitado."
        )
    elif estilo == "SOCRATICO":
        draft = (
            f"🤔 **Vamos construir o raciocínio juntos! Você marcou a alternativa ({selected_alt})**.\n\n"
            f"{prefixo_vicio}"
            f"Releia atentamente o trecho-chave do enunciado da {banca}:\n"
            f"> *\"{enunciado[:160]}...\"*\n\n"
            f"Agora reflita: ao afirmar que *\"{texto_marcado}\"*, isso não contradiz uma premissa estabelecida no próprio texto? "
            f"Se você testar a alternativa correta **({gabarito})** sob a mesma ótica, qual é a diferença fundamental no resultado?"
        )
    else:  # TEORICO
        draft = (
            f"📖 **Dissecação Forense Completa — Banca {banca} ({disciplina})**\n\n"
            f"{prefixo_vicio}"
            f"**Gabarito Homologado Oficial:** Alternativa **({gabarito})**\n\n"
            f"### 1. Desconstrução do Distrator Marcado ({selected_alt})\n"
            f"A proposição *\"{texto_marcado}\"* aparenta veracidade superficial, mas incorre em erro clássico de premissa em *{assunto}*. "
            f"Bancas como a {banca} exploram essa confusão conceitual comum para capturar respostas impulsivas.\n\n"
            f"### 2. Fundamentação da Alternativa Homologada ({gabarito})\n"
            f"A alternativa *\"{texto_correto}\"* é a única irrefutavelmente válida perante o edital do certame.\n\n"
            f"### 3. Síntese Didática\n"
            f"Fixe este conceito: a formulação correta decorre estritamente da relação fundamental da matéria."
        )

    return {
        "mentor_draft_response": draft,
        "is_correct": False,
        "error_classification": causa_erro,
        "cognitive_profile_summary": snapshot,
        "verification_attempts": state.get("verification_attempts", 0) + 1,
    }
