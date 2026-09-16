import os
from datetime import datetime
from fpdf import FPDF

def sanitizar(texto):
    if texto is None:
        return ""
    txt = str(texto)
    subs = {
        "—": "-", "–": "-", "“": '"', "”": '"', "‘": "'", "’": "'",
        "•": "-", "…": "...", "→": "->", "←": "<-", "°": "o", "º": "o", "ª": "a",
        "[!]": "(!)", "[+]": "(+)"
    }
    for orig, dest in subs.items():
        txt = txt.replace(orig, dest)
    return txt.encode("latin-1", "replace").decode("latin-1")

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
    
    pdf.set_xy(x, y + 2)
    pdf.set_font("helvetica", "B", 7)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(w, 3.5, sanitizar(titulo), 0, 0, "C")
    
    pdf.set_xy(x, y + 6)
    pdf.set_font("helvetica", "B", 11.5)
    pdf.set_text_color(*cor_txt)
    pdf.cell(w, 5.5, sanitizar(valor), 0, 0, "C")
    
    pdf.set_xy(x, y + 12)
    pdf.set_font("helvetica", "I", 6.5)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(w, 3.5, sanitizar(subtitulo), 0, 0, "C")

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
    classif_str = sanitizar(classificacao or "Avaliado")
    sinal_v = str(sinal_vermelho).strip().lower() in ["sim", "true", "1", "ativo"]

    # Identificação
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(203, 213, 225)
    pdf.set_font("helvetica", "B", 7.5)
    pdf.set_text_color(51, 65, 85)

    pdf.cell(28, 5.5, " CANDIDATO(A):", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 7.5)
    pdf.cell(102, 5.5, f" {nome_c.upper()}", 1, 0, "L")
    pdf.set_font("helvetica", "B", 7.5)
    pdf.cell(30, 5.5, " EMISSÃO:", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 7.5)
    pdf.cell(30, 5.5, f" {data_emissao}", 1, 1, "C")

    pdf.set_font("helvetica", "B", 7.5)
    pdf.cell(28, 5.5, " CARGO / NÍVEL:", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 7.5)
    pdf.cell(102, 5.5, f" {vaga_c.upper()} ({nivel_c.upper()})", 1, 0, "L")
    pdf.set_font("helvetica", "B", 7.5)
    pdf.cell(30, 5.5, " ARQUÉTIPO:", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 7.5)
    pdf.cell(30, 5.5, f" {arq_c[:20]}", 1, 1, "C")
    pdf.ln(3)

    # 1. Sumário Executivo de Aderência Ponderada (Cards com posicionamento blindado)
    pdf.set_font("helvetica", "B", 8.5)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 5, sanitizar("1. SUMÁRIO EXECUTIVO DE ADERÊNCIA E DIRETRIZ FINAL"), 0, 1, "L")
    
    y_cards = pdf.get_y()
    card_w = 61.3
    card_h = 16.5

    desenhar_card(pdf, 10, y_cards, card_w, card_h, "FASE 1: TAROT COMPORTAMENTAL", f"{p1:.1f}%", "Peso Aplicado: 70%", (241, 245, 249), (30, 41, 59))
    desenhar_card(pdf, 10 + card_w + 3, y_cards, card_w, card_h, "FASE 2: ESTRUTURAL & TRÂNSITOS", f"{p2:.1f}%", "Peso Aplicado: 30%", (241, 245, 249), (30, 41, 59))
    
    cor_bg_ig = (254, 242, 242) if sinal_v else (240, 253, 244)
    cor_tx_ig = (185, 28, 28) if sinal_v else (21, 128, 61)
    desenhar_card(pdf, 10 + (card_w * 2) + 6, y_cards, card_w, card_h, "ÍNDICE GLOBAL INTEGRADO", f"{ig:.1f}%", classif_str[:32], cor_bg_ig, cor_tx_ig)

    pdf.set_xy(10, y_cards + card_h + 2)
    if sinal_v:
        pdf.set_fill_color(254, 226, 226)
        pdf.set_draw_color(239, 68, 68)
        pdf.set_font("helvetica", "B", 7)
        pdf.set_text_color(185, 28, 28)
        pdf.cell(0, 4.5, sanitizar(" (!) SINAL VERMELHO ATIVADO: Ponto crítico detectado nas bases de Resiliência ou Ética."), 1, 1, "L", True)
    else:
        pdf.set_fill_color(240, 253, 244)
        pdf.set_draw_color(34, 197, 94)
        pdf.set_font("helvetica", "B", 7)
        pdf.set_text_color(21, 128, 61)
        pdf.cell(0, 4.5, sanitizar(" (+) SINAL VERMELHO DESATIVADO: Bases comportamentais, psíquicas e éticas preservadas."), 1, 1, "L", True)
    pdf.set_draw_color(203, 213, 225)
    pdf.ln(2.5)

    # 2. Deliberação Executiva
    pdf.set_font("helvetica", "B", 8.5)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 4.8, sanitizar("2. DELIBERAÇÃO EXECUTIVA E PARECER DE ADEQUAÇÃO AO CARGO"), 0, 1, "L")
    pdf.set_font("helvetica", "", 7.2)
    pdf.set_text_color(30, 41, 59)
    pdf.multi_cell(0, 3.6, sanitizar(texto_conclusao_f3 or "Avaliação executiva concluída."), border=1)
    pdf.ln(2.5)

    # 3. Matriz Psicométrica (8 Casas)
    pdf.set_font("helvetica", "B", 8.5)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 4.8, sanitizar("3. MATRIZ PSICOMÉTRICA E COMPORTAMENTAL (MÉTODO 8 CASAS)"), 0, 1, "L")
    pdf.set_font("helvetica", "B", 6.8)
    pdf.set_fill_color(226, 232, 240)
    pdf.set_text_color(30, 41, 59)

    pdf.cell(8, 4.8, "POS", 1, 0, "C", True)
    pdf.cell(28, 4.8, "COMPETÊNCIA", 1, 0, "L", True)
    pdf.cell(48, 4.8, "CARTAS (CENTRAL / NEG. / POS.)", 1, 0, "L", True)
    pdf.cell(10, 4.8, "NOTA", 1, 0, "C", True)
    pdf.cell(96, 4.8, "RESUMO DA LEITURA (SÍNTESE IA)", 1, 1, "L", True)

    pdf.set_font("helvetica", "", 6.5)
    if dados_tabela_f1 and isinstance(dados_tabela_f1, list):
        for item in dados_tabela_f1:
            pos = str(item.get("pos", ""))
            comp = sanitizar(item.get("nome", ""))
            cartas_raw = item.get("cartas", "")
            # Formatação limpa das 3 cartas
            cartas_limpas = " | ".join([linha.strip() for linha in cartas_raw.splitlines() if linha.strip()])
            nota = f"{float(item.get('nota', 0)):.0f}"
            resumo = sanitizar(item.get("resumo", ""))

            pdf.cell(8, 7.5, pos, 1, 0, "C")
            pdf.cell(28, 7.5, f" {comp[:18]}", 1, 0, "L")
            
            # Sub-bloco com cartas sem corte truncado
            x_curr, y_curr = pdf.get_x(), pdf.get_y()
            pdf.rect(x_curr, y_curr, 48, 7.5)
            pdf.set_xy(x_curr + 0.5, y_curr + 0.5)
            pdf.multi_cell(47, 3.2, sanitizar(cartas_limpas), border=0, align="L")
            
            pdf.set_xy(x_curr + 48, y_curr)
            pdf.cell(10, 7.5, f"{nota}/5", 1, 0, "C")

            # Sub-bloco com síntese detalhada
            x_res = pdf.get_x()
            pdf.rect(x_res, y_curr, 96, 7.5)
            pdf.set_xy(x_res + 0.5, y_curr + 0.5)
            pdf.multi_cell(95, 3.2, resumo, border=0, align="L")
            pdf.set_xy(10, y_curr + 7.5)

    # =========================================================================
    # PÁGINA 2: MATRIZ DAS 12 CASAS (FASE 2) E GOVERNANÇA CORPORATIVA
    # =========================================================================
    pdf.add_page()

    pdf.set_font("helvetica", "B", 8.5)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 5, sanitizar("4. MATRIZ ESTRUTURAL DAS 12 CASAS PONDERADAS POR ARQUÉTIPO (DIAGNÓSTICO)"), 0, 1, "L")
    pdf.set_font("helvetica", "B", 7)
    pdf.set_fill_color(226, 232, 240)
    pdf.set_text_color(30, 41, 59)

    pdf.cell(10, 5, "CASA", 1, 0, "C", True)
    pdf.cell(32, 5, "SIGNO (CÚSPIDE)", 1, 0, "L", True)
    pdf.cell(14, 5, "NOTA", 1, 0, "C", True)
    pdf.cell(14, 5, "PESO", 1, 0, "C", True)
    pdf.cell(46, 5, "CLIMA DE TRÂNSITO", 1, 0, "L", True)
    pdf.cell(74, 5, "DIAGNÓSTICO (SÍNTESE)", 1, 1, "L", True)

    pdf.set_font("helvetica", "", 6.8)
    if mandala_dados:
        casas_lista = mandala_dados if isinstance(mandala_dados, list) else list(mandala_dados.values())
        for idx, m_item in enumerate(casas_lista, 1):
            c_label = f"C{idx}"
            # Mapeamento resiliente para evitar valores fixos
            s_cuspide = sanitizar(m_item.get("signo_cuspide") or m_item.get("signo") or m_item.get("cuspide", "Estável"))
            
            raw_nota = m_item.get("nota_ajustada") or m_item.get("nota") or m_item.get("nota_base", 4.0)
            n_val = f"{float(raw_nota):.1f}/5"
            
            raw_peso = m_item.get("peso") or m_item.get("peso_aplicado", 1.0)
            p_val = f"{float(raw_peso):.1f}x"
            
            clima = sanitizar(m_item.get("clima_transito") or m_item.get("clima") or m_item.get("transito", "Estável"))
            diag = sanitizar(m_item.get("diagnostico") or m_item.get("sintese") or m_item.get("resumo", "Estabilidade funcional."))

            y_linha = pdf.get_y()
            pdf.cell(10, 8.5, c_label, 1, 0, "C")
            pdf.cell(32, 8.5, f" {s_cuspide[:20]}", 1, 0, "L")
            pdf.cell(14, 8.5, n_val, 1, 0, "C")
            pdf.cell(14, 8.5, p_val, 1, 0, "C")
            
            # Bloco clima
            x_clima = pdf.get_x()
            pdf.rect(x_clima, y_linha, 46, 8.5)
            pdf.set_xy(x_clima + 0.5, y_linha + 0.5)
            pdf.multi_cell(45, 3.6, clima, border=0, align="L")

            # Bloco diagnóstico
            x_diag = x_clima + 46
            pdf.set_xy(x_diag, y_linha)
            pdf.rect(x_diag, y_linha, 74, 8.5)
            pdf.set_xy(x_diag + 0.5, y_linha + 0.5)
            pdf.multi_cell(73, 3.6, diag, border=0, align="L")

            pdf.set_xy(10, y_linha + 8.5)

    pdf.ln(12)

    # Assinaturas formais de governança
    y_sign = pdf.get_y()
    pdf.set_draw_color(100, 116, 139)
    pdf.line(20, y_sign, 85, y_sign)
    pdf.line(125, y_sign, 190, y_sign)

    pdf.set_xy(20, y_sign + 1)
    pdf.set_font("helvetica", "B", 7.5)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(65, 4, sanitizar("COMITÊ AVALIADOR / RH"), 0, 0, "C")

    pdf.set_xy(125, y_sign + 1)
    pdf.cell(65, 4, sanitizar("DIRETORIA EXECUTIVA / COMPLIANCE"), 0, 1, "C")

    pdf_bytes = bytes(pdf.output())
    try:
        with open(output_pdf, "wb") as f:
            f.write(pdf_bytes)
    except Exception:
        pass

    return pdf_bytes