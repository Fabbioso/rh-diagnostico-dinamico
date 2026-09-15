from datetime import datetime
import math
import re
from fpdf import FPDF

def sanitizar_pdf(texto):
    if not texto:
        return ""
    texto = str(texto).replace("•", "-")
    texto = texto.replace("**", "").replace("###", "").replace("##", "").replace("#", "").replace("*", "").replace("$", "")
    texto = texto.replace("✨", "[+] ").replace("🛡️", "[!] ").replace("⚡", "[*] ")
    texto = texto.replace("°", chr(186)).replace("deg", chr(186))
    texto = re.sub(r'[^\x00-\xFF]', '', texto)
    try:
        return texto.encode('latin-1', 'replace').decode('latin-1')
    except Exception:
        return str(texto)

def quebrar_texto_em_linhas(pdf, texto, largura_max, estilo="", tam_fonte=6.5):
    linhas = []
    pdf.set_font("helvetica", estilo, tam_fonte)
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

ESCOPO_CORPORATIVO_CASA = {
    1: "Identidade executiva e liderança",
    2: "Gestão orçamentária e recursos",
    3: "Comunicação e alinhamento tático",
    4: "Sustentação interna e equipe",
    5: "Criatividade e apetite ao risco",
    6: "Rotina operacional e eficiência",
    7: "Alianças e relações bilaterais",
    8: "Gestão de crises e compliance",
    9: "Visão estratégica e expansão",
    10: "Metas executivas e governança",
    11: "Articulação e projetos coletivos",
    12: "Riscos ocultos e resiliência"
}

def gerar_laudo_fase3_pdf(c_nome, c_vaga, c_nivel, arq_ativo, perc_fase1, perc_fase2, indice_global, classificacao, sinal_vermelho, texto_conclusao, mandala_dados, dados_casas_f1):
    pdf = FPDF()
    
    # -------------------------------------------------------------
    # PÁGINA 1: CAPA EXECUTIVA, PAINEL MÉTRICO & DELIBERAÇÃO FINAL
    # -------------------------------------------------------------
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)
    
    # Barra Superior Azul
    pdf.set_fill_color(24, 43, 73)
    pdf.rect(10, 10, 190, 4, "F")
    
    pdf.set_xy(10, 18)
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 7, sanitizar_pdf("LAUDO EXECUTIVO INTEGRADO DE RECRUTAMENTO"), 0, 1, "C")
    
    pdf.set_font("helvetica", "I", 8.5)
    pdf.set_text_color(100, 110, 120)
    pdf.cell(0, 5, sanitizar_pdf("Fase 3: Governança Final, Cruzamento Ponderado & Deliberação Executiva"), 0, 1, "C")
    pdf.ln(3)
    
    # Card 1: Identificação Executiva
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(245, 247, 250)
    pdf.set_draw_color(205, 212, 222)
    
    y_card1 = pdf.get_y()
    pdf.rect(10, y_card1, 190, 20, "DF")
    
    pdf.set_font("helvetica", "B", 7.5)
    pdf.text(13, y_card1 + 5.5, "CANDIDATO(A):")
    pdf.text(13, y_card1 + 11.5, "VAGA / CARGO:")
    pdf.text(13, y_card1 + 17.5, "ARQUÉTIPO:")
    
    pdf.set_font("helvetica", "", 7.5)
    pdf.text(38, y_card1 + 5.5, sanitizar_pdf(c_nome.upper() if c_nome else 'NÃO INFORMADO'))
    pdf.text(38, y_card1 + 11.5, sanitizar_pdf(f"{c_vaga.upper() if c_vaga else 'NÃO INFORMADA'} ({c_nivel.upper()})"))
    pdf.text(38, y_card1 + 17.5, sanitizar_pdf(arq_ativo))
    
    pdf.set_font("helvetica", "B", 7.5)
    pdf.text(145, y_card1 + 5.5, "DATA DE EMISSÃO:")
    pdf.set_font("helvetica", "", 7.5)
    pdf.text(174, y_card1 + 5.5, datetime.now().strftime("%d/%m/%Y"))
    
    # Card 2: Painel Métrico Consolidado
    pdf.set_xy(10, y_card1 + 24)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_fill_color(230, 235, 242)
    pdf.cell(0, 5.5, sanitizar_pdf(" 1. SUMÁRIO EXECUTIVO DE ADERÊNCIA E DIRETRIZ FINAL"), 1, 1, "L", True)
    
    y_box_m = pdf.get_y()
    w_m = 63.3
    h_box_m = 18
    
    pdf.rect(10, y_box_m, w_m, h_box_m)
    pdf.rect(10 + w_m, y_box_m, w_m, h_box_m)
    pdf.rect(10 + (2 * w_m), y_box_m, w_m + 0.1, h_box_m)
    
    # Fase 1
    pdf.set_xy(10, y_box_m + 2.0)
    pdf.set_font("helvetica", "B", 6.8)
    pdf.cell(w_m, 3.2, "FASE 1: TAROT COMPORTAMENTAL", 0, 1, "C")
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(40, 60, 90)
    pdf.cell(w_m, 6.0, f"{perc_fase1:.1f}%", 0, 1, "C")
    pdf.set_font("helvetica", "I", 6.5)
    pdf.set_text_color(110, 110, 110)
    pdf.cell(w_m, 3.2, "Peso Aplicado: 70%", 0, 0, "C")
    
    # Fase 2
    pdf.set_xy(10 + w_m, y_box_m + 2.0)
    pdf.set_font("helvetica", "B", 6.8)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(w_m, 3.2, "FASE 2: ESTRUTURAL & TRÂNSITOS", 0, 1, "C")
    pdf.set_x(10 + w_m)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(40, 60, 90)
    pdf.cell(w_m, 6.0, f"{perc_fase2:.1f}%", 0, 1, "C")
    pdf.set_x(10 + w_m)
    pdf.set_font("helvetica", "I", 6.5)
    pdf.set_text_color(110, 110, 110)
    pdf.cell(w_m, 3.2, "Peso Aplicado: 30%", 0, 0, "C")
    
    # Global
    pdf.set_xy(10 + (2 * w_m), y_box_m + 2.0)
    pdf.set_font("helvetica", "B", 6.8)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(w_m, 3.2, "ÍNDICE GLOBAL INTEGRADO", 0, 1, "C")
    pdf.set_x(10 + (2 * w_m))
    pdf.set_font("helvetica", "B", 11.5)
    if indice_global >= 65:
        pdf.set_text_color(20, 110, 60)
    else:
        pdf.set_text_color(170, 30, 30)
    pdf.cell(w_m, 6.0, f"{indice_global:.1f}%", 0, 1, "C")
    pdf.set_x(10 + (2 * w_m))
    pdf.set_font("helvetica", "B", 6.5)
    pdf.cell(w_m, 3.2, sanitizar_pdf(classificacao.split('(')[0].strip()), 0, 0, "C")
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(10, y_box_m + h_box_m + 3.0)
    
    # Barra de Status do Sinal Vermelho
    y_alerta = pdf.get_y()
    pdf.set_font("helvetica", "B", 7.2)
    if str(sinal_vermelho).strip().upper() == "SIM":
        pdf.set_fill_color(253, 237, 237)
        pdf.set_draw_color(230, 130, 130)
        pdf.set_text_color(160, 20, 20)
        pdf.rect(10, y_alerta, 190, 6.5, "DF")
        pdf.text(14, y_alerta + 4.5, sanitizar_pdf("[!] SINAL VERMELHO ATIVADO: Ponto crítico detectado nas bases de Resiliência ou Ética (Casas 6, 7 ou 8)."))
    else:
        pdf.set_fill_color(235, 247, 238)
        pdf.set_draw_color(140, 200, 150)
        pdf.set_text_color(20, 110, 40)
        pdf.rect(10, y_alerta, 190, 6.5, "DF")
        pdf.text(14, y_alerta + 4.5, sanitizar_pdf("[+] SINAL VERMELHO DESATIVADO: Bases comportamentais, psíquicas e éticas preservadas."))
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_draw_color(205, 212, 222)
    pdf.set_xy(10, y_alerta + 10.0)
    
    # Card 3: Deliberação Executiva Ampla (Ocupa o restante nobre da Página 1)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_fill_color(230, 235, 242)
    pdf.cell(0, 5.5, sanitizar_pdf(" 2. DELIBERAÇÃO EXECUTIVA E PARECER DE ADEQUAÇÃO AO CARGO"), 1, 1, "L", True)
    
    linhas_parecer = quebrar_texto_em_linhas(pdf, texto_conclusao, 186, estilo="", tam_fonte=7.5)
    h_parecer = max(40.0, float(len(linhas_parecer) * 3.8) + 6.0)
    
    y_box_p = pdf.get_y()
    pdf.rect(10, y_box_p, 190, h_parecer)
    pdf.set_font("helvetica", "", 7.5)
    for idx_p, l_str in enumerate(linhas_parecer):
        pdf.text(13, y_box_p + 4.5 + (idx_p * 3.8), sanitizar_pdf(l_str))

    # -------------------------------------------------------------
    # PÁGINA 2: MATRIZ FASE 1 + MATRIZ FASE 2 + ASSINATURAS
    # -------------------------------------------------------------
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)
    
    # Barra Superior
    pdf.set_fill_color(24, 43, 73)
    pdf.rect(10, 10, 190, 3.5, "F")
    
    # 1. Matriz de 8 Casas (Fase 1)
    pdf.set_xy(10, 16)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_fill_color(230, 235, 242)
    pdf.cell(0, 5.0, sanitizar_pdf(" 3. MATRIZ PSICOMÉTRICA E COMPORTAMENTAL (MÉTODO 8 CASAS)"), 1, 1, "L", True)
    
    w_pos = 8
    w_comp = 28
    w_cart = 60
    w_nota = 10
    w_sint = 84

    pdf.set_font("helvetica", "B", 6.5)
    pdf.set_fill_color(240, 243, 246)
    pdf.cell(w_pos, 4.5, "POS", 1, 0, "C", True)
    pdf.cell(w_comp, 4.5, "COMPETÊNCIA", 1, 0, "L", True)
    pdf.cell(w_cart, 4.5, "CARTAS (CENTRAL / NEGATIVA / POSITIVA)", 1, 0, "L", True)
    pdf.cell(w_nota, 4.5, "NOTA", 1, 0, "C", True)
    pdf.cell(w_sint, 4.5, "RESUMO DA LEITURA", 1, 1, "L", True)
    
    cursor_y_f1 = pdf.get_y()
    
    for item in dados_casas_f1:
        i_num = item["pos"]
        nome_c = item["nome"]
        cartas_t = item["cartas"]
        nota_v = item["nota"]
        resumo_t = item["resumo"]
        
        l_c = quebrar_texto_em_linhas(pdf, nome_c, w_comp, estilo="", tam_fonte=6.2)
        l_cr = quebrar_texto_em_linhas(pdf, cartas_t, w_cart, estilo="", tam_fonte=6.0)
        l_s = quebrar_texto_em_linhas(pdf, resumo_t, w_sint, estilo="", tam_fonte=6.0)
        
        max_l = max(len(l_c), len(l_cr), len(l_s), 3)
        h_linha = max(11.0, float(max_l * 2.8) + 1.8)
        
        pdf.rect(10, cursor_y_f1, w_pos, h_linha)
        pdf.rect(10 + w_pos, cursor_y_f1, w_comp, h_linha)
        pdf.rect(10 + w_pos + w_comp, cursor_y_f1, w_cart, h_linha)
        pdf.rect(10 + w_pos + w_comp + w_cart, cursor_y_f1, w_nota, h_linha)
        pdf.rect(10 + w_pos + w_comp + w_cart + w_nota, cursor_y_f1, w_sint, h_linha)
        
        pdf.set_font("helvetica", "", 6.5)
        pdf.text(10 + (w_pos / 2) - 1.2, cursor_y_f1 + (h_linha / 2) + 1.0, str(i_num))
        
        pdf.set_font("helvetica", "", 6.2)
        for idx, t in enumerate(l_c):
            pdf.text(10 + w_pos + 1.2, cursor_y_f1 + 2.8 + (idx * 2.7), sanitizar_pdf(t))
            
        pdf.set_font("helvetica", "", 6.0)
        for idx, t in enumerate(l_cr):
            pdf.text(10 + w_pos + w_comp + 1.2, cursor_y_f1 + 2.8 + (idx * 2.6), sanitizar_pdf(t))
            
        pdf.set_font("helvetica", "", 6.5)
        pdf.text(10 + w_pos + w_comp + w_cart + (w_nota / 2) - 1.2, cursor_y_f1 + (h_linha / 2) + 1.0, str(nota_v))
        
        pdf.set_font("helvetica", "", 6.0)
        for idx, t in enumerate(l_s):
            pdf.text(10 + w_pos + w_comp + w_cart + w_nota + 1.2, cursor_y_f1 + 2.8 + (idx * 2.6), sanitizar_pdf(t))
            
        cursor_y_f1 += h_linha
    
    # 2. Matriz de 12 Casas (Fase 2)
    pdf.set_xy(10, cursor_y_f1 + 4.0)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_fill_color(230, 235, 242)
    pdf.cell(0, 5.0, sanitizar_pdf(" 4. MATRIZ ESTRUTURAL DAS 12 CASAS PONDERADAS POR ARQUÉTIPO (DIAGNÓSTICO)"), 1, 1, "L", True)
    
    w_c_casa = 10
    w_c_sig = 32
    w_c_nota = 12
    w_c_peso = 12
    w_c_clima = 54
    w_c_diag = 70

    pdf.set_font("helvetica", "B", 6.5)
    pdf.set_fill_color(240, 243, 246)
    pdf.cell(w_c_casa, 4.5, "CASA", 1, 0, "C", True)
    pdf.cell(w_c_sig, 4.5, "SIGNO (CÚSPIDE)", 1, 0, "L", True)
    pdf.cell(w_c_nota, 4.5, "NOTA", 1, 0, "C", True)
    pdf.cell(w_c_peso, 4.5, "PESO", 1, 0, "C", True)
    pdf.cell(w_c_clima, 4.5, "CLIMA DE TRÂNSITO", 1, 0, "L", True)
    pdf.cell(w_c_diag, 4.5, "DIAGNÓSTICO (SÍNTESE)", 1, 1, "L", True)

    cursor_y_f2 = pdf.get_y()

    for i in range(1, 13):
        k_casa = f"Casa {i}"
        d_val = mandala_dados.get(k_casa, {})
        signo_str = f"{d_val.get('signo', '')} ({d_val.get('grau', '')})"
        clima_raw = d_val.get('clima', 'Estável')
        escopo_casa = ESCOPO_CORPORATIVO_CASA.get(i, "Gestão de processos")
        
        esta_ativada = any(p in clima_raw for p in ["Júpiter", "Saturno", "Urano"])
        estilo_txt = "B" if esta_ativada else ""
        
        if "Júpiter" in clima_raw:
            clima_formatado = "[+] Ativado por Júpiter (Crescimento)"
            diag_txt = f"Ciclo expansivo: alavanca para {escopo_casa.lower()} com alta projeção."
        elif "Saturno" in clima_raw:
            clima_formatado = "[!] Ativado por Saturno (Rigor)"
            diag_txt = f"Ciclo de cobrança: exige auditoria, disciplina e controle em {escopo_casa.lower()}."
        elif "Urano" in clima_raw:
            clima_formatado = "[*] Ativado por Urano (Inovação)"
            diag_txt = f"Ciclo disruptivo: impulsiona transformações ágeis e inovação em {escopo_casa.lower()}."
        else:
            clima_formatado = "Estável"
            diag_txt = f"{escopo_casa} operando em estabilidade funcional."

        linhas_cl = quebrar_texto_em_linhas(pdf, clima_formatado, w_c_clima, estilo_txt, tam_fonte=6.2)
        linhas_dg = quebrar_texto_em_linhas(pdf, diag_txt, w_c_diag, estilo_txt, tam_fonte=6.2)
        max_l = max(len(linhas_cl), len(linhas_dg), 1)
        h_linha_m = max(5.6, float(max_l * 2.7) + 1.4)

        if esta_ativada:
            pdf.set_fill_color(244, 246, 249)
        else:
            pdf.set_fill_color(255, 255, 255)

        pdf.rect(10, cursor_y_f2, w_c_casa, h_linha_m, "DF")
        pdf.rect(10 + w_c_casa, cursor_y_f2, w_c_sig, h_linha_m, "DF")
        pdf.rect(10 + w_c_casa + w_c_sig, cursor_y_f2, w_c_nota, h_linha_m, "DF")
        pdf.rect(10 + w_c_casa + w_c_sig + w_c_nota, cursor_y_f2, w_c_peso, h_linha_m, "DF")
        pdf.rect(10 + w_c_casa + w_c_sig + w_c_nota + w_c_peso, cursor_y_f2, w_c_clima, h_linha_m, "DF")
        pdf.rect(10 + w_c_casa + w_c_sig + w_c_nota + w_c_peso + w_c_clima, cursor_y_f2, w_c_diag, h_linha_m, "DF")

        pdf.set_font("helvetica", estilo_txt, 6.2)
        pdf.text(10 + (w_c_casa / 2) - 1.2, cursor_y_f2 + (h_linha_m / 2) + 0.9, f"C{i}")
        pdf.text(10 + w_c_casa + 1.2, cursor_y_f2 + (h_linha_m / 2) + 0.9, sanitizar_pdf(signo_str))
        pdf.text(10 + w_c_casa + w_c_sig + (w_c_nota / 2) - 1.2, cursor_y_f2 + (h_linha_m / 2) + 0.9, f"{d_val.get('nota_base', ''):.1f}/5")
        pdf.text(10 + w_c_casa + w_c_sig + w_c_nota + (w_c_peso / 2) - 1.2, cursor_y_f2 + (h_linha_m / 2) + 0.9, f"{d_val.get('peso', '')}x")
        
        for idx_c, l_txt in enumerate(linhas_cl):
            pdf.text(10 + w_c_casa + w_c_sig + w_c_nota + w_c_peso + 1.2, cursor_y_f2 + 2.7 + (idx_c * 2.6), sanitizar_pdf(l_txt))

        for idx_d, l_txt in enumerate(linhas_dg):
            pdf.text(10 + w_c_casa + w_c_sig + w_c_nota + w_c_peso + w_c_clima + 1.2, cursor_y_f2 + 2.7 + (idx_d * 2.6), sanitizar_pdf(l_txt))

        cursor_y_f2 += h_linha_m

    pdf.set_xy(10, cursor_y_f2 + 4.5)
    
    # 3. Quadro de Assinaturas e Governança
    y_sign = pdf.get_y()
    pdf.rect(10, y_sign, 190, 18)
    
    pdf.set_font("helvetica", "B", 7)
    pdf.text(25, y_sign + 11.5, "__________________________________________")
    pdf.text(115, y_sign + 11.5, "__________________________________________")
    
    pdf.text(40, y_sign + 15.5, "COMITÊ AVALIADOR / RH")
    pdf.text(130, y_sign + 15.5, "DIRETORIA EXECUTIVA")
    
    res = pdf.output(dest="S")
    return res.encode("latin1") if isinstance(res, str) else bytes(res)