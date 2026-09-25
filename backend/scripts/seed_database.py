#!/usr/bin/env python3
"""
lg2m/backend/scripts/seed_database.py
Script de inicialização do schema e ingestão em lote do dataset canônico no banco de dados.
"""

import json
import os
import sys
from pathlib import Path

# Adiciona backend ao PYTHONPATH
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from app.core.database import Base, engine, SessionLocal
from app.models.entities import (
    Banca,
    Certame,
    Disciplina,
    Assunto,
    Questao,
    Alternativa,
    Usuario,
    PerfilEstudante,
)


def seed():
    print("=" * 70)
    print("  INICIALIZAÇÃO E SEED DO BANCO DE DADOS LG2M")
    print("=" * 70)

    # 1. Cria todas as tabelas
    print("\n1. Criando tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)
    print("   [OK] Tabelas criadas com sucesso!")

    db = SessionLocal()

    try:
        # 2. Cadastro das Bancas Canônicas
        print("\n2. Inserindo Bancas Oficiais...")
        bancas_data = [
            {"sigla": "COMPEC", "nome": "Comissão Permanente de Concursos - UFAM", "descricao": "Banca responsável pelo PSC e vestibulares da Universidade Federal do Amazonas."},
            {"sigla": "Vunesp", "nome": "Fundação Vunesp", "descricao": "Fundação para o Vestibular da Universidade Estadual Paulista, responsável pelo SIS UEA."},
        ]
        bancas_map = {}
        for b_info in bancas_data:
            existente = db.query(Banca).filter_by(sigla=b_info["sigla"]).first()
            if not existente:
                novo = Banca(**b_info)
                db.add(novo)
                db.flush()
                bancas_map[b_info["sigla"]] = novo.id
            else:
                bancas_map[b_info["sigla"]] = existente.id
        db.commit()
        print(f"   [OK] {len(bancas_map)} bancas registradas.")

        # 3. Cadastro dos Certames Oficiais
        print("\n3. Inserindo Certames Piloto...")
        certames_data = [
            {"sigla": "PSC", "nome": "Processo Seletivo Contínuo", "instituicao": "UFAM", "banca_id": bancas_map["COMPEC"], "tipo_certame": "VESTIBULAR", "esfera": "ESTADUAL"},
            {"sigla": "SIS", "nome": "Sistema de Ingresso Seriado", "instituicao": "UEA", "banca_id": bancas_map["Vunesp"], "tipo_certame": "VESTIBULAR", "esfera": "ESTADUAL"},
        ]
        certames_map = {}
        for c_info in certames_data:
            existente = db.query(Certame).filter_by(sigla=c_info["sigla"]).first()
            if not existente:
                novo = Certame(**c_info)
                db.add(novo)
                db.flush()
                certames_map[c_info["sigla"]] = novo.id
            else:
                certames_map[c_info["sigla"]] = existente.id
        db.commit()
        print(f"   [OK] {len(certames_map)} certames registrados.")

        # 4. Ingestão em Lote das 5.771 Questões Canônicas
        dataset_file = backend_dir.parent / "data" / "canonical_dataset_mvp.jsonl"
        if not dataset_file.exists():
            raise FileNotFoundError(f"Dataset não encontrado em {dataset_file}")

        print(f"\n4. Lendo e ingerindo questões de {dataset_file.name}...")

        disciplinas_map = {}
        assuntos_map = {}
        total_questoes_inseridas = 0
        total_alternativas_inseridas = 0

        # Carrega disciplinas e assuntos existentes
        for d in db.query(Disciplina).all():
            disciplinas_map[d.nome] = d.id
        for a in db.query(Assunto).all():
            assuntos_map[(a.disciplina_id, a.nome)] = a.id

        batch_questoes = []
        batch_alternativas = []
        batch_size = 500

        with open(dataset_file, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, 1):
                if not line.strip():
                    continue
                q_data = json.loads(line)

                # Garante Disciplina
                disc_nome = q_data.get("disciplina", "Conhecimentos Gerais")
                area_nome = q_data.get("area_conhecimento", "GERAIS")
                if disc_nome not in disciplinas_map:
                    nova_disc = Disciplina(nome=disc_nome, area_conhecimento=area_nome)
                    db.add(nova_disc)
                    db.flush()
                    disciplinas_map[disc_nome] = nova_disc.id

                disc_id = disciplinas_map[disc_nome]

                # Garante Assunto
                assunto_nome = q_data.get("assunto", disc_nome)
                if (disc_id, assunto_nome) not in assuntos_map:
                    novo_assunto = Assunto(disciplina_id=disc_id, nome=assunto_nome)
                    db.add(novo_assunto)
                    db.flush()
                    assuntos_map[(disc_id, assunto_nome)] = novo_assunto.id

                assunto_id = assuntos_map[(disc_id, assunto_nome)]

                # Certame ID
                cert_sigla = q_data.get("certame", {}).get("sigla", "PSC")
                c_id = certames_map.get(cert_sigla, certames_map["PSC"])

                # Questao Model
                q_id = q_data["id"]
                q_existente = db.query(Questao).filter_by(id=q_id).first()
                if not q_existente:
                    q_obj = Questao(
                        id=q_id,
                        codigo_referencia=q_data.get("codigo_referencia", q_id),
                        certame_id=c_id,
                        assunto_id=assunto_id,
                        ano=q_data.get("ano", 2025),
                        etapa_edicao=str(q_data.get("etapa_edicao", "1")),
                        numero_questao=q_data.get("numero_questao", 1),
                        disciplina_nome=disc_nome,
                        area_conhecimento=area_nome,
                        topico_especifico=q_data.get("topico_especifico"),
                        texto_base=q_data.get("texto_base"),
                        enunciado=q_data.get("enunciado", ""),
                        gabarito_oficial=q_data.get("gabarito_oficial", "ANULADA"),
                        tem_imagem=q_data.get("tem_imagem", False),
                        imagens=q_data.get("imagens", []),
                        possui_formula_matematica=q_data.get("possui_formula_matematica", False),
                        tags=q_data.get("tags", []),
                    )
                    db.add(q_obj)
                    total_questoes_inseridas += 1

                    # Alternativas
                    gab = q_data.get("gabarito_oficial", "ANULADA")
                    distratores_info = q_data.get("distratores_info", {})
                    for letra, texto in q_data.get("alternativas", {}).items():
                        eh_c = (letra == gab)
                        dist_data = distratores_info.get(letra, {})
                        alt_obj = Alternativa(
                            questao_id=q_id,
                            letra=letra,
                            texto=texto,
                            eh_correta=eh_c,
                            tipo_pegadinha=dist_data.get("tipo_pegadinha", "DESCONHECIDO"),
                            explicacao_distrator=dist_data.get("explicacao"),
                        )
                        db.add(alt_obj)
                        total_alternativas_inseridas += 1
                else:
                    # Atualiza taxonomia enriquecida de questões existentes
                    q_existente.assunto_id = assunto_id
                    q_existente.disciplina_nome = disc_nome
                    q_existente.area_conhecimento = area_nome
                    q_existente.topico_especifico = q_data.get("topico_especifico")
                    q_existente.enunciado = q_data.get("enunciado", "")
                    q_existente.tags = q_data.get("tags", [])
                    q_existente.possui_formula_matematica = q_data.get("possui_formula_matematica", False)
                    total_questoes_inseridas += 1

                if idx % batch_size == 0:
                    db.commit()
                    print(f"   ... Processadas {idx} questões")

        db.commit()
        print(f"   [OK] Ingestão concluída: {total_questoes_inseridas} questões e {total_alternativas_inseridas} alternativas persistidas.")

        # 5. Cria Usuário e Perfil Piloto para Demonstração
        print("\n5. Criando Usuário Piloto (Persona Lucas Eduardo)...")
        email_demo = "lucas.eduardo@lg2m.com"
        usuario_demo = db.query(Usuario).filter_by(email=email_demo).first()
        if not usuario_demo:
            usuario_demo = Usuario(
                email=email_demo,
                nome="Lucas Eduardo",
                tipo_plano="FREE",
            )
            db.add(usuario_demo)
            db.flush()

            perfil_demo = PerfilEstudante(
                usuario_id=usuario_demo.id,
                certame_foco="PSC",
                estilo_didatico_padrao="DIRETO",
            )
            db.add(perfil_demo)
            db.commit()
            print(f"   [OK] Usuário Lucas Eduardo criado com sucesso! (ID: {usuario_demo.id})")
        else:
            print("   [OK] Usuário Lucas Eduardo já existente.")

        print("\n" + "=" * 70)
        print("  BANCO DE DADOS PERSISTIDO E PRONTO COM SUCESSO!")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"[ERRO NO SEED]: {e}")
        import traceback
        traceback.print_exc()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed()
