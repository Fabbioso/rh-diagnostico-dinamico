from datetime import datetime
import io
import math
import random
import re
import sqlite3
import unicodedata
from fpdf import FPDF
from geopy.geocoders import Nominatim
import pandas as pd
import plotly.graph_objects as go
import pytz
import streamlit as st
import os
import importlib
import reports.gerar_pdf_fase3
from reports.gerar_pdf import gerar_pdf_profissional
from reports.gerar_pdf_fase2 import gerar_laudo_fase2_pdf
from reports.gerar_pdf_fase3 import gerar_laudo_fase3_pdf

importlib.reload(reports.gerar_pdf_fase3)
from core.constants import (
    PESO_FASE_1,
    PESO_FASE_2,
    NOTA_CRITICA_SINAL_VERMELHO,
    CASAS_CRITICAS_GOVERNANCA,
    FAIXAS_DELIBERACAO,
    COMPETENCIAS_FASE_1,
)
from services.database_service import init_db, salvar_avaliacao, listar_candidatos_salvos, obter_avaliacao_por_id
from services.ai_service import configurar_gemini, gerar_analise_fase1, gerar_deliberacao_fase3
from services.scoring_service import sortear_cartas_fase1, calcular_pontuacao_fase1, calcular_pontuacao_fase2, calcular_indice_global_integrado
# Configuração inicial da página
st.set_page_config(
    page_title="Sistema de Diagnóstico Corporativo Dinâmico - RH", layout="wide"
)
init_db()

st.markdown(
    """
    <style>
    /* =========================================================
       1. ABAS DAS FASES 1, 2 e 3 (STEP PILLS EXECUTIVOS)
       ========================================================= */
    div[data-testid="stTabs"] [role="tablist"] {
        gap: 12px !important;
        border-bottom: 2px solid #CBD5E1 !important;
        padding-bottom: 10px !important;
    }

    div[data-testid="stTabs"] [role="tab"] {
        background-color: #F1F5F9 !important;
        border: 1.8px solid #CBD5E1 !important;
        border-radius: 8px !important;
        padding: 10px 22px !important;
        min-height: 42px !important;
        margin-right: 6px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
        transition: all 0.2s ease-in-out !important;
        cursor: pointer !important;
    }

    div[data-testid="stTabs"] [role="tab"]:hover {
        background-color: #E2E8F0 !important;
        border-color: #94A3B8 !important;
        transform: translateY(-1px) !important;
    }

    div[data-testid="stTabs"] [role="tab"] * {
        color: #334155 !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        text-decoration: none !important;
    }

    div[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%) !important;
        border: 1.8px solid #1E3A8A !important;
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.3) !important;
        transform: translateY(-1px) !important;
    }

    div[data-testid="stTabs"] [role="tab"][aria-selected="true"] * {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    /* Remove compulsoriamente a barra/linha vermelha nativa */
    div[data-testid="stTabs"] [role="tablist"] > :not([role="tab"]),
    div[data-testid="stTabs"] [data-baseweb="tab-highlight"],
    div[data-testid="stTabs"] [data-baseweb="tab-border"] {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
        opacity: 0 !important;
        border: none !important;
    }

    /* =========================================================
       2. FASE 1: BOTÃO "NOVA AVALIAÇÃO" (CINZA UTILITÁRIO NEUTRO)
       ========================================================= */
    div[data-testid="stButton"] button[aria-label*="Nova Avaliação"],
    .st-key-nova_avaliacao button {
        background-color: #F8FAFC !important;
        border: 1.8px solid #94A3B8 !important;
        border-radius: 8px !important;
        min-height: 40px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
        transition: all 0.2s ease-in-out !important;
    }

    div[data-testid="stButton"] button[aria-label*="Nova Avaliação"] *,
    .st-key-nova_avaliacao button * {
        color: #334155 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }

    div[data-testid="stButton"] button[aria-label*="Nova Avaliação"]:hover,
    .st-key-nova_avaliacao button:hover {
        background-color: #E2E8F0 !important;
        border-color: #64748B !important;
        transform: translateY(-1px) !important;
    }

    /* =========================================================
       3. FASES 1, 2 E 3: DOWNLOADS EM PDF (VERDE ESMERALDA EXECUTIVO)
       ========================================================= */
    div[data-testid="stDownloadButton"] button {
        background: linear-gradient(135deg, #065F46 0%, #047857 100%) !important;
        border: 1px solid #065F46 !important;
        border-radius: 8px !important;
        min-height: 44px !important;
        box-shadow: 0 3px 8px rgba(4, 120, 87, 0.25) !important;
        transition: all 0.2s ease-in-out !important;
    }

    div[data-testid="stDownloadButton"] button * {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 14px !important;
    }

    div[data-testid="stDownloadButton"] button:hover {
        background: linear-gradient(135deg, #047857 0%, #059669 100%) !important;
        border-color: #047857 !important;
        box-shadow: 0 5px 14px rgba(4, 120, 87, 0.35) !important;
        transform: translateY(-1px) !important;
    }

    /* =========================================================
       FASE 3: PERSISTÊNCIA SQLITE (NAVY ARDÓSIA PROFUNDO #0F172A)
       ========================================================= */
    .st-key-salvar_sqlite button,
    div[data-testid="stButton"] button[aria-label*="SQLite"],
    div[data-testid="stButton"] button[aria-label*="Banco"] {
        background-color: #0F172A !important;
        border: 1.5px solid #334155 !important;
        border-radius: 8px !important;
        min-height: 44px !important;
        box-shadow: 0 3px 8px rgba(15, 23, 42, 0.35) !important;
        transition: all 0.2s ease-in-out !important;
    }

    .st-key-salvar_sqlite button *,
    div[data-testid="stButton"] button[aria-label*="SQLite"] *,
    div[data-testid="stButton"] button[aria-label*="Banco"] * {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 14px !important;
    }

    .st-key-salvar_sqlite button:hover,
    div[data-testid="stButton"] button[aria-label*="SQLite"]:hover,
    div[data-testid="stButton"] button[aria-label*="Banco"]:hover {
        background-color: #1E293B !important;
        border-color: #475569 !important;
        box-shadow: 0 5px 12px rgba(15, 23, 42, 0.45) !important;
        transform: translateY(-1px) !important;
    }

    /* =========================================================
       5. BOTÕES PRIMÁRIOS DE PROCESSAMENTO (AZUL CORPORATIVO)
       ========================================================= */
    button[data-testid="stBaseButton-primary"],
    button[kind="primary"] {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        min-height: 44px !important;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.25) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Constantes de Faturamento da API Gemini (Flash)
PRECO_ENTRADA_PER_TOKEN_USD = 0.075 / 1_000_000
PRECO_SAIDA_PER_TOKEN_USD = 0.30 / 1_000_000
TAXA_CAMBIO_USD_BRL = 5.50

# Inicialização da API Gemini
try:
    api_key_val = None
    if hasattr(st, "secrets"):
        if "GEMINI_API_KEY" in st.secrets:
            api_key_val = st.secrets["GEMINI_API_KEY"]
        elif "gemini_api_key" in st.secrets:
            api_key_val = st.secrets["gemini_api_key"]
            
    if not api_key_val and "GEMINI_API_KEY" in os.environ:
        api_key_val = os.environ["GEMINI_API_KEY"]

    GEMINI_API_DISPONIVEL = configurar_gemini(api_key_val)
except Exception as e:
    GEMINI_API_DISPONIVEL = False

try:
    from kerykeion import AstrologicalSubject
    KERYKEION_DISPONIVEL = True
    KERYKEION_ERRO = None
except Exception as e:
    KERYKEION_DISPONIVEL = False
    KERYKEION_ERRO = str(e)

TRADUCAO_SIGNOS = {
    "Ari": "Áries", "Aries": "Áries", "Tau": "Touro", "Taurus": "Touro",
    "Gem": "Gêmeos", "Gemini": "Gêmeos", "Can": "Câncer", "Cancer": "Câncer",
    "Leo": "Leão", "Vir": "Virgem", "Virgo": "Virgem", "Lib": "Libra",
    "Libra": "Libra", "Sco": "Escorpião", "Scorpio": "Escorpião",
    "Sag": "Sagitário", "Sagittarius": "Sagitário", "Cap": "Capricórnio",
    "Capricorn": "Capricórnio", "Aqu": "Aquário", "Aquarius": "Aquário",
    "Pis": "Peixes", "Pisces": "Peixes",
}

ELEMENTOS_SIGNOS = {
    "Áries": "Fogo", "Leão": "Fogo", "Sagitário": "Fogo",
    "Touro": "Terra", "Virgem": "Terra", "Capricórnio": "Terra",
    "Gêmeos": "Ar", "Libra": "Ar", "Aquário": "Ar",
    "Câncer": "Água", "Escorpião": "Água", "Peixes": "Água"
}

PREFERENCIA_ELEMENTO_CASA = {
    1: ["Fogo", "Terra"],
    2: ["Terra"],
    3: ["Ar"],
    4: ["Água"],
    5: ["Fogo"],
    6: ["Terra"],
    7: ["Ar"],
    8: ["Água", "Terra"],
    9: ["Fogo", "Ar"],
    10: ["Terra", "Fogo"],
    11: ["Ar", "Fogo"],
    12: ["Água"]
}

SYSTEM_PROMPT_RH = """
Você é um especialista em psicologia organizacional e estrategista de RH sênior. 
Sua tarefa é redigir a análise qualitativa completa para a Ficha de Avaliação de Recrutamento corporativo baseada no método de tiragem estruturada de 3 cartas por competência.

Diretrizes obrigatórias:
1. Mantenha um tom estritamente corporativo, analítico, neutro e executivo.
2. NUNCA utilize jargões místicos, esotéricos ou religiosos. Trate os símbolos como arquétipos de comportamento humano, padrões cognitivos e dinâmicas de trabalho.
3. É OBRIGATÓRIO incluir a análise detalhada de TODAS AS 8 COMPETÊNCIAS na sequência exata: 
   1. Hard Skills, 2. Soft Skills, 3. Fit Cultural, 4. Desafios, 5. Potencial Futuro, 6. Equilíbrio Emocional, 7. Saúde Psicológica e 8. Confiabilidade e Ética. Não omita nenhuma posição.
4. Para cada competência, utilize um cabeçalho claro no formato "### X. Nome da Competência" seguido explicitamente pelos seguintes campos:
   - CARTA CENTRAL: [Nome da Carta] - [Análise técnica detalhada da resposta central]
   - CARTA NEGATIVA: [Nome da Carta] - [Análise técnica detalhada de pontos de atrito/risco]
   - CARTA POSITIVA: [Nome da Carta] - [Análise técnica detalhada de alavancas/potenciais]
   - RESUMO DA LEITURA: [Resumo executivo em 1 ou 2 frases da leitura combinada das 3 cartas para esta competência]
5. Conclua com uma seção intitulada "### CONCLUSÃO" avaliando a adequação geral do perfil para a vaga.
6. Escreva de forma limpa, sem notação matemática LaTeX ($) e sem linhas de separação markdown (---).
"""

def calcular_nota_astrologica_casa(casa_num, signo_nome):
    elemento_signo = ELEMENTOS_SIGNOS.get(signo_nome, "Terra")
    prefs = PREFERENCIA_ELEMENTO_CASA.get(casa_num, ["Terra"])
    if elemento_signo in prefs:
        return 5
    return 4

def remover_acentos(texto):
    if not texto:
        return ""
    nfkd = unicodedata.normalize('NFKD', str(texto))
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower()

def sanitizar_pdf(texto):
    if not texto:
        return ""
    texto = str(texto).replace("•", "-")
    texto = texto.replace("°", chr(186)).replace("deg", chr(186))
    texto = re.sub(r'\$\(?(\d+/\d+)\)?\$', r'\1', texto)
    texto = texto.replace("**", "").replace("###", "").replace("##", "").replace("#", "").replace("*", "").replace("$", "")
    texto = texto.replace("☐", "").replace("☑", "").replace("☒", "")
    texto = re.sub(r'[^\x00-\xFF]', '', texto)
    try:
        return texto.encode('latin-1', 'replace').decode('latin-1')
    except Exception:
        return str(texto)

def quebrar_texto_em_linhas(pdf, texto, largura_max, tam_fonte=7):
    linhas = []
    pdf.set_font("helvetica", "", tam_fonte)
    for paragrafo in str(texto).split("\n"):
        palavras = paragrafo.split(" ")
        linha_atual = ""
        for p in palavras:
            if not p:
                continue
            teste = f"{linha_atual} {p}".strip() if linha_atual else p
            if pdf.get_string_width(teste) <= (largura_max - 2):
                linha_atual = teste
            else:
                if linha_atual:
                    linhas.append(linha_atual)
                linha_atual = p
        if linha_atual:
            linhas.append(linha_atual)
    return linhas if linhas else ["-"]

def extrair_secao_competencia(texto_ia, pos_num, nome_comp):
    if not texto_ia:
        return ""
    
    padroes_secao = [
        rf"(?:#{1,6}\s*)?\[?\s*CASA\s*{pos_num}\s*:[^\n]*{re.escape(nome_comp)}[^\n]*\]?",
        rf"(?:#{1,6}\s*)?(?:{pos_num}\.|\b{pos_num}\b)[^\n]*{re.escape(nome_comp)}[^\n]*",
        rf"Casa\s*{pos_num}\s*:[^\n]*{re.escape(nome_comp)}[^\n]*",
        rf"(?:#{1,6}\s*)?(?:{pos_num}\.|\b{pos_num}\b)[^\n]*(?:Desafio|Crise)[^\n]*",
        rf"(?:#{1,6}\s*)?\[?\s*CASA\s*{pos_num}\s*:[^\n]*",
        rf"(?:#{1,6}\s*)?(?:{pos_num}\.|\b{pos_num}\b)\s+[A-Za-zÀ-ÿ][^\n]*",
        rf"Casa\s*{pos_num}\s*:[^\n]*",
        rf"(?:#{1,6}\s*)?(?:{pos_num}\.|\b{pos_num}\b)\s*{re.escape(nome_comp)}",
    ]

    cabecalho_conclusao = r"^(?:\s*(?:#{1,6}|\*\*)?\s*(?:\d+\.\s*)?(?:\*\*)?\s*CONCLUS[ÃA]O\s*(?:\*\*)?\s*:?(?:\s|$))"
    proximos_marcadores = [
        r"(?:#{1,6}\s*)?\[?\s*CASA\s*\d+\s*:",
        r"(?:###?\s*)?\d+\.\s*[A-Z]",
        r"Casa\s*\d+\s*:",
        cabecalho_conclusao
    ]
    reg_proximos = "|".join(proximos_marcadores)
    
    for padrao in padroes_secao:
        match = re.search(rf"{padrao}(.*?)(?={reg_proximos}|\Z)", texto_ia, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        if match and len(match.group(1).strip()) > 15:
            trecho = match.group(1).strip()
            trecho = re.sub(r"^\s*\(Nota:\s*\d+/\d+\)\s*", "", trecho, flags=re.IGNORECASE)
            trecho = re.sub(r"\n\s*---\s*", "\n", trecho)
            return trecho
            
    return ""

def extrair_descricao_competencia(texto_ia, pos_num, nome_comp):
    resultado_vazio = {
        "central": "",
        "negativa": "",
        "positiva": "",
        "resumo": "",
    }

    if not texto_ia:
        return resultado_vazio

    trecho_comp = extrair_secao_competencia(texto_ia, pos_num, nome_comp)
    if not trecho_comp:
        return resultado_vazio

    def escapar_rotulo(rotulo):
        return re.escape(rotulo).replace(r"\ ", r"\s*")

    prefixo = r"(?:^|\n)\s*(?:[-*•]\s*|\*\*\s*)?(?:\d+\.\s*)?(?:\*\*)?\s*"
    rotulos = {
        "central": escapar_rotulo("CARTA CENTRAL"),
        "negativa": escapar_rotulo("CARTA NEGATIVA"),
        "positiva": escapar_rotulo("CARTA POSITIVA"),
        "resumo": r"(?:RESUMO\s*DA\s*LEITURA|S[ií]ntese\s*T[ée]cnica)",
    }
    proximos_campos = "|".join(rotulos.values())
    limite_cabecalho = (
        rf"(?:#{{1,6}}\s*|\d+\.\s+[^\n]+|[-*•]\s*(?:{proximos_campos}))"
    )
    padroes = []
    for nome_chave, rotulo in rotulos.items():
        if nome_chave == "resumo":
            limite = rf"(?=\n\s*{limite_cabecalho}|\n\s*\n|$)"
        else:
            limite = (
                rf"(?=\n\s*(?:[-*•]\s*|\*\*\s*)?(?:\d+\.\s*)?"
                rf"(?:\*\*)?\s*(?:{proximos_campos})\s*(?:\*\*)?\s*:|$)"
            )
        regex_padrao = (
            rf"(?is){prefixo}{rotulo}\s*(?:\*\*)?\s*:\s*(.*?)"
            rf"{limite}"
        )
        padroes.append((nome_chave, regex_padrao))

    resultado = resultado_vazio.copy()
    for nome_chave, regex_padrao in padroes:
        try:
            match = re.search(regex_padrao, trecho_comp)
        except re.error:
            return resultado_vazio
        valor = match.group(1).strip().replace("\n", " ") if match else ""
        valor = re.sub(r"^\s*[:\-–—]+\s*", "", valor).strip()
        if valor:
            resultado[nome_chave] = valor

    return resultado


def remover_nome_carta_descricao(descricao, nome_carta):
    descricao = str(descricao or "").strip()
    nome_carta = str(nome_carta or "").strip()
    if not descricao or not nome_carta:
        return descricao
    return re.sub(
        rf"^{re.escape(nome_carta)}(?:(?:\s*[:\-–—]\s*)|\s+)",
        "",
        descricao,
        count=1,
        flags=re.IGNORECASE,
    ).strip()


def extrair_sintese_competencia(texto_ia, pos_num, nome_comp):
    dados = extrair_descricao_competencia(texto_ia, pos_num, nome_comp)
    sintese = dados.get("resumo", "").strip()
    if len(sintese) > 5:
        return sintese
    return "Avaliação metodológica integrada dos arcanos alinhada à competência."

def armazenar_analise_fase1(texto_ia, competencias_nomes):
    """Persiste os campos parseados da análise para uso pelos relatórios."""
    for pos_num, nome_comp in enumerate(competencias_nomes, start=1):
        dados = extrair_descricao_competencia(texto_ia, pos_num, nome_comp)
        carta_central = st.session_state.get(f"t_central_{pos_num}", "-")
        carta_negativa = st.session_state.get(f"t_negativa_{pos_num}", "-")
        carta_positiva = st.session_state.get(f"t_positiva_{pos_num}", "-")
        st.session_state[f"analise_fase1_casa_{pos_num}"] = {
            "resumo": dados.get("resumo", ""),
            "central_desc": remover_nome_carta_descricao(dados.get("central", ""), carta_central),
            "negativa_desc": remover_nome_carta_descricao(dados.get("negativa", ""), carta_negativa),
            "positiva_desc": remover_nome_carta_descricao(dados.get("positiva", ""), carta_positiva),
        }

def chave_analise_ia(c_nome, c_vaga):
    return f"ai_analise_v3_{c_nome}_{c_vaga}"


def obter_ou_gerar_analise_ia(c_nome, c_vaga, arq_ativo, sinal_vermelho=None):
    # Incremento de versão no cache para descartar pareceres antigos gravados em sessão
    cache_key = chave_analise_ia(c_nome, c_vaga)
    competencias_nomes = [
        "Hard Skills", "Soft Skills", "Fit Cultural",
        "Desafios", "Potencial Futuro", "Equilíbrio Emocional",
        "Saúde Psicológica", "Confiabilidade e Ética"
    ]
    if cache_key in st.session_state:
        armazenar_analise_fase1(st.session_state[cache_key], competencias_nomes)
        return st.session_state[cache_key]

    dados_casas = {}
    for i in range(1, 9):
        dados_casas[i] = {
            "nome": competencias_nomes[i-1],
            "central": st.session_state.get(f"t_central_{i}", "Não informada"),
            "negativa": st.session_state.get(f"t_negativa_{i}", "Não informada"),
            "positiva": st.session_state.get(f"t_positiva_{i}", "Não informada"),
            "nota": st.session_state.get(f"t_pontos_{i}", 3)
        }

    # Validação mandatória de veto corporativo (Sinal Vermelho)
    is_sinal_v = (sinal_vermelho in ["Sim", True]) or any(
        dados_casas[i]["nota"] <= 2 for i in [6, 7, 8]
    )

    if GEMINI_API_DISPONIVEL:
        try:
            sucesso, texto_gerado, telemetria = gerar_analise_fase1(
                c_nome or "Candidato",
                c_vaga or "Geral",
                st.session_state.get("candidato_nivel", "Nível"),
                arq_ativo,
                dados_casas,
            )
            if not sucesso:
                st.error(texto_gerado)
                return texto_gerado

            st.session_state[f"cost_{cache_key}"] = {
                "tokens_in": telemetria.get("input_tokens", 0),
                "tokens_out": telemetria.get("output_tokens", 0),
                "tokens_total": telemetria.get("total_tokens", 0),
                "custo_usd": telemetria.get("custo_usd", 0),
                "custo_brl": telemetria.get("custo_usd", 0) * TAXA_CAMBIO_USD_BRL
            }

            st.session_state[cache_key] = texto_gerado
            armazenar_analise_fase1(texto_gerado, competencias_nomes)
            st.session_state["ultima_analise_fase1_fallback"] = not sucesso
            return texto_gerado
        except Exception as e:
            msg_erro = f"Erro na execução da API do Gemini: {e}"
            st.error(msg_erro)
            st.session_state["ultima_analise_fase1_fallback"] = True
            return msg_erro
    else:
        st.session_state["ultima_analise_fase1_fallback"] = True
        texto_padrao = "Análise qualitativa padrão (Configure a GEMINI_API_KEY em st.secrets para habilitar a geração avançada por IA)."
        armazenar_analise_fase1(texto_padrao, competencias_nomes)
        return texto_padrao

def classificar_arquétipo_manual(vaga_texto, selecao_manual="Automático (Detectado por IA)"):
    if selecao_manual != "Automático (Detectado por IA)":
        pesos_map = {
            "Inovação, Estratégia e Expansão": {1: 1.2, 2: 0.9, 3: 1.0, 4: 0.9, 5: 1.5, 6: 0.8, 7: 1.0, 8: 0.8, 9: 1.5, 10: 1.3, 11: 1.3, 12: 1.0},
            "Governança, Compliance e Riscos": {1: 0.9, 2: 1.4, 3: 1.0, 4: 1.2, 5: 0.8, 6: 1.4, 7: 1.3, 8: 1.5, 9: 0.9, 10: 1.1, 11: 1.0, 12: 1.4},
            "Operações, Processos e Manutenção": {1: 1.0, 2: 1.3, 3: 0.9, 4: 1.1, 5: 0.8, 6: 1.5, 7: 1.0, 8: 1.2, 9: 0.8, 10: 1.4, 11: 0.9, 12: 1.0},
            "Comercial, Negócios e Relacionamento": {1: 1.1, 2: 1.0, 3: 1.5, 4: 0.8, 5: 1.2, 6: 0.9, 7: 1.5, 8: 1.0, 9: 1.1, 10: 1.0, 11: 1.4, 12: 0.9},
            "Padrão / Geral": {i: 1.0 for i in range(1, 13)}
        }
        return selecao_manual, pesos_map.get(selecao_manual, {i: 1.0 for i in range(1, 13)})

    if not vaga_texto or not vaga_texto.strip():
        return "Padrão / Geral", {i: 1.0 for i in range(1, 13)}
    
    txt = remover_acentos(vaga_texto)
    palavras_isoladas = set(re.findall(r'\b\w+\b', txt))
    
    termos_inovacao = ["inovacao", "estrategia", "expansao", "planejamento", "transformacao", "digital", "negocios", "head", "diretor", "produtos", "futuro", "marketing", "tecnologia", "ti", "software", "produto", "pesquisa"]
    termos_governanca = ["compliance", "auditoria", "juridico", "risco", "riscos", "controladoria", "governanca", "financeiro", "regulatorio", "processos", "contabil", "qualidade", "seguranca", "adm", "administrativo", "rh", "pessoal", "financas", "tesouraria"]
    termos_operacoes = ["operacao", "operacoes", "producao", "manutencao", "logistica", "planta", "fabrica", "engenharia", "industrial", "supply", "cadeia", "campo", "execucao", "facilities", "almoxarifado", "estoque", "expedicao", "operacional"]
    termos_comercial = ["comercial", "vendas", "account", "cliente", "mercado", "relacionamento", "parcerias", "key account", "business development", "sucesso do cliente", "cs", "atendimento", "varejo", "contas", "kam"]
    
    def pontuar_categoria(lista_termos):
        pontos = 0
        for termo in lista_termos:
            termo_limpo = remover_acentos(termo)
            if " " in termo_limpo:
                if termo_limpo in txt: pontos += 1
            else:
                if termo_limpo in palavras_isoladas: pontos += 1
        return pontos

    scores = {
        "Operações, Processos e Manutenção": pontuar_categoria(termos_operacoes),
        "Comercial, Negócios e Relacionamento": pontuar_categoria(termos_comercial),
        "Governança, Compliance e Riscos": pontuar_categoria(termos_governanca),
        "Inovação, Estratégia e Expansão": pontuar_categoria(termos_inovacao),
    }
    
    maior_score = max(scores.values())
    if maior_score == 0:
        return "Padrão / Geral", {i: 1.0 for i in range(1, 13)}
        
    arq_vitorioso = max(scores, key=scores.get)
    pesos_finais = {
        "Inovação, Estratégia e Expansão": {1: 1.2, 2: 0.9, 3: 1.0, 4: 0.9, 5: 1.5, 6: 0.8, 7: 1.0, 8: 0.8, 9: 1.5, 10: 1.3, 11: 1.3, 12: 1.0},
        "Governança, Compliance e Riscos": {1: 0.9, 2: 1.4, 3: 1.0, 4: 1.2, 5: 0.8, 6: 1.4, 7: 1.3, 8: 1.5, 9: 0.9, 10: 1.1, 11: 1.0, 12: 1.4},
        "Operações, Processos e Manutenção": {1: 1.0, 2: 1.3, 3: 0.9, 4: 1.1, 5: 0.8, 6: 1.5, 7: 1.0, 8: 1.2, 9: 0.8, 10: 1.4, 11: 0.9, 12: 1.0},
        "Comercial, Negócios e Relacionamento": {1: 1.1, 2: 1.0, 3: 1.5, 4: 0.8, 5: 1.2, 6: 0.9, 7: 1.5, 8: 1.0, 9: 1.1, 10: 1.0, 11: 1.4, 12: 0.9}
    }
    return arq_vitorioso, pesos_finais.get(arq_vitorioso, {i: 1.0 for i in range(1, 13)})

def obter_nota_por_carta(nome_carta):
    nome = remover_acentos(nome_carta)
    if not nome: return 3
    if any(m in nome for m in ["o mago", "a imperatriz", "o hierofante", "o imperador", "a forca", "a estrela", "a justica", "o mundo", "rei de", "rainha de"]): return 5
    if any(m in nome for m in ["o pendurado", "o eremita", "o louco", "o sol", "a sacerdoti", "a papisa", "os enamorados", "os amantes", "a temperanca", "o carro"]): return 2
    if any(c in nome for c in ["pajem de", "cavaleiro de"]): return 1
    if "o julgamento" in nome: return 4
    if any(m in nome for m in ["a morte", "a lua"]): return 2
    if "a roda da fortuna" in nome: return 3
    if "as de" in nome: return 5
    if any(n in nome for n in ["10 de paus", "10 de espadas", "5 de ouros"]): return 1
    if any(n in nome for n in ["8 de", "9 de", "10 de"]): return 4
    if any(n in nome for n in ["5 de", "7 de"]): return 2
    if any(n in nome for n in ["2 de", "3 de", "4 de", "6 de"]): return 3
    return 3

def calcular_nota_metodologica(casa_num, c_cent, c_neg, c_pos):
    nota_base = obter_nota_por_carta(c_cent)
    neg_limpo = remover_acentos(c_neg)
    pos_limpo = remover_acentos(c_pos)
    if casa_num == 1 and any(k in pos_limpo for k in ["ouros", "espadas", "mago", "as de"]):
        if nota_base < 5: nota_base += 1
    if any(k in neg_limpo for k in ["torre", "diabo", "cinco de ouros", "oito de espadas", "nove de espadas", "dez de espadas", "dez de paus"]):
        if nota_base > 1: nota_base -= 1
    return max(1, min(5, nota_base))

init_db()

if "astro_data_raw" not in st.session_state: st.session_state["astro_data_raw"] = "01/01/1999"
if "astro_local" not in st.session_state: st.session_state["astro_local"] = "São Paulo, SP"
if "astro_hora" not in st.session_state: st.session_state["astro_hora"] = datetime.strptime("12:00", "%H:%M").time()
if "candidato_nome" not in st.session_state: st.session_state["candidato_nome"] = ""
if "candidato_cargo" not in st.session_state: st.session_state["candidato_cargo"] = ""
if "candidato_nivel" not in st.session_state: st.session_state["candidato_nivel"] = ""
if "sorteio_realizado" not in st.session_state: st.session_state["sorteio_realizado"] = False
if "manual_validado" not in st.session_state: st.session_state["manual_validado"] = False

NIVEIS_CARGO = ["", "Diretor", "Gerente", "Coordenador", "Supervisor", "Especialista", "Analista", "Assistente"]


def inferir_nivel(cargo_texto: str) -> str:
    if not cargo_texto or not cargo_texto.strip():
        return ""
    c = cargo_texto.lower().strip()

    if re.search(r'\b(diretor|diretora|diretoria|cfo|ceo|cto|coo|c-level|vp|vice-presidente)\b', c):
        return "Diretor"
    if re.search(r'\b(gerente|gerência|gerencia|head)\b', c):
        return "Gerente"
    if re.search(r'\b(coordenador|coordenadora|coordenação|coordenacao)\b', c):
        return "Coordenador"
    if re.search(r'\b(supervisor|supervisora|supervisão|supervisao|líder|lider)\b', c):
        return "Supervisor"
    if re.search(r'\b(especialista|consultor|consultora)\b', c):
        return "Especialista"
    if re.search(r'\b(assistente|auxiliar|estagiário|estagiaria|estagiária|estagiario)\b', c):
        return "Assistente"
    return "Analista"


def deduzir_nivel_por_cargo(cargo: str, niveis_disponiveis: list) -> str:
    """Infere o nível hierárquico com base em palavras-chave no cargo pretendido."""
    if not cargo:
        return niveis_disponiveis[0] if niveis_disponiveis else ""
    return inferir_nivel(cargo)


def inferir_nivel_hierarquico(cargo: str) -> str:
    cargo_normalizado = remover_acentos(cargo)
    niveis_por_padrao = [
        (r"\b(ceo|cfo|coo|cto|cmo|cio|vp|vice presidente|presidente|c level|c-level|chief)\b", "C-Level / Executivo"),
        (r"\b(diretor|diretora|director|director[a]?)\b", "Diretor"),
        (r"\b(gerente|gerencia|head|manager)\b", "Gerente"),
        (r"\b(coordenador|coordenadora|coordenacao)\b", "Coordenador"),
        (r"\b(supervisor|supervisora|supervisao)\b", "Supervisor"),
        (r"\b(especialista|analista)\b", "Especialista / Analista"),
        (r"\b(tecnico|tecnica)\b", "Técnico"),
        (r"\b(operacional|operador|operadora)\b", "Operacional"),
    ]
    for padrao, nivel in niveis_por_padrao:
        if re.search(padrao, cargo_normalizado):
            return nivel
    return "Especialista / Analista"

def auto_detectar_nivel_hierarquico():
    cargo = st.session_state.get("candidato_cargo", "")
    nivel_inferido = inferir_nivel(cargo)
    if cargo.strip():
        st.session_state["candidato_nivel"] = nivel_inferido


def atualizar_nivel_automatico():
    cargo = st.session_state.get("candidato_cargo", "")
    st.session_state["candidato_nivel"] = inferir_nivel(cargo)


# reset completo será executado diretamente no botão da Fase 1

st.title("Sistema de Diagnóstico Corporativo Dinâmico: Tarot & Astrologia Ponderada com Trânsitos")
st.markdown("Plataforma avançada com classificação semântica inteligente, 4 pilares de arquétipos corporativos, override manual, trânsitos atuais e IA.")

tab1, tab2, tab3 = st.tabs([
    "1. Cadastro e Avaliação (Tarot 8 Casas)",
    "2. Mapeamento Astrológico & Trânsitos Atuais",
    "3. Ficha de Avaliação e Cruzamento Analítico",
])

DECK_TAROT = [
    "O Mago", "A Sacerdotisa", "A Imperatriz", "O Imperador", "O Hierofante",
    "Os Enamorados", "O Carro", "A Justiça", "O Eremita", "A Roda da Fortuna",
    "A Força", "O Pendurado", "A Morte", "A Temperança", "O Diabo", "A Torre",
    "A Estrela", "A Lua", "O Sol", "O Julgamento", "O Mundo", "O Louco",
    "Ás de Ouros", "Dois de Ouros", "Três de Ouros", "Quatro de Ouros",
    "Cinco de Ouros", "Seis de Ouros", "Sete de Ouros", "Oito de Ouros",
    "Nove de Ouros", "Dez de Ouros", "Ás de Copas", "Dois de Copas",
    "Três de Copas", "Quatro de Copas", "Cinco de Copas", "Seis de Copas",
    "Sete de Copas", "Oito de Copas", "Nove de Copas", "Dez de Copas",
    "Ás de Espadas", "Dois de Espadas", "Três de Espadas", "Quatro de Espadas",
    "Cinco de Espadas", "Seis de Espadas", "Sete de Espadas", "Oito de Espadas",
    "Nove de Espadas", "Dez de Espadas", "Ás de Paus", "Dois de Paus",
    "Três de Paus", "Quatro de Paus", "Cinco de Paus", "Seis de Paus",
    "Sete de Paus", "Oito de Paus", "Nove de Paus", "Dez de Paus",
]

with tab1:
    col_topo_t1, col_topo_t2 = st.columns([4, 1])
    with col_topo_t1:
        st.header("Fase 1: Parâmetros do Candidato e Detecção de Arquétipo")
    with col_topo_t2:
        if st.button("🔄 Nova Avaliação", key="btn_nova_avaliacao"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    candidatos_existentes = listar_candidatos_salvos()
    opcoes_candidatos = []
    for candidato in candidatos_existentes:
        nome = candidato.get("nome_candidato", "")
        cargo = candidato.get("cargo_pretendido", "")
        indice = candidato.get("indice_global", 0.0)
        if nome:
            opcoes_candidatos.append({
                "id": candidato.get("id"),
                "label": f"{candidato.get('id')} - {nome} | {cargo} (Índice: {indice:.1f}%)",
                "nome": nome,
                "cargo": cargo,
                "nivel": candidato.get("nivel_hierarquico", ""),
                "payload": candidato.get("payload", {})
            })

    tipo_cad = st.radio("Modo de Candidato", ["Selecionar Existente", "Cadastrar Novo"], index=1, horizontal=True, key="tipo_cad_modo")

    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        if tipo_cad == "Selecionar Existente":
            if opcoes_candidatos:
                opcoes_select = [
                    {"id": None, "label": "Selecionar Candidato Cadastrado...", "nome": "", "cargo": "", "nivel": "", "payload": {}}
                ] + opcoes_candidatos
                escolha_cand = st.selectbox(
                    "Candidato(a) Registrado",
                    options=opcoes_select,
                    format_func=lambda item: item["label"] if item else "Selecionar Candidato Cadastrado...",
                    key="select_cand_existente_ativo",
                )
                if escolha_cand and escolha_cand.get("id") is not None:
                    dados_candidato = obter_avaliacao_por_id(escolha_cand["id"])
                    if dados_candidato:
                        st.session_state["candidato_nome"] = dados_candidato.get("nome_candidato", "")
                        st.session_state["candidato_cargo"] = dados_candidato.get("cargo_pretendido", "")
                        st.session_state["candidato_nivel"] = dados_candidato.get("nivel_hierarquico", "Analista")
                        nome_candidato = dados_candidato.get("nome_candidato", "")
                    else:
                        nome_candidato = escolha_cand.get("nome", "")
                else:
                    nome_candidato = ""
            else:
                st.info("Nenhum candidato registrado.")
                nome_candidato = ""
        else:
            nome_candidato = st.text_input("Nome Completo do Novo Candidato(a)", key="candidato_nome")

    with col_c2:
        def on_cargo_change():
            cargo = st.session_state.get("candidato_cargo", "")
            if cargo and cargo.strip():
                st.session_state["candidato_nivel"] = inferir_nivel(cargo)
            else:
                st.session_state["candidato_nivel"] = ""

        vaga_cargo = st.text_input(
            "Vaga / Cargo Pretendido",
            key="candidato_cargo",
            on_change=on_cargo_change,
        )
    with col_c3:
        if tipo_cad == "Selecionar Existente":
            if opcoes_candidatos:
                candidato_selecionado = st.session_state.get("select_cand_existente_ativo")
                if isinstance(candidato_selecionado, dict) and candidato_selecionado.get("id") is not None:
                    dados_completos = obter_avaliacao_por_id(candidato_selecionado["id"])
                    if dados_completos:
                        st.session_state["candidato_nivel"] = dados_completos.get("nivel_hierarquico", "")
        if "candidato_nivel" not in st.session_state or st.session_state["candidato_nivel"] not in NIVEIS_CARGO:
            st.session_state["candidato_nivel"] = ""

        nivel_atual = st.session_state.get("candidato_nivel", "")
        idx_nivel = NIVEIS_CARGO.index(nivel_atual) if nivel_atual in NIVEIS_CARGO else 0
        nivel_hierarquico = st.selectbox(
            "Nível Hierárquico",
            options=NIVEIS_CARGO,
            index=idx_nivel,
            format_func=lambda x: "Selecione o nível..." if x == "" else x,
            key="candidato_nivel"
        )

    modo_arq_input = st.selectbox(
        "Ajuste de Arquétipo (Automático ou Forçado)",
        [
            "Automático (Detectado por IA)",
            "Inovação, Estratégia e Expansão",
            "Governança, Compliance e Riscos",
            "Operações, Processos e Manutenção",
            "Comercial, Negócios e Relacionamento",
            "Padrão / Geral"
        ],
        key="select_override_arq"
    )

    arq_nome, arq_pesos = classificar_arquétipo_manual(vaga_cargo, modo_arq_input)
    st.info(f"🎯 **Arquétipo Corporativo Ativo:** `{arq_nome}` (Aplicando pesos customizados na Fase 2)")

    st.markdown("---")
    st.subheader("Modo de Geração da Leitura das Cartas")
    def on_modo_geracao_change():
        modo_atual = st.session_state.get("modo_geracao_cartas")
        st.session_state["sorteio_realizado"] = False
        st.session_state["manual_validado"] = False

    modo_geracao = st.radio(
        "Selecione como deseja preencher as cartas nas 8 casas:",
        ["Manual (Preenchimento Direto)", "Automático (Assistente Especialista com Regras Metodológicas)"],
        index=1,
        key="modo_geracao_cartas",
        on_change=on_modo_geracao_change,
    )

    if modo_geracao == "Automático (Assistente Especialista com Regras Metodológicas)":
        if st.button("🎲 Executar Sorteio e Cálculo Inteligente via Regras", key="btn_sortear_fase1", type="primary"):
            definicoes_casas = {
                i: {"nome": nome}
                for i, nome in enumerate(COMPETENCIAS_FASE_1, start=1)
            }
            resultado_sorteio = sortear_cartas_fase1(DECK_TAROT, definicoes_casas)
            for i, dados_casa in resultado_sorteio.items():
                st.session_state[f"t_central_{i}"] = dados_casa["central"]
                st.session_state[f"t_negativa_{i}"] = dados_casa["negativa"]
                st.session_state[f"t_positiva_{i}"] = dados_casa["positiva"]
                st.session_state[f"t_pontos_{i}"] = dados_casa["nota"]
            st.session_state["sorteio_realizado"] = True
            st.success("Sorteio e atribuição de notas concluídos com sucesso!")
            st.rerun()

    deve_exibir_matriz = (
        modo_geracao == "Manual (Preenchimento Direto)"
        or st.session_state.get("sorteio_realizado", False)
    )
    casas_preenchidas = False
    resultado_calculado = (
        st.session_state.get("sorteio_realizado", False)
        if modo_geracao == "Automático (Assistente Especialista com Regras Metodológicas)"
        else st.session_state.get("manual_validado", False)
    )

    if deve_exibir_matriz:
        st.markdown("---")
        st.subheader("Matriz de Avaliação por Casas (Notas de 1 a 5)")
        casas_config = [
            (1, "Hard Skills (Competência Técnica e Rotina)", "Casa 6 Astrológica"),
            (2, "Soft Skills (Inteligência Social e Comunicação)", "Casa 3 Astrológica"),
            (3, "Fit Cultural (Alinhamento de Valores e Coletivo)", "Casa 11 Astrológica"),
            (4, "Desafios (Pontos Cegos e Autossabotagem)", "Casa 12 Astrológica"),
            (5, "Potencial Futuro (Projeção e Liderança de Longo Prazo)", "Casa 10 Astrológica"),
            (6, "Equilíbrio Emocional (Resiliência sob Pressão)", "Casa 4 Astrológica"),
            (7, "Saúde Psicológica (Foco Cognitivo e Burnout)", "Casa 1 Astrológica"),
            (8, "Confiabilidade e Ética (Compliance e Acordos)", "Casa 8 Astrológica"),
        ]

        col_esq, col_dir = st.columns(2)
        for num, titulo, base_astro in casas_config:
            col_alvo = col_esq if num <= 4 else col_dir
            with col_alvo:
                with st.expander(f"Casa {num}: {titulo} — [{base_astro}]"):
                    st.text_input("Carta Central (Resposta)", key=f"t_central_{num}", placeholder="Ex: O Mago")
                    st.text_input("Carta Negativa (Dificuldades)", key=f"t_negativa_{num}", placeholder="Ex: Ás de Ouros")
                    st.text_input("Carta Positiva (Pontos Fortes)", key=f"t_positiva_{num}", placeholder="Ex: 4 de Copas")
                    st.number_input("Nota (1-5)", min_value=1, max_value=5, value=3, key=f"t_pontos_{num}")

        casas_preenchidas = all(
            str(st.session_state.get(f"t_{campo}_{numero}", "")).strip()
            for numero in range(1, 9)
            for campo in ("central", "negativa", "positiva")
        )

        if modo_geracao == "Manual (Preenchimento Direto)":
            if st.button("📊 Confirmar e Calcular Leitura Manual", key="btn_confirmar_manual"):
                if not casas_preenchidas:
                    st.error("Preencha as cartas Central, Negativa e Positiva das 8 casas antes de confirmar.")
                else:
                    st.session_state["sorteio_realizado"] = True
                    st.session_state["manual_validado"] = True
                    st.rerun()

        if resultado_calculado and (modo_geracao == "Automático (Assistente Especialista com Regras Metodológicas)" or st.session_state.get("manual_validado", False)):
            dados_casas_f1 = {
                i: {"nota": st.session_state.get(f"t_pontos_{i}", 3)}
                for i in range(1, 9)
            }
            total_t1, perc_t1, classificacao_f1 = calcular_pontuacao_fase1(dados_casas_f1)
            pontuacoes_t1 = [dados_casas_f1[i]["nota"] for i in range(1, 9)]

            p6, p7, p8 = st.session_state.get("t_pontos_6", 3), st.session_state.get("t_pontos_7", 3), st.session_state.get("t_pontos_8", 3)
            sinal_vermelho_f1 = "Sim" if (p6 <= 2 or p7 <= 2 or p8 <= 2) else "Não"

            if sinal_vermelho_f1 in ["Sim", True]:
                classificacao_f1 = "Não Recomendado (Veto de Governança)"

            st.markdown("---")
            st.info(f"📊 **Resultado Individual da Fase 1 (Tarot):** {total_t1} / 40 pontos ({perc_t1:.1f}% de aderência comportamental)")
        elif modo_geracao == "Manual (Preenchimento Direto)":
            st.info("💡 Preencha as cartas e notas das 8 casas e clique em 'Confirmar e Calcular Leitura Manual' para apurar o resultado.")
    else:
        st.info("💡 Preencha os dados do candidato e clique em **'Executar Sorteio e Cálculo Inteligente via Regras'** para gerar a leitura das 8 casas.")

    c_nome_val = st.session_state.get("candidato_nome") or st.session_state.get("candidato_nome", "") or (nome_candidato if 'nome_candidato' in locals() else "")
    cache_key_check = f"ai_analise_v3_{c_nome_val}_{st.session_state.get('candidato_cargo', vaga_cargo)}"

    if resultado_calculado and casas_preenchidas:
        if st.button("🤖 Gerar Análise Qualitativa por IA (Fase 1)", type="primary"):
            with st.spinner("Consultando o Gemini 3.8 Flash para gerar o parecer completo das 8 casas..."):
                obter_ou_gerar_analise_ia(c_nome_val, vaga_cargo, arq_nome)
            if st.session_state.get("ultima_analise_fase1_fallback", False):
                st.warning("A síntese de contingência foi aplicada devido à indisponibilidade da geração por IA.")
            else:
                st.success("Análise gerada e pronta para exportação!")
    elif deve_exibir_matriz:
        st.info("💡 Preencha as cartas Central, Negativa e Positiva das 8 casas e confirme o cálculo para liberar a análise qualitativa e o PDF.")

    cost_info_key = f"cost_{cache_key_check}"
    if cost_info_key in st.session_state:
        c_meta = st.session_state[cost_info_key]
        st.caption(
            f"💰 **Consumo da API:** {c_meta['tokens_in']} tokens in | {c_meta['tokens_out']} tokens out "
            f"({c_meta['tokens_total']} total) — **Custo Estimado:** US$ {c_meta['custo_usd']:.5f} (R$ {c_meta['custo_brl']:.4f})"
        )

    def gerar_ficha_pdf_fase1(c_nome, c_vaga, total_pts, classif, sinal_vermelho_val):
        cache_key_pdf = chave_analise_ia(c_nome, c_vaga)
        texto_ia_doc = st.session_state.get(cache_key_pdf)
        if not texto_ia_doc:
            texto_ia_doc = obter_ou_gerar_analise_ia(c_nome, c_vaga, arq_nome)

        veto_governanca = sinal_vermelho_val in ["Sim", True]
        classif = "Não Recomendado (Veto de Governança)" if veto_governanca else classif

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=False)

        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 6, sanitizar_pdf("FICHA DE AVALIAÇÃO PARA RECRUTAMENTO"), 0, 1, "C")
        pdf.set_font("helvetica", "I", 8)
        pdf.cell(0, 5, sanitizar_pdf("RELATÓRIO DE AVALIAÇÃO PSICOMÉTRICA E COMPORTAMENTAL (MÉTODO 8 CASAS)"), 0, 1, "C")
        pdf.ln(3)

        pdf.set_font("helvetica", "B", 8)
        pdf.set_fill_color(245, 247, 250)
        pdf.cell(0, 5.5, sanitizar_pdf(f"   CANDIDATO(A): {c_nome.upper() if c_nome else 'NÃO INFORMADO'}"), 1, 1, "L", True)
        pdf.cell(0, 5.5, sanitizar_pdf(f"   VAGA / CARGO: {c_vaga.upper() if c_vaga else 'NÃO INFORMADA'} ({nivel_hierarquico.upper()})         DATA: {datetime.now().strftime('%d/%m/%Y')}"), 1, 1, "L", True)
        pdf.ln(3)

        w_pos = 8
        w_comp = 28
        w_cart = 62
        w_nota = 10
        w_sint = 82

        pdf.set_font("helvetica", "B", 7.5)
        pdf.set_fill_color(230, 235, 240)
        pdf.cell(w_pos, 6, "POS", 1, 0, "C", True)
        pdf.cell(w_comp, 6, "COMPETÊNCIA", 1, 0, "L", True)
        pdf.cell(w_cart, 6, "CARTAS (CENTRAL / NEGATIVA / POSITIVA)", 1, 0, "L", True)
        pdf.cell(w_nota, 6, "NOTA", 1, 0, "C", True)
        pdf.cell(w_sint, 6, "RESUMO DA LEITURA", 1, 1, "L", True)

        competencias_nomes = [
            "Hard Skills", "Soft Skills", "Fit Cultural",
            "Desafios", "Potencial Futuro", "Equilíbrio Emocional",
            "Saúde Psicológica", "Confiabilidade e Ética"
        ]

        cursor_y = pdf.get_y()

        for i in range(1, 9):
            c_cent = st.session_state.get(f"t_central_{i}", "-")
            c_neg = st.session_state.get(f"t_negativa_{i}", "-")
            c_pos = st.session_state.get(f"t_positiva_{i}", "-")
            nota = st.session_state.get(f"t_pontos_{i}", 3)

            cartas_txt = f"Carta Central: {c_cent}\nCarta Negativa: {c_neg}\nCarta Positiva: {c_pos}"
            obs_txt = extrair_sintese_competencia(texto_ia_doc, i, competencias_nomes[i-1])

            linhas_comp = quebrar_texto_em_linhas(pdf, competencias_nomes[i-1], w_comp, tam_fonte=7)
            linhas_cart = quebrar_texto_em_linhas(pdf, cartas_txt, w_cart, tam_fonte=6.8)
            linhas_sint = quebrar_texto_em_linhas(pdf, obs_txt, w_sint, tam_fonte=6.8)

            max_linhas = max(len(linhas_comp), len(linhas_cart), len(linhas_sint), 3)
            h_linha = max(14.0, float(max_linhas * 3.4) + 2.8)

            pdf.rect(10, cursor_y, w_pos, h_linha)
            pdf.rect(10 + w_pos, cursor_y, w_comp, h_linha)
            pdf.rect(10 + w_pos + w_comp, cursor_y, w_cart, h_linha)
            pdf.rect(10 + w_pos + w_comp + w_cart, cursor_y, w_nota, h_linha)
            pdf.rect(10 + w_pos + w_comp + w_cart + w_nota, cursor_y, w_sint, h_linha)

            pdf.set_font("helvetica", "", 7)
            pdf.text(10 + (w_pos / 2) - 1.2, cursor_y + (h_linha / 2) + 1.2, str(i))

            for idx_c, l_txt in enumerate(linhas_comp):
                pdf.text(10 + w_pos + 1.2, cursor_y + 3.8 + (idx_c * 3.2), sanitizar_pdf(l_txt))

            pdf.set_font("helvetica", "", 6.8)
            for idx_cr, l_txt in enumerate(linhas_cart):
                pdf.text(10 + w_pos + w_comp + 1.2, cursor_y + 3.8 + (idx_cr * 3.0), sanitizar_pdf(l_txt))

            pdf.set_font("helvetica", "", 7)
            pdf.text(10 + w_pos + w_comp + w_cart + (w_nota / 2) - 1.2, cursor_y + (h_linha / 2) + 1.2, str(nota))

            pdf.set_font("helvetica", "", 6.8)
            for idx_s, l_txt in enumerate(linhas_sint):
                pdf.text(10 + w_pos + w_comp + w_cart + w_nota + 1.2, cursor_y + 3.8 + (idx_s * 3.0), sanitizar_pdf(l_txt))

            cursor_y += h_linha
            pdf.set_xy(10, cursor_y)

        pdf.ln(3)

        pdf.set_font("helvetica", "B", 8)
        pdf.cell(0, 5, sanitizar_pdf(f"PONTUAÇÃO TOTAL: {total_pts} / 40  |  CLASSIFICAÇÃO: {classif}  |  SINAL VERMELHO: {sinal_vermelho_val}"), 0, 1, "L")
        pdf.ln(1.5)

        pdf.set_font("helvetica", "B", 8)
        pdf.cell(0, 4.5, sanitizar_pdf("PARECER FINAL DO AVALIADOR:"), 0, 1)
        pdf.set_font("helvetica", "", 7.5)
        notas_competencias = {
            competencias_nomes[idx - 1]: float(st.session_state.get(f"t_pontos_{idx}", 3))
            for idx in range(1, 9)
        }
        maiores_forcas = sorted(notas_competencias.items(), key=lambda item: item[1], reverse=True)[:2]
        focos_ressalva = sorted(notas_competencias.items(), key=lambda item: item[1])[:2]
        forcas_txt = ", ".join(f"{nome} ({nota:.0f}/5)" for nome, nota in maiores_forcas)
        ressalvas_txt = ", ".join(f"{nome} ({nota:.0f}/5)" for nome, nota in focos_ressalva)
        deliberacao_txt = (
            "deliberação desfavorável, com veto de governança"
            if veto_governanca else
            f"deliberação de {classif.lower()}"
        )
        if veto_governanca:
            parecer_ficha = (
                f"SUMÁRIO EXECUTIVO: Para a vaga de {c_vaga or 'Geral'} ({nivel_hierarquico}), o perfil alcançou "
                f"{total_pts} / 40 pontos ({perc_t1:.1f}% de aderência). Maiores forças: {forcas_txt}. "
                f"Focos de ressalva ou veto: {ressalvas_txt}. A {deliberacao_txt} decorre de risco crítico "
                f"em Equilíbrio Emocional, Saúde Psicológica ou Confiabilidade e Ética. Classificação: '{classif}'."
            )
        else:
            parecer_ficha = (
                f"SUMÁRIO EXECUTIVO: Para a vaga de {c_vaga or 'Geral'} ({nivel_hierarquico}), o perfil alcançou "
                f"{total_pts} / 40 pontos ({perc_t1:.1f}% de aderência). Maiores forças: {forcas_txt}. "
                f"Focos de ressalva: {ressalvas_txt}. A avaliação sustenta {deliberacao_txt}, "
                f"considerando o alinhamento comportamental e estrutural mapeado."
            )
        pdf.set_fill_color(248, 249, 250)
        pdf.set_draw_color(200, 205, 210)
        pdf.multi_cell(0, 4.2, sanitizar_pdf(parecer_ficha), border=1, fill=True)

        # Página 2 em diante: Análise Qualitativa
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 6, sanitizar_pdf("ANÁLISE QUALITATIVA DAS COMPETÊNCIAS"), 0, 1, "L")
        pdf.ln(2)

        def renderizar_item_analise(pdf, label_prefix, nome_carta, texto_corpo, largura_bloco):
            """Garante 'RÓTULO: NOME DA CARTA - ' em negrito estrito."""
            if not nome_carta:
                cabecalho_negrito = f"{label_prefix}: "
            else:
                cabecalho_negrito = f"{label_prefix}: {nome_carta} - "

            pdf.set_font("helvetica", "B", 7.5)
            w_cabecalho = pdf.get_string_width(cabecalho_negrito)

            palavras = str(texto_corpo).strip().split(" ")
            linhas_geradas = []
            linha_atual = ""
            primeira_linha = True

            for p in palavras:
                if not p:
                    continue
                largura_limite = (largura_bloco - w_cabecalho - 2) if primeira_linha else (largura_bloco - 2)
                teste = f"{linha_atual} {p}".strip() if linha_atual else p

                pdf.set_font("helvetica", "", 7.5)
                if pdf.get_string_width(teste) <= largura_limite:
                    linha_atual = teste
                else:
                    if linha_atual:
                        linhas_geradas.append(linha_atual)
                        primeira_linha = False
                    linha_atual = p
            if linha_atual:
                linhas_geradas.append(linha_atual)

            x_ini = pdf.get_x()
            y_ini = pdf.get_y()

            pdf.set_font("helvetica", "B", 7.5)
            pdf.text(x_ini, y_ini + 3.0, sanitizar_pdf(cabecalho_negrito))

            pdf.set_font("helvetica", "", 7.5)
            if linhas_geradas:
                pdf.text(x_ini + w_cabecalho + 0.5, y_ini + 3.0, sanitizar_pdf(linhas_geradas[0]))
                for idx_sub, resto_linha in enumerate(linhas_geradas[1:], start=1):
                    pdf.text(x_ini, y_ini + 3.0 + (idx_sub * 3.4), sanitizar_pdf(resto_linha))
                h_ocupada = float(len(linhas_geradas) * 3.4)
            else:
                h_ocupada = 3.4

            pdf.set_xy(x_ini, y_ini + h_ocupada + 1.2)
            return h_ocupada + 1.2

        for i in range(1, 9):
            desc_central = ""
            desc_negativa = ""
            desc_positiva = ""
            resumo = ""

            nota_comp = st.session_state.get(f"t_pontos_{i}", 3)
            c_cent = st.session_state.get(f"t_central_{i}", "-")
            c_neg = st.session_state.get(f"t_negativa_{i}", "-")
            c_pos = st.session_state.get(f"t_positiva_{i}", "-")

            cartas_str = f"Carta Central: {c_cent}  |  Carta Negativa: {c_neg}  |  Carta Positiva: {c_pos}"
            conteudo_comp = extrair_secao_competencia(texto_ia_doc, i, competencias_nomes[i-1])

        dados_competencia = st.session_state.get(f"analise_fase1_casa_{i}")
        tem_conteudo = bool(dados_competencia and any(str(dados_competencia.get(k, "")).strip() for k in ["central_desc", "negativa_desc", "positiva_desc", "resumo"]))
        if not tem_conteudo:
            dados_competencia = extrair_descricao_competencia(texto_ia_doc, i, competencias_nomes[i-1])
            desc_central = remover_nome_carta_descricao(dados_competencia.get("central", ""), c_cent)
            desc_negativa = remover_nome_carta_descricao(dados_competencia.get("negativa", ""), c_neg)
            desc_positiva = remover_nome_carta_descricao(dados_competencia.get("positiva", ""), c_pos)
            resumo = dados_competencia.get("resumo", "")
        else:
            desc_central = dados_competencia.get("central_desc", "") or remover_nome_carta_descricao(dados_competencia.get("central", ""), c_cent)
            desc_negativa = dados_competencia.get("negativa_desc", "") or remover_nome_carta_descricao(dados_competencia.get("negativa", ""), c_neg)
            desc_positiva = dados_competencia.get("positiva_desc", "") or remover_nome_carta_descricao(dados_competencia.get("positiva", ""), c_pos)
            resumo = dados_competencia.get("resumo", "")

            blocos_parsed = []
            if desc_central:
                blocos_parsed.append(("CARTA CENTRAL", c_cent, desc_central))
            if desc_negativa:
                blocos_parsed.append(("CARTA NEGATIVA", c_neg, desc_negativa))
            if desc_positiva:
                blocos_parsed.append(("CARTA POSITIVA", c_pos, desc_positiva))
            if resumo:
                blocos_parsed.append(("RESUMO DA LEITURA", "", resumo))

            if not blocos_parsed:
                blocos_parsed = [("", "", "Competência sem descrição disponível no laudo gerado.")]

            pdf.set_font("helvetica", "", 7.5)
            h_corpo_total = 0.0
            for r_txt, c_nome_item, c_txt in blocos_parsed:
                prefixo_tam = f"{r_txt}: {c_nome_item} - " if c_nome_item else f"{r_txt}: "
                w_tot = pdf.get_string_width(f"{prefixo_tam}{c_txt}")
                linhas_bloco = max(1, math.ceil(w_tot / 184.0))
                h_corpo_total += float(linhas_bloco * 3.4) + 1.5

            h_total_card = 6.0 + 5.0 + h_corpo_total + 4.0

            if pdf.get_y() + h_total_card > 275:
                pdf.add_page()

            y_box = pdf.get_y()
            pdf.set_draw_color(200, 205, 212)
            pdf.rect(10, y_box, 190, 6.0 + 5.0 + h_corpo_total + 2.0)

            # Cabeçalho da competência
            pdf.set_font("helvetica", "B", 8.5)
            pdf.set_fill_color(240, 243, 246)
            pdf.cell(0, 6.0, sanitizar_pdf(f"  {i}. {competencias_nomes[i-1]} (Nota: {nota_comp}/5)"), 0, 1, "L", True)

            # Subtítulo com os arcanos
            pdf.set_font("helvetica", "I", 7.5)
            pdf.set_xy(13, y_box + 6.2)
            pdf.cell(184, 4.8, sanitizar_pdf(cartas_str), 0, 1, "L", False)

            # Renderização de cada item com Caixa Alta e Negrito
            pdf.set_xy(13, y_box + 11.5)
            for r_txt, c_nome_item, c_txt in blocos_parsed:
                if r_txt:
                    renderizar_item_analise(pdf, r_txt, c_nome_item, c_txt, 184)
                else:
                    pdf.set_font("helvetica", "", 7.5)
                    pdf.multi_cell(184, 3.6, sanitizar_pdf(c_txt), 0, "L", False)

            pdf.set_xy(10, y_box + 6.0 + 5.0 + h_corpo_total + 5.0)

        match_conclusao = re.search(
            r"^(?:\s*(?:#{1,6}|\*\*)?\s*(?:\d+\.\s*)?(?:\*\*)?\s*CONCLUS[ÃA]O\s*(?:\*\*)?\s*:?(?:\s|$))(.*)$",
            texto_ia_doc,
            re.DOTALL | re.IGNORECASE | re.MULTILINE,
        )
        if veto_governanca:
            texto_conclusao = (
                f"PARECER FINAL: Não Recomendado (Veto de Governança).\n"
                f"JUSTIFICATIVA EXECUTIVA: Embora o candidato tenha somado {total_pts} pontos "
                f"({perc_t1:.1f}% de aderência), a candidatura foi vetada pelas regras de integridade e governança corporativa. "
                f"As maiores forças identificadas foram {forcas_txt}; os focos de ressalva ou veto foram {ressalvas_txt}. "
                "Riscos críticos em bases emocionais, psíquicas ou éticas representam ponto de ruptura para a governança da posição."
            )
        elif match_conclusao and len(match_conclusao.group(1).strip()) > 10:
            raw_c = match_conclusao.group(1).strip()
            raw_c = re.sub(r"^(?:E\s+)?RECOMENDA[ÇC][ÃA]O\s+FINAL\s*", "", raw_c, flags=re.IGNORECASE).strip()
            raw_c = re.sub(r"^PARECER\s+FINAL\s*:[^\n]+\n*", "", raw_c, flags=re.IGNORECASE).strip()
            raw_c = re.sub(r"^JUSTIFICATIVA\s+EXECUTIVA\s*:\s*", "", raw_c, flags=re.IGNORECASE).strip()
            raw_c = re.sub(r"\n*(?:For[çc]as\s+principais|Focos\s+de\s+ressalva)[\s\S]*$", "", raw_c, flags=re.IGNORECASE).strip()
            classif_limpo = str(classif).rstrip(".")
            texto_conclusao = (
                f"PARECER FINAL: {classif_limpo}.\n"
                f"JUSTIFICATIVA EXECUTIVA: {raw_c}\n"
                f"Forças principais: {forcas_txt}. Focos de ressalva: {ressalvas_txt}."
            )
        else:
            texto_conclusao = (
                f"PARECER FINAL: {classif}.\n"
                f"JUSTIFICATIVA EXECUTIVA: O candidato obteve {total_pts} pontos ({perc_t1:.1f}% de aderência). "
                f"As competências de maior força foram {forcas_txt}; os principais focos de ressalva são {ressalvas_txt}. "
                "A deliberação considera o equilíbrio entre desempenho, riscos mapeados e aderência à vaga."
            )

        pdf.set_font("helvetica", "", 7.5)
        parags_conc = [p.strip() for p in texto_conclusao.split("\n") if p.strip()]
        linhas_totais_conc = sum([max(1, math.ceil(pdf.get_string_width(p) / 175.0)) for p in parags_conc]) + len(parags_conc)
        h_estimada_conc = 6.0 + float(linhas_totais_conc * 3.6) + 8.0

        if pdf.get_y() + h_estimada_conc > 275:
            pdf.add_page()

        y_conc = pdf.get_y()
        pdf.set_font("helvetica", "B", 9)
        pdf.set_fill_color(230, 235, 242)
        pdf.set_xy(10, y_conc)
        pdf.cell(190, 6.0, sanitizar_pdf("  CONCLUSÃO E RECOMENDAÇÃO FINAL"), 0, 1, "L", True)

        pdf.set_font("helvetica", "", 7.5)
        pdf.set_xy(13, y_conc + 7.5)
        pdf.multi_cell(184, 3.6, sanitizar_pdf(texto_conclusao), 0, "L", False)

        y_fim_conc = pdf.get_y() + 3.0
        altura_final_box = max(18.0, y_fim_conc - y_conc)
        pdf.set_draw_color(190, 195, 202)
        pdf.rect(10, y_conc, 190, altura_final_box)
        pdf.set_y(y_conc + altura_final_box + 4.0)

        res = pdf.output(dest="S")
        return res.encode("latin1") if isinstance(res, str) else bytes(res)

    if resultado_calculado and casas_preenchidas and cache_key_check in st.session_state and st.session_state.get(cache_key_check):
        pdf_stream = gerar_ficha_pdf_fase1(c_nome_val, vaga_cargo, total_t1, classificacao_f1, sinal_vermelho_f1)
        st.download_button(
            label="📥 Baixar Ficha de Avaliação Completa em PDF",
            data=pdf_stream,
            file_name=f"Ficha_Avaliacao_Recrutamento_{(c_nome_val or 'Candidato').replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
    elif resultado_calculado and casas_preenchidas:
        st.info("💡 Clique no botão acima **'🤖 Gerar Análise Qualitativa por IA (Fase 1)'** para habilitar o download do PDF completo.")

with tab2:
    st.header("Fase 2: Motor Astrológico Ponderado & Trânsitos Atuais")
    st.markdown(f"**Arquétipo Ativo:** `{arq_nome}` – Cruzamento de pesos corporativos com as efemérides planetárias")

    if not KERYKEION_DISPONIVEL:
        st.warning(f"⚠️ Kerykeion indisponível: `{KERYKEION_ERRO or 'Módulo não carregado'}`")

    col_astro1, col_astro2 = st.columns(2)
    with col_astro1:
        data_nasc_raw = st.text_input(
            "Data de Nascimento (DD/MM/AAAA)",
            placeholder="02/05/1978",
            key="astro_data_raw",
        )
        local_nasc = st.text_input(
            "Local de Nascimento (Cidade/Estado)",
            placeholder="São Paulo, SP",
            key="astro_local",
        )
    with col_astro2:
        hora_nasc = st.time_input("Horário de Nascimento", key="astro_hora")
        sistema_casas = st.selectbox("Sistema de Casas", ["Plácidus", "Koch", "Signo Inteiro"], index=0)
    def calcular_mandala_ponderada_com_transitos(d_nasc_str, h_nasc, loc, pesos_dict):
        if not d_nasc_str or h_nasc is None or not loc or not loc.strip():
            st.error("⚠️ Preencha Data, Horário e Local de Nascimento.")
            return None, None, {}

        digits = "".join(filter(str.isdigit, d_nasc_str))
        if len(digits) != 8:
            st.error("❌ Formato de data inválido. Use DD/MM/AAAA (ex: 02/05/1978).")
            return None, None, {}

        try:
            d_nasc = datetime.strptime(digits, "%d%m%Y").date()
        except ValueError:
            st.error("❌ Data inválida.")
            return None, None, {}

        geolocator = Nominatim(user_agent="rh_astrology_dinamico_v3")
        lat, lon = None, None
        try:
            loc_obj = geolocator.geocode(loc)
            if loc_obj:
                lat, lon = loc_obj.latitude, loc_obj.longitude
            else:
                st.error(f"❌ Coordenadas não encontradas para '{loc}'.")
                return None, None, {}
        except Exception as e:
            st.error(f"❌ Erro de geolocalização: {e}")
            return None, None, {}

        casas_res = {}
        big_three = {}
        transitos_info = {}

        if KERYKEION_DISPONIVEL:
            try:
                tz_br = pytz.timezone("America/Sao_Paulo")
                dt_local = datetime(d_nasc.year, d_nasc.month, d_nasc.day, h_nasc.hour, h_nasc.minute)
                dt_aware = tz_br.localize(dt_local)
                dt_utc = dt_aware.astimezone(pytz.utc)

                subject = AstrologicalSubject(
                    name="Candidato", year=dt_utc.year, month=dt_utc.month, day=dt_utc.day,
                    hour=dt_utc.hour, minute=dt_utc.minute, city=loc, nation="BR",
                    lat=lat, lng=lon, tz_str="UTC",
                )
                
                agora_utc = datetime.now(pytz.utc)
                transit_subject = AstrologicalSubject(
                    name="Transitos_Correntes", year=agora_utc.year, month=agora_utc.month, day=agora_utc.day,
                    hour=agora_utc.hour, minute=agora_utc.minute, city=loc, nation="BR",
                    lat=lat, lng=lon, tz_str="UTC",
                )

                def extrair_signo_grau(obj_attr):
                    if not obj_attr: return "Desconhecido", 0.0
                    if isinstance(obj_attr, dict):
                        s = obj_attr.get("sign", "Desconhecido")
                        p = obj_attr.get("position", obj_attr.get("pos", 0.0))
                    else:
                        s = getattr(obj_attr, "sign", "Desconhecido")
                        p = getattr(obj_attr, "position", getattr(obj_attr, "pos", 0.0))
                    return TRADUCAO_SIGNOS.get(s, s), p

                sun_s, sun_p = extrair_signo_grau(getattr(subject, "sun", None))
                moon_s, moon_p = extrair_signo_grau(getattr(subject, "moon", None))
                asc_s, asc_p = extrair_signo_grau(getattr(subject, "first_house", None))

                big_three = {
                    "Solar": {"signo": sun_s, "grau": f"{int(sun_p % 30)}º {int((sun_p % 1) * 60)}'"},
                    "Ascendente": {"signo": asc_s, "grau": f"{int(asc_p % 30)}º {int((asc_p % 1) * 60)}'"},
                    "Lunar": {"signo": moon_s, "grau": f"{int(moon_p % 30)}º {int((moon_p % 1) * 60)}'"},
                }

                planetas_transito = {
                    "Júpiter (Expansão)": extrair_signo_grau(getattr(transit_subject, "jupiter", None))[0],
                    "Saturno (Estrutura/Cobrança)": extrair_signo_grau(getattr(transit_subject, "saturn", None))[0],
                    "Urano (Inovação/Mudança)": extrair_signo_grau(getattr(transit_subject, "uranus", None))[0]
                }

                house_attrs = [
                    "first_house", "second_house", "third_house", "fourth_house",
                    "fifth_house", "sixth_house", "seventh_house", "eighth_house",
                    "ninth_house", "tenth_house", "eleventh_house", "twelfth_house",
                ]
                
                for i, attr in enumerate(house_attrs, start=1):
                    if hasattr(subject, attr):
                        signo, pos = extrair_signo_grau(getattr(subject, attr))
                    else:
                        signo, pos = "Desconhecido", 0.0

                    nota_base_casa = calcular_nota_astrologica_casa(i, signo)
                    peso_arq = pesos_dict.get(i, 1.0)
                    
                    fator_transito = 1.0
                    clima_transito = "Estável"
                    for p_nome, p_sig in planetas_transito.items():
                        if p_sig == signo:
                            if "Júpiter" in p_nome:
                                fator_transito = 1.15
                                clima_transito = "✨ Ativado por Júpiter (Ciclo de Crescimento)"
                            elif "Saturno" in p_nome:
                                fator_transito = 0.90
                                clima_transito = "🛡️ Ativado por Saturno (Ciclo de Reestruturação e Rigor)"
                            elif "Urano" in p_nome:
                                fator_transito = 1.10
                                clima_transito = "⚡ Ativado por Urano (Ciclo de Inovação e Ruptura)"

                    nota_final_calculada = min(5.0, nota_base_casa * fator_transito)

                    casas_res[f"Casa {i}"] = {
                        "signo": signo,
                        "grau": f"{int(pos % 30)}º {int((pos % 1) * 60)}'",
                        "nota_base": round(nota_final_calculada, 1),
                        "peso": peso_arq,
                        "clima": clima_transito,
                        "analise": f"Signo: {signo} | Nota Trânsito: {nota_final_calculada:.1f}/5 | Arquétipo: {peso_arq}x",
                    }
                return casas_res, big_three, planetas_transito

            except Exception as e:
                st.error(f"Erro no cálculo de trânsitos Kerykeion: {e}")
                return None, None, {}

        signos = ["Áries", "Touro", "Gêmeos", "Câncer", "Leão", "Virgem", "Libra", "Escorpião", "Sagitário", "Capricórnio", "Aquário", "Peixes"]
        seed = d_nasc.toordinal() + int(h_nasc.hour * 60 + h_nasc.minute)
        big_three = {
            "Solar": {"signo": signos[seed % 12], "grau": "12º 0'"},
            "Ascendente": {"signo": signos[(seed + 6) % 12], "grau": "8º 15'"},
            "Lunar": {"signo": signos[(seed + 3) % 12], "grau": "15º 30'"},
        }
        casas_res = {}
        for c in range(1, 13):
            sig = signos[(seed + c * 7) % 12]
            nb = calcular_nota_astrologica_casa(c, sig)
            p = pesos_dict.get(c, 1.0)
            casas_res[f"Casa {c}"] = {
                "signo": sig, "grau": "10º", "nota_base": nb, "peso": p,
                "clima": "Estável", "analise": f"Signo: {sig} | Nota Base: {nb}/5 | Peso: {p}x"
            }
        return casas_res, big_three, {}

    if st.button("Processar Mandala Ponderada & Trânsitos Atuais", type="primary"):
        with st.spinner("Calculando efemérides natais, trânsitos atuais e aplicando matrizes..."):
            mandala, big_three, transitos = calcular_mandala_ponderada_com_transitos(data_nasc_raw, hora_nasc, local_nasc, arq_pesos)
            if mandala and big_three:
                st.session_state["mandala_calculada"] = mandala
                st.session_state["big_three_calculado"] = big_three
                st.session_state["transitos_calculados"] = transitos
                st.session_state["arq_utilizado"] = arq_nome
                st.session_state["astro_loc_resolvido"] = local_nasc
                st.success("Mapeamento astrológico e conjuntural concluído com sucesso!")

    if "mandala_calculada" in st.session_state:
        if "big_three_calculado" in st.session_state:
            b3 = st.session_state["big_three_calculado"]
            st.markdown("### Trindade Principal")
            cb1, cb2, cb3 = st.columns(3)
            with cb1: st.metric("Signo Solar", b3['Solar']['signo'], b3['Solar']['grau'])
            with cb2: st.metric("Signo Ascendente", b3['Ascendente']['signo'], b3['Ascendente']['grau'])
            with cb3: st.metric("Signo Lunar", b3['Lunar']['signo'], b3['Lunar']['grau'])
            st.markdown("")

        if "transitos_calculados" in st.session_state and st.session_state["transitos_calculados"]:
            st.markdown("### 🌐 Clima Planetário em Trânsito (Ano Corrente)")
            t_cols = st.columns(len(st.session_state["transitos_calculados"]))
            for idx, (p_nome, p_sig) in enumerate(st.session_state["transitos_calculados"].items()):
                with t_cols[idx]:
                    st.metric(p_nome, p_sig)
            st.markdown("")

        mandala_items = list(st.session_state["mandala_calculada"].items())
        casas_astrologicas_f2 = {
            indice: {"nota": dados.get("nota_base", 4.0)}
            for indice, (_, dados) in enumerate(mandala_items, start=1)
        }
        pesos_arquetipo_f2 = {
            f"C{indice}": dados.get("peso", 1.0)
            for indice, (_, dados) in enumerate(mandala_items, start=1)
        }
        pontos_fase2, aderencia_pct, diagnostico_fase2 = calcular_pontuacao_fase2(
            casas_astrologicas_f2,
            pesos_arquetipo_f2,
        )
        total_t2_ajustado = (aderencia_pct / 100.0) * 60.0
        perc_t2 = aderencia_pct
        if aderencia_pct >= 80.0:
            status_fase2 = "Alta Sinergia"
            descricao_fase2 = "Desempenho Robusto"
            recomendacao_fase2 = "Prontidão Imediata"
        elif aderencia_pct >= 65.0:
            status_fase2 = "Aderência Operacional"
            descricao_fase2 = "Desempenho Consistente com Atenção Pontual"
            recomendacao_fase2 = "Acompanhamento direcionado"
        else:
            status_fase2 = "Ponto de Atenção"
            descricao_fase2 = "Ciclo Desafiador"
            recomendacao_fase2 = "Vulnerabilidade Temporária"

        st.markdown("### Síntese da Fase 2")
        quadro_pontuacao, quadro_aderencia = st.columns(2)
        with quadro_pontuacao:
            with st.container(border=True):
                st.markdown(f"**PONTUAÇÃO AJUSTADA DA FASE 2: {pontos_fase2:.1f} / 60 PONTOS**")
                st.caption("**A Matemática:** 12 casas x 5 pontos = teto de 60 pontos.")
                st.caption("**O Ajuste:** Modulação dinâmica ponderada pelos trânsitos contemporâneos.")
                st.caption("**Significado:** Capacidade e resiliência comportamental líquida.")
                st.success(f"**Análise do Resultado:** {status_fase2} / {descricao_fase2}")
        with quadro_aderencia:
            with st.container(border=True):
                st.markdown(f"**ADERÊNCIA ESTRUTURAL AO CICLO: {aderencia_pct:.1f}%**")
                st.caption("**A Matemática:** Proporção direta da pontuação líquida sobre o teto de 60 pontos.")
                st.caption("**Significado Corporativo:** Grau de prontidão imediata e harmonia com o momento contemporâneo.")
                st.info(f"**Análise do Resultado:** {status_fase2} / {recomendacao_fase2}")

        st.info(
            f"**Diagnóstico Executivo Integrado:** A pontuação líquida de {pontos_fase2:.1f} pontos representa "
            f"{aderencia_pct:.1f}% de aderência estrutural, enquadrando o candidato em **{status_fase2}** "
            f"com **{descricao_fase2.lower()}** e recomendação de **{recomendacao_fase2.lower()}**."
        )
        st.markdown("")

        pdf_fase2_bytes = gerar_laudo_fase2_pdf(
            st.session_state.get("candidato_nome", nome_candidato if 'nome_candidato' in locals() else "Candidato"),
            st.session_state.get("candidato_cargo", vaga_cargo),
            st.session_state.get("candidato_nivel", nivel_hierarquico),
            st.session_state.get("arq_utilizado", arq_nome),
            data_nasc_raw,
            hora_nasc,
            st.session_state.get("astro_loc_resolvido", local_nasc),
            st.session_state["big_three_calculado"],
            st.session_state.get("transitos_calculados", {}),
            st.session_state["mandala_calculada"],
            total_t2_ajustado,
            perc_t2
        )
        
        st.download_button(
            label="📥 Baixar Laudo Estrutural e Conjuntural em PDF (Fase 2)",
            data=pdf_fase2_bytes,
            file_name=f"Laudo_Estrutural_Fase2_{(nome_candidato or 'Candidato').replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
        st.markdown("---")

        for idx_linha in range(0, len(mandala_items), 3):
            cols_grid = st.columns(3)
            for col_idx in range(3):
                if idx_linha + col_idx < len(mandala_items):
                    k, v = mandala_items[idx_linha + col_idx]
                    with cols_grid[col_idx]:
                        with st.container(border=True):
                            st.markdown(f"**{k}** *(Base/Trânsito: {v['nota_base']} | Peso: {v['peso']}x)*")
                            st.markdown(f"### {v['signo']} `({v['grau']})`")
                            st.caption(f"{v['clima']} — {v['analise']}")
    else:
        st.info("Processe a mandala astrológica para visualizar o resultado ponderado e os trânsitos.")

with tab3:
    st.header("Fase 3: FICHA DE AVALIAÇÃO INTEGRADA E PONDERADA")
    st.markdown("Governança final cruzando o Tarot, a Astrologia Ponderada por Arquétipo e Momentos de Trânsito.")

    if st.button("Gerar Ficha de Avaliação Integrada", type="primary", key="btn_gerar_ficha_fase3"):
        with st.spinner("🤖 A IA está cruzando a Fase 1 (Tarot) com a Fase 2 (Astrologia) e redigindo a Deliberação Executiva..."):
            pontuacoes_f1_btn = [st.session_state.get(f"t_pontos_{i}", 3) for i in range(1, 9)]
            notas_f1_btn = {
                indice: {"nota": pontuacoes_f1_btn[indice - 1]}
                for indice in range(1, 9)
            }
            _, perc_f1_btn, _ = calcular_pontuacao_fase1(notas_f1_btn)
            mandala_btn = st.session_state.get("mandala_calculada", {})
            if mandala_btn:
                itens_mandala_btn = list(mandala_btn.items())
                casas_btn = {
                    indice: {"nota": dados.get("nota_base", 4.0)}
                    for indice, (_, dados) in enumerate(itens_mandala_btn, start=1)
                }
                pesos_btn = {
                    f"C{indice}": dados.get("peso", 1.0)
                    for indice, (_, dados) in enumerate(itens_mandala_btn, start=1)
                }
                _, perc_f2_btn, _ = calcular_pontuacao_fase2(casas_btn, pesos_btn)
            else:
                perc_f2_btn = 80.0
            indice_btn, classificacao_btn, sinal_btn, _ = calcular_indice_global_integrado(
                perc_f1_btn,
                perc_f2_btn,
                notas_f1_btn,
            )

            notas_btn = {
                nome: pontuacoes_f1_btn[idx]
                for idx, nome in enumerate([
                    "Hard Skills", "Soft Skills", "Fit Cultural", "Desafios",
                    "Potencial Futuro", "Equilíbrio Emocional", "Saúde Psicológica",
                    "Confiabilidade e Ética"
                ])
            }
            forcas_btn = ", ".join(f"{nome} ({nota}/5)" for nome, nota in sorted(notas_btn.items(), key=lambda item: item[1], reverse=True)[:2])
            atencoes_btn = ", ".join(f"{nome} ({nota}/5)" for nome, nota in sorted(notas_btn.items(), key=lambda item: item[1])[:2])

            sucesso_deliberacao, parecer_deliberacao, telemetria_deliberacao = gerar_deliberacao_fase3(
                st.session_state.get("candidato_nome", "Candidato(a)"),
                st.session_state.get("candidato_cargo", vaga_cargo),
                st.session_state.get("candidato_nivel", nivel_hierarquico),
                st.session_state.get("arq_utilizado", arq_nome),
                perc_f1_btn,
                perc_f2_btn,
                indice_btn,
                classificacao_btn,
                sinal_btn,
                forcas_btn,
                atencoes_btn,
            )
            st.session_state["parecer_tecnico"] = parecer_deliberacao
            st.session_state["telemetria_fase3"] = telemetria_deliberacao
            st.session_state["ficha_integrada_gerada"] = True
            st.session_state["ficha_gerada"] = True
            if not sucesso_deliberacao:
                st.warning("A síntese de contingência da deliberação integrada foi aplicada.")
        st.success("Dossiê Integrado consolidado com sucesso!")
        st.rerun()

    if st.session_state.get("ficha_integrada_gerada", st.session_state.get("ficha_gerada", False)):
        pontuacoes_t1 = [st.session_state.get(f"t_pontos_{i}", 3) for i in range(1, 9)]
        total_t1 = sum(pontuacoes_t1)
        perc_t1 = (total_t1 / 40.0) * 100

        mandala_dados = st.session_state.get("mandala_calculada", {})
        if mandala_dados:
            mandala_items = list(mandala_dados.items())
            casas_f2 = {
                indice: {"nota": dados.get("nota_base", 4.0)}
                for indice, (_, dados) in enumerate(mandala_items, start=1)
            }
            pesos_f2 = {
                f"C{indice}": dados.get("peso", 1.0)
                for indice, (_, dados) in enumerate(mandala_items, start=1)
            }
            _, perc_t2, _ = calcular_pontuacao_fase2(casas_f2, pesos_f2)
            total_t2_ajustado = (perc_t2 / 100.0) * 60.0
        else:
            total_t2_ajustado = 48.0
            perc_t2 = 80.0

        notas_fase1_f3 = {
            indice: {"nota": st.session_state.get(f"t_pontos_{indice}", 3)}
            for indice in range(1, 9)
        }
        indice_global, classificacao, sinal_ativo, motivo_sinal = calcular_indice_global_integrado(
            perc_t1,
            perc_t2,
            notas_fase1_f3,
        )
        sinal_vermelho = "Sim" if sinal_ativo else "Não"

        c_nome = st.session_state.get("candidato_nome", "Candidato(a)")
        c_vaga = st.session_state.get("candidato_cargo", "Cargo")
        c_nivel = st.session_state.get("candidato_nivel", "Nível")
        arq_ativo_ficha = st.session_state.get("arq_utilizado", arq_nome)
        data_atual = datetime.now().strftime("%d / %m / %Y")

        st.markdown("---")
        st.markdown(f"**CANDIDATO(A):** {c_nome} | **VAGA:** {c_vaga} ({c_nivel}) | **ARQUÉTIPO:** {arq_ativo_ficha}")
        st.markdown("---")

        cr1, cr2, cr3 = st.columns(3)
        with cr1: st.metric("Fase 1 (Tarot)", f"{total_t1} / 40", f"{perc_t1:.1f}%")
        with cr2: st.metric("Fase 2 (Astrologia Ponderada & Trânsitos)", f"{total_t2_ajustado:.1f} / 60", f"{perc_t2:.1f}%")
        with cr3: st.metric("Índice Global Integrado", f"{indice_global:.1f}%")

        st.markdown(f"**Classificação Final:** {classificacao}")
        if sinal_vermelho == "Sim":
            st.error("🚨 SINAL VERMELHO ATIVADO: Risco crítico nas Casas 6, 7 ou 8.")
        else:
            st.success("✅ SINAL VERMELHO DESATIVADO: Bases emocionais e éticas preservadas.")

        sub_t1, sub_t2, sub_t3 = st.tabs(["Gráfico Radar & Parecer", "Cruzamento por Arquétipo", "Histórico do Projeto & Custos"])

        with sub_t1:
            categories = ["Hard Skills", "Soft Skills", "Fit Cultural", "Desafios", "Potencial Futuro", "Equilíbrio Emocional", "Saúde Psicológica", "Confiabilidade e Ética"]
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=pontuacoes_t1 + [pontuacoes_t1[0]], theta=categories + [categories[0]], fill="toself", name="Candidato", line_color="#00cc96", fillcolor="rgba(0, 204, 150, 0.25)"))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5], dtick=1), bgcolor="rgba(22, 26, 29, 0.6)"), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=380, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### Parecer Técnico Dinâmico & Conjuntural")
            st.write(f"Avaliação direcionada ao arquétipo **{arq_ativo_ficha}** para a posição de **{c_vaga}**. O cruzamento integra a análise comportamental e o ciclo conjuntural ativo de trânsitos, resultando em um **Índice Global de {indice_global:.1f}%** (*{classificacao}*).")

            texto_ia_laudo = obter_ou_gerar_analise_ia(c_nome, c_vaga, arq_ativo_ficha, sinal_vermelho=sinal_vermelho)
            texto_conclusao_f3 = st.session_state.get(
                "parecer_tecnico",
                f"O candidato apresenta um Índice Global de {indice_global:.1f}%, enquadrando-se na diretriz de "
                f"'{classificacao}'. A avaliação cruza a base comportamental do Tarot (Fase 1: {perc_t1:.1f}%) "
                f"com o mapa astrológico ponderado pelo arquétipo de {arq_ativo_ficha} e os trânsitos celestes correntes "
                f"(Fase 2: {perc_t2:.1f}%)."
            )

            competencias_nomes = [
                "Hard Skills", "Soft Skills", "Fit Cultural", 
                "Desafios", "Potencial Futuro", "Equilíbrio Emocional", 
                "Saúde Psicológica", "Confiabilidade e Ética"
            ]
            armazenar_analise_fase1(texto_ia_laudo, competencias_nomes)
            dados_tabela_f1 = []
            for idx_c in range(1, 9):
                desc_central = ""
                desc_negativa = ""
                desc_positiva = ""
                resumo = ""

                c_cent_v = st.session_state.get(f"t_central_{idx_c}", "-")
                c_neg_v = st.session_state.get(f"t_negativa_{idx_c}", "-")
                c_pos_v = st.session_state.get(f"t_positiva_{idx_c}", "-")

                dados_competencia = st.session_state.get(f"analise_fase1_casa_{idx_c}")
                if not dados_competencia:
                    dados_competencia = extrair_descricao_competencia(texto_ia_laudo, idx_c, competencias_nomes[idx_c - 1])
                    desc_central = remover_nome_carta_descricao(dados_competencia.get("central", ""), c_cent_v)
                    desc_negativa = remover_nome_carta_descricao(dados_competencia.get("negativa", ""), c_neg_v)
                    desc_positiva = remover_nome_carta_descricao(dados_competencia.get("positiva", ""), c_pos_v)
                else:
                    desc_central = dados_competencia.get("central_desc", "")
                    desc_negativa = dados_competencia.get("negativa_desc", "")
                    desc_positiva = dados_competencia.get("positiva_desc", "")
                resumo = dados_competencia.get("resumo", "")

                if not resumo:
                    resumo = extrair_sintese_competencia(texto_ia_laudo, idx_c, competencias_nomes[idx_c - 1])

                dados_tabela_f1.append({
                    "pos": idx_c,
                    "nome": competencias_nomes[idx_c - 1],
                    "cartas": f"Central: {c_cent_v}\nNegativa: {c_neg_v}\nPositiva: {c_pos_v}",
                    "nota": st.session_state.get(f"t_pontos_{idx_c}", 3),
                    "resumo": resumo or "Resumo da competência não disponível."
                })

  # Geração do Dossiê Master Unificado
            pdf_fase3_bytes = gerar_laudo_fase3_pdf(
                c_nome, c_vaga, c_nivel, arq_ativo_ficha,
                perc_t1, perc_t2, indice_global, classificacao,
                sinal_vermelho, texto_conclusao_f3, mandala_dados, dados_tabela_f1
            )

            col_a1, col_a2 = st.columns(2)
            with col_a1:
                st.download_button(
                    label="📄 Baixar Dossiê Executivo Master Integrado em PDF (Fase 3)",
                    data=pdf_fase3_bytes,
                    file_name=f"Laudo_Executivo_Integrado_{(c_nome or 'Candidato').replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            with col_a2:
                if st.button("💾 Salvar no Banco Dinâmico (SQLite)", use_container_width=True, key="salvar_sqlite"):
                    dados_para_salvar = {
                        "nome": st.session_state.get("candidato_nome", ""),
                        "cargo": st.session_state.get("candidato_cargo", ""),
                        "nivel": st.session_state.get("candidato_nivel", ""),
                        "arquetipo": st.session_state.get("arquetipo_ativo", ""),
                        "pontuacao_fase1": st.session_state.get("pontuacao_fase1", 0.0),
                        "aderencia_fase1": st.session_state.get("aderencia_fase1", 0.0),
                        "pontuacao_fase2": st.session_state.get("pontuacao_fase2", 0.0),
                        "aderencia_fase2": st.session_state.get("aderencia_fase2", 0.0),
                        "indice_global": st.session_state.get("indice_global", 0.0),
                        "classificacao": st.session_state.get("classificacao_final", ""),
                        "sinal_vermelho": st.session_state.get("sinal_vermelho", False),
                        "parecer_tecnico": st.session_state.get("parecer_tecnico", ""),
                        "notas_casas": st.session_state.get("notas_casas", {}),
                    }
                    
                    sucesso, mensagem = salvar_avaliacao(dados_para_salvar)
                    if sucesso:
                        st.success(mensagem)
                    else:
                        st.error(mensagem)

        with sub_t2:
            st.markdown("### Cruzamento entre Tarot, Arquétipo e Trânsitos")
            map_c = [
                (1, "Hard Skills", 6, "Casa 6 (Trabalho/Rotina)"),
                (2, "Soft Skills", 3, "Casa 3 (Comunicação)"),
                (3, "Fit Cultural", 11, "Casa 11 (Grupos)"),
                (4, "Desafios", 12, "Casa 12 (Inconsciente)"),
                (5, "Potencial Liderança", 10, "Casa 10 (Carreira)"),
                (6, "Equilíbrio Emocional", 4, "Casa 4 (Base)"),
                (7, "Saúde Psicológica", 1, "Casa 1 (Self)"),
                (8, "Confiabilidade", 8, "Casa 8 (Compliance)")
            ]
            for tn, tnom, an, adesc in map_c:
                s_info = "Não calculated"
                clima_info = ""
                if f"Casa {an}" in mandala_dados:
                    d_casa = mandala_dados[f"Casa {an}"]
                    s_info = f"{d_casa['signo']} (Peso: {d_casa['peso']}x)"
                    clima_info = f" | {d_casa['clima']}"
                st.write(rf"- **{tnom} (Tarot Casa {tn})** $\leftrightarrow$ **{adesc}**: Cúspide: **{s_info}**{clima_info}")

        with sub_t3:
            with sqlite3.connect("rh_diagnostico_dinamico.db") as conn_db:
                df_hist = pd.read_sql_query("SELECT id, nome, vaga, nivel, data, pontos, classificacao, arquétipo, tokens_in, tokens_out, custo_brl FROM avaliacoes", conn_db)
            if not df_hist.empty:
                total_gastos = df_hist["custo_brl"].sum()
                max_gasto = df_hist["custo_brl"].max()
                total_tokens = df_hist["tokens_in"].sum() + df_hist["tokens_out"].sum()

                cm1, cm2, cm3, cm4 = st.columns(4)
                with cm1: st.metric("Avaliações Registradas", f"{len(df_hist)}")
                with cm2: st.metric("Tokens Totais", f"{total_tokens:,}")
                with cm3: st.metric("Gasto Total Acumulado", f"R$ {total_gastos:.4f}")
                with cm4: st.metric("Gasto Máximo / Avaliação", f"R$ {max_gasto:.4f}")

                st.markdown("---")
                st.dataframe(df_hist, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum registro no banco dinâmico.")