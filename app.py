from datetime import datetime
import io
import random
import sqlite3
from fpdf import FPDF
from geopy.geocoders import Nominatim
import pandas as pd
import plotly.graph_objects as go
import pytz
import streamlit as st

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

def calcular_nota_astrologica_casa(casa_num, signo_nome):
    elemento_signo = ELEMENTOS_SIGNOS.get(signo_nome, "Terra")
    prefs = PREFERENCIA_ELEMENTO_CASA.get(casa_num, ["Terra"])
    if elemento_signo in prefs:
        return 5
    return 4

def classificar_arquétipo(vaga_texto):
    if not vaga_texto or not vaga_texto.strip():
        return "Padrão / Geral", {i: 1.0 for i in range(1, 13)}
    
    txt = vaga_texto.lower()
    termos_inovacao = [
        "inovação", "inovacao", "estratégia", "estrategia", "expansão", "expansao",
        "planejamento", "transformação", "transformacao", "digital", "negócios",
        "negocios", "head", "diretor", "produtos", "futuro"
    ]
    termos_governanca = [
        "compliance", "auditoria", "jurídico", "juridico", "risco", "riscos",
        "controladoria", "governança", "governanca", "financeiro", "regulatório",
        "regulatorio", "processos", "contábil", "contabil", "qualidade", "segurança"
    ]
    
    score_inov = sum(1 for t in termos_inovacao if t in txt)
    score_gov = sum(1 for t in termos_governanca if t in txt)
    
    if score_inov > score_gov:
        return "Inovação, Estratégia e Expansão", {
            1: 1.2, 2: 0.9, 3: 1.0, 4: 0.9, 5: 1.5, 6: 0.8, 7: 1.0, 8: 0.8, 9: 1.5, 10: 1.3, 11: 1.3, 12: 1.0
        }
    elif score_gov > score_inov:
        return "Governança, Compliance e Riscos", {
            1: 0.9, 2: 1.4, 3: 1.0, 4: 1.2, 5: 0.8, 6: 1.4, 7: 1.3, 8: 1.5, 9: 0.9, 10: 1.1, 11: 1.0, 12: 1.4
        }
    else:
        return "Padrão / Geral", {i: 1.0 for i in range(1, 13)}

ATIVADORES_NOTA_5 = {
    1: ["O Mago", "Rei de Ouros", "Rainha de Espadas"],
    2: ["A Imperatriz", "Rei de Paus", "Rainha de Copas"],
    3: ["O Hierofante", "Rei de Ouros", "Rainha de Copas"],
    4: ["O Mundo", "Rei de Ouros", "Rainha de Ouros"],
    5: ["O Imperador", "Rei de Ouros", "Rainha de Paus"],
    6: ["A Força", "Rei de Copas", "Rainha de Ouros"],
    7: ["A Estrela", "Rei de Espadas", "Rainha de Espadas"],
    8: ["A Justiça", "Rei de Espadas", "Rainha de Ouros"],
}

FALSOS_POSITIVOS = {
    1: ["O Pendurado"], 2: ["O Eremita"], 3: ["O Louco"], 4: ["O Sol"],
    5: ["A Sacerdotisa", "A Papisa"], 6: ["Os Enamorados", "Os Amantes"],
    7: ["A Temperança"], 8: ["O Carro"],
}

ALERTAS_IMATURIDADE = {
    1: ["Pajem de Paus", "Pajem de Ouros", "Pajem de Espadas", "Pajem de Copas"],
    2: ["Cavaleiro de Espadas"], 3: ["Cavaleiro de Copas"],
    4: ["Pajem de Ouros"], 5: ["Pajem de Espadas"],
    6: ["Cavaleiro de Paus"], 7: ["Cavaleiro de Ouros"], 8: ["Pajem de Copas"],
}

OBS_MAP = {
    1: "Apresenta padrão esperado para condução das rotinas e competências técnicas atribuídas.",
    2: "Boa capacidade de comunicação e integração colaborativa com o time.",
    3: "Alinhamento adequado aos valores e princípios coletivos da organização.",
    4: "Gerenciamento funcional dos pontos cegos e riscos operacionais.",
    5: "Projeção consistente de autonomia e entregas de médio e longo prazo.",
    6: "Estabilidade emocional adequada para absorção das demandas sob pressão.",
    7: "Foco cognitivo preservado e boa resiliência frente a cenários de exaustão.",
    8: "Comprometimento ético satisfatório e respeito aos acordos firmados.",
}

def calcular_nota_metodologica(casa_num, c_cent, c_neg, c_pos):
    nota_base = 3
    cent_limpo = str(c_cent).strip().lower() if c_cent else ""
    neg_limpo = str(c_neg).strip().lower() if c_neg else ""
    pos_limpo = str(c_pos).strip().lower() if c_pos else ""

    if any(atrib.lower() in cent_limpo for atrib in ATIVADORES_NOTA_5.get(casa_num, [])):
        nota_base = 5
    elif any(fp.lower() in cent_limpo for fp in FALSOS_POSITIVOS.get(casa_num, [])):
        nota_base = 2
    elif any(imato.lower() in cent_limpo for imato in ALERTAS_IMATURIDADE.get(casa_num, [])):
        nota_base = 1

    if casa_num == 1 and any(k in pos_limpo for k in ["ouros", "espadas", "mago"]):
        if nota_base < 5:
            nota_base += 1

    if any(k in neg_limpo for k in ["torre", "diabo", "cinco de ouros", "oito de espadas", "nove de espadas", "dez de espadas"]):
        if nota_base > 1:
            nota_base -= 1

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
    if not nome or not nome.strip() or nome.strip() in ["Candidato(a)", "Selecionar Candidato Cadastrado..."]:
        return False
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

if "astro_data_raw" not in st.session_state:
    st.session_state["astro_data_raw"] = "01/01/1999"
if "astro_local" not in st.session_state:
    st.session_state["astro_local"] = "São Paulo, SP"
if "astro_hora" not in st.session_state:
    st.session_state["astro_hora"] = datetime.strptime("12:00", "%H:%M").time()
if "input_nome_cand" not in st.session_state:
    st.session_state["input_nome_cand"] = ""

def disparar_nova_avaliacao():
    st.session_state["input_nome_cand"] = ""
    st.session_state["input_vaga_cand"] = ""
    st.session_state["input_nivel_cand"] = "C-Level / Executivo"
    st.session_state["astro_data_raw"] = "01/01/1999"
    st.session_state["astro_hora"] = datetime.strptime("12:00", "%H:%M").time()
    st.session_state["astro_local"] = "São Paulo, SP"
    st.session_state["ficha_gerada"] = False
    if "mandala_calculada" in st.session_state:
        del st.session_state["mandala_calculada"]
    if "big_three_calculado" in st.session_state:
        del st.session_state["big_three_calculado"]
    for i in range(1, 9):
        st.session_state[f"t_central_{i}"] = ""
        st.session_state[f"t_negativa_{i}"] = ""
        st.session_state[f"t_positiva_{i}"] = ""
        st.session_state[f"t_pontos_{i}"] = 3
    st.rerun()

st.title("Sistema de Diagnóstico Corporativo Dinâmico: Tarot & Astrologia Ponderada")
st.markdown(
    "Plataforma avançada com classificação semântica de cargos, pesos dinâmicos por arquétipo de vaga e motor astronômico real (Kerykeion)."
)

tab1, tab2, tab3 = st.tabs([
    "1. Cadastro e Avaliação (Tarot 8 Casas)",
    "2. Mapeamento Astrológico Dinâmico (12 Casas)",
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

    # Detecção automática do arquétipo corporativo
        arq_nome, arq_pesos = classificar_arquétipo(vaga_cargo)
    st.info(f"🎯 **Arquétipo Corporativo Detectado Automaticamente:** `{arq_nome}` (Aplicando pesos customizados na Fase 2)")

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
                st.text_input("Arcano Central (Resposta)", key=f"t_central_{num}", placeholder="Ex: O Mago")
                st.text_input("Carta Negativa (Dificuldades)", key=f"t_negativa_{num}", placeholder="Ex: Ás de Ouros")
                st.text_input("Carta Positiva (Pontos Fortes)", key=f"t_positiva_{num}", placeholder="Ex: 4 de Copas")
                st.number_input("Nota (1-5)", min_value=1, max_value=5, value=3, key=f"t_pontos_{num}")

    pontuacoes_t1 = [st.session_state.get(f"t_pontos_{i}", 3) for i in range(1, 9)]
    total_t1 = sum(pontuacoes_t1)
    perc_t1 = (total_t1 / 40.0) * 100
    st.markdown("---")
    st.info(f"📊 **Resultado Individual da Fase 1 (Tarot):** {total_t1} / 40 pontos ({perc_t1:.1f}% de aderência comportamental)")

with tab2:
    st.header("Fase 2: Motor Astrológico Ponderado por Arquétipo de Vaga")
    st.markdown(f"**Arquétipo Ativo:** `{arq_nome}` — As 12 casas astrológicas recebem pesos diferenciados conforme a prioridade da cadeira.")

    if not KERYKEION_DISPONIVEL:
        st.warning("⚠️ A biblioteca **kerykeion** não foi detectada.")

    col_astro1, col_astro2 = st.columns(2)
    with col_astro1:
        data_nasc_raw = st.text_input("Data de Nascimento (DD/MM/AAAA)", placeholder="02/05/1978", key="astro_data_raw")
        local_nasc = st.text_input("Local de Nascimento (Cidade/Estado)", placeholder="São Paulo, SP", key="astro_local")
    with col_astro2:
        hora_nasc = st.time_input("Horário de Nascimento", key="astro_hora")
        sistema_casas = st.selectbox("Sistema de Casas", ["Plácidus", "Koch", "Signo Inteiro"], key="astro_sistema")

    def calcular_mandala_ponderada(d_nasc_str, h_nasc, loc, pesos_dict):
        if not d_nasc_str or h_nasc is None or not loc or not loc.strip():
            st.error("⚠️ Preencha Data, Horário e Local de Nascimento.")
            return None, None

        digits = "".join(filter(str.isdigit, d_nasc_str))
        if len(digits) != 8:
            st.error("❌ Formato de data inválido.")
            return None, None

        try:
            d_nasc = datetime.strptime(digits, "%d%m%Y").date()
        except ValueError:
            st.error("❌ Data inválida.")
            return None, None

        geolocator = Nominatim(user_agent="rh_astrology_dinamico_v1")
        lat, lon = None, None
        try:
            loc_obj = geolocator.geocode(loc)
            if loc_obj:
                lat, lon = loc_obj.latitude, loc_obj.longitude
            else:
                st.error(f"❌ Coordenadas não encontradas para '{loc}'.")
                return None, None
        except Exception as e:
            st.error(f"❌ Erro de geolocalização: {e}")
            return None, None

        if KERYKEION_DISPONIVEL:
            try:
                subject = AstrologicalSubject(
                    name="Candidato", year=d_nasc.year, month=d_nasc.month, day=d_nasc.day,
                    hour=h_nasc.hour, minute=h_nasc.minute, city=loc, nation="BR",
                    lat=lat, lng=lon, tz_str="America/Sao_Paulo",
                )
                def extrair_signo_grau(obj_attr):
                    if not obj_attr:
                        return "Desconhecido", 0.0
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

                casas_res = {}
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
                    peso_casa = pesos_dict.get(i, 1.0)
                    
                    casas_res[f"Casa {i}"] = {
                        "signo": signo,
                        "grau": f"{int(pos % 30)}° {int((pos % 1) * 60)}'",
                        "nota_base": nota_base_casa,
                        "peso": peso_casa,
                        "analise": f"Signo: {signo} | Nota Base: {nota_base_casa}/5 | Peso Arquétipo: {peso_casa}x",
                    }
                return casas_res, big_three
            except Exception as e:
                st.error(f"Erro no cálculo Kerykeion: {e}")
                return None, None

        # Fallback determinístico
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
                "analise": f"Signo: {sig} | Nota Base: {nb}/5 | Peso: {p}x"
            }
        return casas_res, big_three

    if st.button("Processar Mandala Ponderada por Arquétipo"):
        with st.spinner("Calculando efemérides e aplicando matriz de pesos..."):
            mandala, big_three = calcular_mandala_ponderada(data_nasc_raw, hora_nasc, local_nasc, arq_pesos)
            if mandala and big_three:
                st.session_state["mandala_calculada"] = mandala
                st.session_state["big_three_calculado"] = big_three
                st.session_state["arq_utilizado"] = arq_nome
                st.success("Mapeamento astrológico dinâmico concluído com sucesso!")

    if "mandala_calculada" in st.session_state:
        if "big_three_calculado" in st.session_state:
            b3 = st.session_state["big_three_calculado"]
            st.markdown("### Trindade Principal")
            cb1, cb2, cb3 = st.columns(3)
            with cb1: st.metric("Signo Solar", b3['Solar']['signo'], b3['Solar']['grau'])
            with cb2: st.metric("Signo Ascendente", b3['Ascendente']['signo'], b3['Ascendente']['grau'])
            with cb3: st.metric("Signo Lunar", b3['Lunar']['signo'], b3['Lunar']['grau'])
            st.markdown("")

        mandala_items = list(st.session_state["mandala_calculada"].items())
        
        # Cálculo ponderado normalizado para escala de 60 pontos
        soma_ponderada = sum([v["nota_base"] * v["peso"] for k, v in mandala_items])
        soma_pesos = sum([v["peso"] for k, v in mandala_items])
        media_ponderada = soma_ponderada / soma_pesos if soma_pesos > 0 else 4.0
        total_t2_ajustado = media_ponderada * 12
        perc_t2 = (total_t2_ajustado / 60.0) * 100

        st.info(f"🌟 **Resultado Ponderado da Fase 2 ({st.session_state.get('arq_utilizado', 'Padrão')}):** {total_t2_ajustado:.1f} / 60 pontos ({perc_t2:.1f}% de aderência estrutural ajustada à vaga)")
        st.markdown("")

        for idx_linha in range(0, len(mandala_items), 3):
            cols_grid = st.columns(3)
            for col_idx in range(3):
                if idx_linha + col_idx < len(mandala_items):
                    k, v = mandala_items[idx_linha + col_idx]
                    with cols_grid[col_idx]:
                        with st.container(border=True):
                            st.markdown(f"**{k}** *(Base: {v['nota_base']} | Peso: {v['peso']}x)*")
                            st.markdown(f"### {v['signo']} `({v['grau']})`")
                            st.caption(v['analise'])
    else:
        st.info("Processe a mandala astrológica para visualizar o resultado ponderado.")

with tab3:
    st.header("Fase 3: FICHA DE AVALIAÇÃO INTEGRADA E PONDERADA")
    st.markdown("Governança final cruzando o Tarot, a Astrologia Ponderada pelo Arquétipo da Vaga e o Índice Global.")

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
        with cr2: st.metric("Fase 2 (Astrologia Ponderada)", f"{total_t2_ajustado:.1f} / 60", f"{perc_t2:.1f}%")
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

            st.markdown("### Parecer Técnico Dinâmico")
            st.write(f"Avaliação direcionada ao arquétipo **{arq_ativo_ficha}** para a posição de **{c_vaga}**. O cruzamento aponta **{perc_t1:.1f}%** na Fase 1 e **{perc_t2:.1f}%** na Fase 2 ponderada, resultando em um **Índice Global de {indice_global:.1f}%** (*{classificacao}*).")

            def gerar_pdf_dinamico():
                pdf = FPDF()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.set_font("helvetica", "B", 11)
                pdf.cell(0, 7, "DIAGNOSTICO CORPORATIVO DINAMICO - LAUDO PONDERADO", 0, 1, "C")
                pdf.set_font("helvetica", "", 8)
                pdf.cell(0, 4, f"Arquétipo Aplicado: {arq_ativo_ficha}", 0, 1, "C")
                pdf.ln(3)
                pdf.set_font("helvetica", "B", 9)
                pdf.cell(0, 5, f"Candidato(a): {c_nome}", 0, 1)
                pdf.cell(0, 5, f"Cargo: {c_vaga} | Nível: {c_nivel}", 0, 1)
                pdf.cell(0, 5, f"Índice Global: {indice_global:.1f}% | {classificacao}", 0, 1)
                pdf.ln(4)
                pdf.set_font("helvetica", "B", 8)
                pdf.cell(8, 5, "Pos", 1, 0, "C", True)
                pdf.cell(37, 5, "Competencia", 1, 0, "L", True)
                pdf.cell(12, 5, "Nota", 1, 0, "C", True)
                pdf.cell(123, 5, "Arcanos", 1, 1, "L", True)
                
                competencias_nomes = ["Hard Skills", "Soft Skills", "Fit Cultural", "Desafios", "Potencial Futuro", "Equilíbrio Emocional", "Saúde Psicológica", "Confiabilidade e Ética"]
                pdf.set_font("helvetica", "", 8)
                for i in range(1, 9):
                    c_cent = st.session_state.get(f"t_central_{i}", "-")
                    nota = st.session_state.get(f"t_pontos_{i}", 3)
                    pdf.cell(8, 5, str(i), 1, 0, "C")
                    pdf.cell(37, 5, competencias_nomes[i-1], 1, 0, "L")
                    pdf.cell(12, 5, str(nota), 1, 0, "C")
                    pdf.cell(123, 5, f"Central: {c_cent}", 1, 1, "L")
                
                res = pdf.output(dest="S")
                return res.encode("latin1") if isinstance(res, str) else bytes(res)

            col_a1, col_a2 = st.columns(2)
            with col_a1:
                st.download_button("📄 Baixar Laudo Ponderado em PDF", data=gerar_pdf_dinamico(), file_name=f"Laudo_Dinamico_{c_nome.replace(' ', '_')}.pdf", mime="application/pdf")
            with col_a2:
                if st.button("💾 Salvar no Banco Dinâmico (SQLite)"):
                    if c_nome in ["", "Candidato(a)"]:
                        st.error("Informe um nome de candidato válido.")
                    else:
                        ok = salvar_no_banco(c_nome, vaga_cargo, nivel_hierarquico, data_atual, int(indice_global), classificacao, sinal_vermelho, arq_ativo_ficha)
                        if ok: st.success("✅ Salvo com sucesso no banco de dados do projeto dinâmico!")

        with sub_t2:
            st.markdown("### Cruzamento entre Tarot e Astrologia Ponderada")
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
                if f"Casa {an}" in mandala_dados:
                    d_casa = mandala_dados[f"Casa {an}"]
                    s_info = f"{d_casa['signo']} (Peso: {d_casa['peso']}x)"
                st.write(f"- **{tnom} (Tarot Casa {tn})** $\leftrightarrow$ **{adesc}**: Signo cuspide: **{s_info}**")

        with sub_t3:
            with sqlite3.connect("rh_diagnostico_dinamico.db") as conn_db:
                df_hist = pd.read_sql_query("SELECT id, nome, vaga, nivel, data, pontos, classificacao, sinal_vermelho, arquétipo FROM avaliacoes", conn_db)
            if not df_hist.empty:
                st.dataframe(df_hist, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum registro no banco dinâmico.")