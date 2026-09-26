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


def seed(clean: bool = False):
    print("=" * 70)
    print("  INICIALIZAÇÃO E SEED DO BANCO DE DADOS LG2M")
    print("=" * 70)

    # 1. Cria todas as tabelas
    if clean:
        print("\n1. Limpando tabelas existentes (clean mode)...")
        Base.metadata.drop_all(bind=engine)
        print("   [OK] Tabelas antigas removidas!")

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
                        descricao_detalhada=q_data.get("descricao_detalhada"),
                        curadoria=q_data.get("curadoria", "MODELO_LOCAL"),
                    )
                    db.add(q_obj)
                    total_questoes_inseridas += 1

                    # Alternativas
                    gab = q_data.get("gabarito_oficial", "ANULADA")
                    for letra, texto in q_data.get("alternativas", {}).items():
                        eh_c = (letra == gab)
                        alt_obj = Alternativa(
                            questao_id=q_id,
                            letra=letra,
                            texto=texto,
                            eh_correta=eh_c,
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
                    q_existente.descricao_detalhada = q_data.get("descricao_detalhada")
                    q_existente.curadoria = q_data.get("curadoria", "MODELO_LOCAL")
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
            perfil_demo = db.query(PerfilEstudante).filter_by(usuario_id=usuario_demo.id).first()

        # 6. Popula Histórico Cognitivo Rico para Demonstração (Heatmap & Vícios)
        if perfil_demo:
            from app.services.cognitive_engine import CognitiveProfileEngine
            from app.models.entities import TentativaQuestao, RegistroDificuldade

            print("\n6. Populando Histórico Cognitivo e Dossiê Epistêmico Piloto...")
            # Limpa tentativas antigas se existirem
            db.query(TentativaQuestao).filter_by(perfil_id=perfil_demo.id).delete()
            db.query(RegistroDificuldade).filter_by(perfil_id=perfil_demo.id).delete()
            db.commit()

            # Busca questões de tópicos-chave para simular o histórico
            questoes_amostra = db.query(Questao).limit(100).all()
            q_por_disc = {}
            for q in questoes_amostra:
                q_por_disc.setdefault(q.disciplina_nome, []).append(q)

            current_p_json = CognitiveProfileEngine.init_empty_profile("Lucas Eduardo", "PSC")

            # Cenários de aprendizado realistas:
            cenarios = [
                # Português: Alta proficiência (85%)
                ("Língua Portuguesa", True, 3),
                ("Língua Portuguesa", False, 1),
                ("Língua Portuguesa", True, 2),
                # História: Alta proficiência (80%)
                ("História", True, 4),
                ("História", False, 1),
                # Biologia: Intermediário (60%)
                ("Biologia", True, 3),
                ("Biologia", False, 2),
                # Química: Atenção (50%)
                ("Química", True, 2),
                ("Química", False, 2),
                # Física: Ponto Cego Crítico (25% com armadilha de unidades)
                ("Física", False, 3),
                ("Física", True, 1),
                ("Física", False, 2),
                # Matemática: Ponto Cego Crítico (30%)
                ("Matemática", False, 3),
                ("Matemática", True, 1),
                ("Matemática", False, 1),
            ]

            for disc, acertou, repeticoes in cenarios:
                cand_list = q_por_disc.get(disc, [])
                for _ in range(repeticoes):
                    if cand_list:
                        q_sel = cand_list.pop(0) if len(cand_list) > 1 else cand_list[0]
                        gab = q_sel.gabarito_oficial or "A"
                        alt_marcada = gab if acertou else ("B" if gab != "B" else "C")
                        q_data = {
                            "id": q_sel.id,
                            "disciplina": q_sel.disciplina_nome,
                            "assunto": q_sel.assunto_rel.nome if q_sel.assunto_rel else q_sel.disciplina_nome,
                            "assunto_id": q_sel.assunto_id,
                            "certame": q_sel.certame.sigla if q_sel.certame else "PSC",
                            "enunciado": q_sel.enunciado,
                            "gabarito_oficial": gab,
                        }

                        current_p_json, dossie_md, is_blind, vicios = CognitiveProfileEngine.update_profile_step(
                            current_profile=current_p_json,
                            question_data=q_data,
                            selected_alt=alt_marcada,
                            is_correct=acertou,
                            timing_seconds=42,
                            student_name="Lucas Eduardo",
                            certame_foco="PSC"
                        )

                        # Registra tentativa individual
                        t = TentativaQuestao(
                            perfil_id=perfil_demo.id,
                            questao_id=q_sel.id,
                            alternativa_marcada=alt_marcada,
                            acertou=acertou,
                            tempo_gasto_segundos=42,
                            causa_erro="CONCEITUAL" if not acertou else None
                        )
                        db.add(t)

            # Persiste perfil atualizado com registros relacionais
            perfil_demo.perfil_cognitivo_json = current_p_json
            perfil_demo.dossie_cognitivo_markdown = dossie_md
            perfil_demo.versao_perfil = current_p_json.get("versao_epistemica", 25)
            db.commit()

            # Cria registros em RegistroDificuldade para todos os tópicos no perfil
            for nome_topico, info in current_p_json.get("topicos", {}).items():
                assunto_db = db.query(Assunto).filter_by(nome=nome_topico).first()
                if not assunto_db:
                    disc_db = db.query(Disciplina).filter_by(nome=info.get("disciplina", "Gerais")).first()
                    if disc_db:
                        assunto_db = Assunto(disciplina_id=disc_db.id, nome=nome_topico)
                        db.add(assunto_db)
                        db.flush()

                if assunto_db:
                    reg = RegistroDificuldade(
                        perfil_id=perfil_demo.id,
                        assunto_id=assunto_db.id,
                        total_tentativas=info["total_tentativas"],
                        total_erros=info["total_erros"],
                        indice_dominio=info["score_dominio"]
                    )
                    db.add(reg)

            db.commit()
            print(f"   [OK] Perfil cognitivo e Heatmap populados com {current_p_json['total_tentativas']} tentativas e {len(current_p_json.get('topicos', {}))} tópicos!")

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
    clean_flag = "--clean" in sys.argv
    seed(clean=clean_flag)
