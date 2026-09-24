import sqlite3
import json
from datetime import datetime
from typing import Tuple, Dict, Any, List, Optional
from contextlib import contextmanager

DB_NAME = "rh diagnostico dinamico.db"

@contextmanager
def get_db_cursor(db_path: str = DB_NAME):
    """
    Context manager seguro que garante abertura, commit/rollback 
    e fechamento definitivo da conexão com suporte a multi-threading.
    """
    conn = sqlite3.connect(db_path, timeout=15.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Habilita Write-Ahead Logging para concorrência segura no Streamlit
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

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
    with get_db_cursor(db_path) as cursor:
        cursor.execute(create_table_sql)

def salvar_avaliacao(dados: Dict[str, Any], db_path: str = DB_NAME) -> Tuple[bool, str]:
    """
    Persiste uma avaliação corporativa consolidada no SQLite com transação atômica.
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
        
        nome = dados.get("nome", "").strip()
        cargo = dados.get("cargo", "").strip() or dados.get("cargo_pretendido", "").strip()
        nivel = dados.get("nivel", "").strip() or dados.get("nivel_hierarquico", "").strip()
        arquetipo = dados.get("arquetipo", "")
        
        pts_f1 = float(dados.get("pontuacao_fase1", 0.0))
        ad_f1 = float(dados.get("aderencia_fase1", 0.0))
        pts_f2 = float(dados.get("pontuacao_fase2", 0.0))
        ad_f2 = float(dados.get("aderencia_fase2", 0.0))
        
        indice_global = float(dados.get("indice_global", 0.0))
        classificacao = dados.get("classificacao", "") or dados.get("classificacao_final", "")
        sinal_vermelho = 1 if dados.get("sinal_vermelho", False) else 0
        parecer = dados.get("parecer_tecnico", "")
        
        payload_json = json.dumps(dados, ensure_ascii=False, default=str)
        
        with get_db_cursor(db_path) as cursor:
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
            
        return True, f"Avaliação de '{nome}' gravada com sucesso no banco de dados!"
            
    except Exception as e:
        return False, f"Erro ao persistir no SQLite: {str(e)}"

def listar_candidatos_salvos(db_path: str = DB_NAME) -> List[Dict[str, Any]]:
    """Retorna a lista resumida de todas as avaliações para seleção e consulta."""
    try:
        query = """
        SELECT id, data_registro, nome_candidato, cargo_pretendido, indice_global, sinal_vermelho, classificacao_final 
        FROM avaliacoes 
        ORDER BY id DESC
        """
        with get_db_cursor(db_path) as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        print(f"[ERRO DB] Falha ao listar candidatos: {e}")
        return []

def obter_avaliacao_por_id(avaliacao_id: int, db_path: str = DB_NAME) -> Optional[Dict[str, Any]]:
    """Recupera os dados completos de uma avaliação pelo ID."""
    try:
        with get_db_cursor(db_path) as cursor:
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

def obter_historico_avaliacoes(db_path: str = DB_NAME):
    """Retorna o histórico completo de avaliações em um DataFrame Pandas com suporte a esquemas legados e atuais."""
    import pandas as pd
    try:
        with get_db_cursor(db_path) as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='avaliacoes'")
            if not cursor.fetchone():
                return pd.DataFrame()
            
            cursor.execute("SELECT * FROM avaliacoes ORDER BY id DESC")
            rows = cursor.fetchall()
            if not rows:
                return pd.DataFrame()
            
            df = pd.DataFrame([dict(r) for r in rows])
            
            # Normalização de compatibilidade de nomes de colunas (legado vs atual)
            if 'vaga' not in df.columns:
                if 'cargo_pretendido' in df.columns and 'cargo' in df.columns:
                    df['vaga'] = df['cargo_pretendido'].fillna(df['cargo'])
                elif 'cargo_pretendido' in df.columns:
                    df['vaga'] = df['cargo_pretendido']
                elif 'cargo' in df.columns:
                    df['vaga'] = df['cargo']
                else:
                    df['vaga'] = 'N/A'

            if 'nome' not in df.columns and 'nome_candidato' in df.columns:
                df['nome'] = df['nome_candidato']
            elif 'nome_candidato' not in df.columns and 'nome' in df.columns:
                df['nome_candidato'] = df['nome']
                
            return df
    except Exception as e:
        print(f"[ERRO DB] Falha ao carregar histórico DataFrame: {e}")
        return pd.DataFrame()