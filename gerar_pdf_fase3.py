import os
from datetime import datetime
from fpdf import FPDF

def sanitizar(texto):
    if texto is None:
        return ""
    txt = str(texto)
    substituicoes = {
        "—": "-", "–": "-", "“": '"', "”": '"', "‘": "'", "’": "'",
        "•": "-", "…": "...", "→": "->", "←": "<-", "°": "o", "º": "o", "ª": "a"
    }
    for orig, dest in substituicoes.items():
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
        self.cell(60, 5, sanitizar(f"Página {self.page_no()}"), 0, 0, "R")

def gerar_laudo_fase3_pdf(
    c_nome, c_vaga, c_nivel, arq_ativo_ficha,
    perc_t1, perc_t2, indice_global, classificacao,
    sinal_vermelho, texto_conclusao_f3, mandala_dados, dados_tabela_f1,
    output_pdf="Laudo_Executivo_Integrado.pdf"
):
    pdf = DossieExecutivoMasterPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    nome_cand = sanitizar(c_nome or "Candidato")
    vaga_cand = sanitizar(c_vaga or "Não informada")
    nivel_cand = sanitizar(c_nivel or "Executivo")
    arq_nome = sanitizar(arq_ativo_ficha or "Geral")
    data_emissao = datetime.now().strftime("%d/%m/%Y")
    
    p1 = float(perc_t1 or 0)
    p2 = float(perc_t2 or 0)
    ig = float(indice_global or 0)
    classif_str = sanitizar(classificacao or "Avaliado")
    sinal_v = str(sinal_vermelho).strip().lower() in ["sim", "true", "1", "ativo"]

    # Grade de Identificação
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(203, 213, 225)
    pdf.set_font("helvetica", "B", 7.5)
    pdf.set_text_color(51, 65, 85)

    pdf.cell(28, 5.5, " CANDIDATO(A):", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 7.5)
    pdf.cell(102, 5.5, f" {nome_cand.upper()}", 1, 0, "L")
    pdf.set_font("helvetica", "B", 7.5)
    pdf.cell(30, 5.5, " EMISSÃO:", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 7.5)
    pdf.cell(30, 5.5, f" {data_emissao}", 1, 1, "C")

    pdf.set_font("helvetica", "B", 7.5)
    pdf.cell(28, 5.5, " CARGO / NÍVEL:", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 7.5)
    pdf.cell(102, 5.5, f" {vaga_cand.upper()} ({nivel_cand})", 1, 0, "L")
    pdf.set_font("helvetica", "B", 7.5)
    pdf.cell(30, 5.5, " ARQUÉTIPO:", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 7.5)
    pdf.cell(30, 5.5, f" {arq_nome[:18]}", 1, 1, "C")
    pdf.ln(3)

    # 1. Sumário Executivo (Cards)
    pdf.set_font("helvetica", "B", 8.5)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 5, sanitizar("1. SUMÁRIO EXECUTIVO DE ADERÊNCIA PONDERADA"), 0, 1, "L")

    card_w = 61.3
    card_h = 16
    y_card = pdf.get_y()

    pdf.set_xy(10, y_card)
    pdf.set_fill_color(241, 245, 249)
    pdf.rect(10, y_card, card_w, card_h, "DF")
    pdf.set_font("helvetica", "B", 7)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(card_w, 4, sanitizar("FASE 1: TAROT COMPORTAMENTAL"), 0, 1, "C")
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(card_w, 6, f"{p1:.1f}%", 0, 1, "C")
    pdf.set_font("helvetica", "I", 6.5)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(card_w, 4, sanitizar("Peso Aplicado: 70%"), 0, 0, "C")

    pdf.set_xy(10 + card_w + 3, y_card)
    pdf.rect(10 + card_w + 3, y_card, card_w, card_h, "DF")
    pdf.set_font("helvetica", "B", 7)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(card_w, 4, sanitizar("FASE 2: ESTRUTURAL & TRÂNSITOS"), 0, 1, "C")
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(card_w, 6, f"{p2:.1f}%", 0, 1, "C")
    pdf.set_font("helvetica", "I", 6.5)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(card_w, 4, sanitizar("Peso Aplicado: 30%"), 0, 0, "C")

    pdf.set_xy(10 + (card_w * 2) + 6, y_card)
    if sinal_v:
        pdf.set_fill_color(254, 242, 242)
        pdf.set_draw_color(239, 68, 68)
    else:
        pdf.set_fill_color(240, 253, 244)
        pdf.set_draw_color(34, 197, 94)
    pdf.rect(10 + (card_w * 2) + 6, y_card, card_w, card_h, "DF")
    pdf.set_font("helvetica", "B", 7)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(card_w, 4, sanitizar("ÍNDICE GLOBAL INTEGRADO"), 0, 1, "C")
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(185, 28, 28) if sinal_v else pdf.set_text_color(21, 128, 61)
    pdf.cell(card_w, 6, f"{ig:.1f}%", 0, 1, "C")
    pdf.set_font("helvetica", "B", 6.5)
    pdf.cell(card_w, 4, sanitizar(classif_str[:30]), 0, 0, "C")

    pdf.set_draw_color(203, 213, 225)
    pdf.set_xy(10, y_card + card_h + 2)

    if sinal_v:
        pdf.set_fill_color(254, 226, 226)
        pdf.set_draw_color(239, 68, 68)
        pdf.set_font("helvetica", "B", 7)
        pdf.set_text_color(185, 28, 28)
        pdf.cell(0, 4.5, sanitizar(" [!] SINAL VERMELHO ATIVADO: Ponto crítico detectado nas bases de Resiliência ou Ética."), 1, 1, "L", True)
    else:
        pdf.set_fill_color(240, 253, 244)
        pdf.set_draw_color(34, 197, 94)
        pdf.set_font("helvetica", "B", 7)
        pdf.set_text_color(21, 128, 61)
        pdf.cell(0, 4.5, sanitizar(" [+] SINAL VERMELHO DESATIVADO: Bases comportamentais, psíquicas e éticas preservadas."), 1, 1, "L", True)
    
    pdf.set_draw_color(203, 213, 225)
    pdf.ln(2)

    # 2. Deliberação Executiva
    pdf.set_font("helvetica", "B", 8.5)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 5, sanitizar("2. DELIBERAÇÃO EXECUTIVA E PARECER DE ADEQUAÇÃO AO CARGO"), 0, 1, "L")
    pdf.set_font("helvetica", "", 7.5)
    pdf.set_text_color(30, 41, 59)
    pdf.multi_cell(0, 4, sanitizar(texto_conclusao_f3 or "Avaliação executiva concluída."), border=1)
    pdf.ln(3)

    # 3. Matriz Psicométrica (Método 8 Casas)
    pdf.set_font("helvetica", "B", 8.5)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 5, sanitizar("3. MATRIZ PSICOMÉTRICA E COMPORTAMENTAL (MÉTODO 8 CASAS)"), 0, 1, "L")
    pdf.set_font("helvetica", "B", 7)
    pdf.set_fill_color(226, 232, 240)
    pdf.set_text_color(30, 41, 59)

    pdf.cell(8, 5, "POS", 1, 0, "C", True)
    pdf.cell(32, 5, "COMPETÊNCIA", 1, 0, "L", True)
    pdf.cell(52, 5, "CARTAS (CENTRAL/NEG./POS.)", 1, 0, "L", True)
    pdf.cell(12, 5, "NOTA", 1, 0, "C", True)
    pdf.cell(86, 5, "RESUMO DA LEITURA (SÍNTESE IA)", 1, 1, "L", True)

    pdf.set_font("helvetica", "", 6.8)
    if dados_tabela_f1 and isinstance(dados_tabela_f1, list):
        for item in dados_tabela_f1:
            pos = str(item.get("pos", ""))
            comp = sanitizar(item.get("nome", ""))
            cartas = sanitizar(item.get("cartas", "").replace("\n", " | "))
            nota = f"{float(item.get('nota', 0)):.0f}"
            resumo = sanitizar(item.get("resumo", ""))

            pdf.cell(8, 4.5, pos, 1, 0, "C")
            pdf.cell(32, 4.5, f" {comp[:20]}", 1, 0, "L")
            pdf.cell(52, 4.5, f" {cartas[:38]}", 1, 0, "L")
            pdf.cell(12, 4.5, f"{nota}/5", 1, 0, "C")
            pdf.cell(86, 4.5, f" {resumo[:60]}...", 1, 1, "L")
    pdf.ln(3)

    # 4. Matriz Estrutural das 12 Casas (Trânsitos)
    if pdf.get_y() > 210:
        pdf.add_page()

    pdf.set_font("helvetica", "B", 8.5)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 5, sanitizar("4. MATRIZ ESTRUTURAL DAS 12 CASAS PONDERADAS POR ARQUÉTIPO (DIAGNÓSTICO)"), 0, 1, "L")
    pdf.set_font("helvetica", "B", 7)
    pdf.set_fill_color(226, 232, 240)
    pdf.set_text_color(30, 41, 59)

    pdf.cell(10, 5, "CASA", 1, 0, "C", True)
    pdf.cell(35, 5, "SIGNO (CÚSPIDE)", 1, 0, "L", True)
    pdf.cell(14, 5, "NOTA", 1, 0, "C", True)
    pdf.cell(14, 5, "PESO", 1, 0, "C", True)
    pdf.cell(45, 5, "CLIMA DE TRÂNSITO", 1, 0, "L", True)
    pdf.cell(72, 5, "DIAGNÓSTICO (SÍNTESE)", 1, 1, "L", True)

    pdf.set_font("helvetica", "", 6.8)
    if mandala_dados:
        casas_lista = mandala_dados if isinstance(mandala_dados, list) else mandala_dados.values()
        for idx, m_item in enumerate(casas_lista, 1):
            if pdf.get_y() > 275:
                pdf.add_page()
            c_label = f"C{idx}"
            s_cuspide = sanitizar(m_item.get("signo", "Estável"))
            n_val = f"{float(m_item.get('nota', 4.0)):.1f}/5"
            p_val = f"{float(m_item.get('peso', 1.0)):.1f}x"
            clima = sanitizar(m_item.get("clima", "Estável"))
            diag = sanitizar(m_item.get("sintese", "Estabilidade funcional."))

            pdf.cell(10, 4.3, c_label, 1, 0, "C")
            pdf.cell(35, 4.3, f" {s_cuspide[:22]}", 1, 0, "L")
            pdf.cell(14, 4.3, n_val, 1, 0, "C")
            pdf.cell(14, 4.3, p_val, 1, 0, "C")
            pdf.cell(45, 4.3, f" {clima[:28]}", 1, 0, "L")
            pdf.cell(72, 4.3, f" {diag[:48]}...", 1, 1, "L")
    pdf.ln(3)

    # Assinaturas
    if pdf.get_y() > 260:
        pdf.add_page()
    pdf.ln(4)
    y_sign = pdf.get_y()
    pdf.set_draw_color(100, 116, 139)
    pdf.line(20, y_sign, 90, y_sign)
    pdf.line(120, y_sign, 190, y_sign)
    pdf.set_xy(20, y_sign + 1)
    pdf.set_font("helvetica", "B", 7)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(70, 4, sanitizar("COMITÊ AVALIADOR / RH"), 0, 0, "C")
    pdf.set_xy(120, y_sign + 1)
    pdf.cell(70, 4, sanitizar("DIRETORIA EXECUTIVA"), 0, 1, "C")

    pdf_bytes = bytes(pdf.output())
    try:
        with open(output_pdf, "wb") as f:
            f.write(pdf_bytes)
    except Exception:
        pass

    return pdf_bytes