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
    system_prompt = f"""Você é o Mentor Didático de IA do LG2M, especialista na preparação de estudantes para os vestibulares seriados do Amazonas (PSC da UFAM e SIS da UEA).
Sua missão é acompanhar o estudante {nome_aluno} com paciência, acolhimento e profunda didática.

LEMBRE-SE SEMPRE:
- O estudante está em processo ativo de aprendizado. Use uma linguagem simples, clara, humana e acolhedora (evite termos como 'axioma', 'análise analítica', 'distrator', 'dissecação forense', 'premissa canônica'). Fale como um excelente professor explicando com carinho na lousa.
- Explicações completas e detalhadas: Nunca forneça respostas curtas, telegráficas ou superficiais. Estruture a resposta passo a passo (Passo 1, Passo 2, Passo 3, etc.), explicando o 'porquê' de cada etapa para que o aluno realmente compreenda e fixe o conteúdo.
- NÃO FORCE PERGUNTAS AO ESTUDANTE: O estudante precisa de explicações claras e soluções, não de interrogatórios. Seu objetivo é ENSINAR e EXPLICAR. Nunca termine com baterias de perguntas e não deixe dúvidas em aberto. Mesmo no estilo Socrático, guie o raciocínio passo a passo de forma acolhedora e encorajadora, sem cobrar respostas do aluno. Nos estilos DIRETO e TEÓRICO, seja 100% afirmativo e expositivo.

DIRETRIZES DO ESTILO DIDÁTICO ({estilo}):
- DIRETO:
  Seja prático e objetivo, mas com explicação completa e passo a passo.
  1) Explique de forma simples o que a questão está pedindo.
  2) Apresente o passo a passo da resolução de forma clara e visual.
  3) Aponte com gentileza onde estava a pegadinha ou detalhe que costuma induzir ao erro.
  4) Dê uma dica de prova prática (macete de ouro) para a banca {banca}.
  *NÃO faça perguntas ao aluno.*

- SOCRATICO:
  Conduza o estudante com acolhimento, mostrando a linha de raciocínio passo a passo.
  1) Contextualize a situação do problema de forma prática e intuitiva.
  2) Demonstre como analisar cada pista do enunciado até chegar à conclusão correta.
  3) Mostre por que a alternativa correta faz todo o sentido e desfaça a confusão da alternativa errada.
  4) Encerre com uma frase de apoio e motivação para os estudos.
  *Evite ficar interrogando o aluno com perguntas reflexivas difíceis.*

- TEORICO:
  Apresente uma aula completa, detalhada e aprofundada, mantendo a didática simples e sem complicação.
  1) Apresente os conceitos teóricos fundamentais com exemplos intuitivos do dia a dia.
  2) Demonstre a resolução detalhada passo a passo, abrindo cada dedução ou fórmula.
  3) Analise as alternativas para mostrar por que a oficial é a correta e por que as outras não se sustentam.
  4) Finalize com um resumo claro em tópicos para o aluno anotar no caderno de estudos.
  *NÃO faça perguntas ao aluno.*

PERFIL DO ESTUDANTE:
- Assunto em foco: {assunto} ({disciplina})
- Nível de Domínio no tópico: {dominio}% ({status_topico})
- Ponto de atenção mapeado: {', '.join(vicios) if vicios else 'Em fase inicial de calibração.'}
- Diretriz Pedagógica: {diretriz}

REGRA INVIOLÁVEL DE CONFIABILIDADE (GROUND TRUTH):
O gabarito oficial homologado pela comissão examinadora é a alternativa ({gabarito}).
Você NUNCA deve contradizer ou alterar a letra do gabarito oficial.
"""

    # Histórico de conversação de curto prazo nesta questão
    messages_hist = state.get("messages") or []
    conversa_previa = ""
    if len(messages_hist) > 1:
        anteriores = [m for m in messages_hist[:-1] if m.get("content")]
        if anteriores:
            linhas = []
            for m in anteriores[-6:]:
                papel = "Estudante" if m.get("role") in ("user", "usuario") else "Mentor Didático"
                conteudo = m.get("content", "").strip()
                if len(conteudo) > 400:
                    conteudo = conteudo[:397] + "..."
                linhas.append(f"- **{papel}**: {conteudo}")
            conversa_previa = "\nHISTÓRICO DO DIÁLOGO ANTERIOR ENTRE VOCÊ E O ESTUDANTE NESTA QUESTÃO:\n" + "\n".join(linhas) + "\n"

    if intent == "DUVIDA_CHAT" and user_msg:
        user_prompt = f"""Questão ({banca} - {disciplina}):
{enunciado}

Alternativas:
{alternativas}
Gabarito Oficial: ({gabarito}) - "{texto_correto}"
{conversa_previa}
NOVA MENSAGEM / DÚVIDA ENVIADA PELO ESTUDANTE {nome_aluno}:
"{user_msg}"

Orientações pedagógicas para sua resposta:
1. Leve em total consideração o histórico do diálogo anterior para manter a coerência e continuidade da conversa (se o estudante se referir a algo dito antes, responda com perfeita contextualização).
2. Explique de maneira acolhedora, clara e passo a passo no estilo {estilo}.
3. Não deixe nenhuma dúvida pendente e NÃO faça perguntas interrogatórias ao aluno."""
    elif is_acerto:
        user_prompt = f"""O estudante acertou a questão marcando a alternativa ({selected_alt})!
Questão ({banca} - {disciplina}):
{enunciado}

Alternativas:
{alternativas}
Gabarito Oficial: ({gabarito}) - "{texto_correto}"

Parabenize {nome_aluno} com entusiasmo e elabore uma explicação pedagógica completa, passo a passo, consolidando por que a alternativa ({selected_alt}) está certa, qual foi o raciocínio correto e uma dica de ouro para fixar esse padrão nas provas da banca {banca} no estilo {estilo}. NÃO faça perguntas ao aluno."""
    else:
        aviso_ponto_cego = ""
        if status_topico == "PONTO_CEGO_CRITICO":
            aviso_ponto_cego = f"""
ATENÇÃO PEDAGÓGICA (PONTO CEGO CRÍTICO IDENTIFICADO):
Note que o estudante {nome_aluno} já teve dificuldades e erros em questões anteriores de {assunto} (retenção atual de apenas {dominio}%).
Inicie sua fala mencionando de forma empática e acolhedora que você notou no histórico dele que {assunto} tem sido um desafio recorrente nos treinos recentes, encorajando-o dizendo que errar no treino faz parte e que agora vocês vão desatar esse nó juntos passo a passo.
"""

        user_prompt = f"""O estudante tentou responder a questão, mas errou.
Questão da banca {banca} ({disciplina} - {assunto}):
{enunciado}

Alternativas:
{alternativas}
Alternativa marcada pelo estudante: ({selected_alt}) -> "{texto_marcado}"
Gabarito oficial correto da banca: ({gabarito}) -> "{texto_correto}"
{aviso_ponto_cego}
Explique para {nome_aluno} com acolhimento, gentileza e didática impecável no estilo {estilo}:
1. O que a questão está pedindo em termos simples.
2. A resolução detalhada passo a passo que leva com certeza à alternativa correta ({gabarito}).
3. Por que a alternativa ({selected_alt}) parecia tentadora (onde estava a pegadinha ou confusão comum) e como não cair mais nela.
4. Uma dica prática e encorajadora para fixar o conteúdo.
Mantenha uma linguagem simples, humana e clara. NÃO faça perguntas ao aluno."""

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
    # 2. FALLBACK COGNITIVO DETERMINÍSTICO DIDÁTICO E PASSO A PASSO
    # -------------------------------------------------------------
    prefixo_vicio = ""
    if vicios:
        prefixo_vicio = f"💡 *Dica do seu Mentor para {assunto}:* Atenção aos detalhes do enunciado para evitar deslizes comuns da banca {banca}!\n\n"
    elif status_topico == "PONTO_CEGO_CRITICO":
        prefixo_vicio = f"💡 *Atenção especial:* O tema **{assunto}** é muito cobrado no certame e vale a pena revisar com carinho este passo a passo.\n\n"

    # Caso Dúvida no Chat
    if intent == "DUVIDA_CHAT" and user_msg:
        if estilo == "SOCRATICO":
            draft = (
                f"Olá, {nome_aluno}! Que ótima dúvida sobre **{assunto}** na prova da **{banca}**.\n\n"
                f"{prefixo_vicio}"
                f"Vamos construir a compreensão juntos, passo a passo:\n\n"
                f"### Passo 1: O que o enunciado nos informa\n"
                f"O comando da questão estabelece:\n"
                f"> *\"{enunciado[:140]}...\"*\n\n"
                f"### Passo 2: Analisando a sua dúvida\n"
                f"Você perguntou sobre *\"{user_msg}\"*. Quando pensamos nesse fenômeno em {disciplina}, "
                f"precisamos observar as condições específicas que a banca determinou. "
                f"Muitas vezes, nossa intuição inicial nos leva a generalizar uma regra que só vale em certas condições.\n\n"
                f"### Passo 3: A conclusão correta\n"
                f"Ao aplicarmos a regra de **{assunto}**, percebemos que a alternativa correta é a **({gabarito})**: *\"{texto_correto}\"*. "
                f"Ela é a única que atende perfeitamente a todos os requisitos do problema.\n\n"
                f"Espero que esse passo a passo tenha clareado as ideias! Estou à disposição para continuarmos aprendendo."
            )
        elif estilo == "DIRETO":
            draft = (
                f"Olá, {nome_aluno}! Vamos esclarecer sua dúvida sobre *\"{user_msg}\"* de forma bem prática e direto ao ponto.\n\n"
                f"{prefixo_vicio}"
                f"### Passo a Passo da Resolução:\n"
                f"1. **Identificando o comando:** A questão de {disciplina} ({assunto}) da banca **{banca}** exige a aplicação direta do conceito central.\n"
                f"2. **Por que a alternativa ({gabarito}) é a correta:** A alternativa **({gabarito})** (*\"{texto_correto}\"*) expressa exatamente a relação correta entre as grandezas do problema.\n"
                f"3. **Onde as outras opções falham:** As outras alternativas colocam condições que contradizem as propriedades fundamentais de {assunto}.\n\n"
                f"📌 **Dica de ouro para a prova da {banca}:** Destaque sempre no texto as palavras-chave antes de marcar sua opção definitiva!"
            )
        else:  # TEORICO
            draft = (
                f"Olá, {nome_aluno}! Vamos fazer uma análise teórica completa e passo a passo sobre sua dúvida em **{assunto}** ({disciplina}).\n\n"
                f"{prefixo_vicio}"
                f"### 1. O Conceito Fundamental\n"
                f"Em {disciplina}, o tópico de **{assunto}** descreve o comportamento dos sistemas sob regras bem definidas. "
                f"Em relação a *\"{user_msg}\"*, é essencial separar o que é dado inicial do que é consequência direta do processo.\n\n"
                f"### 2. Demonstração Passo a Passo\n"
                f"- **Etapa 1:** Analisamos as condições de contorno fornecidas no enunciado da banca **{banca}**.\n"
                f"- **Etapa 2:** Aplicamos as leis da matéria correspondentes.\n"
                f"- **Etapa 3:** Verificamos que a alternativa **({gabarito})** (*\"{texto_correto}\"*) é a única que satisfaz todas as equações e relações conceituais.\n\n"
                f"### 3. Resumo para seu Caderno de Estudos\n"
                f"Guarde esta relação: nas provas da {banca}, questões de {assunto} cobram a compreensão da definição essencial da matéria."
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
                f"🎉 **Parabéns, {nome_aluno}! Você acertou em cheio: Alternativa ({gabarito})!**\n\n"
                f"Você dominou com muita clareza o padrão da banca **{banca}** para {disciplina} (*{assunto}*).\n\n"
                f"### Passo a Passo do que você fez certo:\n"
                f"1. **Leitura precisa:** Você identificou a premissa central do enunciado.\n"
                f"2. **Aplicação do conceito:** Aplicou a regra de {assunto} sem cair nas pegadinhas das outras opções.\n"
                f"3. **Gabarito confirmado:** A alternativa **({gabarito})** (*\"{texto_correto}\"*) é a resposta correta.\n\n"
                f"📌 **Dica de Ouro:** Seu domínio no tema subiu para **{min(100.0, dominio + 10.0):.0f}%**. Continue nesse ritmo!"
            )
        elif estilo == "SOCRATICO":
            draft = (
                f"👏 **Excelente trabalho, {nome_aluno}! A resposta correta é mesmo a alternativa ({gabarito})!**\n\n"
                f"É muito bom ver sua evolução em **{assunto}**. Vamos recapitular o raciocínio vitorioso que você seguiu:\n\n"
                f"1. **Identificação das pistas:** Você percebeu o que o enunciado da banca **{banca}** realmente solicitava.\n"
                f"2. **Eliminação dos distratores:** Você desconsiderou as opções que tentavam induzir ao erro de leitura rápida.\n"
                f"3. **Confirmação:** A alternativa **({gabarito})** (*\"{texto_correto}\"*) encaixa perfeitamente com a teoria de {disciplina}.\n\n"
                f"Parabéns pelo foco e dedicação aos estudos!"
            )
        else:  # TEORICO
            draft = (
                f"📚 **Gabarito Oficial Confirmado com Sucesso: Alternativa ({gabarito})!**\n\n"
                f"Parabéns pela resolução, {nome_aluno}! Sua dedução foi impecável em {disciplina} (*{assunto}*).\n\n"
                f"### Fundamentação Teórica da Resolução:\n"
                f"- **Preceito Central:** A questão avalia a capacidade de relacionar os fundamentos de {assunto} com a situação proposta pela banca **{banca}**.\n"
                f"- **Validação da Alternativa ({gabarito}):** A proposição *\"{texto_correto}\"* é plenamente coerente com as definições conceituais da matéria.\n"
                f"- **Análise dos Distratores:** As demais alternativas continham contradições ou condições não atendidas pelo enunciado.\n\n"
                f"Excelente domínio do conteúdo! Mantenha essa sólida base teórica para as próximas questões."
            )

        return {
            "mentor_draft_response": draft,
            "is_correct": True,
            "error_classification": None,
            "cognitive_profile_summary": snapshot,
            "verification_attempts": state.get("verification_attempts", 0) + 1,
        }

    # Caso Erro (Explicação acolhedora e passo a passo)
    causa_erro = "CONCEITUAL"
    if any(k in disciplina.lower() for k in ["física", "química", "matemática"]):
        causa_erro = "OPERACIONAL" if "cálculo" in enunciado.lower() else "CONCEITUAL"
    elif "assinale a incorreta" in enunciado.lower() or "falsa" in enunciado.lower():
        causa_erro = "PEGADINHA"

    if estilo == "DIRETO":
        draft = (
            f"Olá, {nome_aluno}! Não se preocupe com o tropeço: errar nas questões de treino é exatamente o melhor jeito de aprender!\n\n"
            f"{prefixo_vicio}"
            f"O gabarito correto da banca **{banca}** é a **Alternativa ({gabarito})**: *\"{texto_correto}\"*.\n\n"
            f"### Vamos entender passo a passo:\n\n"
            f"**Passo 1 — O que a questão pede:**\n"
            f"O enunciado trata de **{assunto}** em {disciplina} e pede para identificar a relação verdadeira conforme o comando.\n\n"
            f"**Passo 2 — Onde estava a pegadinha na sua escolha ({selected_alt}):**\n"
            f"Você marcou *\"{texto_marcado}\"*. Essa alternativa parece atraente à primeira vista, mas ela desconsidera um detalhe crucial do problema.\n\n"
            f"**Passo 3 — Por que a alternativa ({gabarito}) é a correta:**\n"
            f"A opção **({gabarito})** (*\"{texto_correto}\"*) atende perfeitamente à definição correta da matéria, sem contradições.\n\n"
            f"📌 **Dica prática para a prova:** No vestibular da {banca}, sempre sublinhe as palavras de restrição do comando para não cair em opções tentadoras!"
        )
    elif estilo == "SOCRATICO":
        draft = (
            f"Olá, {nome_aluno}! Fique tranquilo: essa é uma questão clássica da banca **{banca}** que pega muitos candidatos desatentos. Vamos desatar esse nó juntos passo a passo!\n\n"
            f"{prefixo_vicio}"
            f"O gabarito oficial homologado é a **Alternativa ({gabarito})**: *\"{texto_correto}\"*.\n\n"
            f"### A Linha de Raciocínio Passo a Passo:\n\n"
            f"**Passo 1: Relembrando o ponto central do enunciado**\n"
            f"O texto da questão traz uma situação específica de **{assunto}**. O segredo aqui é observar as condições impostas pela questão.\n\n"
            f"**Passo 2: Entendendo por que você marcou ({selected_alt})**\n"
            f"A alternativa ({selected_alt}) que você marcou (*\"{texto_marcado}\"*) é uma armadilha comum montada pela banca para quem faz uma leitura rápida da premissa.\n\n"
            f"**Passo 3: Como chegar com segurança na alternativa ({gabarito})**\n"
            f"Quando aplicamos a regra correta de {disciplina}, vemos com clareza que a alternativa **({gabarito})** é a única que fecha perfeitamente com todos os fatos do enunciado.\n\n"
            f"Conte comigo nessa caminhada, {nome_aluno}! Cada erro compreendido agora é um ponto a mais garantido na sua prova."
        )
    else:  # TEORICO
        draft = (
            f"Olá, {nome_aluno}! Vamos fazer uma análise pedagógica completa e detalhada desta questão de **{disciplina}** ({assunto}) da banca **{banca}**.\n\n"
            f"{prefixo_vicio}"
            f"**Gabarito Homologado:** Alternativa **({gabarito})** — *\"{texto_correto}\"*\n\n"
            f"### 1. Entendendo o Conceito Teórico\n"
            f"Em {disciplina}, o estudo de **{assunto}** requer atenção aos princípios fundamentais. A situação descrita no enunciado exige relacionar as variáveis em jogo sem misturar causas e efeitos.\n\n"
            f"### 2. Resolução Passo a Passo\n"
            f"- **Passo 1:** Identificamos as grandezas e hipóteses dadas no problema.\n"
            f"- **Passo 2:** Aplicamos os conceitos teóricos pertinentes a {assunto}.\n"
            f"- **Passo 3:** Chegamos à alternativa **({gabarito})**, que é rigorosamente consistente com a teoria e resolve o problema de ponta a ponta.\n\n"
            f"### 3. Análise da Opção Marcada ({selected_alt})\n"
            f"A proposição *\"{texto_marcado}\"* é um distrator elaborado intencionalmente para explorar confusões frequentes dos estudantes. Ao atentar para o detalhe central do enunciado, você conseguirá eliminá-la com facilidade nas próximas questões.\n\n"
            f"### 4. Resumo para seu Caderno de Estudos\n"
            f"Fixe este conceito: revise sempre as definições fundamentais de {assunto} para ganhar velocidade e segurança na prova."
        )

    return {
        "mentor_draft_response": draft,
        "is_correct": False,
        "error_classification": causa_erro,
        "cognitive_profile_summary": snapshot,
        "verification_attempts": state.get("verification_attempts", 0) + 1,
    }
