import sqlite3

from services.database_service import init_db, obter_historico_avaliacoes


def test_obter_historico_avaliacoes_sem_registros(tmp_path):
    db_path = tmp_path / "historico_vazio.db"
    init_db(str(db_path))

    historico = obter_historico_avaliacoes(str(db_path))

    assert historico.empty


def test_obter_historico_avaliacoes_com_esquema_legado(tmp_path):
    db_path = tmp_path / "historico_legado.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE avaliacoes (
                id INTEGER PRIMARY KEY,
                nome TEXT,
                cargo TEXT,
                nivel TEXT,
                data TEXT,
                pontos REAL,
                classificacao TEXT,
                arquetipo TEXT
            )
            """
        )
        conn.execute(
            """
            INSERT INTO avaliacoes
                (nome, cargo, nivel, data, pontos, classificacao, arquetipo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("Candidato Teste", "Analista", "Pleno", "2026-09-20", 32.0, "Recomendado", "Operacoes"),
        )

    init_db(str(db_path))
    historico = obter_historico_avaliacoes(str(db_path))

    assert len(historico) == 1
    assert historico.loc[0, "nome"] == "Candidato Teste"
    assert historico.loc[0, "vaga"] == "Analista"
    assert historico.loc[0, "nivel"] == "Pleno"
    assert historico.loc[0, "pontos"] == 32.0
    assert historico.loc[0, "classificacao"] == "Recomendado"

def test_exportar_e_restaurar_banco_bytes(tmp_path):
    from services.database_service import init_db, salvar_avaliacao, exportar_banco_bytes, restaurar_banco_bytes, obter_historico_avaliacoes
    db_origem = tmp_path / "origem.db"
    init_db(str(db_origem))
    salvar_avaliacao({"nome": "Candidato Backup", "cargo": "Diretor", "indice_global": 75.0}, db_path=str(db_origem))
    
    # 1. Exporta os bytes
    bytes_exportados = exportar_banco_bytes(db_path=str(db_origem))
    assert len(bytes_exportados) > 0
    assert bytes_exportados.startswith(b"SQLite format 3")
    
    # 2. Restaura em um novo caminho
    db_destino = tmp_path / "destino.db"
    sucesso, msg = restaurar_banco_bytes(bytes_exportados, db_path=str(db_destino))
    assert sucesso is True
    
    # 3. Verifica dados restaurados
    df_restaurado = obter_historico_avaliacoes(db_path=str(db_destino))
    assert len(df_restaurado) == 1
    assert df_restaurado.loc[0, "nome"] == "Candidato Backup"

def test_restaurar_banco_rejeita_arquivo_invalido(tmp_path):
    from services.database_service import restaurar_banco_bytes
    db_teste = tmp_path / "invalido.db"
    arquivo_corrompido = b"conteudo de texto qualquer nao sqlite"
    sucesso, msg = restaurar_banco_bytes(arquivo_corrompido, db_path=str(db_teste))
    assert sucesso is False
    assert "Arquivo rejeitado" in msg
