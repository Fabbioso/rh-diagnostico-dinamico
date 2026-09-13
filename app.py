from datetime import datetime

import io

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



try:

    from google import genai

    if "GEMINI_API_KEY" in st.secrets:

        gemini_client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

        GEMINI_API_DISPONIVEL = True

    else:

        GEMINI_API_DISPONIVEL = False

except Exception:

    GEMINI_API_DISPONIVEL = False



try:

    from kerykeion import AstrologicalSubject

    KERYKEION_DISPONIVEL = True

except ImportError:

    KERYKEION_DISPONIVEL = False



st.set_page_config(

    page_title="Sistema de Diagnóstico Corporativo Dinâmico - RH", layout="wide"

)



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

Sua tarefa é redigir a análise qualitativa (Análise do Jogo) completa para a Ficha de Avaliação de Recrutamento corporativo baseada no método de tiragem estruturada de 3 cartas por competência.



Diretrizes obrigatórias:

1. Mantenha um tom estritamente corporativo, analítico, neutro e executivo.

2. NUNCA utilize jargões místicos, esotéricos ou religiosos. Trate os símbolos como arquétipos de comportamento humano, padrões cognitivos e dinâmicas de trabalho.

3. É OBRIGATÓRIO incluir a análise detalhada de TODAS AS 8 COMPETÊNCIAS na sequência exata: 

   1. Hard Skills, 2. Soft Skills, 3. Fit Cultural, 4. Desafios, 5. Potencial Futuro, 6. Equilíbrio Emocional, 7. Saúde Psicológica e 8. Confiabilidade e Ética. Não omita nenhuma posição.

4. Para cada competência, utilize obrigatoriamente e de forma explícita os seguintes termos para estruturar a análise:

   - Carta Central

   - Carta Negativa

   - Carta Positiva

   É terminantemente proibido o uso de nomenclaturas alternativas como "Padrao Central" ou "Ponto de Fricção".

5. Conclua com uma seção de CONCLUSÃO avaliando a adequação geral do perfil para a vaga.

6. Escreva de forma limpa, evitando formatações complexas em Markdown ou LaTeX ($) para facilitar a exportação em PDF.

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

    texto = str(texto).replace("°", " deg ")

    texto = texto.replace("**", "").replace("###", "").replace("##", "").replace("#", "").replace("*", "").replace("$", "")

    texto = texto.replace("☐", "").replace("☑", "").replace("☒", "")

    try:

        return texto.encode('latin-1', 'replace').decode('latin-1')

    except Exception:

        return str(texto)



def obter_ou_gerar_analise_ia(c_nome, c_vaga, arq_ativo):

    cache_key = f"ai_analise_{c_nome}_{c_vaga}"

    if cache_key in st.session_state:

        return st.session_state[cache_key]

    

    dados_casas = {}

    competencias_nomes = [

        "Hard Skills", "Soft Skills", "Fit Cultural", 

        "Desafios", "Potencial Futuro", "Equilíbrio Emocional", 

        "Saúde Psicológica", "Confiabilidade e Ética"

    ]

    for i in range(1, 9):

        dados_casas[i] = {

            "titulo": competencias_nomes[i-1],

            "central": st.session_state.get(f"t_central_{i}", "Não informada"),

            "negativa": st.session_state.get(f"t_negativa_{i}", "Não informada"),

            "positiva": st.session_state.get(f"t_positiva_{i}", "Não informada"),

            "nota": st.session_state.get(f"t_pontos_{i}", 3)

        }



    if GEMINI_API_DISPONIVEL:

        try:

            prompt_usuario = f"""

            Gere a Análise do Jogo detalhada e o Parecer Final para o seguinte processo seletivo:

            - Candidato(a): {c_nome or 'Candidato'}

            - Vaga/Cargo: {c_vaga or 'Geral'}

            - Arquétipo Organizacional Ativo: {arq_ativo}



            Cartas sorteadas e notas por competência nas 8 posições:

            """

            for num, d in dados_casas.items():

                prompt_usuario += f"\n- Casa {num} ({d['titulo']} - Nota {d['nota']}/5): Carta Central: {d['central']} | Carta Negativa: {d['negativa']} | Carta Positiva: {d['positiva']}"

            

            prompt_usuario += "\n\nGaranta a cobertura completa e detalhada da Casa 1 até a Casa 8 utilizando obrigatoriamente os termos Carta Central, Carta Negativa e Carta Positiva, finalizando com a seção de CONCLUSÃO. Não utilize formatação LaTeX como cifrões."



            response = gemini_client.models.generate_content(

                model="gemini-3.6-flash",

                contents=prompt_usuario,

                config=genai.types.GenerateContentConfig(

                    system_instruction=SYSTEM_PROMPT_RH,

                    temperature=0.4,

                    max_output_tokens=8192,

                ),

            )

            texto_gerado = response.text

            st.session_state[cache_key] = texto_gerado

            return texto_gerado

        except Exception as e:

            return f"Erro ao gerar análise automatizada via IA: {e}"

    else:

        return "Análise qualitativa padrão (Configure a GEMINI_API_KEY em st.secrets para habilitar a geração avançada por IA)."



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



def inicializar_banco():

    with sqlite3.connect("rh_diagnostico_dinamico.db") as conn:

        cursor = conn.cursor()

        cursor.execute("""

            CREATE TABLE IF NOT EXISTS avaliacoes (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                nome TEXT,

                vaga TEXT,

                nivel TEXT,

                data TEXT,

                pontos INTEGER,

                classificacao TEXT,

                sinal_vermelho TEXT,

                arquétipo TEXT

            )

        """)

        conn.commit()



inicializar_banco()



def salvar_no_banco(nome, vaga, nivel, data, pontos, classificacao, sinal_vermelho, arq):

    if not nome or not nome.strip() or nome.strip() in ["Candidato(a)", "Selecionar Candidato Cadastrado..."]: return False

    with sqlite3.connect("rh_diagnostico_dinamico.db") as conn:

        cursor = conn.cursor()

        cursor.execute(

            """

            INSERT INTO avaliacoes (nome, vaga, nivel, data, pontos, classificacao, sinal_vermelho, arquétipo)

            VALUES (?, ?, ?, ?, ?, ?, ?, ?)

            """,

            (nome.strip(), vaga, nivel, data, pontos, classificacao, sinal_vermelho, arq),

        )

        conn.commit()

    return True



if "astro_data_raw" not in st.session_state: st.session_state["astro_data_raw"] = "01/01/1999"

if "astro_local" not in st.session_state: st.session_state["astro_local"] = "São Paulo, SP"

if "astro_hora" not in st.session_state: st.session_state["astro_hora"] = datetime.strptime("12:00", "%H:%M").time()

if "input_nome_cand" not in st.session_state: st.session_state["input_nome_cand"] = ""



def disparar_nova_avaliacao():

    st.session_state["input_nome_cand"] = ""

    st.session_state["input_vaga_cand"] = ""

    st.session_state["input_nivel_cand"] = "C-Level / Executivo"

    st.session_state["astro_data_raw"] = "01/01/1999"

    st.session_state["astro_hora"] = datetime.strptime("12:00", "%H:%M").time()

    st.session_state["astro_local"] = "São Paulo, SP"

    st.session_state["ficha_gerada"] = False

    for key in list(st.session_state.keys()):

        if key.startswith("ai_analise_"):

            del st.session_state[key]

    if "mandala_calculada" in st.session_state: del st.session_state["mandala_calculada"]

    if "big_three_calculado" in st.session_state: del st.session_state["big_three_calculado"]

    if "transitos_calculados" in st.session_state: del st.session_state["transitos_calculados"]

    for i in range(1, 9):

        st.session_state[f"t_central_{i}"] = ""

        st.session_state[f"t_negativa_{i}"] = ""

        st.session_state[f"t_positiva_{i}"] = ""

        st.session_state[f"t_pontos_{i}"] = 3

    st.rerun()



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

        st.button("🔄 Nova Avaliação", on_click=disparar_nova_avaliacao, use_container_width=True)



    with sqlite3.connect("rh_diagnostico_dinamico.db") as conn_db:

        cursor_db = conn_db.cursor()

        cursor_db.execute("SELECT DISTINCT nome FROM avaliacoes")

        candidatos_existentes = [row[0] for row in cursor_db.fetchall() if row[0]]



    tipo_cad = st.radio("Modo de Candidato", ["Selecionar Existente", "Cadastrar Novo"], index=1, horizontal=True, key="tipo_cad_modo")



    col_c1, col_c2, col_c3 = st.columns(3)

    with col_c1:

        if tipo_cad == "Selecionar Existente":

            if candidatos_existentes:

                escolha_cand = st.selectbox("Candidato(a) Registrado", ["Selecionar Candidato Cadastrado..."] + candidatos_existentes, key="select_cand_existente_ativo")

                nome_candidato = escolha_cand if escolha_cand != "Selecionar Candidato Cadastrado..." else ""

            else:

                st.info("Nenhum candidato registrado.")

                nome_candidato = ""

        else:

            nome_candidato = st.text_input("Nome Completo do Novo Candidato(a)", key="input_nome_cand")



    with col_c2:

        vaga_cargo = st.text_input("Vaga / Cargo Pretendido", key="input_vaga_cand")

    with col_c3:

        nivel_hierarquico = st.selectbox("Nível Hierárquico", ["C-Level / Executivo", "Diretor", "Gerente", "Supervisor", "Coordenador", "Especialista / Analista", "Técnico", "Operacional"], key="input_nivel_cand")



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

    modo_geracao = st.radio("Selecione como deseja preencher as cartas nas 8 casas:", ["Manual (Preenchimento Direto)", "Automático (Assistente Especialista com Regras Metodológicas)"], key="radio_modo_tarot")



    if modo_geracao == "Automático (Assistente Especialista com Regras Metodológicas)":

        if st.button("🎲 Executar Sorteio e Cálculo Inteligente via Regras"):

            cartas_embaralhadas = random.sample(DECK_TAROT, len(DECK_TAROT))

            idx = 0

            for i in range(1, 9):

                c_cent = cartas_embaralhadas[idx % len(DECK_TAROT)]; idx += 1

                c_neg = cartas_embaralhadas[idx % len(DECK_TAROT)]; idx += 1

                c_pos = cartas_embaralhadas[idx % len(DECK_TAROT)]; idx += 1

                st.session_state[f"t_central_{i}"] = c_cent

                st.session_state[f"t_negativa_{i}"] = c_neg

                st.session_state[f"t_positiva_{i}"] = c_pos

                st.session_state[f"t_pontos_{i}"] = calcular_nota_metodologica(i, c_cent, c_neg, c_pos)

            st.success("Sorteio e atribuição de notas concluídos com sucesso!")

            st.rerun()



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



    pontuacoes_t1 = [st.session_state.get(f"t_pontos_{i}", 3) for i in range(1, 9)]

    total_t1 = sum(pontuacoes_t1)

    perc_t1 = (total_t1 / 40.0) * 100

    

    p6, p7, p8 = st.session_state.get("t_pontos_6", 3), st.session_state.get("t_pontos_7", 3), st.session_state.get("t_pontos_8", 3)

    sinal_vermelho_f1 = "Sim" if (p6 <= 2 or p7 <= 2 or p8 <= 2) else "Não"

    

    if total_t1 >= 32:

        classificacao_f1 = "Altamente Recomendado"

    elif total_t1 >= 24:

        classificacao_f1 = "Recomendado com Ressalvas"

    else:

        classificacao_f1 = "Não Recomendado"



    st.markdown("---")

    st.info(f"📊 **Resultado Individual da Fase 1 (Tarot):** {total_t1} / 40 pontos ({perc_t1:.1f}% de aderência comportamental)")



    c_nome_val = nome_candidato if 'nome_candidato' in locals() else st.session_state.get("input_nome_cand", "")

    cache_key_check = f"ai_analise_{c_nome_val}_{vaga_cargo}"

    

    if st.button("🤖 Gerar Análise Qualitativa por IA (Fase 1)"):
        with st.spinner("Consultando o Gemini para gerar o parecer completo das 8 casas..."):
            obter_ou_gerar_analise_ia(c_nome_val, vaga_cargo, arq_nome)
        st.success("Análise gerada e pronta para exportação!")
        st.rerun()



    def gerar_ficha_pdf_fase1(c_nome, c_vaga, total_pts, classif, sinal_vermelho_val):

        pdf = FPDF()

        pdf.add_page()

        pdf.set_auto_page_break(auto=True, margin=15)

        

        # Cabeçalho Executivo Compartimentalizado

        pdf.set_font("helvetica", "B", 11)

        pdf.cell(0, 6, sanitizar_pdf("FICHA DE AVALIAÇÃO PARA RECRUTAMENTO"), 0, 1, "C")

        pdf.set_font("helvetica", "I", 8)

        pdf.cell(0, 5, sanitizar_pdf("RELATÓRIO DE AVALIAÇÃO PSICOMÉTRICA E COMPORTAMENTAL (MÉTODO 8 CASAS)"), 0, 1, "C")

        pdf.ln(4)

        

        # Dados do Candidato em Caixa Compartimentalizada

        pdf.set_font("helvetica", "B", 8)

        pdf.set_fill_color(245, 247, 250)

        pdf.cell(0, 6, sanitizar_pdf(f"  CANDIDATO(A): {c_nome.upper() if c_nome else 'NÃO INFORMADO'}"), 1, 1, "L", True)

        pdf.cell(0, 6, sanitizar_pdf(f"  VAGA / CARGO: {c_vaga.upper() if c_vaga else 'NÃO INFORMADA'}          DATA: {datetime.now().strftime('%d/%m/%Y')}"), 1, 1, "L", True)

        pdf.ln(4)

        

        # Tabela das Casas (Fase 1) com altura adaptada e larguras robustas (evitando desalinhamentos)

        pdf.set_font("helvetica", "B", 8)

        pdf.set_fill_color(230, 235, 240)

        pdf.cell(8, 7, "POS", 1, 0, "C", True)

        pdf.cell(34, 7, "COMPETÊNCIA", 1, 0, "L", True)

        pdf.cell(64, 7, "CARTAS (CENTRAL / NEGATIVA / POSITIVA)", 1, 0, "L", True)

        pdf.cell(12, 7, "NOTA", 1, 0, "C", True)

        pdf.cell(70, 7, "OBSERVAÇÃO TÉCNICA", 1, 1, "L", True)

        

        competencias_nomes = [

            "Hard Skills", "Soft Skills", "Fit Cultural", 

            "Desafios", "Potencial Futuro", "Equilíbrio Emocional", 

            "Saúde Psicológica", "Confiabilidade e Ética"

        ]

        

        pdf.set_font("helvetica", "", 7.5)

        for i in range(1, 9):

            c_cent = st.session_state.get(f"t_central_{i}", "-")

            c_neg = st.session_state.get(f"t_negativa_{i}", "-")

            c_pos = st.session_state.get(f"t_positiva_{i}", "-")

            nota = st.session_state.get(f"t_pontos_{i}", 3)

            

            cartas_txt = f"Central: {c_cent} | Negativa: {c_neg} | Positiva: {c_pos}"

            obs_txt = f"Análise metodológica baseada no arcano (Nota {nota}/5)."

            

            # Altura padronizada de 15mm para acomodar confortavelmente o texto sem vazamento

            row_h = 15.0

            pdf.cell(8, row_h, str(i), 1, 0, "C")

            pdf.cell(34, row_h, sanitizar_pdf(competencias_nomes[i-1]), 1, 0, "L")

            

            x_pos_atual = pdf.get_x()

            y_pos_atual = pdf.get_y()

            pdf.rect(x_pos_atual, y_pos_atual, 64, row_h)

            pdf.set_xy(x_pos_atual + 1, y_pos_atual + 1.5)

            pdf.multi_cell(62, 3.8, sanitizar_pdf(cartas_txt), 0, "L")

            pdf.set_xy(x_pos_atual + 64, y_pos_atual)

            

            pdf.cell(12, row_h, str(nota), 1, 0, "C")

            pdf.cell(70, row_h, sanitizar_pdf(obs_txt), 1, 1, "L")

            

        pdf.ln(4)

        

        # Resumo Estatístico em Bloco Limpo

        pdf.set_font("helvetica", "B", 8)

        pdf.cell(0, 5, sanitizar_pdf(f"PONTUAÇÃO TOTAL: {total_pts} / 40  |  CLASSIFICAÇÃO: {classif}  |  SINAL VERMELHO: {sinal_vermelho_val}"), 0, 1, "L")

        pdf.ln(2)

        

        # Caixa Diferenciada e Compartimentalizada para o Parecer Final do Avaliador

        pdf.set_font("helvetica", "B", 8)

        pdf.cell(0, 5, sanitizar_pdf("PARECER FINAL DO AVALIADOR:"), 0, 1)

        pdf.set_font("helvetica", "", 8)

        parecer_ficha = (

            f"Perfil avaliado para a vaga de {c_vaga or 'Geral'}. O candidato atinge {total_pts} pontos no total, "

            f"enquadrando-se na diretriz de '{classif}'. A avaliação reflete o alinhamento comportamental e estrutural mapeado."

        )

        pdf.set_fill_color(248, 249, 250)

        pdf.set_draw_color(200, 205, 210)

        pdf.multi_cell(0, 5, sanitizar_pdf(parecer_ficha), border=1, fill=True)

        pdf.ln(6)



        # Seção de Análise Qualitativa Detalhada em Layout de Cartões Executivos (Card-based Layout)

        pdf.add_page()

        pdf.set_font("helvetica", "B", 10)

        pdf.cell(0, 6, sanitizar_pdf("ANÁLISE QUALITATIVA DAS COMPETÊNCIAS (ANÁLISE DO JOGO)"), 0, 1, "L")

        pdf.ln(2)



        texto_ia = obter_ou_gerar_analise_ia(c_nome, c_vaga, arq_nome)



        for i in range(1, 9):

            if pdf.get_y() > 245:

                pdf.add_page()



            pdf.set_font("helvetica", "B", 8.5)

            pdf.set_fill_color(240, 243, 246)

            pdf.set_draw_color(200, 205, 210)



            nota_comp = st.session_state.get(f"t_pontos_{i}", 3)

            titulo_card = f"  {i}. {competencias_nomes[i-1]} (Nota: {nota_comp}/5)"

            pdf.cell(0, 5.5, sanitizar_pdf(titulo_card), 1, 1, "L", True)



            c_cent = st.session_state.get(f"t_central_{i}", "-")

            c_neg = st.session_state.get(f"t_negativa_{i}", "-")

            c_pos = st.session_state.get(f"t_positiva_{i}", "-")



            cartas_str = f"  Carta Central: {c_cent}   |   Carta Negativa: {c_neg}   |   Carta Positiva: {c_pos}"

            pdf.set_font("helvetica", "I", 7.5)

            pdf.cell(0, 4.5, sanitizar_pdf(cartas_str), "LR", 1, "L", False)



            padrao_busca = rf"{i}\.\s*{re.escape(competencias_nomes[i-1])}(.*?)(?=(?:\d+\.\s*[A-ZÀ-Ú]|$))"

            match = re.search(padrao_busca, texto_ia, re.DOTALL | re.IGNORECASE)

            if match:

                conteudo_comp = match.group(1).strip()

                conteudo_comp = re.sub(r"^[:\-–]\s*", "", conteudo_comp)

            else:

                conteudo_comp = f"Análise executiva para {competencias_nomes[i-1]} baseada na tiragem estruturada de arcanos."



            pdf.set_font("helvetica", "", 7.5)

            pdf.multi_cell(0, 3.8, sanitizar_pdf(conteudo_comp), "LRB", "L", False)

            pdf.ln(3)



        res = pdf.output(dest="S")

        return res.encode("latin1") if isinstance(res, str) else bytes(res)



    if cache_key_check in st.session_state:

        pdf_stream = gerar_ficha_pdf_fase1(c_nome_val, vaga_cargo, total_t1, classificacao_f1, sinal_vermelho_f1)

        st.download_button(

            label="📥 Baixar Ficha de Avaliação Completa em PDF",

            data=pdf_stream,

            file_name=f"Ficha_Avaliacao_Recrutamento_{(c_nome_val or 'Candidato').replace(' ', '_')}.pdf",

            mime="application/pdf"

        )

    else:

        st.info("💡 Clique no botão acima **'🤖 Gerar Análise Qualitativa por IA (Fase 1)'** para habilitar o download do PDF completo.")



with tab2:

    st.header("Fase 2: Motor Astrológico Ponderado & Trânsitos Atuais")

    st.markdown(f"**Arquétipo Ativo:** `{arq_nome}` — Cruzamento de pesos corporativos com as efemérides e trânsitos do ano corrente.")



    if not KERYKEION_DISPONIVEL:

        st.warning("⚠️ A biblioteca **kerykeion** não foi detectada.")



    col_astro1, col_astro2 = st.columns(2)

    with col_astro1:

        data_nasc_raw = st.text_input("Data de Nascimento (DD/MM/AAAA)", placeholder="02/05/1978", key="astro_data_raw")

        local_nasc = st.text_input("Local de Nascimento (Cidade/Estado)", placeholder="São Paulo, SP", key="astro_local")

    with col_astro2:

        hora_nasc = st.time_input("Horário de Nascimento", key="astro_hora")

        sistema_casas = st.selectbox("Sistema de Casas", ["Plácidus", "Koch", "Signo Inteiro"], key="astro_sistema")



    def calcular_mandala_ponderada_com_transitos(d_nasc_str, h_nasc, loc, pesos_dict):

        if not d_nasc_str or h_nasc is None or not loc or not loc.strip():

            st.error("⚠️ Preencha Data, Horário e Local de Nascimento.")

            return None, None, {}



        digits = "".join(filter(str.isdigit, d_nasc_str))

        if len(digits) != 8:

            st.error("❌ Formato de data inválido.")

            return None, None, {}



        try:

            d_nasc = datetime.strptime(digits, "%d%m%Y").date()

        except ValueError:

            st.error("❌ Data inválida.")

            return None, None, {}



        geolocator = Nominatim(user_agent="rh_astrology_dinamico_v2")

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

                subject = AstrologicalSubject(

                    name="Candidato", year=d_nasc.year, month=d_nasc.month, day=d_nasc.day,

                    hour=h_nasc.hour, minute=h_nasc.minute, city=loc, nation="BR",

                    lat=lat, lng=lon, tz_str="America/Sao_Paulo",

                )

                

                agora = datetime.now()

                transit_subject = AstrologicalSubject(

                    name="Transitos_Correntes", year=agora.year, month=agora.month, day=agora.day,

                    hour=agora.hour, minute=agora.minute, city=loc, nation="BR",

                    lat=lat, lng=lon, tz_str="America/Sao_Paulo",

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

                    "Solar": {"signo": sun_s, "grau": f"{int(sun_p % 30)}° {int((sun_p % 1) * 60)}'"},

                    "Ascendente": {"signo": asc_s, "grau": f"{int(asc_p % 30)}° {int((asc_p % 1) * 60)}'"},

                    "Lunar": {"signo": moon_s, "grau": f"{int(moon_p % 30)}° {int((moon_p % 1) * 60)}'"},

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

                        "grau": f"{int(pos % 30)}° {int((pos % 1) * 60)}'",

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

            "Solar": {"signo": signos[seed % 12], "grau": "12° 0'"},

            "Ascendente": {"signo": signos[(seed + 6) % 12], "grau": "8° 15'"},

            "Lunar": {"signo": signos[(seed + 3) % 12], "grau": "15° 30'"},

        }

        casas_res = {}

        for c in range(1, 13):

            sig = signos[(seed + c * 7) % 12]

            nb = calcular_nota_astrologica_casa(c, sig)

            p = pesos_dict.get(c, 1.0)

            casas_res[f"Casa {c}"] = {

                "signo": sig, "grau": "10°", "nota_base": nb, "peso": p,

                "clima": "Estável", "analise": f"Signo: {sig} | Nota Base: {nb}/5 | Peso: {p}x"

            }

        return casas_res, big_three, {}



    if st.button("Processar Mandala Ponderada & Trânsitos Atuais"):

        with st.spinner("Calculando efemérides natais, trânsitos atuais e aplicando matrizes..."):

            mandala, big_three, transitos = calcular_mandala_ponderada_com_transitos(data_nasc_raw, hora_nasc, local_nasc, arq_pesos)

            if mandala and big_three:

                st.session_state["mandala_calculada"] = mandala

                st.session_state["big_three_calculado"] = big_three

                st.session_state["transitos_calculados"] = transitos

                st.session_state["arq_utilizado"] = arq_nome

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

        soma_ponderada = sum([v["nota_base"] * v["peso"] for k, v in mandala_items])

        soma_pesos = sum([v["peso"] for k, v in mandala_items])

        media_ponderada = soma_ponderada / soma_pesos if soma_pesos > 0 else 4.0

        total_t2_ajustado = media_ponderada * 12

        perc_t2 = (total_t2_ajustado / 60.0) * 100



        st.info(f"🌟 **Resultado Ponderado & Conjuntural da Fase 2 ({st.session_state.get('arq_utilizado', 'Padrão')}):** {total_t2_ajustado:.1f} / 60 pontos ({perc_t2:.1f}% de aderência estrutural ajustada ao momento)")

        st.markdown("")



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



    if st.button("Gerar Ficha de Avaliação Integrada"):

        st.session_state["ficha_gerada"] = True



    if st.session_state.get("ficha_gerada", False):

        pontuacoes_t1 = [st.session_state.get(f"t_pontos_{i}", 3) for i in range(1, 9)]

        total_t1 = sum(pontuacoes_t1)

        perc_t1 = (total_t1 / 40.0) * 100



        mandala_dados = st.session_state.get("mandala_calculada", {})

        if mandala_dados:

            mandala_items = list(mandala_dados.items())

            soma_p = sum([v["nota_base"] * v["peso"] for k, v in mandala_items])

            soma_w = sum([v["peso"] for k, v in mandala_items])

            total_t2_ajustado = (soma_p / soma_w) * 12 if soma_w > 0 else 48.0

            perc_t2 = (total_t2_ajustado / 60.0) * 100

        else:

            total_t2_ajustado = 48.0

            perc_t2 = 80.0



        indice_global = (perc_t1 * 0.7) + (perc_t2 * 0.3)

        p6, p7, p8 = st.session_state.get("t_pontos_6", 3), st.session_state.get("t_pontos_7", 3), st.session_state.get("t_pontos_8", 3)

        sinal_vermelho = "Sim" if (p6 <= 2 or p7 <= 2 or p8 <= 2) else "Não"



        if indice_global >= 80:

            classificacao = "Altamente Recomendado (Aderência Superior a 80%)"

        elif indice_global >= 65:

            classificacao = "Recomendado com Ressalvas (Aderência entre 65% e 79%)"

        else:

            classificacao = "Não Recomendado (Abaixo de 65%: Riscos severos)"



        c_nome = st.session_state.get("input_nome_cand", "Candidato(a)")

        c_vaga = st.session_state.get("input_vaga_cand", "Cargo")

        c_nivel = st.session_state.get("input_nivel_cand", "Nível")

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



        st.markdown("---")

        sub_t1, sub_t2, sub_t3 = st.tabs(["Gráfico Radar & Parecer", "Cruzamento por Arquétipo", "Histórico do Projeto"])



        with sub_t1:

            categories = ["Hard Skills", "Soft Skills", "Fit Cultural", "Desafios", "Potencial Futuro", "Equilíbrio Emocional", "Saúde Psicológica", "Confiabilidade e Ética"]

            fig = go.Figure()

            fig.add_trace(go.Scatterpolar(r=pontuacoes_t1 + [pontuacoes_t1[0]], theta=categories + [categories[0]], fill="toself", name="Candidato", line_color="#00cc96", fillcolor="rgba(0, 204, 150, 0.25)"))

            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5], dtick=1), bgcolor="rgba(22, 26, 29, 0.6)"), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=380, showlegend=False)

            st.plotly_chart(fig, use_container_width=True)



            st.markdown("### Parecer Técnico Dinâmico & Conjuntural")

            st.write(f"Avaliação direcionada ao arquétipo **{arq_ativo_ficha}** para a posição de **{c_vaga}**. O cruzamento integra a análise comportamental e o ciclo conjuntural ativo de trânsitos, resultando em um **Índice Global de {indice_global:.1f}%** (*{classificacao}*).")



            def gerar_pdf_dinamico():

                pdf = FPDF()

                pdf.add_page()

                pdf.set_auto_page_break(auto=True, margin=15)

                

                # Cabeçalho do Laudo Completo

                pdf.set_font("helvetica", "B", 12)

                pdf.cell(0, 7, sanitizar_pdf("LAUDO DE DIAGNÓSTICO CORPORATIVO DINÂMICO"), 0, 1, "C")

                pdf.set_font("helvetica", "I", 9)

                pdf.cell(0, 5, sanitizar_pdf("Análise Comportamental, Estrutural e Conjuntural por Trânsitos"), 0, 1, "C")

                pdf.ln(4)



                # 1. Dados do Candidato em Caixa Compartimentalizada

                pdf.set_font("helvetica", "B", 9)

                pdf.set_fill_color(240, 243, 246)

                pdf.cell(0, 6, sanitizar_pdf(" 1. DADOS GERAIS E ENQUADRAMENTO"), 1, 1, "L", True)

                pdf.set_font("helvetica", "", 8.5)

                pdf.cell(0, 5, sanitizar_pdf(f"  Candidato(a): {c_nome}  |  Cargo: {c_vaga} ({c_nivel})"), 0, 1)

                pdf.cell(0, 5, sanitizar_pdf(f"  Arquétipo Aplicado: {arq_ativo_ficha}"), 0, 1)

                pdf.cell(0, 5, sanitizar_pdf(f"  Índice Global Integrado: {indice_global:.1f}% - {classificacao}"), 0, 1)

                pdf.ln(3)



                # 2. Parecer Executivo em Bloco de Destaque

                pdf.set_font("helvetica", "B", 9)

                pdf.cell(0, 6, sanitizar_pdf(" 2. PARECER EXECUTIVO E MOMENTO CONJUNTURAL"), 0, 1, "L")

                pdf.set_font("helvetica", "", 8)

                parecer_texto = (

                    f"O candidato apresenta um Índice Global de {indice_global:.1f}%, enquadrando-se na diretriz de "

                    f"'{classificacao}'. A avaliação cruza a base comportamental do Tarot (Fase 1: {perc_t1:.1f}%) "

                    f"com o mapa astrológico ponderado pelo arquétipo de {arq_ativo_ficha} e os trânsitos celestes correntes "

                    f"(Fase 2: {perc_t2:.1f}%). O modelo avalia não apenas a competência estrutural, mas o alinhamento "

                    f"com os ciclos de expansão ou cobrança ativa no período."

                )

                pdf.set_fill_color(248, 249, 250)

                pdf.set_draw_color(200, 205, 210)

                pdf.multi_cell(0, 4.5, sanitizar_pdf(parecer_texto), border=1, fill=True)

                pdf.ln(4)



                # 3. Análise Qualitativa Detalhada (IA) em Layout de Cartões Executivos

                pdf.add_page()

                pdf.set_font("helvetica", "B", 10)

                pdf.cell(0, 6, sanitizar_pdf(" 3. ANÁLISE QUALITATIVA DAS COMPETÊNCIAS (8 CASAS)"), 0, 1, "L")

                pdf.ln(2)

                

                texto_ia_laudo = obter_ou_gerar_analise_ia(c_nome, c_vaga, arq_ativo_ficha)

                competencias_nomes = [

                    "Hard Skills", "Soft Skills", "Fit Cultural", 

                    "Desafios", "Potencial Futuro", "Equilíbrio Emocional", 

                    "Saúde Psicológica", "Confiabilidade e Ética"

                ]



                for i in range(1, 9):

                    if pdf.get_y() > 245:

                        pdf.add_page()



                    pdf.set_font("helvetica", "B", 8.5)

                    pdf.set_fill_color(240, 243, 246)

                    pdf.set_draw_color(200, 205, 210)



                    nota_comp = st.session_state.get(f"t_pontos_{i}", 3)

                    titulo_card = f"  {i}. {competencias_nomes[i-1]} (Nota: {nota_comp}/5)"

                    pdf.cell(0, 5.5, sanitizar_pdf(titulo_card), 1, 1, "L", True)



                    c_cent = st.session_state.get(f"t_central_{i}", "-")

                    c_neg = st.session_state.get(f"t_negativa_{i}", "-")

                    c_pos = st.session_state.get(f"t_positiva_{i}", "-")



                    cartas_str = f"  Carta Central: {c_cent}   |   Carta Negativa: {c_neg}   |   Carta Positiva: {c_pos}"

                    pdf.set_font("helvetica", "I", 7.5)

                    pdf.cell(0, 4.5, sanitizar_pdf(cartas_str), "LR", 1, "L", False)



                    padrao_busca = rf"{i}\.\s*{re.escape(competencias_nomes[i-1])}(.*?)(?=(?:\d+\.\s*[A-ZÀ-Ú]|$))"

                    match = re.search(padrao_busca, texto_ia_laudo, re.DOTALL | re.IGNORECASE)

                    if match:

                        conteudo_comp = match.group(1).strip()

                        conteudo_comp = re.sub(r"^[:\-–]\s*", "", conteudo_comp)

                    else:

                        conteudo_comp = f"Análise executiva para {competencias_nomes[i-1]} baseada na tiragem estruturada de arcanos."



                    pdf.set_font("helvetica", "", 7.5)

                    pdf.multi_cell(0, 3.8, sanitizar_pdf(conteudo_comp), "LRB", "L", False)

                    pdf.ln(3)



                # 4. Mapa Astrológico Ponderado (12 Casas) com Larguras Ajustadas

                pdf.add_page()

                pdf.set_font("helvetica", "B", 9)

                pdf.cell(0, 6, sanitizar_pdf(" 4. MAPA ASTROLÓGICO PONDERADO (12 CASAS)"), 0, 1, "L")

                pdf.set_font("helvetica", "B", 8)

                pdf.set_fill_color(220, 225, 230)

                pdf.cell(14, 6, "Casa", 1, 0, "C", True)

                pdf.cell(42, 6, "Signo (Cúspide)", 1, 0, "L", True)

                pdf.cell(18, 6, "Nota Base", 1, 0, "C", True)

                pdf.cell(18, 6, "Peso Arq.", 1, 0, "C", True)

                pdf.cell(98, 6, "Clima de Trânsito / Análise", 1, 1, "L", True)



                pdf.set_font("helvetica", "", 7.5)

                mandala_dados = st.session_state.get("mandala_calculada", {})

                for k_casa, d_val in mandala_dados.items():

                    signo_str = f"{d_val.get('signo', '')} ({d_val.get('grau', '')})"

                    clima_str = d_val.get('clima', '')

                    pdf.cell(14, 5.5, k_casa.replace("Casa ", ""), 1, 0, "C")

                    pdf.cell(42, 5.5, sanitizar_pdf(signo_str), 1, 0, "L")

                    pdf.cell(18, 5.5, str(d_val.get('nota_base', '')), 1, 0, "C")

                    pdf.cell(18, 5.5, f"{d_val.get('peso', '')}x", 1, 0, "C")

                    pdf.cell(98, 5.5, sanitizar_pdf(clima_str), 1, 1, "L")

                pdf.ln(4)



                res = pdf.output(dest="S")

                return res.encode("latin1") if isinstance(res, str) else bytes(res)



            col_a1, col_a2 = st.columns(2)

            with col_a1:

                st.download_button("📄 Baixar Laudo Ponderado Completo em PDF", data=gerar_pdf_dinamico(), file_name=f"Laudo_Integrado_{c_nome.replace(' ', '_')}.pdf", mime="application/pdf")

            with col_a2:

                if st.button("💾 Salvar no Banco Dinâmico (SQLite)"):

                    if c_nome in ["", "Candidato(a)"]:

                        st.error("Informe um nome de candidato válido.")

                    else:

                        ok = salvar_no_banco(c_nome, vaga_cargo, nivel_hierarquico, data_atual, int(indice_global), classificacao, sinal_vermelho, arq_ativo_ficha)

                        if ok: st.success("✅ Salvo com sucesso no banco de dados!")



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

                s_info = "Não calculado"

                clima_info = ""

                if f"Casa {an}" in mandala_dados:

                    d_casa = mandala_dados[f"Casa {an}"]

                    s_info = f"{d_casa['signo']} (Peso: {d_casa['peso']}x)"

                    clima_info = f" | {d_casa['clima']}"

                st.write(f"- **{tnom} (Tarot Casa {tn})** $\leftrightarrow$ **{adesc}**: Cúspide: **{s_info}**{clima_info}")



        with sub_t3:

            with sqlite3.connect("rh_diagnostico_dinamico.db") as conn_db:

                df_hist = pd.read_sql_query("SELECT id, nome, vaga, nivel, data, pontos, classificacao, sinal_vermelho, arquétipo FROM avaliacoes", conn_db)

            if not df_hist.empty:

                st.dataframe(df_hist, use_container_width=True, hide_index=True)

            else:

                st.info("Nenhum registro no banco dinâmico.")