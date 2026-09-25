"""
lg2m/backend/tests/test_multiagent_flow.py
Testes unitários e de integração do fluxo do grafo multiagente da LG2M.
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from app.agents.graph import multiagent_engine
from app.agents.state import AgentState


def test_fluxo_mentoria_erro():
    print("\n--- TESTE 1: Fluxo de Mentoria e Dissecação de Distrator ---")
    mock_question = {
        "id": "PSC_2025_E1_LP_01",
        "disciplina": "Língua Portuguesa",
        "assunto": "Sintaxe",
        "certame": {"sigla": "PSC"},
        "enunciado": "Leia o texto... Assinale o fragmento com elipse do sujeito:",
        "alternativas": {
            "A": "Agora jazem de nariz para o ar.",
            "B": "Em todos os rostos vê-se impressa a angústia.",
            "C": "Na sala reina um desconsolo.",
            "D": "O que há é que não há assunto.",
            "E": "Uma dessas frivolidades."
        },
        "gabarito_oficial": "A",
    }

    initial_state: AgentState = {
        "user_input_message": "Marquei a letra B",
        "selected_alternative": "B",  # Errou! Gabarito é A
        "current_question_data": mock_question,
        "current_question_id": "PSC_2025_E1_LP_01",
        "estilo_didatico": "DIRETO",
        "verification_attempts": 0,
        "messages": [],
    }

    result = multiagent_engine.invoke(initial_state)

    print(f"Intenção detectada:    {result.get('intent_detected')}")
    print(f"Acertou?               {result.get('is_correct')}")
    print(f"Causa do Erro:         {result.get('error_classification')}")
    print(f"Status do Guardrail:   {result.get('guardrail_status')}")
    print(f"Score Atualizado:      {result.get('subject_score_updated')}%")
    print(f"\nExplicação Validada do Mentor:\n{result.get('verified_response')}\n")

    assert result.get("intent_detected") == "DISSECAR_RESPOSTA"
    assert result.get("is_correct") is False
    assert result.get("guardrail_status") == "APPROVED"
    assert "Atenção à armadilha da banca" in result.get("verified_response", "")
    print(">>> TESTE 1 PASSOU COM SUCESSO! <<<\n")


def test_fluxo_busca_semantica():
    print("\n--- TESTE 2: Fluxo de Busca Semântica em Linguagem Natural ---")
    initial_state: AgentState = {
        "user_input_message": "buscar questões sobre cálculo de velocidade média em física",
        "estilo_didatico": "DIRETO",
        "messages": [],
    }

    result = multiagent_engine.invoke(initial_state)
    similares = result.get("similar_questions_found", [])

    print(f"Intenção detectada:    {result.get('intent_detected')}")
    print(f"Questões retornadas:   {len(similares)}")
    if similares:
        print(f"Top-1 ID:              {similares[0]['id']}")
        print(f"Top-1 Disciplina:      {similares[0]['disciplina']}")
        print(f"Top-1 Enunciado:       {similares[0]['enunciado'][:90]}...")

    assert result.get("intent_detected") == "BUSCAR_QUESTAO"
    assert len(similares) > 0
    print(">>> TESTE 2 PASSOU COM SUCESSO! <<<\n")


def test_fluxo_flywheel_semelhantes():
    print("\n--- TESTE 3: Fluxo Flywheel de Questões Semelhantes (Cross-Banca) ---")
    mock_question = {
        "id": "PSC_2025_E1_FISICA_41",
        "disciplina": "Física",
        "assunto": "Cinemática",
        "certame": {"sigla": "PSC"},
        "enunciado": "Um móvel se desloca em linha reta com aceleração constante...",
    }

    initial_state: AgentState = {
        "user_input_message": "Quero treinar uma questão semelhante a esta",
        "current_question_data": mock_question,
        "current_question_id": "PSC_2025_E1_FISICA_41",
        "messages": [],
    }

    result = multiagent_engine.invoke(initial_state)
    similares = result.get("similar_questions_found", [])

    print(f"Intenção detectada:    {result.get('intent_detected')}")
    print(f"Questões irmãs achadas:{len(similares)}")
    for i, sim in enumerate(similares[:3], 1):
        print(f"   [{i}] {sim['id']} (Banca: {sim.get('banca')}, Score: {sim.get('score_similaridade')})")

    assert result.get("intent_detected") == "BUSCAR_SEMELHANTES"
    assert len(similares) > 0
    print(">>> TESTE 3 PASSOU COM SUCESSO! <<<\n")


if __name__ == "__main__":
    test_fluxo_mentoria_erro()
    test_fluxo_busca_semantica()
    test_fluxo_flywheel_semelhantes()
