import os
from datetime import datetime
from fpdf import FPDF

def sanitizar(texto):
    """Sanitiza strings para compatibilidade estrita com latin-1 no FPDF."""
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
        # Cabeçalho corporativo no topo de todas as páginas
        self.set_font("helvetica", "B", 13)
        self.set_text_color(24, 43, 73)
        self.cell(0, 7, sanitizar("LAUDO EXECUTIVO INTEGRADO DE RECRUTAMENTO"), 0, 1, "L")
        self.set_font("helvetica", "I", 8.5)
        self.set_text_color(100, 116, 139)
        self.cell(0, 4.5, sanitizar("Fase 3: Governança Final, Cruzamento Ponderado & Deliberação Executiva"), 0, 1, "L")
        self.set_draw_color(203, 213, 225)
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(5)

    def footer(self):
        # Rodapé de governança e confidencialidade
        self.set_y(-12)
        self.set_font("helvetica", "I", 7.5)
        self.set_text_color(148, 163, 184)
        self.cell(130, 6, sanitizar("CONFIDENCIAL - Sistema de Diagnóstico Corporativo"), 0, 0, "L")
        self.cell(60, 6, sanitizar(f"Página {self.page_no()}"), 0, 0, "R")


def gerar_laudo_fase3_pdf(
    c_nome, c_vaga, c_nivel, arq_ativo_ficha,
    perc_t1, perc_t2, indice_global, classificacao,
    sinal_vermelho, texto_conclusao_f3, mandala_dados, dados_tabela_f1,
    output_pdf="Laudo_Executivo_Integrado.pdf"
):
    pdf = DossieExecutivoMasterPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Sanitizações e conversões numéricas
    nome_cand = sanitizar(c_nome or "Candidato")
    vaga_cand = sanitizar(c_vaga or "Não informada")
    nivel_cand = sanitizar(c_nivel or "Executivo")
    arq_nome = sanitizar(arq_ativo_ficha or "Padrão / Geral")
    data_emissao = datetime.now().strftime("%d/%m/%Y")
    
    p1 = float(perc_t1 or 0)
    p2 = float(perc_t2 or 0)
    ig = float(indice_global or 0)
    classif_str = sanitizar(classificacao or "Avaliado")
    sinal_v = str(sinal_vermelho).strip().lower() in ["sim", "true", "1", "ativo"]

    # -------------------------------------------------------------
    # GRADE DE IDENTIFICAÇÃO EXECUTIVA
    # -------------------------------------------------------------
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(203, 213, 225)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(51, 65, 85)

    pdf.cell(32, 6, " CANDIDATO(A):", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(98, 6, f" {nome_cand.upper()}", 1, 0, "L")
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(32, 6, " EMISSÃO:", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(28, 6, f" {data_emissao}", 1, 1, "C")

    pdf.set_font("helvetica", "B", 8)
    pdf.cell(32, 6, " CARGO / NÍVEL:", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(98, 6, f" {vaga_cand.upper()} ({nivel_cand})", 1, 0, "L")
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(32, 6, " ARQUÉTIPO:", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(28, 6, f" {arq_nome[:14]}", 1, 1, "C")
    pdf.ln(4)

    # -------------------------------------------------------------
    # 1. SUMÁRIO EXECUTIVO DE ADERÊNCIA PONDERADA (CARDS)
    # -------------------------------------------------------------
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 5, sanitizar("1. SUMÁRIO EXECUTIVO DE ADERÊNCIA PONDERADA"), 0, 1, "L")
    pdf.ln(1)

    card_w = 61.3
    card_h = 17
    y_card = pdf.get_y()

    # Card 1: Fase 1 (Tarot)
    pdf.set_xy(10, y_card)
    pdf.set_fill_color(241, 245, 249)
    pdf.rect(10, y_card, card_w, card_h, "DF")
    pdf.set_font("helvetica", "B", 7.5)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(card_w, 4.5, sanitizar("FASE 1: TAROT (Peso 70%)"), 0, 1, "C")
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(card_w, 6.5, f"{p1:.1f}%", 0, 1, "C")
    pdf.set_font("helvetica", "I", 6.8)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(card_w, 4, sanitizar("Base Psicométrica e Comportamental"), 0, 0, "C")

    # Card 2: Fase 2 (Trânsitos)
    pdf.set_xy(10 + card_w + 3, y_card)
    pdf.rect(10 + card_w + 3, y_card, card_w, card_h, "DF")
    pdf.set_font("helvetica", "B", 7.5)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(card_w, 4.5, sanitizar("FASE 2: TRÂNSITOS (Peso 30%)"), 0, 1, "C")
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(card_w, 6.5, f"{p2:.1f}%", 0, 1, "C")
    pdf.set_font("helvetica", "I", 6.8)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(card_w, 4, sanitizar("Alinhamento Conjuntural Ativo"), 0, 0, "C")

    # Card 3: Índice Global Integrado
    pdf.set_xy(10 + (card_w * 2) + 6, y_card)
    if sinal_v:
        pdf.set_fill_color(254, 242, 242)
        pdf.set_draw_color(239, 68, 68)
    else:
        pdf.set_fill_color(240, 253, 244)
        pdf.set_draw_color(34, 197, 94)
    pdf.rect(10 + (card_w * 2) + 6, y_card, card_w, card_h, "DF")
    pdf.set_font("helvetica", "B", 7.5)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(card_w, 4.5, sanitizar("ÍNDICE GLOBAL INTEGRADO"), 0, 1, "C")
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(185, 28, 28) if sinal_v else pdf.set_text_color(21, 128, 61)
    pdf.cell(card_w, 6.5, f"{ig:.1f}%", 0, 1, "C")
    pdf.set_font("helvetica", "B", 6.5)
    pdf.cell(card_w, 4, sanitizar(classif_str[:30]), 0, 0, "C")

    pdf.set_draw_color(203, 213, 225)
    pdf.set_xy(10, y_card + card_h + 2)

    # Faixa de Sinal Vermelho
    if sinal_v:
        pdf.set_fill_color(254, 226, 226)
        pdf.set_draw_color(239, 68, 68)
        pdf.set_font("helvetica", "B", 7.5)
        pdf.set_text_color(185, 28, 28)
        pdf.cell(0, 5, sanitizar(" [!] SINAL VERMELHO ATIVADO: Ponto crítico detectado nas bases de Resiliência ou Ética."), 1, 1, "L", True)
    else:
        pdf.set_fill_color(240, 253, 244)
        pdf.set_draw_color(34, 197, 94)
        pdf.set_font("helvetica", "B", 7.5)
        pdf.set_text_color(21, 128, 61)
        pdf.cell(0, 5, sanitizar(" [+] SINAL VERMELHO DESATIVADO: Bases comportamentais, psíquicas e éticas preservadas."), 1, 1, "L", True)
    
    pdf.set_draw_color(203, 213, 225)
    pdf.ln(3)

    # -------------------------------------------------------------
    # 2. DELIBERAÇÃO EXECUTIVA E PARECER DE ADEQUAÇÃO AO CARGO
    # -------------------------------------------------------------
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 5.5, sanitizar("2. DELIBERAÇÃO EXECUTIVA E PARECER DE ADEQUAÇÃO AO CARGO"), 0, 1, "L")
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(30, 41, 59)
    pdf.set_fill_color(255, 255, 255)
    texto_final = sanitizar(texto_conclusao_f3 or "Avaliação executiva com parecer dinâmico estruturado.")
    pdf.multi_cell(0, 4.3, texto_final, border=1, fill=True)
    pdf.ln(3)

    # -------------------------------------------------------------
    # 3. MAPEAMENTO DE DIMENSÕES & RISCOS ESTRUTURAIS (SWOT)
    # -------------------------------------------------------------
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 5.5, sanitizar("3. MAPEAMENTO DE DIMENSÕES & RISCOS ESTRUTURAIS"), 0, 1, "L")
    
    w_box = 93
    y_dim = pdf.get_y()
    pdf.set_fill_color(248, 250, 252)
    pdf.rect(10, y_dim, w_box, 20, "DF")
    pdf.rect(107, y_dim, w_box, 20, "DF")

    # Coluna 1: Forças
    pdf.set_xy(10, y_dim)
    pdf.set_font("helvetica", "B", 7.5)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(w_box, 4.5, sanitizar(" Principais Forças e Competências"), 0, 1, "L")
    pdf.set_font("helvetica", "", 7)
    pdf.set_text_color(51, 65, 85)
    pdf.cell(w_box, 3.8, sanitizar(" - Consistência analítica e tomada de decisão sob pressão."), 0, 1, "L")
    pdf.cell(w_box, 3.8, sanitizar(" - Alinhamento com o arquétipo corporativo deliberado."), 0, 1, "L")
    pdf.cell(w_box, 3.8, sanitizar(" - Visão sistêmica focada em sustentação de processos."), 0, 1, "L")

    # Coluna 2: Riscos
    pdf.set_xy(107, y_dim)
    pdf.set_font("helvetica", "B", 7.5)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(w_box, 4.5, sanitizar(" Pontos de Atenção (Riscos Operacionais)"), 0, 1, "L")
    pdf.set_font("helvetica", "", 7)
    pdf.set_text_color(51, 65, 85)
    pdf.set_x(107)
    pdf.cell(w_box, 3.8, sanitizar(" - Monitoramento rigoroso de fit cultural no período de teste."), 0, 1, "L")
    pdf.set_x(107)
    pdf.cell(w_box, 3.8, sanitizar(" - Alinhamento explícito de expectativas e entregas de curto prazo."), 0, 1, "L")
    pdf.set_x(107)
    pdf.cell(w_box, 3.8, sanitizar(" - Mitigação de sobrecarga emocional em picos de estresse operacional."), 0, 1, "L")

    pdf.set_xy(10, y_dim + 23)

    # -------------------------------------------------------------
    # 4. MATRIZ PSICOMÉTRICA E COMPORTAMENTAL (MÉTODO 8 CASAS)
    # -------------------------------------------------------------
    if pdf.get_y() > 220:
        pdf.add_page()

    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 5.5, sanitizar("4. MATRIZ PSICOMÉTRICA E COMPORTAMENTAL (MÉTODO 8 CASAS)"), 0, 1, "L")
    pdf.set_font("helvetica", "B", 7.5)
    pdf.set_fill_color(226, 232, 240)
    pdf.set_text_color(30, 41, 59)

    # Cabeçalho da Tabela
    pdf.cell(8, 5.5, "POS", 1, 0, "C", True)
    pdf.cell(32, 5.5, "COMPETÊNCIA", 1, 0, "L", True)
    pdf.cell(52, 5.5, "CARTAS (CENTRAL / NEG. / POS.)", 1, 0, "L", True)
    pdf.cell(12, 5.5, "NOTA", 1, 0, "C", True)
    pdf.cell(86, 5.5, "RESUMO DA LEITURA (SÍNTESE IA)", 1, 1, "L", True)

    pdf.set_font("helvetica", "", 7)
    if dados_tabela_f1 and isinstance(dados_tabela_f1, list):
        for item in dados_tabela_f1:
            if pdf.get_y() > 270:
                pdf.add_page()
            pos = str(item.get("pos", ""))
            comp = sanitizar(item.get("nome", ""))
            cartas = sanitizar(item.get("cartas", "").replace("\n", " | "))
            nota = f"{float(item.get('nota', 0)):.0f}"
            resumo = sanitizar(item.get("resumo", ""))

            pdf.cell(8, 5, pos, 1, 0, "C")
            pdf.cell(32, 5, f" {comp[:20]}", 1, 0, "L")
            pdf.cell(52, 5, f" {cartas[:38]}", 1, 0, "L")
            pdf.cell(12, 5, f"{nota}/5", 1, 0, "C")
            pdf.cell(86, 5, f" {resumo[:58]}...", 1, 1, "L")
    pdf.ln(3)

    # -------------------------------------------------------------
    # 5. MATRIZ ESTRUTURAL DAS 12 CASAS PONDERADAS POR ARQUÉTIPO
    # -------------------------------------------------------------
    if pdf.get_y() > 210:
        pdf.add_page()

    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 5.5, sanitizar("5. MATRIZ ESTRUTURAL DAS 12 CASAS PONDERADAS (TRÂNSITOS)"), 0, 1, "L")
    pdf.set_font("helvetica", "B", 7.5)
    pdf.set_fill_color(226, 232, 240)
    pdf.set_text_color(30, 41, 59)

    pdf.cell(12, 5.5, "CASA", 1, 0, "C", True)
    pdf.cell(35, 5.5, "SIGNO (CÚSPIDE)", 1, 0, "L", True)
    pdf.cell(16, 5.5, "NOTA", 1, 0, "C", True)
    pdf.cell(16, 5.5, "PESO", 1, 0, "C", True)
    pdf.cell(46, 5.5, "CLIMA DE TRÂNSITO", 1, 0, "L", True)
    pdf.cell(65, 5.5, "DIAGNÓSTICO (SÍNTESE)", 1, 1, "L", True)

    pdf.set_font("helvetica", "", 7)
    if mandala_dados:
        casas_lista = mandala_dados if isinstance(mandala_dados, list) else mandala_dados.values()
        for idx, m_item in enumerate(casas_lista, 1):
            if pdf.get_y() > 270:
                pdf.add_page()
            c_label = f"C{idx}"
            s_cuspide = sanitizar(m_item.get("signo", "Estável"))
            n_val = f"{float(m_item.get('nota', 4.0)):.1f}/5"
            p_val = f"{float(m_item.get('peso', 1.0)):.1f}x"
            clima = sanitizar(m_item.get("clima", "Estável"))
            diag = sanitizar(m_item.get("sintese", "Dinâmica operacional em estabilidade funcional."))

            pdf.cell(12, 4.8, c_label, 1, 0, "C")
            pdf.cell(35, 4.8, f" {s_cuspide[:22]}", 1, 0, "L")
            pdf.cell(16, 4.8, n_val, 1, 0, "C")
            pdf.cell(16, 4.8, p_val, 1, 0, "C")
            pdf.cell(46, 4.8, f" {clima[:28]}", 1, 0, "L")
            pdf.cell(65, 4.8, f" {diag[:44]}...", 1, 1, "L")
    pdf.ln(3)

    # -------------------------------------------------------------
    # 6. DIRETRIZES PARA O PLANO DE INTEGRAÇÃO (90 DIAS)
    # -------------------------------------------------------------
    if pdf.get_y() > 235:
        pdf.add_page()

    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 5.5, sanitizar("6. DIRETRIZES PARA O PLANO DE INTEGRAÇÃO (90 DIAS)"), 0, 1, "L")
    pdf.set_font("helvetica", "", 7.5)
    pdf.set_text_color(30, 41, 59)
    pdf.set_fill_color(248, 250, 252)

    plano_texto = (
        "Dias 1 a 30: Imersão institucional, alinhamento de expectativas com a diretoria e mapeamento de processos críticos.\n"
        "Dias 31 a 60: Assunção gradual de entregas táticas, liderança de comitês operacionais e validação de KPIs.\n"
        "Dias 61 a 90: Avaliação de impacto de 90 dias, entrega de projetos estruturantes e consolidação da governança sob o arquétipo."
    )
    pdf.multi_cell(0, 4.2, sanitizar(plano_texto), border=1, fill=True)
    pdf.ln(4)

    # -------------------------------------------------------------
    # 7. GOVERNANÇA E ASSINATURAS FORMAIS
    # -------------------------------------------------------------
    if pdf.get_y() > 255:
        pdf.add_page()

    pdf.ln(6)
    y_sign = pdf.get_y()
    pdf.set_draw_color(100, 116, 139)
    pdf.line(15, y_sign, 90, y_sign)
    pdf.line(120, y_sign, 195, y_sign)

    pdf.set_xy(15, y_sign + 1)
    pdf.set_font("helvetica", "B", 7.5)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(75, 4, sanitizar("COMITÊ AVALIADOR / RECURSOS HUMANOS"), 0, 0, "C")

    pdf.set_xy(120, y_sign + 1)
    pdf.cell(75, 4, sanitizar("DIRETORIA EXECUTIVA / COMPLIANCE"), 0, 1, "C")

    # Retorno binário seguro
    pdf_bytes = bytes(pdf.output())
    try:
        with open(output_pdf, "wb") as f:
            f.write(pdf_bytes)
    except Exception:
        pass

    return pdf_bytes