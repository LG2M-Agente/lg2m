"""
lg2m/backend/tests/test_api_endpoints.py
Bateria de testes automatizados de integração das APIs REST e agentes.
"""

import sys
import os

# Adiciona o backend ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["total_questoes_banco"] >= 5000
    print(f"Health check OK: {data['total_questoes_banco']} questões ativas.")


def test_student_profile_and_heatmap():
    response = client.get("/api/v1/student/profile")
    assert response.status_code == 200
    perfil = response.json()
    assert perfil["nome"] == "Lucas Eduardo"
    print(f"Perfil verificado: {perfil['nome']} ({perfil['certame_foco']})")

    response_heat = client.get("/api/v1/student/heatmap")
    assert response_heat.status_code == 200
    heat = response_heat.json()
    assert "heatmap" in heat
    print(f"Heatmap verificado: {heat['total_assuntos_avaliados']} assuntos no mapa.")


def test_questions_search():
    # Busca por semântica livre
    response = client.get("/api/v1/questions/search?query=Newton+forca&limit=3")
    assert response.status_code == 200
    questoes = response.json()
    assert len(questoes) > 0
    q = questoes[0]
    assert "alternativas" in q
    assert len(q["alternativas"]) >= 4
    # Garante que NÃO vaza o gabarito na busca
    assert "gabarito" not in q
    assert "resposta_correta" not in q
    print(f"Busca semântica OK: Questão encontrada {q['codigo_referencia']} ({q['disciplina']})")
    return q["id"]


def test_attempt_submission(questao_id):
    # Envia uma tentativa deliberada
    payload = {
        "alternativa_marcada": "A",
        "tempo_gasto_segundos": 42,
        "estilo_didatico": "SOCRATICO"
    }
    response = client.post(f"/api/v1/attempts/{questao_id}", json=payload)
    assert response.status_code == 200
    resultado = response.json()
    assert "acertou" in resultado
    assert "gabarito_oficial" in resultado
    assert resultado["gabarito_oficial"] in ["A", "B", "C", "D", "E"]
    assert "explicacao_mentor" in resultado
    print(f"Tentativa submetida com sucesso: Gabarito Oficial={resultado['gabarito_oficial']}, Acertou={resultado['acertou']}")


def test_simulado_lifecycle():
    # 1. Cria um simulado de 5 questões do PSC
    create_payload = {
        "certame_sigla": "PSC",
        "etapa": "1",
        "tipo": "GERAL",
        "quantidade_questoes": 5
    }
    response = client.post("/api/v1/simulados/", json=create_payload)
    assert response.status_code == 200
    simulado = response.json()
    assert len(simulado["itens"]) == 5
    simulado_id = simulado["simulado_id"]
    print(f"Simulado criado com ID {simulado_id} (5 questões PSC-1)")

    # 2. Submete o simulado
    respostas = {item["questao_id"]: "A" for item in simulado["itens"]}
    submit_payload = {
        "respostas": respostas,
        "tempo_utilizado_segundos": 300
    }
    response_submit = client.post(f"/api/v1/simulados/{simulado_id}/submit", json=submit_payload)
    assert response_submit.status_code == 200
    diagnostico = response_submit.json()
    assert diagnostico["total_questoes"] == 5
    assert "diagnostico_ia" in diagnostico
    print(f"Simulado finalizado: {diagnostico['acertos']}/5 acertos ({diagnostico['aproveitamento_percentual']}%).")


def test_mentor_chat(questao_id):
    payload = {
        "questao_id": questao_id,
        "mensagem": "Não entendi por que a alternativa B está incorreta. Pode me dar uma dica?",
        "estilo_didatico": "SOCRATICO"
    }
    response = client.post("/api/v1/mentor/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "resposta" in data
    assert len(data["resposta"]) > 10
    print(f"Mentor Chat OK ({data['estilo_didatico']}): {data['resposta'][:80]}...")


if __name__ == "__main__":
    print("Iniciando testes da API LG2M...")
    test_health_check()
    test_student_profile_and_heatmap()
    qid = test_questions_search()
    test_attempt_submission(qid)
    test_simulado_lifecycle()
    test_mentor_chat(qid)
    print("\nTODOS OS TESTES DA API FORAM CONCLUÍDOS COM 100% DE SUCESSO!")
