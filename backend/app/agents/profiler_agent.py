"""
lg2m/backend/app/agents/profiler_agent.py
Agente 4 — Profiler Cognitivo & Gestor de Dificuldades.
Guardião da memória evolutiva de longo prazo:
1. Atualiza registros de dificuldade e médias ponderadas de domínio curricular.
2. Analisa baterias completas de exames e gera diagnósticos reflexivos.
3. Constrói e atualiza o Dossiê Cognitivo vivo do estudante (Markdown) entre sessões.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.agents.state import AgentState
from app.core.database import SessionLocal
from app.models.entities import (
    TentativaQuestao,
    RegistroDificuldade,
    Assunto,
    PerfilEstudante,
    Simulado,
    Questao,
)


def _formatar_dossie_inicial(perfil: PerfilEstudante) -> str:
    """Gera a estrutura inicial do Dossiê Cognitivo para o estudante."""
    nome = perfil.usuario.nome if perfil.usuario else "Estudante"
    return f"""# Dossiê Cognitivo & Memória Epistêmica — {nome}
**Certame-Alvo:** {perfil.certame_foco} | **Estilo Didático:** {perfil.estilo_didatico_padrao}
**Data de Abertura:** {datetime.utcnow().strftime('%d/%m/%Y')} | **Versão:** 1

---

## 1. Síntese do Modelo Mental
Estudante em fase de calibração ativa de conhecimentos para o vestibular seriado {perfil.certame_foco}. 
Acompanhamento contínuo de taxas de retenção, modelos mentais e identificação de vícios conceituais.

## 2. Mapa Dinâmico de Pontos Cegos e Fragilidades
*Nenhum ponto cego crítico consolidado até o momento. Conclua mais baterias de questões para refinar o diagnóstico.*

## 3. Linha do Tempo e Diário de Baterias Realizadas
"""


def profiler_node(state: AgentState) -> Dict[str, Any]:
    """
    Nó do Profiler no LangGraph:
    Registra a tentativa individual, recalcula o score ponderado de domínio do assunto
    e atualiza a memória de longo prazo no dossiê cognitivo do estudante.
    """
    db = SessionLocal()
    try:
        perfil_id = state.get("perfil_id")
        current_q = state.get("current_question_data") or {}
        q_id = current_q.get("id")
        selected_alt = state.get("selected_alternative")
        is_acerto = state.get("is_correct", False)
        causa = state.get("error_classification") or ("ACERTO" if is_acerto else "CONCEITUAL")
        tempo_gasto = state.get("tempo_resolucao_segundos", 45)

        # Se não houver perfil_id informado, usa o perfil demo ativo
        if not perfil_id:
            perfil = db.query(PerfilEstudante).first()
            perfil_id = perfil.id if perfil else None

        if not perfil_id or not q_id or not selected_alt:
            return {"subject_score_updated": None}

        perfil = db.query(PerfilEstudante).filter_by(id=perfil_id).first()
        if not perfil:
            return {"subject_score_updated": None}

        # 1. Registra a tentativa individual
        tentativa = TentativaQuestao(
            perfil_id=perfil_id,
            questao_id=q_id,
            alternativa_marcada=selected_alt,
            acertou=is_acerto,
            tempo_gasto_segundos=tempo_gasto,
            causa_erro=causa if not is_acerto else None,
        )
        db.add(tentativa)
        db.flush()

        # 2. Localiza o Assunto da questão
        assunto_id = current_q.get("assunto_id")
        assunto_nome = current_q.get("assunto", "Geral")
        disc_nome = current_q.get("disciplina", "Geral")

        if not assunto_id:
            assunto_obj = db.query(Assunto).filter_by(nome=assunto_nome).first()
            assunto_id = assunto_obj.id if assunto_obj else None

        novo_score = 100.0 if is_acerto else 0.0
        ponto_cego = False

        if assunto_id:
            reg = db.query(RegistroDificuldade).filter_by(
                perfil_id=perfil_id,
                assunto_id=assunto_id
            ).first()

            if not reg:
                reg = RegistroDificuldade(
                    perfil_id=perfil_id,
                    assunto_id=assunto_id,
                    total_tentativas=1,
                    total_erros=0 if is_acerto else 1,
                    indice_dominio=100.0 if is_acerto else 0.0,
                )
                db.add(reg)
            else:
                reg.total_tentativas += 1
                if not is_acerto:
                    reg.total_erros += 1

                # Média ponderada de acertos
                acertos = reg.total_tentativas - reg.total_erros
                reg.indice_dominio = round((acertos / reg.total_tentativas) * 100.0, 1)

            db.commit()
            novo_score = reg.indice_dominio
            ponto_cego = (novo_score < 50.0 and reg.total_tentativas >= 2)

        # 3. Atualização Reflexiva do Dossiê Cognitivo (Memória Viva)
        dossie = perfil.dossie_cognitivo_markdown or _formatar_dossie_inicial(perfil)
        timestamp = datetime.utcnow().strftime("%d/%m/%Y %H:%M")

        status_str = "ACERTO" if is_acerto else f"ERRO ({causa})"
        nota_tentativa = f"\n- **[{timestamp}]** Questão `{q_id}` ({disc_nome} - *{assunto_nome}*): Resultado: **{status_str}**. "
        if not is_acerto:
            nota_tentativa += f"Marcou ({selected_alt}). Gabarito era ({current_q.get('gabarito_oficial')}). Requer atenção no tema."
        else:
            nota_tentativa += f"Raciocínio correto demonstrado no conceito."

        # Mantém dossiê compacto limitando logs muito extensos
        if len(dossie) > 4000:
            linhas = dossie.split("\n")
            dossie = "\n".join(linhas[:40]) + "\n\n*(registros anteriores consolidados)*\n"

        perfil.dossie_cognitivo_markdown = dossie + nota_tentativa
        perfil.versao_perfil = (perfil.versao_perfil or 1) + 1
        db.commit()

        return {
            "subject_score_updated": novo_score,
            "critical_blindspot_detected": ponto_cego,
            "profile_version": perfil.versao_perfil,
        }

    except Exception as e:
        db.rollback()
        print(f"[ERRO NO PROFILER]: {e}")
        return {"subject_score_updated": None}
    finally:
        db.close()


def diagnose_simulado_battery(simulado_id: str, db: Session) -> str:
    """
    Função do Agente Profiler acionada após o término de uma BATERIA de questões (Simulado).
    Analisa os acertos e erros, identifica padrões cognitivos recorrentes
    e sintetiza um relatório qualitativo para o dossiê cognitivo do estudante.
    """
    sim = db.query(Simulado).filter_by(id=simulado_id).first()
    if not sim:
        return "Simulado não localizado."

    perfil = sim.perfil
    itens = sim.itens
    total = len(itens)
    if total == 0:
        return "Nenhum item avaliado."

    acertos = sum(1 for it in itens if it.acertou)
    taxa = round((acertos / total) * 100.0, 1)

    # Agrupa por disciplina
    disciplinas_stats = {}
    erros_detalhados = []

    for item in itens:
        q = db.query(Questao).filter_by(id=item.questao_id).first()
        if not q:
            continue
        disc = q.disciplina_nome
        assunto = q.assunto_rel.nome if q.assunto_rel else disc
        if disc not in disciplinas_stats:
            disciplinas_stats[disc] = {"total": 0, "acertos": 0, "assuntos_erros": []}
        disciplinas_stats[disc]["total"] += 1

        if item.acertou:
            disciplinas_stats[disc]["acertos"] += 1
        else:
            disciplinas_stats[disc]["assuntos_erros"].append(assunto)
            erros_detalhados.append({
                "id": q.id,
                "disc": disc,
                "assunto": assunto,
                "marcada": item.alternativa_marcada,
                "gabarito": q.gabarito_oficial
            })

    # Síntese do Parecer do Profiler
    pontos_fortes = [d for d, s in disciplinas_stats.items() if (s["acertos"] / s["total"]) >= 0.70]
    pontos_atencao = [d for d, s in disciplinas_stats.items() if (s["acertos"] / s["total"]) < 0.50]

    diagnostico_linhas = [
        f"### Diagnóstico Pedagógico do Profiler — Bateria #{sim.id[:8]}",
        f"**Rendimento Global:** {acertos}/{total} acertos ({taxa}%) em {sim.tipo} ({sim.certame_sigla} Etapa {sim.etapa}).",
    ]

    if taxa >= 80:
        diagnostico_linhas.append("🟢 **Avaliação:** Desempenho de excelência com alta consistência nas premissas fundamentais.")
    elif taxa >= 60:
        diagnostico_linhas.append("🟡 **Avaliação:** Rendimento satisfatório, mas com vulnerabilidades localizadas em tópicos específicos.")
    else:
        diagnostico_linhas.append("🔴 **Avaliação:** Lacunas conceituais críticas detectadas. Recomenda-se mentoria socrática focada.")

    if pontos_fortes:
        diagnostico_linhas.append(f"- **Pontos Fortes Demonstrados:** {', '.join(pontos_fortes)}.")
    if pontos_atencao:
        diagnostico_linhas.append(f"- **Pontos de Atenção Crítica (Revisão Imediata):** {', '.join(pontos_atencao)}.")

    if erros_detalhados:
        diagnostico_linhas.append("\n**Padrão dos Erros Identificados na Bateria:**")
        for err in erros_detalhados[:4]:
            diagnostico_linhas.append(
                f"  * `{err['id']}` ({err['disc']} - *{err['assunto']}*): marcou ({err['marcada']}) em vez de ({err['gabarito']})."
            )

    diagnostico_final = "\n".join(diagnostico_linhas)

    # 4. Salva diagnóstico no simulado
    sim.diagnostico_profiler = diagnostico_final

    # 5. Atualiza o Dossiê Cognitivo vivo do estudante
    if perfil:
        dossie = perfil.dossie_cognitivo_markdown or _formatar_dossie_inicial(perfil)
        timestamp = datetime.utcnow().strftime("%d/%m/%Y")
        nova_sessao = f"\n\n### [Bateria #{sim.id[:8]}] - {timestamp} ({sim.certame_sigla} {sim.etapa})\n{diagnostico_final}\n"

        perfil.dossie_cognitivo_markdown = dossie + nova_sessao
        perfil.versao_perfil = (perfil.versao_perfil or 1) + 1
        db.commit()

    return diagnostico_final
