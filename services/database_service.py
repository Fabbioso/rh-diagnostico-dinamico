import sqlite3
import json
from datetime import datetime
from typing import Tuple, Dict, Any, List, Optional

DB_NAME = "rh diagnostico dinamico.db"

def get_connection(db_path: str = DB_NAME) -> sqlite3.Connection:
    """Cria e retorna uma conexão configurada com o SQLite."""
    conn = sqlite3.connect(db_path, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = DB_NAME) -> None:
    """Inicializa a tabela de avaliações caso ela não exista."""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS avaliacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_registro TEXT NOT NULL,
        nome_candidato TEXT NOT NULL,
        cargo_pretendido TEXT,
        nivel_hierarquico TEXT,
        arquetipo_ativo TEXT,
        pontuacao_fase1 REAL,
        aderencia_fase1 REAL,
        pontuacao_fase2 REAL,
        aderencia_fase2 REAL,
        indice_global REAL,
        classificacao_final TEXT,
        sinal_vermelho INTEGER,
        parecer_tecnico TEXT,
        payload_completo_json TEXT
    );
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(create_table_sql)
        conn.commit()

def salvar_avaliacao(dados: Dict[str, Any], db_path: str = DB_NAME) -> Tuple[bool, str]:
    """
    Persiste uma avaliação corporativa consolidada no SQLite.
    Retorna uma tupla (sucesso: bool, mensagem: str).
    """
    insert_sql = """
    INSERT INTO avaliacoes (
        data_registro,
        nome_candidato,
        cargo_pretendido,
        nivel_hierarquico,
        arquetipo_ativo,
        pontuacao_fase1,
        aderencia_fase1,
        pontuacao_fase2,
        aderencia_fase2,
        indice_global,
        classificacao_final,
        sinal_vermelho,
        parecer_tecnico,
        payload_completo_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """
    try:
        init_db(db_path)
        data_registro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Extração e normalização dos dados recebidos
        nome = dados.get("nome", "").strip()
        cargo = dados.get("cargo", "").strip()
        nivel = dados.get("nivel", "").strip()
        arquetipo = dados.get("arquetipo", "")
        
        pts_f1 = float(dados.get("pontuacao_fase1", 0.0))
        ad_f1 = float(dados.get("aderencia_fase1", 0.0))
        pts_f2 = float(dados.get("pontuacao_fase2", 0.0))
        ad_f2 = float(dados.get("aderencia_fase2", 0.0))
        
        indice_global = float(dados.get("indice_global", 0.0))
        classificacao = dados.get("classificacao", "")
        sinal_vermelho = 1 if dados.get("sinal_vermelho", False) else 0
        parecer = dados.get("parecer_tecnico", "")
        
        # Converte dicionários de notas ou estado completo em JSON de auditoria
        payload_json = json.dumps(dados, ensure_ascii=False, default=str)
        
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(insert_sql, (
                data_registro,
                nome,
                cargo,
                nivel,
                arquetipo,
                pts_f1,
                ad_f1,
                pts_f2,
                ad_f2,
                indice_global,
                classificacao,
                sinal_vermelho,
                parecer,
                payload_json
            ))
            conn.commit()
            return True, f"Avaliação de '{nome}' gravada com sucesso no banco de dados!"
            
    except Exception as e:
        return False, f"Erro ao persistir no SQLite: {str(e)}"

def listar_candidatos_salvos(db_path: str = DB_NAME) -> List[Dict[str, Any]]:
    """Retorna a lista de todas as avaliações para seleção e consulta."""
    try:
        init_db(db_path)
        query = "SELECT id, data_registro, nome_candidato, cargo_pretendido, indice_global FROM avaliacoes ORDER BY id DESC"
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        print(f"[ERRO DB] Falha ao listar candidatos: {e}")
        return []


def obter_avaliacao_por_id(avaliacao_id: int, db_path: str = DB_NAME) -> Optional[Dict[str, Any]]:
    """Recupera os dados completos de uma avaliação pelo ID."""
    try:
        init_db(db_path)
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM avaliacoes WHERE id = ?", (avaliacao_id,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                if d.get("payload_completo_json"):
                    try:
                        d["payload"] = json.loads(d["payload_completo_json"])
                    except Exception:
                        d["payload"] = {}
                return d
            return None
    except Exception as e:
        print(f"[ERRO DB] Falha ao obter avaliação {avaliacao_id}: {e}")
        return None
