import os
import math
import re
from datetime import datetime
from fpdf import FPDF

# Escopo corporativo idêntico ao da Fase 2 para geração dos diagnósticos reais
ESCOPO_CORPORATIVO_CASA = {
    1: "Identidade executiva e postura de liderança",
    2: "Gestão orçamentária e recursos materiais",
    3: "Comunicação, negociação e alinhamento tático",
    4: "Sustentação interna e clima da equipe",
    5: "Criatividade estratégica e tomada de risco",
    6: "Rotina operacional, eficiência e processos",
    7: "Alianças estratégicas e relações bilaterais",
    8: "Gestão de crises, fusões e compliance",
    9: "Visão de longo prazo e expansão de mercado",
    10: "Metas executivas, reputação e governança",
    11: "Articulação institucional e projetos coletivos",
    12: "Pontos cegos, riscos ocultos e resiliência"
}

def sanitizar(texto):
    if texto is None:
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
        "•": "-", "…": "...", "→": "->", "←": "<-", "º": "°", "ª": "a",
        "`": ""
    }
    for orig, dest in subs.items():
        txt = txt.replace(orig, dest)
    txt = re.sub(r"[ \t]+", " ", txt)
    return txt.encode("latin-1", "replace").decode("latin-1")

def formatar_cuspide(grau):
    if not grau:
        return "0° 0'"
    numeros = re.findall(r"\d+", str(grau))
    if len(numeros) >= 2:
        return f"{numeros[0]}° {numeros[1]}'"
    if len(numeros) == 1:
        return f"{numeros[0]}° 0'"
    return str(grau)

class DossieExecutivoMasterPDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 12)
        self.set_text_color(24, 43, 73)
        self.cell(0, 6, sanitizar("LAUDO EXECUTIVO INTEGRADO DE RECRUTAMENTO"), 0, 1, "L")
        self.set_font("helvetica", "I", 8)
        self.set_text_color(100, 116, 139)
        self.cell(0, 4, sanitizar("Fase 3: Governança Final, Cruzamento Ponderado & Deliberação Executiva"), 0, 1, "L")
        self.set_draw_color(203, 213, 225)
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(4)

    def footer(self):
        self.set_y(-10)
        self.set_font("helvetica", "I", 7.5)
        self.set_text_color(148, 163, 184)
        self.cell(130, 5, sanitizar("CONFIDENCIAL - Sistema de Diagnóstico Corporativo"), 0, 0, "L")
        self.cell(60, 5, sanitizar(f"Página {self.page_no()} de 2"), 0, 0, "R")

def desenhar_card(pdf, x, y, w, h, titulo, valor, subtitulo, cor_bg, cor_txt):
    pdf.set_fill_color(*cor_bg)
    pdf.set_draw_color(203, 213, 225)
    pdf.rect(x, y, w, h, "DF")
    
    pdf.set_xy(x, y + 1.8)
    pdf.set_font("helvetica", "B", 6.8)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(w, 3.2, sanitizar(titulo), 0, 0, "C")
    
    pdf.set_xy(x, y + 5.2)
    pdf.set_font("helvetica", "B", 11.0)
    pdf.set_text_color(*cor_txt)
    pdf.cell(w, 5.0, sanitizar(valor), 0, 0, "C")
    
    pdf.set_xy(x, y + 10.8)
    pdf.set_font("helvetica", "I", 5.6)
    pdf.set_text_color(100, 116, 139)
    pdf.multi_cell(w, 2.7, sanitizar(subtitulo), 0, "C")

def gerar_laudo_fase3_pdf(
    c_nome, c_vaga, c_nivel, arq_ativo_ficha,
    perc_t1, perc_t2, indice_global, classificacao,
    sinal_vermelho, texto_conclusao_f3, mandala_dados, dados_tabela_f1,
    output_pdf="Laudo_Executivo_Integrado.pdf"
):
    pdf = DossieExecutivoMasterPDF()
    pdf.set_auto_page_break(auto=False)
    
    # =========================================================================
    # PÁGINA 1: IDENTIFICAÇÃO, DASHBOARD, DELIBERAÇÃO E MATRIZ 8 CASAS
    # =========================================================================
    pdf.add_page()

    nome_c = sanitizar(c_nome or "Candidato")
    vaga_c = sanitizar(c_vaga or "Não informada")
    nivel_c = sanitizar(c_nivel or "Executivo")
    arq_c = sanitizar(arq_ativo_ficha or "Geral")
    data_emissao = datetime.now().strftime("%d/%m/%Y")

    p1 = float(perc_t1 or 0)
    p2 = float(perc_t2 or 0)
    ig = float(indice_global or 0)
    sinal_v = str(sinal_vermelho).strip().lower() in ["sim", "true", "1", "ativo"]
    classif_str = (
        "Não Recomendado (Veto de Governança)"
        if sinal_v else sanitizar(classificacao or "Avaliado")
    )
    classif_str = classif_str.replace("Aderência entre 65% a 79%", "Aderência entre 65% e 79%")

    # Identificação
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(203, 213, 225)
    pdf.set_font("helvetica", "B", 7.2)
    pdf.set_text_color(51, 65, 85)

    pdf.cell(28, 5.0, " CANDIDATO(A):", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 7.2)
    pdf.cell(102, 5.0, f" {nome_c.upper()}", 1, 0, "L")
    pdf.set_font("helvetica", "B", 7.2)
    pdf.cell(30, 5.0, " EMISSÃO:", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 7.2)
    pdf.cell(30, 5.0, f" {data_emissao}", 1, 1, "C")

    pdf.set_font("helvetica", "B", 7.2)
    pdf.cell(28, 5.0, " CARGO / NÍVEL:", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 7.2)
    pdf.cell(72, 5.0, f" {vaga_c.upper()} ({nivel_c.upper()})", 1, 0, "L")
    pdf.set_font("helvetica", "B", 7.2)
    pdf.cell(27, 5.0, " ARQUÉTIPO:", 1, 0, "L", True)
    
    tam_fonte_arq = 6.2 if len(str(arq_c)) > 26 else 7.0
    pdf.set_font("helvetica", "", tam_fonte_arq)
    pdf.cell(63, 5.0, f" {arq_c}", 1, 1, "L")
    pdf.ln(2.0)

    # 1. Sumário Executivo de Aderência
    pdf.set_font("helvetica", "B", 8.0)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 4.2, sanitizar("1. SUMÁRIO EXECUTIVO DE ADERÊNCIA E DIRETRIZ FINAL"), 0, 1, "L")
    
    y_cards = pdf.get_y()
    card_w = 61.3
    card_h = 17.5

    desenhar_card(pdf, 10, y_cards, card_w, card_h, "FASE 1: TAROT COMPORTAMENTAL", f"{p1:.1f}%", "Peso Aplicado: 70%", (241, 245, 249), (30, 41, 59))
    desenhar_card(pdf, 10 + card_w + 3, y_cards, card_w, card_h, sanitizar("FASE 2: ESTRUTURAL & TRÂNSITOS"), f"{p2:.1f}%", "Peso Aplicado: 30%", (241, 245, 249), (30, 41, 59))
    
    cor_bg_ig = (254, 242, 242) if sinal_v else (240, 253, 244)
    cor_tx_ig = (185, 28, 28) if sinal_v else (21, 128, 61)
    desenhar_card(pdf, 10 + (card_w * 2) + 6, y_cards, card_w, card_h, "ÍNDICE GLOBAL INTEGRADO", f"{ig:.1f}%", classif_str, cor_bg_ig, cor_tx_ig)

    pdf.set_xy(10, y_cards + card_h + 1.8)
    if sinal_v:
        pdf.set_fill_color(254, 226, 226)
        pdf.set_draw_color(239, 68, 68)
        pdf.set_font("helvetica", "B", 6.8)
        pdf.set_text_color(185, 28, 28)
        pdf.cell(0, 4.0, sanitizar(" [-] SINAL VERMELHO ATIVADO: Veto Mandatório de Governança (Risco em bases críticas)"), 1, 1, "L", True)
    else:
        pdf.set_fill_color(240, 253, 244)
        pdf.set_draw_color(34, 197, 94)
        pdf.set_font("helvetica", "B", 6.8)
        pdf.set_text_color(21, 128, 61)
        pdf.cell(0, 4.0, sanitizar(" [+] SINAL VERMELHO DESATIVADO: Bases comportamentais, psíquicas e éticas preservadas."), 1, 1, "L", True)
    pdf.set_draw_color(203, 213, 225)
    pdf.ln(1.8)

    # 2. Deliberação Executiva
    pdf.set_font("helvetica", "B", 8.0)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 4.2, sanitizar("2. DELIBERAÇÃO EXECUTIVA E PARECER DE ADEQUAÇÃO AO CARGO"), 0, 1, "L")
    pdf.set_font("helvetica", "", 6.7)
    pdf.set_text_color(30, 41, 59)
    
    # Tratamento harmonizado de parágrafos para eliminar quebras excessivas
    parecer_limpo = re.sub(r"\n{2,}", "\n", sanitizar(texto_conclusao_f3 or "Avaliação executiva concluída.")).strip()
    pdf.multi_cell(0, 3.1, parecer_limpo, border=1)
    pdf.ln(1.8)

    # 3. Matriz Psicométrica (8 Casas) com Altura Otimizada
    pdf.set_font("helvetica", "B", 8.0)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 4.2, sanitizar("3. MATRIZ PSICOMÉTRICA E COMPORTAMENTAL (MÉTODO 8 CASAS)"), 0, 1, "L")
    pdf.set_font("helvetica", "B", 6.5)
    pdf.set_fill_color(226, 232, 240)
    pdf.set_text_color(30, 41, 59)

    pdf.cell(8, 4.2, "POS", 1, 0, "C", True)
    pdf.cell(28, 4.2, "COMPETÊNCIA", 1, 0, "L", True)
    pdf.cell(48, 4.2, "CARTAS (CENTRAL / NEG. / POS.)", 1, 0, "L", True)
    pdf.cell(10, 4.2, "NOTA", 1, 0, "C", True)
    pdf.cell(96, 4.2, "RESUMO DA LEITURA (SÍNTESE IA)", 1, 1, "L", True)

    if dados_tabela_f1 and isinstance(dados_tabela_f1, list):
        for item in dados_tabela_f1:
            pos = str(item.get("pos", ""))
            comp = sanitizar(item.get("nome", ""))
            cartas_raw = item.get("cartas", "")
            
            partes_cartas = [p.strip().replace("Carta Central:", "Central:").replace("Carta Negativa:", "Negativa:").replace("Carta Positiva:", "Positiva:") 
                             for p in str(cartas_raw).replace("\n", " | ").split("|") if p.strip()]
            cartas_txt = "\n".join(partes_cartas[:3])
            
            nota = f"{float(item.get('nota', 0)):.0f}"
            resumo = sanitizar(item.get("resumo", ""))

            pdf.set_font("helvetica", "", 5.8)
            palavras_r = resumo.split()
            linhas_r = 1
            linha_atual = ""
            for p in palavras_r:
                teste = f"{linha_atual} {p}".strip()
                if pdf.get_string_width(teste) <= 93:
                    linha_atual = teste
                else:
                    linhas_r += 1
                    linha_atual = p
            
            linhas_comp = 2 if pdf.get_string_width(comp) > 25 else 1
            total_linhas = max(3, len(partes_cartas[:3]), linhas_r, linhas_comp)
            row_h = (total_linhas * 2.7) + 1.4

            y_row = pdf.get_y()
            y_text = y_row + 0.8

            pdf.rect(10, y_row, 8, row_h)
            pdf.set_xy(10, y_text)
            pdf.set_font("helvetica", "B", 6.8)
            pdf.cell(8, 3.0, pos, 0, 0, "C")

            pdf.rect(18, y_row, 28, row_h)
            pdf.set_xy(19, y_text)
            pdf.set_font("helvetica", "B", 6.8)
            pdf.multi_cell(26, 2.9, comp, 0, "L")

            pdf.rect(46, y_row, 48, row_h)
            pdf.set_xy(47, y_text)
            pdf.set_font("helvetica", "", 5.8)
            pdf.multi_cell(46, 2.7, sanitizar(cartas_txt), 0, "L")

            pdf.rect(94, y_row, 10, row_h)
            pdf.set_xy(94, y_text)
            pdf.set_font("helvetica", "B", 6.8)
            pdf.cell(10, 3.0, f"{nota}/5", 0, 0, "C")

            pdf.rect(104, y_row, 96, row_h)
            pdf.set_xy(105, y_text)
            pdf.set_font("helvetica", "", 5.8)
            pdf.multi_cell(94, 2.7, resumo, 0, "L")

            pdf.set_xy(10, y_row + row_h)

    # =========================================================================
    # PÁGINA 2: MATRIZ DAS 12 CASAS (FASE 2) E GOVERNANÇA CORPORATIVA
    # =========================================================================
    pdf.add_page()

    pdf.set_font("helvetica", "B", 8.0)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 4.8, sanitizar("4. MATRIZ ESTRUTURAL DAS 12 CASAS PONDERADAS POR ARQUÉTIPO (DIAGNÓSTICO)"), 0, 1, "L")
    pdf.set_font("helvetica", "B", 6.8)
    pdf.set_fill_color(226, 232, 240)
    pdf.set_text_color(30, 41, 59)

    w_c, w_s, w_n, w_p, w_cl, w_dg = 10, 32, 14, 14, 48, 72

    pdf.cell(w_c, 5.0, "CASA", 1, 0, "C", True)
    pdf.cell(w_s, 5.0, "SIGNO (CÚSPIDE)", 1, 0, "L", True)
    pdf.cell(w_n, 5.0, "NOTA", 1, 0, "C", True)
    pdf.cell(w_p, 5.0, "PESO", 1, 0, "C", True)
    pdf.cell(w_cl, 5.0, "CLIMA DE TRÂNSITO", 1, 0, "L", True)
    pdf.cell(w_dg, 5.0, "DIAGNÓSTICO (SÍNTESE)", 1, 1, "L", True)

    def calc_linhas_t2(texto, larg_col, estilo):
        pdf.set_font("helvetica", estilo, 6.3)
        cont = 0
        for pedaco in str(texto).split("\n"):
            w = pdf.get_string_width(pedaco)
            cont += max(1, math.ceil(w / max(1.0, larg_col - 3)))
        return max(1, cont)

    for i in range(1, 13):
        k_casa = f"Casa {i}"
        d_val = mandala_dados.get(k_casa, {}) if isinstance(mandala_dados, dict) else {}
        
        signo_base = d_val.get('signo', 'Estável')
        grau_base = d_val.get('grau', '')
        signo_str = f"{sanitizar(signo_base)} ({formatar_cuspide(grau_base)})"
        
        nota_val = d_val.get('nota_base', d_val.get('nota', 4.0))
        peso_val = d_val.get('peso', 1.0)
        
        clima_raw = str(d_val.get('clima', 'Estável'))
        escopo_casa = ESCOPO_CORPORATIVO_CASA.get(i, "Gestão de processos")

        if any(p in clima_raw for p in ["Júpiter", "Jupiter"]):
            clima_formatado = "[+] Ativado por Júpiter (Crescimento)"
            diag_txt = f"Ciclo expansivo: alavanca para {escopo_casa.lower()} com alta projeção de resultados."
        elif "Saturno" in clima_raw:
            clima_formatado = "[!] Ativado por Saturno (Rigor)"
            diag_txt = f"Ciclo de cobrança: exige auditoria, disciplina e controle rigoroso em {escopo_casa.lower()}."
        elif "Urano" in clima_raw:
            clima_formatado = "Ativado por Urano (Inovação)"
            diag_txt = f"Ciclo disruptivo: impulsiona transformações ágeis e quebra de padrões em {escopo_casa.lower()}."
        else:
            clima_formatado = "Estável"
            diag_txt = f"{escopo_casa} operando em estabilidade funcional."

        esta_ativ = any(p in clima_formatado for p in ["Júpiter", "Saturno", "Urano"])
        estilo_txt = "B" if esta_ativ else ""

        l_clima = calc_linhas_t2(clima_formatado, w_cl, estilo_txt)
        l_diag = calc_linhas_t2(diag_txt, w_dg, "")
        max_l = max(l_clima, l_diag, 1)
        row_h2 = max(6.0, float(max_l * 2.8) + 1.8)

        y_topo = pdf.get_y()

        pdf.set_draw_color(203, 213, 225)
        pdf.set_fill_color(241, 245, 249) if esta_ativ else pdf.set_fill_color(255, 255, 255)

        # Grade retangular idêntica à da Fase 2
        pdf.rect(10, y_topo, w_c, row_h2, "DF")
        pdf.rect(10 + w_c, y_topo, w_s, row_h2, "DF")
        pdf.rect(10 + w_c + w_s, y_topo, w_n, row_h2, "DF")
        pdf.rect(10 + w_c + w_s + w_n, y_topo, w_p, row_h2, "DF")
        pdf.rect(10 + w_c + w_s + w_n + w_p, y_topo, w_cl, row_h2, "DF")
        pdf.rect(10 + w_c + w_s + w_n + w_p + w_cl, y_topo, w_dg, row_h2, "DF")

        # Textos das colunas
        pdf.set_text_color(24, 43, 73)
        pdf.set_font("helvetica", "B", 6.8)
        pdf.set_xy(10, y_topo + (row_h2 / 2) - 1.6)
        pdf.cell(w_c, 3.2, f"C{i}", 0, 0, "C")

        pdf.set_font("helvetica", "", 6.3)
        pdf.set_xy(10 + w_c + 1, y_topo + (row_h2 / 2) - 1.6)
        pdf.cell(w_s - 2, 3.2, sanitizar(signo_str), 0, 0, "L")

        pdf.set_font("helvetica", "B", 6.8)
        pdf.set_xy(10 + w_c + w_s, y_topo + (row_h2 / 2) - 1.6)
        pdf.cell(w_n, 3.2, f"{float(nota_val):.1f}/5", 0, 0, "C")

        pdf.set_font("helvetica", "", 6.8)
        pdf.set_xy(10 + w_c + w_s + w_n, y_topo + (row_h2 / 2) - 1.6)
        pdf.cell(w_p, 3.2, f"{float(peso_val):.1f}x", 0, 0, "C")

        pdf.set_font("helvetica", estilo_txt, 6.3)
        pdf.set_xy(10 + w_c + w_s + w_n + w_p + 1, y_topo + 1.0)
        pdf.multi_cell(w_cl - 2, 2.7, sanitizar(clima_formatado), 0, "L")

        pdf.set_font("helvetica", "", 6.3)
        pdf.set_xy(10 + w_c + w_s + w_n + w_p + w_cl + 1, y_topo + 1.0)
        pdf.multi_cell(w_dg - 2, 2.7, sanitizar(diag_txt), 0, "L")

        # Avanço do cursor exatamente pela altura da linha atual
        pdf.set_xy(10, y_topo + row_h2)

    # Assinaturas e Governança
    pdf.ln(8.0)
    y_sign = pdf.get_y()
    pdf.set_draw_color(100, 116, 139)
    pdf.line(20, y_sign, 85, y_sign)
    pdf.line(125, y_sign, 190, y_sign)

    pdf.set_xy(20, y_sign + 1.5)
    pdf.set_font("helvetica", "B", 7.2)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(65, 4, sanitizar("COMITÊ AVALIADOR / RECURSOS HUMANOS"), 0, 0, "C")

    pdf.set_xy(125, y_sign + 1.5)
    pdf.cell(65, 4, sanitizar("DIRETORIA EXECUTIVA / COMPLIANCE"), 0, 1, "C")

    pdf_bytes = bytes(pdf.output())
    try:
        with open(output_pdf, "wb") as f:
            f.write(pdf_bytes)
    except Exception:
        pass

    return pdf_bytes
