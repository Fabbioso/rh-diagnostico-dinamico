import os
import math
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from fpdf import FPDF, XPos, YPos
from core.constants import COMPETENCIAS_FASE_1

def sanitizar_pdf(texto: Any) -> str:
    """Normaliza strings removendo markdown, sintaxe LaTeX e caracteres incompatíveis com latin-1."""
    if not texto:
        return ""
    txt = str(texto)
    txt = re.sub(r"\$([^\$]+)\$", r"\1", txt)
    txt = txt.replace("$", "")
    txt = re.sub(r"^#{1,6}\s*", "", txt, flags=re.MULTILINE)
    txt = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", txt)
    txt = re.sub(r"_{1,3}(.*?)_{1,3}", r"\1", txt)
    txt = txt.replace("**", "").replace("*", "")
    subs = {
        "—": "-", "–": "-", "“": '"', "”": '"', "‘": "'", "’": "'",
        "•": "-", "…": "...", "→": "->", "←": "<-", "º": chr(186), "ª": "a",
        "`": "", "☐": "", "☑": "", "☒": ""
    }
    for orig, dest in subs.items():
        txt = txt.replace(orig, dest)
    txt = txt.replace("°", chr(186)).replace("deg", chr(186))
    txt = re.sub(r"[ \t]+", " ", txt)
    txt = re.sub(r"[^\x00-\xFF]", "", txt)
    try:
        return txt.encode("latin-1", "replace").decode("latin-1")
    except Exception:
        return str(txt)

def quebrar_texto_em_linhas(pdf: FPDF, texto: Any, largura_max: float, tam_fonte: float = 7.0) -> List[str]:
    """Segmenta o texto em linhas proporcionais para caber nas colunas da tabela."""
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

def renderizar_item_analise(pdf: FPDF, label_prefix: str, nome_carta: str, texto_corpo: str, largura_bloco: float) -> float:
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

def extrair_justificativa_ia(texto_ia_doc: str) -> str:
    """Extrai a justificativa executiva do texto fornecido pela IA."""
    if not texto_ia_doc:
        return ""
    linhas_ia = str(texto_ia_doc).splitlines()
    capturando = False
    buffer_justificativa = []

    for l_orig in linhas_ia:
        l_limpa = re.sub(r"[\*\_#`]", "", l_orig).strip()
        l_upper = l_limpa.upper()

        if "JUSTIFICATIVA EXECUTIVA" in l_upper:
            capturando = True
            partes = re.split(r"JUSTIFICATIVA\s+EXECUTIVA\s*[:\-–—]", l_limpa, flags=re.IGNORECASE)
            if len(partes) > 1 and partes[1].strip():
                buffer_justificativa.append(partes[1].strip())
            continue

        if capturando:
            if any(l_upper.startswith(pref) for pref in ["FORÇAS PRINCIPAIS", "FORCAS PRINCIPAIS", "FOCOS DE RESSALVA", "PARECER FINAL", "---"]):
                break
            if l_limpa:
                buffer_justificativa.append(l_limpa)

    if buffer_justificativa:
        return " ".join(buffer_justificativa).strip()

    m_concl = re.search(
        r"(?:CONCLUS[ÃÃO]|JUSTIFICATIVA\s*EXECUTIVA)(.*?)(?=(?:For[çc]as\s*principais|Focos\s*de\s*ressalva|\Z))",
        texto_ia_doc,
        re.DOTALL | re.IGNORECASE,
    )
    if m_concl:
        cand = m_concl.group(1).strip()
        cand = re.sub(r"^[\s\S]*?JUSTIFICATIVA\s*EXECUTIVA\s*[:\-\–\—]*", "", cand, flags=re.IGNORECASE)
        cand = re.sub(r"^[\s\S]*?PARECER\s*FINAL\s*:[^\n]+\n*", "", cand, flags=re.IGNORECASE)
        cand = re.sub(r"[\*\_#`]", "", cand).strip()
        if len(cand) > 30:
            return re.sub(r"\s+", " ", cand).strip()
    return ""

def gerar_ficha_pdf_fase1(
    c_nome: str,
    c_vaga: str,
    c_nivel: str,
    total_pts: float,
    perc_t1: float,
    classif: str,
    sinal_vermelho_val: Any,
    texto_ia_doc: str,
    dados_casas: List[Dict[str, Any]],
) -> bytes:
    """Gera o laudo completo em PDF da Fase 1 (Método 8 Casas) sem acoplamento com a interface gráfica."""
    veto_governanca = sinal_vermelho_val in ["Sim", True]
    classif_efetiva = "Não Recomendado (Veto de Governança)" if veto_governanca else classif

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)

    # =========================================================================
    # PÁGINA 1: CABEÇALHO, TABELA MATRIZ E SUMÁRIO EXECUTIVO
    # =========================================================================
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 6, sanitizar_pdf("FICHA DE AVALIAÇÃO PARA RECRUTAMENTO"), border=0, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("helvetica", "I", 8)
    pdf.cell(0, 5, sanitizar_pdf("RELATÓRIO DE AVALIAÇÃO PSICOMÉTRICA E COMPORTAMENTAL (MÉTODO 8 CASAS)"), border=0, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)

    pdf.set_font("helvetica", "B", 8)
    pdf.set_fill_color(245, 247, 250)
    pdf.cell(0, 5.5, sanitizar_pdf(f"   CANDIDATO(A): {c_nome.upper() if c_nome else 'NÃO INFORMADO'}"), border=1, align="L", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 5.5, sanitizar_pdf(f"   VAGA / CARGO: {c_vaga.upper() if c_vaga else 'NÃO INFORMADA'} ({c_nivel.upper() if c_nivel else 'PLENO'})          DATA: {datetime.now().strftime('%d/%m/%Y')}"), border=1, align="L", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)

    w_pos = 8
    w_comp = 28
    w_cart = 62
    w_nota = 10
    w_sint = 82

    pdf.set_font("helvetica", "B", 7.5)
    pdf.set_fill_color(230, 235, 240)
    pdf.cell(w_pos, 6, "POS", border=1, align="C", fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(w_comp, 6, "COMPETÊNCIA", border=1, align="L", fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(w_cart, 6, "CARTAS (CENTRAL / NEGATIVA / POSITIVA)", border=1, align="L", fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(w_nota, 6, "NOTA", border=1, align="C", fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(w_sint, 6, "RESUMO DA LEITURA", border=1, align="L", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    cursor_y = pdf.get_y()

    for idx, item in enumerate(dados_casas, start=1):
        num_pos = item.get("pos", idx)
        nome_comp = item.get("nome", COMPETENCIAS_FASE_1[idx - 1] if idx <= len(COMPETENCIAS_FASE_1) else f"Casa {idx}")
        c_cent = item.get("central", "-")
        c_neg = item.get("negativa", "-")
        c_pos = item.get("positiva", "-")
        nota = item.get("nota", 3)
        obs_txt = item.get("resumo", "Avaliação metodológica integrada.")

        cartas_txt = f"Carta Central: {c_cent}\nCarta Negativa: {c_neg}\nCarta Positiva: {c_pos}"

        linhas_comp = quebrar_texto_em_linhas(pdf, nome_comp, w_comp, tam_fonte=7)
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
        pdf.text(10 + (w_pos / 2) - 1.2, cursor_y + (h_linha / 2) + 1.2, str(num_pos))

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
    pdf.cell(0, 5, sanitizar_pdf(f"PONTUAÇÃO TOTAL: {total_pts} / 40  |  CLASSIFICAÇÃO: {classif_efetiva}  |  SINAL VERMELHO: {sinal_vermelho_val}"), border=0, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(1.5)

    pdf.set_font("helvetica", "B", 8)
    pdf.cell(0, 4.5, sanitizar_pdf("PARECER FINAL DO AVALIADOR:"), border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("helvetica", "", 7.5)

    notas_competencias = {
        item.get("nome", COMPETENCIAS_FASE_1[i - 1]): float(item.get("nota", 3))
        for i, item in enumerate(dados_casas, start=1)
    }
    maiores_forcas = sorted(notas_competencias.items(), key=lambda x: x[1], reverse=True)[:2]
    focos_ressalva = sorted(notas_competencias.items(), key=lambda x: x[1])[:2]
    forcas_txt = ", ".join(f"{nome} ({nota:.0f}/5)" for nome, nota in maiores_forcas)
    ressalvas_txt = ", ".join(f"{nome} ({nota:.0f}/5)" for nome, nota in focos_ressalva)
    deliberacao_txt = (
        "deliberação desfavorável, com veto de governança"
        if veto_governanca else
        f"deliberação de {classif_efetiva.lower()}"
    )

    cargo_rotulo = c_vaga or "Geral"
    nivel_rotulo = c_nivel or "Pleno"

    if veto_governanca:
        parecer_ficha = (
            f"SUMÁRIO EXECUTIVO: Para a vaga de {cargo_rotulo} ({nivel_rotulo}), o perfil alcançou "
            f"{total_pts} / 40 pontos ({perc_t1:.1f}% de aderência). Maiores forças: {forcas_txt}. "
            f"Focos de ressalva ou veto: {ressalvas_txt}. A {deliberacao_txt} decorre de risco crítico "
            f"em Equilíbrio Emocional, Saúde Psicológica ou Confiabilidade e Ética. Classificação: '{classif_efetiva}'."
        )
    else:
        parecer_ficha = (
            f"SUMÁRIO EXECUTIVO: Para a vaga de {cargo_rotulo} ({nivel_rotulo}), o perfil alcançou "
            f"{total_pts} / 40 pontos ({perc_t1:.1f}% de aderência). Maiores forças: {forcas_txt}. "
            f"Focos de ressalva: {ressalvas_txt}. A avaliação sustenta {deliberacao_txt}, "
            f"considerando o alinhamento comportamental e estrutural mapeado."
        )

    pdf.set_fill_color(248, 249, 250)
    pdf.set_draw_color(200, 205, 210)
    pdf.multi_cell(0, 4.2, sanitizar_pdf(parecer_ficha), border=1, fill=True)

    # =========================================================================
    # PÁGINA 2 EM DIANTE: ANÁLISE QUALITATIVA DAS COMPETÊNCIAS
    # =========================================================================
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 6, sanitizar_pdf("ANÁLISE QUALITATIVA DAS COMPETÊNCIAS"), border=0, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    for idx, item in enumerate(dados_casas, start=1):
        num_pos = item.get("pos", idx)
        c_nome_comp = item.get("nome", COMPETENCIAS_FASE_1[idx - 1] if idx <= len(COMPETENCIAS_FASE_1) else f"Casa {idx}")
        nota_comp = item.get("nota", 3)
        c_cent = item.get("central", "-")
        c_neg = item.get("negativa", "-")
        c_pos = item.get("positiva", "-")

        cartas_str = f"Carta Central: {c_cent}  |  Carta Negativa: {c_neg}  |  Carta Positiva: {c_pos}"

        desc_central = item.get("desc_central", "") or f"Análise central desenvolvida para o arcano {c_cent} no contexto de {c_nome_comp}."
        desc_negativa = item.get("desc_negativa", "") or f"Ponto de ressalva e vulnerabilidade mapeado através do arcano {c_neg}."
        desc_positiva = item.get("desc_positiva", "") or f"Fator de alavancagem e potencial comportamental alinhado ao arcano {c_pos}."
        resumo = item.get("resumo", "") or f"Síntese metodológica integrada para {c_nome_comp}."

        blocos_parsed = [
            ("CARTA CENTRAL", c_cent, desc_central),
            ("CARTA NEGATIVA", c_neg, desc_negativa),
            ("CARTA POSITIVA", c_pos, desc_positiva),
            ("RESUMO DA LEITURA", "", resumo),
        ]

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
        pdf.cell(0, 6.0, sanitizar_pdf(f"  {num_pos}. {c_nome_comp} (Nota: {nota_comp}/5)"), border=0, align="L", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Subtítulo com os arcanos
        pdf.set_font("helvetica", "I", 7.5)
        pdf.set_xy(13, y_box + 6.2)
        pdf.cell(184, 4.8, sanitizar_pdf(cartas_str), border=0, align="L", fill=False, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Renderização dos blocos
        pdf.set_xy(13, y_box + 11.5)
        for r_txt, c_nome_item, c_txt in blocos_parsed:
            if r_txt:
                renderizar_item_analise(pdf, r_txt, c_nome_item, c_txt, 184)
            else:
                pdf.set_font("helvetica", "", 7.5)
                pdf.multi_cell(184, 3.6, sanitizar_pdf(c_txt), 0, "L", False)

        pdf.set_xy(10, y_box + 6.0 + 5.0 + h_corpo_total + 5.0)

    # =========================================================================
    # CONCLUSÃO E RECOMENDAÇÃO FINAL
    # =========================================================================
    raw_c = extrair_justificativa_ia(texto_ia_doc)

    if veto_governanca:
        classif_final = "Não Recomendado (Veto de Governança)"
        if raw_c:
            texto_conclusao = (
                f"PARECER FINAL: {classif_final}.\n"
                f"JUSTIFICATIVA EXECUTIVA: {raw_c}\n"
                f"Forças principais: {forcas_txt}. Focos de ressalva ou veto: {ressalvas_txt}."
            )
        else:
            texto_conclusao = (
                f"PARECER FINAL: {classif_final}.\n"
                f"JUSTIFICATIVA EXECUTIVA: Embora o candidato tenha somado {total_pts} pontos "
                f"({perc_t1:.1f}% de aderência), a candidatura foi vetada pelas regras de integridade e governança corporativa. "
                f"As maiores forças identificadas foram {forcas_txt}; os focos de ressalva ou veto foram {ressalvas_txt}. "
                f"Riscos críticos em bases emocionais, psíquicas ou éticas representam ponto de ruptura para a governança da posição."
            )
    elif raw_c:
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
            f"A deliberação considera o equilíbrio entre desempenho, riscos mapeados e aderência à vaga."
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
    pdf.cell(190, 6.0, sanitizar_pdf("  CONCLUSÃO E RECOMENDAÇÃO FINAL"), border=0, align="L", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("helvetica", "", 7.5)
    pdf.set_xy(13, y_conc + 7.5)
    pdf.multi_cell(184, 3.6, sanitizar_pdf(texto_conclusao), 0, "L", False)

    y_fim_conc = pdf.get_y() + 3.0
    altura_final_box = max(18.0, y_fim_conc - y_conc)
    pdf.set_draw_color(190, 195, 202)
    pdf.rect(10, y_conc, 190, altura_final_box)
    pdf.set_y(y_conc + altura_final_box + 4.0)

    return bytes(pdf.output())
