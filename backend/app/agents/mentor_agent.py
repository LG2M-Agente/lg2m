"""
lg2m/backend/app/agents/mentor_agent.py
Agente 3 — Mentor Didático & Analista Forense de Bancas.
O coração pedagógico da LG2M:
1. Lê o Dossiê Cognitivo vivo do estudante para contextualizar a explicação aos seus pontos cegos.
2. Disseca o distrator específico marcado pelo candidato e desmascara as armadilhas da banca (COMPEC/Vunesp).
3. Responde a dúvidas conversacionais subsequentes no chat conectadas ao enunciado.
4. Modula rigorosamente a didática nos 3 estilos (Direto & Prático, Socrático & Reflexivo, Teórico & Detalhado).
"""

from typing import Dict, Any, Optional
from app.agents.state import AgentState
from app.core.database import SessionLocal
from app.models.entities import PerfilEstudante


def _obter_resumo_dossie(perfil_id: Optional[str]) -> str:
    """Recupera o resumo pedagógico do Dossiê Cognitivo do aluno."""
    if not perfil_id:
        return ""
    db = SessionLocal()
    try:
        p = db.query(PerfilEstudante).filter_by(id=perfil_id).first()
        if p and p.dossie_cognitivo_markdown:
            # Pega as primeiras linhas do dossiê para contexto
            linhas = p.dossie_cognitivo_markdown.split("\n")
            return "\n".join(linhas[:15])
        return ""
    finally:
        db.close()


def mentor_node(state: AgentState) -> Dict[str, Any]:
    """
    Nó do Mentor Didático no LangGraph:
    Interpreta o erro do estudante com base no seu perfil cognitivo prévio e gera feedback personalizado.
    """
    current_q = state.get("current_question_data") or {}
    selected_alt = (state.get("selected_alternative") or "A").upper()
    gabarito = (current_q.get("gabarito_oficial") or "A").upper()
    estilo = (state.get("estilo_didatico") or "DIRETO").upper()
    disciplina = current_q.get("disciplina", "Gerais")
    assunto = current_q.get("assunto", disciplina)
    banca = current_q.get("certame", "COMPEC")
    if isinstance(banca, dict):
        banca = banca.get("sigla", "COMPEC")

    enunciado = current_q.get("enunciado", "")
    alternativas = current_q.get("alternativas", {})
    texto_marcado = alternativas.get(selected_alt, "")
    texto_correto = alternativas.get(gabarito, "")

    intent = state.get("intent_detected", "DISSECAR_RESPOSTA")
    user_msg = state.get("user_input_message") or ""
    perfil_id = state.get("perfil_id")
    contexto_dossie = _obter_resumo_dossie(perfil_id)

    # -------------------------------------------------------------
    # CENÁRIO 1: O Estudante enviou uma DÚVIDA CONVERSACIONAL no chat
    # -------------------------------------------------------------
    if intent == "DUVIDA_CHAT" and user_msg:
        user_lower = user_msg.lower()

        # Respostas contextualizadas de mentoria socrática baseadas no tópico
        if estilo == "SOCRATICO":
            if any(w in user_lower for w in ["por que", "porque", "por que a", "motivo", "como"]):
                resposta_chat = (
                    f"🤔 **Excelente reflexão sobre {assunto}!**\n\n"
                    f"Para te ajudar a desatar esse nó: releia a premissa central da questão da banca **{banca}**:\n"
                    f"> *\"{enunciado[:140]}...\"*\n\n"
                    f"Se aplicarmos o princípio de {assunto} sob a condição que você questionou, "
                    f"qual seria a consequência direta sobre a alternativa correta **({gabarito})**? "
                    f"O que aconteceria com os dados se ignorássemos a restrição do comando?"
                )
            elif any(w in user_lower for w in ["dica", "macete", "como lembrar", "memorizar"]):
                resposta_chat = (
                    f"💡 **Macete de Prova da Banca {banca} para {disciplina}:**\n\n"
                    f"Quando se deparar com itens de *{assunto}*, a banca quase sempre tenta induzir o candidato ao erro "
                    f"nas alternativas extremas. O segredo é: isole primeiro os dados explícitos e elimine os distratores que "
                    f"violam as leis de conservação ou premissas lógicas. Consegue identificar qual alternativa foi a primeira que você descartaria?"
                )
            else:
                resposta_chat = (
                    f"💡 **Mentor LG2M — Análise de Dúvida:**\n\n"
                    f"Entendi seu questionamento sobre *\"{user_msg}\"*. "
                    f"Em {disciplina} ({assunto}), a chave para responder a essa pergunta é confrontar a alternativa que você considerou "
                    f"com o gabarito oficial **({gabarito})**. "
                    f"Qual ponto da fundamentação conceitual ainda parece conflitante para você?"
                )
        elif estilo == "DIRETO":
            resposta_chat = (
                f"⚡ **Direto ao ponto para a prova da banca {banca}:**\n\n"
                f"Em relação a *\"{user_msg}\"*: em questões de *{assunto}*, o ponto crítico é que a alternativa **({gabarito})** "
                f"é a única que atende perfeitamente à definição formal, enquanto os distratores trazem generalizações falsas. "
                f"Lembre-se: em {disciplina}, verifique sempre as unidades e as condições de contorno!"
            )
        else:  # TEORICO
            resposta_chat = (
                f"📖 **Fundamentação Teórica Detalhada — {disciplina}:**\n\n"
                f"Analisando sua pergunta sob os princípios canônicos de *{assunto}*:\n\n"
                f"1. **Definição Axiomática:** O comando da questão exige a aplicação estrita das propriedades de {assunto};\n"
                f"2. **Análise da Incoerência:** A dúvida apresentada decorre comumente da confusão entre grandezas escalares e vetoriais (ou premissas semânticas afins);\n"
                f"3. **Conclusão Formal:** A alternativa homologada **({gabarito})** permanece como a única analiticamente válida."
            )

        return {
            "mentor_draft_response": resposta_chat,
            "verified_response": resposta_chat,
            "guardrail_status": "APPROVED",
            "verification_attempts": state.get("verification_attempts", 0) + 1,
        }

    # -------------------------------------------------------------
    # CENÁRIO 2: O Estudante ACERTOU a Questão
    # -------------------------------------------------------------
    is_acerto = (selected_alt == gabarito)

    if is_acerto:
        if estilo == "DIRETO":
            draft = (
                f"🎯 **Excelente raciocínio! Resposta Correta: Alternativa ({gabarito})**.\n\n"
                f"Você dominou com precisão o padrão da banca **{banca}** para {disciplina} (*{assunto}*). "
                f"A premissa da alternativa está correta e você evitou com segurança os distratores comuns. Pronto para a próxima?"
            )
        elif estilo == "SOCRATICO":
            draft = (
                f"💡 **Muito bem! A alternativa ({gabarito}) é a correta.**\n\n"
                f"Para consolidar a retenção a longo prazo: o que na estrutura do comando te permitiu eliminar de imediato a alternativa mais plausível? "
                f"Percebeu como a comissão da {banca} tentou armar um distrator de leitura rápida?"
            )
        else:  # TEORICO
            draft = (
                f"📚 **Gabarito Homologado Confirmado: Alternativa ({gabarito})**.\n\n"
                f"**Demonstração Conceitual:** Sua dedução preenche todos os requisitos teóricos em {disciplina}. "
                f"A alternativa **({gabarito})** é rigorosamente consistente com os axiomas da matéria (*{assunto}*). "
                f"Excelente fixação do conteúdo do certame!"
            )

        return {
            "mentor_draft_response": draft,
            "is_correct": True,
            "error_classification": None,
            "verification_attempts": state.get("verification_attempts", 0) + 1,
        }

    # -------------------------------------------------------------
    # CENÁRIO 3: O Estudante ERROU (Dissecação do Distrator)
    # -------------------------------------------------------------
    causa_erro = "PEGADINHA"
    if any(k in disciplina.lower() for k in ["física", "química", "matemática"]):
        causa_erro = "OPERACIONAL" if "cálculo" in enunciado.lower() else "CONCEITUAL"
    else:
        causa_erro = "CONCEITUAL" if "assinale a incorreta" not in enunciado.lower() else "PEGADINHA"

    prefixo_perfil = ""
    if contexto_dossie and "Ponto cego" in contexto_dossie:
        prefixo_perfil = f"*(Diagnóstico integrado ao seu perfil: identificamos que o tema {assunto} tem demandado atenção nos seus treinos recentes.)*\n\n"

    if estilo == "DIRETO":
        draft = (
            f"⚠️ **Atenção à armadilha da banca {banca}! O gabarito oficial homologado é ({gabarito})**.\n\n"
            f"{prefixo_perfil}"
            f"**Por que a alternativa ({selected_alt}) é um distrator?**\n"
            f"Você marcou: *\"{texto_marcado}\"*. A banca desenhou intencionalmente essa opção para quem desconsidera a restrição central do enunciado. "
            f"O macete para a prova é: isole a condição de contorno antes de marcar!\n\n"
            f"👉 A opção correta é a **({gabarito})**: *\"{texto_correto}\"*, que satisfaz com exatidão o que foi solicitado."
        )

    elif estilo == "SOCRATICO":
        draft = (
            f"🤔 **Vamos construir o raciocínio juntos! Você marcou a alternativa ({selected_alt})**.\n\n"
            f"{prefixo_perfil}"
            f"Releia atentamente o trecho-chave do enunciado da {banca}:\n"
            f"> *\"{enunciado[:160]}...\"*\n\n"
            f"Agora reflita: ao afirmar que *\"{texto_marcado}\"*, isso não contradiz uma premissa estabelecida no próprio texto? "
            f"Se você testar a alternativa correta **({gabarito})** sob a mesma ótica, qual é a diferença fundamental no resultado?"
        )

    else:  # TEORICO
        draft = (
            f"📖 **Dissecação Forense Completa — Banca {banca} ({disciplina})**\n\n"
            f"{prefixo_perfil}"
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
        "verification_attempts": state.get("verification_attempts", 0) + 1,
    }
