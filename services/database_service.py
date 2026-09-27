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
    """Inicializa a tabela de avaliações e aplica migrações automáticas de colunas."""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS avaliacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_registro TEXT,
        nome_candidato TEXT,
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
    colunas_obrigatorias = {
        "data_registro": "TEXT",
        "nome_candidato": "TEXT",
        "cargo_pretendido": "TEXT",
        "nivel_hierarquico": "TEXT",
        "arquetipo_ativo": "TEXT",
        "pontuacao_fase1": "REAL",
        "aderencia_fase1": "REAL",
        "pontuacao_fase2": "REAL",
        "aderencia_fase2": "REAL",
        "indice_global": "REAL",
        "classificacao_final": "TEXT",
        "sinal_vermelho": "INTEGER",
        "parecer_tecnico": "TEXT",
        "payload_completo_json": "TEXT",
        "tokens_in": "INTEGER",
        "tokens_out": "INTEGER",
        "custo_brl": "REAL",
    }
    with get_db_cursor(db_path) as cursor:
        cursor.execute(create_table_sql)
        cursor.execute("PRAGMA table_info(avaliacoes);")
        existentes = {row["name"] for row in cursor.fetchall()}
        for col, tipo_def in colunas_obrigatorias.items():
            if col not in existentes:
                try:
                    cursor.execute(f"ALTER TABLE avaliacoes ADD COLUMN {col} {tipo_def};")
                except Exception as e:
                    print(f"[AVISO DB] Falha ao adicionar coluna {col}: {e}")

def salvar_avaliacao(dados: Dict[str, Any], db_path: str = DB_NAME) -> Tuple[bool, str]:
    """Persiste uma avaliação corporativa consolidada no SQLite com transação atômica."""
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
        data_registro = dados.get("data_registro") or datetime.now().strftime("%d/%m/%Y %H:%M")
        
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
            
            # Vaga / Cargo
            vaga_resolvida = pd.Series(index=df.index, dtype=object)
            for c in ["cargo_pretendido", "cargo", "vaga"]:
                if c in df.columns:
                    val = df[c].fillna("").astype(str).str.strip().replace({"": None, "None": None, "nan": None})
                    vaga_resolvida = vaga_resolvida.combine_first(val)
            df["vaga"] = vaga_resolvida.fillna("N/A").replace("", "N/A")

            # Nome
            nome_resolvido = pd.Series(index=df.index, dtype=object)
            for c in ["nome_candidato", "nome"]:
                if c in df.columns:
                    val = df[c].fillna("").astype(str).str.strip().replace({"": None, "None": None, "nan": None})
                    nome_resolvido = nome_resolvido.combine_first(val)
            df["nome"] = nome_resolvido.fillna("N/A").replace("", "N/A")

            # Nível
            nivel_resolvido = pd.Series(index=df.index, dtype=object)
            for c in ["nivel_hierarquico", "nivel"]:
                if c in df.columns:
                    val = df[c].fillna("").astype(str).str.strip().replace({"": None, "None": None, "nan": None})
                    nivel_resolvido = nivel_resolvido.combine_first(val)
            df["nivel"] = nivel_resolvido.fillna("N/A").replace("", "N/A")

            # Data
            data_resolvida = pd.Series(index=df.index, dtype=object)
            for c in ["data_registro", "data"]:
                if c in df.columns:
                    val = df[c].fillna("").astype(str).str.strip().replace({"": None, "None": None, "nan": None})
                    data_resolvida = data_resolvida.combine_first(val)
            df["data"] = data_resolvida.fillna("")

            # Pontos (prioriza coluna preenchida não nula entre pontos e métricas estruturais)
            pontos_resolvidos = pd.Series(index=df.index, dtype=float)
            for c in ["pontos", "indice_global", "pontuacao_fase1"]:
                if c in df.columns:
                    val = pd.to_numeric(df[c], errors="coerce")
                    pontos_resolvidos = pontos_resolvidos.combine_first(val)
            df["pontos"] = pontos_resolvidos.fillna(0.0)

            # Classificação
            class_resolvida = pd.Series(index=df.index, dtype=object)
            for c in ["classificacao_final", "classificacao"]:
                if c in df.columns:
                    val = df[c].fillna("").astype(str).str.strip().replace({"": None, "None": None, "nan": None})
                    class_resolvida = class_resolvida.combine_first(val)
            df["classificacao"] = class_resolvida.fillna("")

            # Arquétipo
            arq_resolvido = pd.Series(index=df.index, dtype=object)
            for c in ["arquetipo_ativo", "arquetipo", "arquétipo"]:
                if c in df.columns:
                    val = df[c].fillna("").astype(str).str.strip().replace({"": None, "None": None, "nan": None})
                    arq_resolvido = arq_resolvido.combine_first(val)
            df["arquétipo"] = arq_resolvido.fillna("")

            # Telemetria com conversão segura
            if "tokens_in" not in df.columns:
                df["tokens_in"] = 0
            else:
                df["tokens_in"] = pd.to_numeric(df["tokens_in"], errors="coerce").fillna(0).astype(int)

            if "tokens_out" not in df.columns:
                df["tokens_out"] = 0
            else:
                df["tokens_out"] = pd.to_numeric(df["tokens_out"], errors="coerce").fillna(0).astype(int)

            if "custo_brl" not in df.columns:
                df["custo_brl"] = 0.0
            else:
                df["custo_brl"] = pd.to_numeric(df["custo_brl"], errors="coerce").fillna(0.0).astype(float)
                
            return df
    except Exception as e:
        print(f"[ERRO DB] Falha ao carregar histórico DataFrame: {e}")
        return pd.DataFrame()
