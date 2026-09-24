from datetime import datetime
import os
import re
from fpdf import FPDF
from services.database_service import get_db_cursor

try:
    from weasyprint import HTML
    WEASYPRINT_DISPONIVEL = True
except Exception:
    WEASYPRINT_DISPONIVEL = False

def sanitizar_pdf(texto):
    """Normaliza strings removendo markdown e caracteres incompatíveis com latin-1."""
    if texto is None:
        return ""
    txt = str(texto)
    subs = {
        "—": "-", "–": "-", "“": '"', "”": '"', "‘": "'", "’": "'",
        "•": "-", "…": "...", "→": "->", "←": "<-", "º": chr(186), "ª": "a",
        "**": "", "###": "", "##": "", "#": "", "*": "", "$": ""
    }
    for orig, dest in subs.items():
        txt = txt.replace(orig, dest)
    txt = txt.replace("°", chr(186)).replace("deg", chr(186))
    txt = re.sub(r'[^\x00-\xFF]', '', txt)
    try:
        return txt.encode('latin-1', 'replace').decode('latin-1')
    except Exception:
        return str(txt)

class DossieExecutivoMasterPDF(FPDF):
    """Classe base executiva padronizada com a identidade visual corporativa da Fase 3."""
    def header(self):
        self.set_font("helvetica", "B", 11)
        self.set_text_color(24, 43, 73)
        self.cell(0, 5.5, sanitizar_pdf("DOSSIÊ EXECUTIVO INTEGRADO DE GOVERNANÇA"), 0, 1, "L")
        self.set_font("helvetica", "I", 7.5)
        self.set_text_color(100, 116, 139)
        self.cell(0, 3.8, sanitizar_pdf("Avaliação C-Level, Cruzamento Ponderado & Diretrizes Corporativas"), 0, 1, "L")
        self.set_draw_color(203, 213, 225)
        self.line(10, self.get_y() + 1.5, 200, self.get_y() + 1.5)
        self.ln(3)

    def footer(self):
        self.set_y(-10)
        self.set_font("helvetica", "I", 7.5)
        self.set_text_color(148, 163, 184)
        self.cell(130, 5, sanitizar_pdf("CONFIDENCIAL - Sistema de Diagnóstico Corporativo"), 0, 0, "L")
        self.cell(60, 5, sanitizar_pdf(f"Página {self.page_no()}"), 0, 0, "R")

def gerar_pdf_profissional(db_path="rh_diagnostico_dinamico.db", output_pdf="Laudo_Executivo_Profissional.pdf"):
    """
    Gera o Dossiê Executivo Integrado de Alta Governança (Fase 3) em HTML/CSS avançado
    com WeasyPrint e fallback automático de alta fidelidade para FPDF.
    """
    if not os.path.exists(db_path):
        print(f"[Aviso] Banco de dados '{db_path}' não encontrado.")
        return None

    # Consulta resiliente com suporte a nomes legados e padronizados de colunas
    with get_db_cursor(db_path) as cursor:
        cursor.execute("SELECT * FROM avaliacoes ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()

    if not row:
        print("[Aviso] Nenhum registro encontrado na tabela 'avaliacoes' para exportação.")
        return None

    d = dict(row)
    nome = d.get("nome_candidato") or d.get("nome") or "Candidato(a)"
    vaga = d.get("cargo_pretendido") or d.get("vaga") or "Não informada"
    nivel = d.get("nivel_hierarquico") or d.get("nivel") or "Executivo"
    data_reg = d.get("data_registro") or d.get("data") or datetime.now().strftime("%d/%m/%Y")
    pontos = d.get("pontuacao_fase1") if d.get("pontuacao_fase1") is not None else d.get("pontos", 0)
    classificacao = d.get("classificacao") or "Avaliado"
    sinal_vermelho = d.get("sinal_vermelho") or "Não"
    arquetipo = d.get("arquetipo_ativo") or d.get("arquetipo") or d.get("arquétipo") or "Governança, Compliance e Riscos"

    is_vermelho = str(sinal_vermelho).strip().lower() in ["sim", "true", "1", "ativo"]
    if is_vermelho:
        classificacao = "Não Recomendado (Veto de Governança)"

    # Indicadores calculados
    score_fase1 = float(pontos) * 2.5
    score_fase2 = float(d.get("score_fase2", 82.2))
    score_global = (score_fase1 * 0.7) + (score_fase2 * 0.3)
    
    if is_vermelho:
        alerta_bg = "#FEE2E2"
        alerta_border = "#EF4444"
        alerta_color = "#991B1B"
        alerta_texto = "[-] SINAL VERMELHO ATIVADO: Veto Mandatório de Governança (Risco em bases críticas)"
    else:
        alerta_bg = "#F0FDF4"
        alerta_border = "#22C55E"
        alerta_color = "#166534"
        alerta_texto = "[+] SINAL VERMELHO DESATIVADO: Bases comportamentais, psíquicas e éticas preservadas com consistência."

    # 1. Tentativa de renderização via WeasyPrint (HTML/CSS)
    if WEASYPRINT_DISPONIVEL:
        try:
            html_content = f"""
            <!DOCTYPE html>
            <html lang="pt-BR">
            <head>
                <meta charset="UTF-8">
                <title>Dossiê Executivo - {nome}</title>
                <style>
                    @page {{
                        size: A4;
                        margin: 15mm;
                        @bottom-right {{
                            content: "Página " counter(page) " de " counter(pages);
                            font-family: Helvetica, Arial, sans-serif;
                            font-size: 7.5pt;
                            color: #718096;
                        }}
                        @bottom-left {{
                            content: "CONFIDENCIAL — Sistema de Diagnóstico Corporativo";
                            font-family: Helvetica, Arial, sans-serif;
                            font-size: 7.5pt;
                            color: #718096;
                        }}
                    }}
                    body {{
                        font-family: Helvetica, Arial, sans-serif;
                        color: #2D3748;
                        font-size: 8.5pt;
                        line-height: 1.45;
                        margin: 0;
                        padding: 0;
                    }}
                    .header-bar {{
                        background-color: #182B49;
                        height: 5px;
                        width: 100%;
                        margin-bottom: 10px;
                    }}
                    h1 {{
                        text-align: center;
                        color: #182B49;
                        font-size: 13pt;
                        margin: 0 0 3px 0;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                    }}
                    .subtitle {{
                        text-align: center;
                        color: #64748B;
                        font-size: 8pt;
                        font-style: italic;
                        margin-bottom: 12px;
                    }}
                    .card-info {{
                        background-color: #F8FAFC;
                        border: 1px solid #CBD5E1;
                        border-radius: 4px;
                        padding: 8px 12px;
                        margin-bottom: 12px;
                    }}
                    .card-info table {{
                        width: 100%;
                        border-collapse: collapse;
                    }}
                    .card-info td {{
                        padding: 2px 0;
                        font-size: 8pt;
                    }}
                    .card-info td.label {{
                        font-weight: bold;
                        color: #475569;
                        width: 22%;
                    }}
                    .section-title {{
                        background-color: #F1F5F9;
                        color: #182B49;
                        font-size: 8.5pt;
                        font-weight: bold;
                        padding: 4px 8px;
                        margin-top: 10px;
                        margin-bottom: 6px;
                        border-left: 3px solid #182B49;
                        text-transform: uppercase;
                    }}
                    .metrics-table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-bottom: 10px;
                    }}
                    .metrics-table th, .metrics-table td {{
                        border: 1px solid #CBD5E1;
                        padding: 5px;
                        text-align: center;
                        font-size: 8pt;
                    }}
                    .metrics-table th {{
                        background-color: #F8FAFC;
                        color: #182B49;
                    }}
                    .metric-value {{
                        font-size: 10.5pt;
                        font-weight: bold;
                        color: #182B49;
                    }}
                    .alerta-box {{
                        background-color: {alerta_bg};
                        border: 1px solid {alerta_border};
                        color: {alerta_color};
                        padding: 6px 10px;
                        border-radius: 4px;
                        font-weight: bold;
                        font-size: 8pt;
                        margin-bottom: 10px;
                        text-align: center;
                    }}
                    .content-box {{
                        background-color: #FFFFFF;
                        border: 1px solid #CBD5E1;
                        border-radius: 4px;
                        padding: 8px 10px;
                        margin-bottom: 10px;
                        text-align: justify;
                    }}
                    .grid-2 {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-bottom: 10px;
                    }}
                    .grid-2 td {{
                        width: 50%;
                        vertical-align: top;
                        padding: 0 4px;
                    }}
                    .grid-2 td:first-child {{ padding-left: 0; }}
                    .grid-2 td:last-child {{ padding-right: 0; }}
                    .sub-box {{
                        background-color: #F8FAFC;
                        border: 1px solid #E2E8F0;
                        border-radius: 4px;
                        padding: 6px 8px;
                        height: 100%;
                    }}
                    .sub-box h4 {{
                        margin: 0 0 4px 0;
                        color: #182B49;
                        font-size: 8.5pt;
                        border-bottom: 1px solid #E2E8F0;
                        padding-bottom: 2px;
                    }}
                    .signature-section {{
                        margin-top: 20px;
                        page-break-inside: avoid;
                    }}
                    .signature-table {{
                        width: 100%;
                        border-collapse: collapse;
                    }}
                    .signature-table td {{
                        width: 50%;
                        text-align: center;
                        padding-top: 20px;
                        font-size: 7.5pt;
                        color: #475569;
                    }}
                    .signature-line {{
                        border-top: 1px solid #94A3B8;
                        width: 75%;
                        margin: 0 auto 3px auto;
                    }}
                </style>
            </head>
            <body>
                <div class="header-bar"></div>
                <h1>Dossiê Executivo Integrado de Governança</h1>
                <div class="subtitle">Avaliação C-Level, Cruzamento Ponderado & Diretrizes de Contratação</div>

                <div class="card-info">
                    <table>
                        <tr>
                            <td class="label">CANDIDATO(A):</td>
                            <td><strong>{nome.upper()}</strong></td>
                            <td class="label">EMISSÃO:</td>
                            <td>{data_reg}</td>
                        </tr>
                        <tr>
                            <td class="label">CARGO / NÍVEL:</td>
                            <td>{vaga.upper()} ({nivel})</td>
                            <td class="label">ARQUÉTIPO:</td>
                            <td>{arquetipo}</td>
                        </tr>
                    </table>
                </div>

                <div class="section-title">1. Sumário Executivo de Aderência Ponderada</div>
                <table class="metrics-table">
                    <tr>
                        <th>FASE 1: TAROT (Peso 70%)</th>
                        <th>FASE 2: TRÂNSITOS (Peso 30%)</th>
                        <th>ÍNDICE GLOBAL INTEGRADO</th>
                    </tr>
                    <tr>
                        <td>
                            <span class="metric-value">{score_fase1:.1f}%</span><br>
                            <small style="color: #64748B;">Base Psicométrica & Comportamental</small>
                        </td>
                        <td>
                            <span class="metric-value">{score_fase2:.1f}%</span><br>
                            <small style="color: #64748B;">Alinhamento Conjuntural Ativo</small>
                        </td>
                        <td>
                            <span class="metric-value" style="color: #166534;">{score_global:.1f}%</span><br>
                            <strong style="color: #182B49;">{classificacao}</strong>
                        </td>
                    </tr>
                </table>

                <div class="alerta-box">
                    {alerta_texto}
                </div>

                <div class="section-title">2. Mapeamento de Dimensões & Riscos Estruturais</div>
                <table class="grid-2">
                    <tr>
                        <td>
                            <div class="sub-box">
                                <h4>Principais Forças e Competências</h4>
                                <ul style="margin: 0; padding-left: 12px; font-size: 8pt;">
                                    <li>Consistência nos fundamentos analíticos e tomada de decisão sob pressão.</li>
                                    <li>Alinhamento direto com o arquétipo de liderança corporativa.</li>
                                    <li>Visão sistêmica apurada para cenários de governança e reestruturação.</li>
                                </ul>
                            </div>
                        </td>
                        <td>
                            <div class="sub-box">
                                <h4>Pontos de Atenção (Riscos Operacionais)</h4>
                                <ul style="margin: 0; padding-left: 12px; font-size: 8pt;">
                                    <li>Monitoramento de alinhamento cultural nos primeiros 90 dias de integração.</li>
                                    <li>Gestão contínua de expectativas em entregas críticas de curto prazo.</li>
                                    <li>Mitigação ativa de pontos cegos mapeados na matriz de resiliência.</li>
                                </ul>
                            </div>
                        </td>
                    </tr>
                </table>

                <div class="section-title">3. Parecer Deliberativo & Contexto Conjuntural</div>
                <div class="content-box">
                    <p style="margin: 0 0 5px 0;">O(A) candidato(a) <strong>{nome}</strong> foi submetido(a) a avaliação analítica para a posição de <strong>{vaga}</strong> sob o arquétipo <strong>{arquetipo}</strong>. O índice global consolidado situa-se em <strong>{classificacao} ({score_global:.1f}%)</strong>.</p>
                    <p style="margin: 0;">A avaliação consolida a base comportamental com o panorama estrutural e trâmites vigentes, provendo subsídios deliberativos de conformidade à diretoria executiva.</p>
                </div>

                <div class="section-title">4. Diretrizes para o Plano de Integração (90 Dias)</div>
                <div class="content-box">
                    <ul style="margin: 0; padding-left: 12px; font-size: 8pt;">
                        <li><strong>Dias 1 a 30:</strong> Imersão institucional, alinhamento de expectativas e mapeamento de processos críticos.</li>
                        <li><strong>Dias 31 a 60:</strong> Assunção gradual de entregas táticas e liderança de comitês operacionais.</li>
                        <li><strong>Dias 61 a 90:</strong> Avaliação de impacto de 90 dias, entrega de projetos estruturantes e consolidação da governança.</li>
                    </ul>
                </div>

                <div class="signature-section">
                    <table class="signature-table">
                        <tr>
                            <td>
                                <div class="signature-line"></div>
                                <strong>COMITÊ AVALIADOR / RECURSOS HUMANOS</strong>
                            </td>
                            <td>
                                <div class="signature-line"></div>
                                <strong>DIRETORIA EXECUTIVA / COMPLIANCE</strong>
                            </td>
                        </tr>
                    </table>
                </div>
            </body>
            </html>
            """
            HTML(string=html_content).write_pdf(output_pdf)
            return output_pdf
        except Exception as e:
            print(f"[Aviso] WeasyPrint indisponível ou falhou ({e}). Recorrendo ao motor executivo FPDF...")

    # 2. Fallback de Alta Fidelidade Executiva via FPDF
    pdf = DossieExecutivoMasterPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Card de identificação
    pdf.set_draw_color(203, 213, 225)
    pdf.set_fill_color(248, 250, 252)
    pdf.set_text_color(24, 43, 73)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(0, 5.0, sanitizar_pdf(f"  CANDIDATO(A): {nome.upper()}   |   EMISSÃO: {data_reg}"), 1, 1, "L", True)
    pdf.set_text_color(71, 85, 105)
    pdf.set_font("helvetica", "", 7.5)
    pdf.cell(0, 4.5, sanitizar_pdf(f"  CARGO: {vaga.upper()} ({nivel})   |   ARQUÉTIPO: {arquetipo}"), "LRB", 1, "L", False)
    pdf.ln(3)

    # 1. Sumário Executivo
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(24, 43, 73)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(0, 5.0, sanitizar_pdf(" 1. SUMÁRIO EXECUTIVO DE ADERÊNCIA PONDERADA"), 1, 1, "L", True)
    
    w_met = 190.0 / 3.0
    y_met = pdf.get_y()
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(10, y_met, w_met, 14, "DF")
    pdf.rect(10 + w_met, y_met, w_met, 14, "DF")
    pdf.rect(10 + (2 * w_met), y_met, w_met, 14, "DF")

    pdf.set_xy(10, y_met + 1.5)
    pdf.set_font("helvetica", "B", 7.0)
    pdf.cell(w_met, 3.5, sanitizar_pdf("FASE 1: TAROT (70%)"), 0, 1, "C")
    pdf.set_font("helvetica", "B", 9.5)
    pdf.cell(w_met, 4.5, f"{score_fase1:.1f}%", 0, 1, "C")
    pdf.set_font("helvetica", "", 6.5)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(w_met, 3.0, "Base Psicométrica", 0, 0, "C")

    pdf.set_xy(10 + w_met, y_met + 1.5)
    pdf.set_font("helvetica", "B", 7.0)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(w_met, 3.5, sanitizar_pdf("FASE 2: TRÂNSITOS (30%)"), 0, 1, "C")
    pdf.set_font("helvetica", "B", 9.5)
    pdf.cell(w_met, 4.5, f"{score_fase2:.1f}%", 0, 1, "C")
    pdf.set_font("helvetica", "", 6.5)
    pdf.set_text_color(100, 116, 139)
    pdf.set_x(10 + w_met)
    pdf.cell(w_met, 3.0, "Alinhamento Conjuntural", 0, 0, "C")

    pdf.set_xy(10 + (2 * w_met), y_met + 1.5)
    pdf.set_font("helvetica", "B", 7.0)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(w_met, 3.5, sanitizar_pdf("ÍNDICE GLOBAL INTEGRADO"), 0, 1, "C")
    pdf.set_font("helvetica", "B", 9.5)
    pdf.set_text_color(22, 101, 52)
    pdf.cell(w_met, 4.5, f"{score_global:.1f}%", 0, 1, "C")
    pdf.set_font("helvetica", "B", 6.5)
    pdf.set_text_color(24, 43, 73)
    pdf.set_x(10 + (2 * w_met))
    pdf.cell(w_met, 3.0, sanitizar_pdf(classificacao), 0, 1, "C")

    pdf.set_xy(10, y_met + 16.5)

    # Box de Alerta (Sinal Vermelho / Verde)
    if is_vermelho:
        pdf.set_fill_color(254, 226, 226)
        pdf.set_draw_color(239, 68, 68)
        pdf.set_text_color(153, 27, 27)
    else:
        pdf.set_fill_color(240, 253, 244)
        pdf.set_draw_color(34, 197, 94)
        pdf.set_text_color(22, 101, 52)

    pdf.set_font("helvetica", "B", 7.0)
    pdf.cell(0, 5.0, sanitizar_pdf(alerta_texto), 1, 1, "L", True)
    pdf.ln(2.5)

    # 2. Mapeamento de Forças e Riscos
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(24, 43, 73)
    pdf.set_fill_color(241, 245, 249)
    pdf.set_draw_color(203, 213, 225)
    pdf.cell(0, 5.0, sanitizar_pdf(" 2. MAPEAMENTO DE FORÇAS E RISCOS ESTRUTURAIS"), 1, 1, "L", True)
    
    w_card = 93.0
    y_card = pdf.get_y()
    pdf.set_fill_color(248, 250, 252)
    pdf.rect(10, y_card, w_card, 21, "DF")
    pdf.rect(10 + w_card + 4.0, y_card, w_card, 21, "DF")

    pdf.set_xy(10 + 2.5, y_card + 1.5)
    pdf.set_font("helvetica", "B", 7.0)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(w_card - 5, 3.5, sanitizar_pdf("PRINCIPAIS FORÇAS E COMPETÊNCIAS"), 0, 1, "L")
    pdf.set_font("helvetica", "", 6.5)
    pdf.set_text_color(71, 85, 105)
    forzes = [
        "- Consistência analítica e tomada de decisão sob pressão.",
        "- Alinhamento direto com o arquétipo corporativo.",
        "- Visão sistêmica apurada para cenários de governança."
    ]
    for f in forzes:
        pdf.set_x(10 + 2.5)
        pdf.cell(w_card - 5, 3.2, sanitizar_pdf(f), 0, 1, "L")

    pdf.set_xy(10 + w_card + 6.5, y_card + 1.5)
    pdf.set_font("helvetica", "B", 7.0)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(w_card - 5, 3.5, sanitizar_pdf("PONTOS DE ATENÇÃO (RISCOS OPERACIONAIS)"), 0, 1, "L")
    pdf.set_font("helvetica", "", 6.5)
    pdf.set_text_color(71, 85, 105)
    riscos = [
        "- Monitoramento de alinhamento cultural nos primeiros 90 dias.",
        "- Gestão contínua de expectativas em entregas de curto prazo.",
        "- Mitigação ativa de pontos cegos mapeados na resiliência."
    ]
    for r in riscos:
        pdf.set_x(10 + w_card + 6.5)
        pdf.cell(w_card - 5, 3.2, sanitizar_pdf(r), 0, 1, "L")

    pdf.set_xy(10, y_card + 23.5)

    # 3. Parecer Deliberativo
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(24, 43, 73)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(0, 5.0, sanitizar_pdf(" 3. PARECER DELIBERATIVO & CONTEXTO CONJUNTURAL"), 1, 1, "L", True)
    
    parecer_txt = (
        f"O(A) candidato(a) {nome} foi submetido(a) a avaliação analítica para a posição de {vaga} sob o arquétipo {arquetipo}. "
        + (
            f"Embora tenha atingido índice quantitativo de {score_global:.1f}%, a candidatura foi vetada compulsóriamente "
            f"pelas diretrizes de integridade e governança corporativa ('{classificacao}')."
            if is_vermelho else
            f"O perfil enquadra-se na diretriz de '{classificacao}' com score global de {score_global:.1f}%. "
            f"A análise cruzada confirma prontidão operacional e convergência com os objetivos da organização."
        )
    )
    pdf.set_font("helvetica", "", 7.5)
    pdf.set_text_color(51, 65, 85)
    pdf.multi_cell(0, 3.8, sanitizar_pdf(parecer_txt), 1, "L", False)
    pdf.ln(2.5)

    # 4. Diretrizes para Integração (90 Dias)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(24, 43, 73)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(0, 5.0, sanitizar_pdf(" 4. DIRETRIZES PARA O PLANO DE INTEGRAÇÃO (90 DIAS)"), 1, 1, "L", True)
    
    plano_txt = (
        "- Dias 1 a 30: Imersão institucional, alinhamento com diretoria e mapeamento de processos críticos.\n"
        "- Dias 31 a 60: Assunção tática gradual, liderança de comitês e validação de metas de desempenho.\n"
        "- Dias 61 a 90: Avaliação de impacto de 90 dias, entrega de projetos estruturantes e consolidação da governança."
    )
    pdf.set_font("helvetica", "", 7.5)
    pdf.set_text_color(51, 65, 85)
    pdf.multi_cell(0, 3.8, sanitizar_pdf(plano_txt), 1, "L", False)
    pdf.ln(5)

    # Assinaturas
    y_sig = pdf.get_y()
    pdf.set_draw_color(148, 163, 184)
    pdf.line(20, y_sig + 6, 90, y_sig + 6)
    pdf.line(120, y_sig + 6, 190, y_sig + 6)
    
    pdf.set_xy(20, y_sig + 7.5)
    pdf.set_font("helvetica", "B", 7.0)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(70, 3.5, "COMITÊ AVALIADOR / RH", 0, 0, "C")
    
    pdf.set_xy(120, y_sig + 7.5)
    pdf.cell(70, 3.5, "DIRETORIA EXECUTIVA / COMPLIANCE", 0, 1, "C")

    res = pdf.output(dest="S")
    with open(output_pdf, "wb") as f:
        f.write(res.encode("latin1") if isinstance(res, str) else bytes(res))
        
    return output_pdf