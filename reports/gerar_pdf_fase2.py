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

def formatar_cuspide(val):
    if not val:
        return "0° 0'"
    nums = re.findall(r'\d+', str(val))
    if len(nums) >= 2:
        return f"{nums[0]}° {nums[1]}'"
    if len(nums) == 1:
        return f"{nums[0]}° 0'"
    return str(val)

def formatar_data_exibicao(d_str):
    digitos = "".join(filter(str.isdigit, str(d_str)))
    if len(digitos) == 8:
        return f"{digitos[:2]}/{digitos[2:4]}/{digitos[4:]}"
    return str(d_str)

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

def obter_faixa_aderencia(aderencia_pct):
    if aderencia_pct >= 80.0:
        return {
            "status": "Alta Sinergia",
            "descricao": "Desempenho Robusto",
            "recomendacao": "Prontidão Imediata"
        }
    if aderencia_pct >= 65.0:
        return {
            "status": "Aderência Operacional",
            "descricao": "Desempenho Consistente com Atenção Pontual",
            "recomendacao": "Acompanhamento direcionado"
        }
    return {
        "status": "Ponto de Atenção",
        "descricao": "Ciclo Desafiador",
        "recomendacao": "Vulnerabilidade Temporária"
    }

def gerar_laudo_fase2_pdf(c_nome, c_vaga, c_nivel, arq_ativo, d_nasc, h_nasc, loc_nasc, big_three, transitos, mandala_dados, total_pts, perc_aderencia):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Cabeçalho Principal
    pdf.set_font("helvetica", "B", 13)
    pdf.cell(0, 6, sanitizar_pdf("LAUDO ESTRUTURAL E CONJUNTURAL DE RECRUTAMENTO"), 0, 1, "C")
    pdf.set_font("helvetica", "I", 8.5)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 5, sanitizar_pdf("Mapeamento Astrológico Ponderado & Clima Planetário em Trânsito (Fase 2)"), 0, 1, "C")
    pdf.ln(3)
    
    # Card 1: Identificação e Dados de Nascimento
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_fill_color(242, 245, 248)
    pdf.cell(0, 5.5, sanitizar_pdf(f"   CANDIDATO(A): {c_nome.upper() if c_nome else 'NÃO INFORMADO'}   |   CARGO: {c_vaga.upper() if c_vaga else 'NÃO INFORMADA'} ({c_nivel.upper()})"), 1, 1, "L", True)
    
    h_str = h_nasc.strftime("%H:%M") if hasattr(h_nasc, "strftime") else str(h_nasc)
    data_formatada = formatar_data_exibicao(d_nasc)
    linha_nasc = f"   Nascimento: {data_formatada} às {h_str}   |   Local: {loc_nasc}   |   Arquétipo: {arq_ativo}"
    pdf.set_font("helvetica", "", 7.5)
    pdf.cell(0, 5, sanitizar_pdf(linha_nasc), "LRB", 1, "L", False)
    pdf.ln(3)
    
    # Card 2: Trindade Principal (Big Three)
    pdf.set_font("helvetica", "B", 8.5)
    pdf.set_fill_color(230, 235, 242)
    pdf.cell(0, 5.5, sanitizar_pdf(" 1. TRINDADE PRINCIPAL (EIXOS ESTRUTURAIS DE PERSONALIDADE)"), 1, 1, "L", True)
    
    pdf.set_font("helvetica", "", 7.5)
    w_col = 63.3
    
    sol = big_three.get("Solar", {})
    asc = big_three.get("Ascendente", {})
    lua = big_three.get("Lunar", {})
    
    y_b3 = pdf.get_y()
    pdf.rect(10, y_b3, w_col, 12)
    pdf.rect(10 + w_col, y_b3, w_col, 12)
    pdf.rect(10 + (2 * w_col), y_b3, w_col + 0.1, 12)
    
    pdf.set_xy(10, y_b3 + 1.5)
    pdf.set_font("helvetica", "B", 7.5)
    pdf.cell(w_col, 4, "SIGNO SOLAR (Identidade/Propósito)", 0, 1, "C")
    pdf.set_font("helvetica", "", 7.5)
    pdf.cell(w_col, 4, sanitizar_pdf(f"{sol.get('signo', '-')} ({formatar_cuspide(sol.get('grau', ''))})"), 0, 0, "C")
    
    pdf.set_xy(10 + w_col, y_b3 + 1.5)
    pdf.set_font("helvetica", "B", 7.5)
    pdf.cell(w_col, 4, "SIGNO ASCENDENTE (Expressão/Postura)", 0, 1, "C")
    pdf.set_x(10 + w_col)
    pdf.set_font("helvetica", "", 7.5)
    pdf.cell(w_col, 4, sanitizar_pdf(f"{asc.get('signo', '-')} ({formatar_cuspide(asc.get('grau', ''))})"), 0, 0, "C")
    
    pdf.set_xy(10 + (2 * w_col), y_b3 + 1.5)
    pdf.set_font("helvetica", "B", 7.5)
    pdf.cell(w_col, 4, "SIGNO LUNAR (Maturidade Emocional)", 0, 1, "C")
    pdf.set_x(10 + (2 * w_col))
    pdf.set_font("helvetica", "", 7.5)
    pdf.cell(w_col, 4, sanitizar_pdf(f"{lua.get('signo', '-')} ({formatar_cuspide(lua.get('grau', ''))})"), 0, 1, "C")
    
    pdf.set_xy(10, y_b3 + 14)
    
    # Card 3: Clima Planetário em Trânsito
    pdf.set_font("helvetica", "B", 8.5)
    pdf.set_fill_color(230, 235, 242)
    pdf.cell(0, 5.5, sanitizar_pdf(" 2. CLIMA PLANETÁRIO EM TRÂNSITO (CICLO DO ANO CORRENTE)"), 1, 1, "L", True)
    
    if transitos:
        qtd_t = len(transitos)
        w_t = 190.0 / max(1, qtd_t)
        y_t = pdf.get_y()
        for idx, (p_nome, p_sig) in enumerate(transitos.items()):
            pdf.rect(10 + (idx * w_t), y_t, w_t, 10)
            pdf.set_xy(10 + (idx * w_t), y_t + 1)
            pdf.set_font("helvetica", "B", 7)
            pdf.cell(w_t, 3.8, sanitizar_pdf(p_nome), 0, 1, "C")
            pdf.set_x(10 + (idx * w_t))
            pdf.set_font("helvetica", "", 7)
            pdf.cell(w_t, 3.8, sanitizar_pdf(f"Posição Ativa: {p_sig}"), 0, 0, "C")
        pdf.set_xy(10, y_t + 12)
    else:
        pdf.set_font("helvetica", "I", 7.5)
        pdf.cell(0, 6, "Informações de trânsito em modo padrão estabilizado.", 1, 1, "C")
        pdf.ln(2)

    # Card 4: Matriz das 12 Casas (Título impresso RIGIDAMENTE antes da tabela)
    pdf.set_font("helvetica", "B", 8.5)
    pdf.set_fill_color(230, 235, 242)
    pdf.cell(0, 5.5, sanitizar_pdf(" 3. MATRIZ ESTRUTURAL DAS 12 CASAS PONDERADAS POR ARQUÉTIPO"), 1, 1, "L", True)
    
    # Definição estrita das 6 colunas (somam 190 mm)
    w_casa = 10
    w_signo = 32
    w_nota = 12
    w_peso = 12
    w_clima = 54
    w_diag = 70

    pdf.set_font("helvetica", "B", 7)
    pdf.set_fill_color(240, 243, 246)
    pdf.cell(w_casa, 5.5, "CASA", 1, 0, "C", True)
    pdf.cell(w_signo, 5.5, "SIGNO (CÚSPIDE)", 1, 0, "L", True)
    pdf.cell(w_nota, 5.5, "NOTA", 1, 0, "C", True)
    pdf.cell(w_peso, 5.5, "PESO", 1, 0, "C", True)
    pdf.cell(w_clima, 5.5, "CLIMA DE TRÂNSITO", 1, 0, "L", True)
    pdf.cell(w_diag, 5.5, "DIAGNÓSTICO (SÍNTESE)", 1, 1, "L", True)
    
    def calc_linhas(texto, larg_col, estilo):
        pdf.set_font("helvetica", estilo, 6.5)
        cont = 0
        for pedaco in str(texto).split("\n"):
            w = pdf.get_string_width(pedaco)
            cont += max(1, math.ceil(w / max(1.0, larg_col - 2)))
        return max(1, cont)

    for i in range(1, 13):
        k_casa = f"Casa {i}"
        d_val = mandala_dados.get(k_casa, {})
        signo_str = f"{d_val.get('signo', '')} ({formatar_cuspide(d_val.get('grau', ''))})"
        clima_raw = d_val.get('clima', 'Estável')
        escopo_casa = ESCOPO_CORPORATIVO_CASA.get(i, "Gestão de processos")
        
        esta_ativada = any(p in clima_raw for p in ["Júpiter", "Saturno", "Urano"])
        estilo_txt = "B" if esta_ativada else ""
        
        if "Júpiter" in clima_raw:
            clima_formatado = "[+] Ativado por Júpiter (Crescimento)"
            diag_txt = f"Ciclo expansivo: alavanca para {escopo_casa.lower()} com alta projeção de resultados."
        elif "Saturno" in clima_raw:
            clima_formatado = "[!] Ativado por Saturno (Rigor)"
            diag_txt = f"Ciclo de cobrança: exige auditoria, disciplina e controle rigoroso em {escopo_casa.lower()}."
        elif "Urano" in clima_raw:
            clima_formatado = "[*] Ativado por Urano (Inovação)"
            diag_txt = f"Ciclo disruptivo: impulsiona transformações ágeis e quebra de padrões em {escopo_casa.lower()}."
        else:
            clima_formatado = "Estável"
            diag_txt = f"{escopo_casa} operando em estabilidade funcional."

        l_clima = calc_linhas(clima_formatado, w_clima, estilo_txt)
        l_diag = calc_linhas(diag_txt, w_diag, estilo_txt)
        max_l = max(l_clima, l_diag, 1)
        h_linha = max(6.2, float(max_l * 3.0) + 1.8)

        y_topo = pdf.get_y()

        # Fundo sombreado para linhas ativadas
        if esta_ativada:
            pdf.set_fill_color(244, 246, 249)
        else:
            pdf.set_fill_color(255, 255, 255)

        # Grade estrutural
        pdf.rect(10, y_topo, w_casa, h_linha, "DF")
        pdf.rect(10 + w_casa, y_topo, w_signo, h_linha, "DF")
        pdf.rect(10 + w_casa + w_signo, y_topo, w_nota, h_linha, "DF")
        pdf.rect(10 + w_casa + w_signo + w_nota, y_topo, w_peso, h_linha, "DF")
        pdf.rect(10 + w_casa + w_signo + w_nota + w_peso, y_topo, w_clima, h_linha, "DF")
        pdf.rect(10 + w_casa + w_signo + w_nota + w_peso + w_clima, y_topo, w_diag, h_linha, "DF")

        # Conteúdo com posicionamento estrito por coluna
        pdf.set_font("helvetica", estilo_txt, 6.5)
        
        pdf.set_xy(10, y_topo + (h_linha / 2) - 1.8)
        pdf.cell(w_casa, 3.5, f"C{i}", 0, 0, "C")
        
        pdf.set_xy(10 + w_casa + 1, y_topo + (h_linha / 2) - 1.8)
        pdf.cell(w_signo - 2, 3.5, sanitizar_pdf(signo_str), 0, 0, "L")
        
        pdf.set_xy(10 + w_casa + w_signo, y_topo + (h_linha / 2) - 1.8)
        pdf.cell(w_nota, 3.5, f"{d_val.get('nota_base', ''):.1f}/5", 0, 0, "C")
        
        pdf.set_xy(10 + w_casa + w_signo + w_nota, y_topo + (h_linha / 2) - 1.8)
        pdf.cell(w_peso, 3.5, f"{d_val.get('peso', '')}x", 0, 0, "C")
        
        pdf.set_xy(10 + w_casa + w_signo + w_nota + w_peso + 1, y_topo + 1.0)
        pdf.multi_cell(w_clima - 2, 2.9, sanitizar_pdf(clima_formatado), 0, "L")

        pdf.set_xy(10 + w_casa + w_signo + w_nota + w_peso + w_clima + 1, y_topo + 1.0)
        pdf.multi_cell(w_diag - 2, 2.9, sanitizar_pdf(diag_txt), 0, "L")

        # Garante avanço perfeito para a base da linha desenhada
        pdf.set_xy(10, y_topo + h_linha)
        
    pdf.ln(3)
    
    # Dashboard executivo com pontuação e aderência calculadas sobre o teto de 60.
    pontos_fase2 = float(total_pts)
    aderencia_pct = (pontos_fase2 / 60.0) * 100
    faixa = obter_faixa_aderencia(aderencia_pct)
    altura_quadros = 28.0
    altura_sintese = 29.0
    if pdf.get_y() + altura_quadros + altura_sintese + 6.0 > 275:
        pdf.add_page()

    x_inicio = 10.0
    largura_quadro = 93.0
    espaco_quadros = 4.0
    y_quadros = pdf.get_y()

    if aderencia_pct >= 80.0:
        cor_badge = (220, 252, 231)
        cor_badge_txt = (22, 101, 52)
    elif aderencia_pct >= 65.0:
        cor_badge = (254, 243, 199)
        cor_badge_txt = (146, 64, 14)
    else:
        cor_badge = (254, 226, 226)
        cor_badge_txt = (153, 27, 27)

    def renderizar_card(x, titulo, valor, badge):
        pdf.set_draw_color(190, 195, 202)
        pdf.set_fill_color(248, 250, 252)
        pdf.rect(x, y_quadros, largura_quadro, altura_quadros, "DF")
        pdf.set_xy(x + 2.5, y_quadros + 2.0)
        pdf.set_font("helvetica", "B", 8)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(largura_quadro - 5, 4.2, sanitizar_pdf(titulo), 0, 1, "L")
        pdf.set_xy(x + 2.5, y_quadros + 7.0)
        pdf.set_font("helvetica", "B", 14)
        pdf.set_text_color(24, 43, 73)
        pdf.cell(largura_quadro - 5, 7.0, sanitizar_pdf(valor), 0, 1, "L")
        y_badge = y_quadros + altura_quadros - 10.5
        pdf.set_fill_color(*cor_badge)
        pdf.rect(x + 2.5, y_badge, largura_quadro - 5, 7.5, "DF")
        pdf.set_xy(x + 4, y_badge + 1.8)
        pdf.set_font("helvetica", "B", 7.0)
        pdf.set_text_color(*cor_badge_txt)
        pdf.cell(largura_quadro - 8, 3.8, sanitizar_pdf(badge.upper()), 0, 0, "C")

    renderizar_card(x_inicio, "CAPACIDADE ESTRUTURAL", f"{pontos_fase2:.1f} / 60.0", f"{faixa['status']} / {faixa['descricao']}")
    renderizar_card(x_inicio + largura_quadro + espaco_quadros, "ADERÊNCIA AO CICLO", f"{aderencia_pct:.1f}%", faixa["recomendacao"])

    y_sintese = y_quadros + altura_quadros + 4.0
    pdf.set_draw_color(190, 195, 202)
    pdf.set_fill_color(248, 250, 252)
    pdf.rect(x_inicio, y_sintese, 190.0, altura_sintese, "DF")
    pdf.set_fill_color(*cor_badge_txt)
    pdf.rect(x_inicio, y_sintese, 3.0, altura_sintese, "F")
    pdf.set_xy(x_inicio + 7, y_sintese + 2.0)
    pdf.set_font("helvetica", "B", 8.5)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(180, 4.5, sanitizar_pdf("DIAGNÓSTICO EXECUTIVO INTEGRADO"), 0, 1, "L")
    pdf.set_font("helvetica", "", 7.5)
    sintese = (
        f"A pontuação líquida de {pontos_fase2:.1f} pontos representa {aderencia_pct:.1f}% de aderência estrutural. "
        f"O resultado enquadra o candidato em {faixa['status']}, com {faixa['descricao'].lower()} "
        f"e recomendação de {faixa['recomendacao'].lower()}."
    )
    pdf.set_xy(x_inicio + 7, y_sintese + 8.0)
    pdf.multi_cell(180, 3.8, sanitizar_pdf(sintese), 0, "L")
    
    res = pdf.output(dest="S")
    return res.encode("latin1") if isinstance(res, str) else bytes(res)