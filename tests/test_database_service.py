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
