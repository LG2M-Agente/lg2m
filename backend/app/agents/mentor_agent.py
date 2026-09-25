"""
lg2m/backend/app/agents/mentor_agent.py
Agente 3 — Mentor Didático & Analista Forense de Bancas.
O coração pedagógico da LG2M: disseca distratores, desmascara pegadinhas e modula a explicação nos 3 estilos didáticos.
"""

from typing import Dict, Any
from app.agents.state import AgentState


def mentor_node(state: AgentState) -> Dict[str, Any]:
    """
    Nó do Mentor Didático: produz a explicação pedagógica orientada ao distrator marcado.
    """
    current_q = state.get("current_question_data") or {}
    selected_alt = state.get("selected_alternative", "A")
    gabarito = current_q.get("gabarito_oficial", "A")
    estilo = state.get("estilo_didatico", "DIRETO").upper()
    disciplina = current_q.get("disciplina", "Gerais")
    banca = current_q.get("certame", "COMPEC")
    if isinstance(banca, dict):
        banca = banca.get("sigla", "COMPEC")

    enunciado = current_q.get("enunciado", "")
    alternativas = current_q.get("alternativas", {})
    texto_marcado = alternativas.get(selected_alt, "")
    texto_correto = alternativas.get(gabarito, "")

    is_acerto = (selected_alt == gabarito)

    # 1. Caso o estudante tenha ACERTADO a questão
    if is_acerto:
        if estilo == "DIRETO":
            draft = (
                f"🎯 **Excelente raciocínio! Resposta Correta: Alternativa ({gabarito})**.\n\n"
                f"Você dominou perfeitamente o padrão da banca **{banca}** para {disciplina}. "
                f"A premissa da alternativa está correta e não caiu nos distratores comuns. Pronto para a próxima?"
            )
        elif estilo == "SOCRATICO":
            draft = (
                f"💡 **Muito bem! A alternativa ({gabarito}) é a correta.**\n\n"
                f"Para consolidar: o que na estrutura do enunciado te fez eliminar imediatamente a alternativa oposta? "
                f"Percebeu como a banca tentou criar uma falsa armadilha de interpretação?"
            )
        else:  # TEORICO
            draft = (
                f"📚 **Gabarito Confirmado: Alternativa ({gabarito})**.\n\n"
                f"**Análise Conceitual:** Sua dedução está perfeitamente alinhada aos fundamentos teóricos de {disciplina}. "
                f"A banca **{banca}** formulou o item exigindo a aplicação direta dos princípios canônicos. "
                f"A alternativa ({gabarito}) preenche todos os requisitos com rigor formal."
            )
        return {
            "mentor_draft_response": draft,
            "is_correct": True,
            "error_classification": None,
            "verification_attempts": state.get("verification_attempts", 0) + 1,
        }

    # 2. Caso o estudante tenha MARCADO UM DISTRATOR (ERRO PEDAGÓGICO)
    # Diagnóstico da pegadinha
    causa_erro = "PEGADINHA"
    if any(k in disciplina.lower() for k in ["física", "química", "matemática"]):
        causa_erro = "OPERACIONAL" if "cálculo" in enunciado.lower() else "CONCEITUAL"
    else:
        causa_erro = "CONCEITUAL" if "assinale a incorreta" not in enunciado.lower() else "PEGADINHA"

    # Modulação Estrita nos 3 Estilos Didáticos
    if estilo == "DIRETO":
        draft = (
            f"⚠️ **Atenção à armadilha da banca {banca}! O gabarito oficial é a alternativa ({gabarito})**.\n\n"
            f"**Por que a alternativa ({selected_alt}) é um distrator?**\n"
            f"Você marcou: *\"{texto_marcado}\"*. A banca propositalmente desenhou essa alternativa para capturar quem desconsidera a restrição principal do comando. "
            f"O macete para a prova é: identifique a premissa central antes de avaliar as opções.\n\n"
            f"👉 A opção correta é a **({gabarito})**: *\"{texto_correto}\"*, que cumpre com exatidão o que foi exigido."
        )

    elif estilo == "SOCRATICO":
        draft = (
            f"🤔 **Vamos analisar com calma! Você marcou a alternativa ({selected_alt})**.\n\n"
            f"Releia o dado fundamental do enunciado:\n"
            f"> *\"{enunciado[:180]}...\"*\n\n"
            f"Agora compare: ao afirmar que *\"{texto_marcado}\"*, isso não contradiz uma condição estrita imposta pela questão? "
            f"Qual seria a consequência se você testasse a alternativa **({gabarito})** sob essa mesma lógica? O que você nota de diferente?"
        )

    else:  # TEORICO
        draft = (
            f"📖 **Dissecação Analítica Completa — Banca {banca}**\n\n"
            f"**Gabarito Homologado:** Alternativa **({gabarito})**\n\n"
            f"### 1. Desconstrução do Distrator Marcado ({selected_alt})\n"
            f"O item *\"{texto_marcado}\"* é um distrator clássico estruturado com base em um equívoco de premissa conceitual em {disciplina}. "
            f"Embora pareça plausível em uma leitura superficial, ele falha formalmente nos axiomas da matéria.\n\n"
            f"### 2. Fundamentação Teórica da Alternativa Correta ({gabarito})\n"
            f"A alternativa *\"{texto_correto}\"* é a única rigorosamente verdadeira, pois satisfaz integralmente a relação científica descrita no texto-base.\n\n"
            f"### 3. Matriz de Distratores das Demais Alternativas\n"
            f"As outras opções foram formuladas como armadilhas secundárias (generalizações indevidas ou inversões de causa e efeito)."
        )

    return {
        "mentor_draft_response": draft,
        "is_correct": False,
        "error_classification": causa_erro,
        "verification_attempts": state.get("verification_attempts", 0) + 1,
    }
