import sqlite3
import json
from datetime import datetime
from typing import Tuple, Dict, Any, List, Optional
from contextlib import contextmanager

DB_NAME = "rh_diagnostico_dinamico.db"

@contextmanager
def get_db_cursor(db_path: str = DB_NAME):
    """
    Context manager seguro que garante abertura, commit/rollback 
    e fechamento definitivo da conexão com suporte a multi-threading.
    """
    conn = sqlite3.connect(db_path, timeout=15.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
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
    """Inicializa a tabela unificada de avaliações caso ela não exista."""
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
        payload_completo_json TEXT,
        tokens_in INTEGER DEFAULT 0,
        tokens_out INTEGER DEFAULT 0,
        custo_brl REAL DEFAULT 0.0
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
        payload_completo_json,
        tokens_in,
        tokens_out,
        custo_brl
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """
    try:
        init_db(db_path)
        data_registro = dados.get("data_registro") or datetime.now().strftime("%d / %m / %Y %H:%M")
        
        nome = str(dados.get("nome", "") or dados.get("nome_candidato", "")).strip()
        cargo = str(dados.get("cargo", "") or dados.get("cargo_pretendido", "")).strip()
        nivel = str(dados.get("nivel", "") or dados.get("nivel_hierarquico", "")).strip()
        arquetipo = str(dados.get("arquetipo", "") or dados.get("arquetipo_ativo", "")).strip()
        
        pts_f1 = float(dados.get("pontuacao_fase1", 0.0))
        ad_f1 = float(dados.get("aderencia_fase1", 0.0))
        pts_f2 = float(dados.get("pontuacao_fase2", 0.0))
        ad_f2 = float(dados.get("aderencia_fase2", 0.0))
        
        indice_global = float(dados.get("indice_global", 0.0))
        classificacao = str(dados.get("classificacao", "") or dados.get("classificacao_final", "")).strip()
        
        sinal_raw = dados.get("sinal_vermelho", False)
        sinal_vermelho = 1 if sinal_raw in [True, 1, "Sim", "sim", "1"] else 0
        
        parecer = str(dados.get("parecer_tecnico", "")).strip()
        
        payload_json = json.dumps(dados, ensure_ascii=False, default=str)
        
        tokens_in = int(dados.get("tokens_in", 0) or 0)
        tokens_out = int(dados.get("tokens_out", 0) or 0)
        custo_brl = float(dados.get("custo_brl", 0.0) or 0.0)
        
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
                payload_json,
                tokens_in,
                tokens_out,
                custo_brl
            ))
            
        return True, f"Avaliação de '{nome}' gravada com sucesso no banco de dados!"
            
    except Exception as e:
        return False, f"Erro ao persistir no SQLite: {str(e)}"

def listar_candidatos_salvos(db_path: str = DB_NAME) -> List[Dict[str, Any]]:
    """Retorna a lista resumida de todas as avaliações para seleção e consulta."""
    try:
        init_db(db_path)
        query = """
        SELECT id, data_registro, nome_candidato, cargo_pretendido, nivel_hierarquico, indice_global, sinal_vermelho, classificacao_final, payload_completo_json
        FROM avaliacoes 
        ORDER BY id DESC
        """
        with get_db_cursor(db_path) as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            resultado = []
            for r in rows:
                item = dict(r)
                if item.get("payload_completo_json"):
                    try:
                        item["payload"] = json.loads(item["payload_completo_json"])
                    except Exception:
                        item["payload"] = {}
                else:
                    item["payload"] = {}
                resultado.append(item)
            return resultado
    except Exception as e:
        print(f"[ERRO DB] Falha ao listar candidatos: {e}")
        return []

def obter_avaliacao_por_id(avaliacao_id: int, db_path: str = DB_NAME) -> Optional[Dict[str, Any]]:
    """Recupera os dados completos de uma avaliação pelo ID."""
    try:
        init_db(db_path)
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
    """Retorna o histórico completo de avaliações em um DataFrame Pandas devidamente formatado."""
    import pandas as pd
    try:
        init_db(db_path)
        with get_db_cursor(db_path) as cursor:
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

            if 'nome' not in df.columns:
                if 'nome_candidato' in df.columns:
                    df['nome'] = df['nome_candidato']
                else:
                    df['nome'] = 'N/A'

            if 'nivel' not in df.columns:
                if 'nivel_hierarquico' in df.columns:
                    df['nivel'] = df['nivel_hierarquico']
                else:
                    df['nivel'] = 'N/A'

            if 'data' not in df.columns:
                if 'data_registro' in df.columns:
                    df['data'] = df['data_registro']
                else:
                    df['data'] = ''

            if 'pontos' not in df.columns:
                if 'indice_global' in df.columns:
                    df['pontos'] = df['indice_global']
                elif 'pontuacao_fase1' in df.columns:
                    df['pontos'] = df['pontuacao_fase1']
                else:
                    df['pontos'] = 0.0

            if 'classificacao' not in df.columns:
                if 'classificacao_final' in df.columns:
                    df['classificacao'] = df['classificacao_final']
                else:
                    df['classificacao'] = ''

            if 'arquétipo' not in df.columns:
                if 'arquetipo_ativo' in df.columns:
                    df['arquétipo'] = df['arquetipo_ativo']
                elif 'arquetipo' in df.columns:
                    df['arquétipo'] = df['arquetipo']
                else:
                    df['arquétipo'] = ''
                
            return df
    except Exception as e:
        print(f"[ERRO DB] Falha ao carregar histórico DataFrame: {e}")
        return pd.DataFrame()
