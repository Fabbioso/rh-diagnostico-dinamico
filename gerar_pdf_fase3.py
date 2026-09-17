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
    subs = {
        "—": "-", "–": "-", "“": '"', "”": '"', "‘": "'", "’": "'",
        "•": "-", "…": "...", "→": "->", "←": "<-", "º": "°", "ª": "a"
    }
    for orig, dest in subs.items():
        txt = txt.replace(orig, dest)
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
    
    pdf.set_xy(x, y + 2)
    pdf.set_font("helvetica", "B", 7)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(w, 3.5, sanitizar(titulo), 0, 0, "C")
    
    pdf.set_xy(x, y + 6)
    pdf.set_font("helvetica", "B", 11.5)
    pdf.set_text_color(*cor_txt)
    pdf.cell(w, 5.5, sanitizar(valor), 0, 0, "C")
    
    pdf.set_xy(x, y + 12)
    pdf.set_font("helvetica", "I", 5.8)
    pdf.set_text_color(100, 116, 139)
    pdf.multi_cell(w, 3.0, sanitizar(subtitulo), 0, "C")

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

    # 1. Sumário Executivo de Aderência
    pdf.set_font("helvetica", "B", 8.5)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 5, sanitizar("1. SUMÁRIO EXECUTIVO DE ADERÊNCIA E DIRETRIZ FINAL"), 0, 1, "L")
    
    y_cards = pdf.get_y()
    card_w = 61.3
    card_h = 19.5

    desenhar_card(pdf, 10, y_cards, card_w, card_h, "FASE 1: TAROT COMPORTAMENTAL", f"{p1:.1f}%", "Peso Aplicado: 70%", (241, 245, 249), (30, 41, 59))
    desenhar_card(pdf, 10 + card_w + 3, y_cards, card_w, card_h, "FASE 2: ESTRUTURAL & TRÂNSITOS", f"{p2:.1f}%", "Peso Aplicado: 30%", (241, 245, 249), (30, 41, 59))
    
    cor_bg_ig = (254, 242, 242) if sinal_v else (240, 253, 244)
    cor_tx_ig = (185, 28, 28) if sinal_v else (21, 128, 61)
    desenhar_card(pdf, 10 + (card_w * 2) + 6, y_cards, card_w, card_h, "ÍNDICE GLOBAL INTEGRADO", f"{ig:.1f}%", classif_str, cor_bg_ig, cor_tx_ig)

    pdf.set_xy(10, y_cards + card_h + 2)
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
    pdf.ln(2.5)

    # 2. Deliberação Executiva
    pdf.set_font("helvetica", "B", 8.5)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 4.8, sanitizar("2. DELIBERAÇÃO EXECUTIVA E PARECER DE ADEQUAÇÃO AO CARGO"), 0, 1, "L")
    pdf.set_font("helvetica", "", 7.2)
    pdf.set_text_color(30, 41, 59)
    pdf.multi_cell(0, 3.6, sanitizar(texto_conclusao_f3 or "Avaliação executiva concluída."), border=1)
    pdf.ln(2.5)

    # 3. Matriz Psicométrica (8 Casas) com Altura Dinâmica
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

    if dados_tabela_f1 and isinstance(dados_tabela_f1, list):
        for item in dados_tabela_f1:
            pos = str(item.get("pos", ""))
            comp = sanitizar(item.get("nome", ""))
            cartas_raw = item.get("cartas", "")
            
            # Formatação em 3 linhas limpas
            partes_cartas = [p.strip().replace("Carta Central:", "Central:").replace("Carta Negativa:", "Negativa:").replace("Carta Positiva:", "Positiva:") 
                             for p in str(cartas_raw).replace("\n", " | ").split("|") if p.strip()]
            cartas_txt = "\n".join(partes_cartas[:3])
            
            nota = f"{float(item.get('nota', 0)):.0f}"
            resumo = sanitizar(item.get("resumo", ""))

            # Cálculo de linhas reais para evitar corte e sobreposição
            pdf.set_font("helvetica", "", 6.2)
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
            
            total_linhas = max(3, len(partes_cartas[:3]), linhas_r)
            row_h = (total_linhas * 3.2) + 2.0

            y_row = pdf.get_y()

            # POS
            pdf.rect(10, y_row, 8, row_h)
            pdf.set_xy(10, y_row + (row_h / 2) - 2)
            pdf.set_font("helvetica", "B", 7)
            pdf.cell(8, 4, pos, 0, 0, "C")

            # COMPETÊNCIA
            pdf.rect(18, y_row, 28, row_h)
            pdf.set_xy(19, y_row + 1.2)
            pdf.set_font("helvetica", "B", 7)
            pdf.multi_cell(26, 3.4, comp, 0, "L")

            # CARTAS
            pdf.rect(46, y_row, 48, row_h)
            pdf.set_xy(47, y_row + 1.2)
            pdf.set_font("helvetica", "", 6.2)
            pdf.multi_cell(46, 3.2, sanitizar(cartas_txt), 0, "L")

            # NOTA
            pdf.rect(94, y_row, 10, row_h)
            pdf.set_xy(94, y_row + (row_h / 2) - 2)
            pdf.set_font("helvetica", "B", 7)
            pdf.cell(10, 4, f"{nota}/5", 0, 0, "C")

            # RESUMO
            pdf.rect(104, y_row, 96, row_h)
            pdf.set_xy(105, y_row + 1.2)
            pdf.set_font("helvetica", "", 6.2)
            pdf.multi_cell(94, 3.2, resumo, 0, "L")

            pdf.set_xy(10, y_row + row_h)

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

    pdf.cell(10, 5.5, "CASA", 1, 0, "C", True)
    pdf.cell(32, 5.5, "SIGNO (CÚSPIDE)", 1, 0, "L", True)
    pdf.cell(14, 5.5, "NOTA", 1, 0, "C", True)
    pdf.cell(14, 5.5, "PESO", 1, 0, "C", True)
    pdf.cell(48, 5.5, "CLIMA DE TRÂNSITO", 1, 0, "L", True)
    pdf.cell(72, 5.5, "DIAGNÓSTICO (SÍNTESE)", 1, 1, "L", True)

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

        # Formatação e diagnósticos alinhados com o laudo da Fase 2
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

        # Linhas do diagnóstico
        pdf.set_font("helvetica", "", 6.5)
        palavras_d = diag_txt.split()
        linhas_d = 1
        linha_at = ""
        for p in palavras_d:
            teste = f"{linha_at} {p}".strip()
            if pdf.get_string_width(teste) <= 70:
                linha_at = teste
            else:
                linhas_d += 1
                linha_at = p

        row_h2 = max(8.0, (linhas_d * 3.4) + 2.0)
        y_l2 = pdf.get_y()

        # CASA
        pdf.rect(10, y_l2, 10, row_h2)
        pdf.set_xy(10, y_l2 + (row_h2 / 2) - 2)
        pdf.set_font("helvetica", "B", 7)
        pdf.cell(10, 4, f"C{i}", 0, 0, "C")

        # SIGNO
        pdf.rect(20, y_l2, 32, row_h2)
        pdf.set_xy(21, y_l2 + 1.2)
        pdf.set_font("helvetica", "", 6.5)
        pdf.multi_cell(30, 3.2, sanitizar(signo_str), 0, "L")

        # NOTA
        pdf.rect(52, y_l2, 14, row_h2)
        pdf.set_xy(52, y_l2 + (row_h2 / 2) - 2)
        pdf.set_font("helvetica", "B", 7)
        pdf.cell(14, 4, f"{float(nota_val):.1f}/5", 0, 0, "C")

        # PESO
        pdf.rect(66, y_l2, 14, row_h2)
        pdf.set_xy(66, y_l2 + (row_h2 / 2) - 2)
        pdf.set_font("helvetica", "", 7)
        pdf.cell(14, 4, f"{float(peso_val):.1f}x", 0, 0, "C")

        # CLIMA
        pdf.rect(80, y_l2, 48, row_h2)
        pdf.set_xy(81, y_l2 + 1.2)
        esta_ativ = any(p in clima_formatado for p in ["Júpiter", "Saturno", "Urano"])
        pdf.set_font("helvetica", "B" if esta_ativ else "", 6.5)
        pdf.multi_cell(46, 3.2, sanitizar(clima_formatado), 0, "L")

        # DIAGNÓSTICO
        pdf.rect(128, y_l2, 72, row_h2)
        pdf.set_xy(129, y_l2 + 1.2)
        pdf.set_font("helvetica", "", 6.5)
        pdf.multi_cell(70, 3.2, sanitizar(diag_txt), 0, "L")

        pdf.set_xy(10, y_l2 + row_h2)

    # 5. Diretrizes para o Plano de Integração (90 Dias)
    pdf.ln(4)
    pdf.set_font("helvetica", "B", 8.5)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 5, sanitizar("5. DIRETRIZES PARA O PLANO DE INTEGRAÇÃO (90 DIAS)"), 0, 1, "L")
    pdf.set_font("helvetica", "", 7.2)
    pdf.set_text_color(30, 41, 59)
    pdf.set_fill_color(248, 250, 252)

    plano_texto = (
        "Dias 1 a 30: Imersão institucional, alinhamento de expectativas com a diretoria e mapeamento de processos críticos.\n"
        "Dias 31 a 60: Assunção gradual de entregas táticas, liderança de comitês operacionais e validação de indicadores de desempenho.\n"
        "Dias 61 a 90: Avaliação de impacto de 90 dias, entrega de projetos estruturantes e consolidação da governança sob o arquétipo."
    )
    pdf.multi_cell(0, 3.8, sanitizar(plano_texto), border=1, fill=True)
    pdf.ln(8)

    # Governança e Assinaturas
    y_sign = pdf.get_y()
    pdf.set_draw_color(100, 116, 139)
    pdf.line(20, y_sign, 85, y_sign)
    pdf.line(125, y_sign, 190, y_sign)

    pdf.set_xy(20, y_sign + 1)
    pdf.set_font("helvetica", "B", 7.5)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(65, 4, sanitizar("COMITÊ AVALIADOR / RECURSOS HUMANOS"), 0, 0, "C")

    pdf.set_xy(125, y_sign + 1)
    pdf.cell(65, 4, sanitizar("DIRETORIA EXECUTIVA / COMPLIANCE"), 0, 1, "C")

    pdf_bytes = bytes(pdf.output())
    try:
        with open(output_pdf, "wb") as f:
            f.write(pdf_bytes)
    except Exception:
        pass

    return pdf_bytes