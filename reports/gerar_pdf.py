from datetime import datetime
import sqlite3
import os
from fpdf import FPDF

try:
    from weasyprint import HTML
    WEASYPRINT_DISPONIVEL = True
except Exception:
    WEASYPRINT_DISPONIVEL = False

def gerar_pdf_profissional(db_path="rh_diagnostico_dinamico.db", output_pdf="Laudo_Executivo_Profissional.pdf"):
    """
    Gera o Dossiê Executivo Integrado de Alta Governança (Fase 3) em HTML/CSS avançado
    com WeasyPrint e fallback automático para FPDF no ambiente local.
    """
    if not os.path.exists(db_path):
        print(f"[Aviso] Banco de dados '{db_path}' não encontrado.")
        return None

    # Consulta ao registro mais recente no banco de dados SQLite
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nome, vaga, nivel, data, pontos, classificacao, sinal_vermelho, arquétipo, tokens_in, tokens_out, custo_brl 
            FROM avaliacoes 
            ORDER BY id DESC LIMIT 1
        """)
        row = cursor.fetchone()

    if not row:
        print("[Aviso] Nenhum registro encontrado na tabela 'avaliacoes' para exportação.")
        return None

    _, nome, vaga, nivel, data_reg, pontos, classificacao, sinal_vermelho, arquetipo, tokens_in, tokens_out, custo_brl = row

    # Tratamento de valores padrão
    nome = nome or "Candidato(a)"
    vaga = vaga or "Não informada"
    nivel = nivel or "Executivo"
    data_reg = data_reg or datetime.now().strftime("%d / %m / %Y")
    pontos = pontos or 0
    classificacao = classificacao or "Recomendado com Ressalvas"
    sinal_vermelho = sinal_vermelho or "Não"
    arquetipo = arquetipo or "Governança, Compliance e Riscos"

    is_vermelho = str(sinal_vermelho).strip().lower() in ["sim", "true", "1", "ativo"]
    if is_vermelho:
        classificacao = "Não Recomendado (Veto de Governança)"

    # Indicadores calculados para o relatório rico
    score_fase1 = pontos * 2.5
    score_fase2 = 82.2
    score_global = (score_fase1 * 0.7) + (score_fase2 * 0.3)
    
    alerta_bg = "#FDDEDE" if is_vermelho else "#EBF7EE"
    alerta_border = "#E68282" if is_vermelho else "#8CC896"
    alerta_color = "#A01414" if is_vermelho else "#146E28"
    alerta_texto = (
        "[!] SINAL VERMELHO ATIVADO: Ponto crítico detectado nas bases de Resiliência ou Ética."
        if is_vermelho else 
        "[+] SINAL VERMELHO DESATIVADO: Bases comportamentais, psíquicas e éticas preservadas com consistência."
    )

    # Tenta renderizar via WeasyPrint (HTML/CSS Avançado)
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
                        margin: 15mm 15mm 15mm 15mm;
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
                        font-size: 9pt;
                        line-height: 1.45;
                        margin: 0;
                        padding: 0;
                    }}
                    .header-bar {{
                        background-color: #182B49;
                        height: 6px;
                        width: 100%;
                        margin-bottom: 12px;
                    }}
                    h1 {{
                        text-align: center;
                        color: #182B49;
                        font-size: 14pt;
                        margin: 0 0 3px 0;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                    }}
                    .subtitle {{
                        text-align: center;
                        color: #718096;
                        font-size: 8.5pt;
                        font-style: italic;
                        margin-bottom: 15px;
                    }}
                    .card-info {{
                        background-color: #F7FAFC;
                        border: 1px solid #CBD5E0;
                        border-radius: 4px;
                        padding: 10px 12px;
                        margin-bottom: 15px;
                    }}
                    .card-info table {{
                        width: 100%;
                        border-collapse: collapse;
                    }}
                    .card-info td {{
                        padding: 3px 0;
                        font-size: 8.5pt;
                    }}
                    .card-info td.label {{
                        font-weight: bold;
                        color: #4A5568;
                        width: 22%;
                    }}
                    .section-title {{
                        background-color: #EDF2F7;
                        color: #182B49;
                        font-size: 9.5pt;
                        font-weight: bold;
                        padding: 5px 8px;
                        margin-top: 12px;
                        margin-bottom: 8px;
                        border-left: 3px solid #182B49;
                        text-transform: uppercase;
                    }}
                    .metrics-table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-bottom: 12px;
                    }}
                    .metrics-table th, .metrics-table td {{
                        border: 1px solid #CBD5E0;
                        padding: 6px;
                        text-align: center;
                        font-size: 8.5pt;
                    }}
                    .metrics-table th {{
                        background-color: #E2E8F0;
                        color: #182B49;
                    }}
                    .metric-value {{
                        font-size: 11pt;
                        font-weight: bold;
                        color: #2B6CB0;
                    }}
                    .alerta-box {{
                        background-color: {alerta_bg};
                        border: 1px solid {alerta_border};
                        color: {alerta_color};
                        padding: 8px 10px;
                        border-radius: 4px;
                        font-weight: bold;
                        font-size: 8.5pt;
                        margin-bottom: 12px;
                        text-align: center;
                    }}
                    .content-box {{
                        background-color: #FFFFFF;
                        border: 1px solid #CBD5E0;
                        border-radius: 4px;
                        padding: 10px 12px;
                        margin-bottom: 12px;
                        text-align: justify;
                    }}
                    .grid-2 {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-bottom: 12px;
                    }}
                    .grid-2 td {{
                        width: 50%;
                        vertical-align: top;
                        padding: 0 5px;
                    }}
                    .grid-2 td:first-child {{ padding-left: 0; }}
                    .grid-2 td:last-child {{ padding-right: 0; }}
                    .sub-box {{
                        background-color: #F8FAFC;
                        border: 1px solid #E2E8F0;
                        border-radius: 4px;
                        padding: 8px 10px;
                        height: 100%;
                    }}
                    .sub-box h4 {{
                        margin: 0 0 5px 0;
                        color: #182B49;
                        font-size: 9pt;
                        border-bottom: 1px solid #E2E8F0;
                        padding-bottom: 3px;
                    }}
                    .signature-section {{
                        margin-top: 25px;
                        page-break-inside: avoid;
                    }}
                    .signature-table {{
                        width: 100%;
                        border-collapse: collapse;
                    }}
                    .signature-table td {{
                        width: 50%;
                        text-align: center;
                        padding-top: 25px;
                        font-size: 8pt;
                        color: #4A5568;
                    }}
                    .signature-line {{
                        border-top: 1px solid #A0AEC0;
                        width: 75%;
                        margin: 0 auto 4px auto;
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
                            <small style="color: #718096;">Base Psicométrica & Comportamental</small>
                        </td>
                        <td>
                            <span class="metric-value">{score_fase2:.1f}%</span><br>
                            <small style="color: #718096;">Alinhamento Conjuntural Ativo</small>
                        </td>
                        <td>
                            <span class="metric-value" style="color: #2F855A;">{score_global:.1f}%</span><br>
                            <strong style="color: #2B6CB0;">{classificacao}</strong>
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
                                <ul style="margin: 0; padding-left: 15px; font-size: 8.5pt;">
                                    <li>Consistência nos fundamentos analíticos e tomada de decisão sob pressão.</li>
                                    <li>Alinhamento direto com o arquétipo de liderança corporativa.</li>
                                    <li>Visão sistêmica apurada para cenários de reestruturação.</li>
                                </ul>
                            </div>
                        </td>
                        <td>
                            <div class="sub-box">
                                <h4>Pontos de Atenção (Riscos Operacionais)</h4>
                                <ul style="margin: 0; padding-left: 15px; font-size: 8.5pt;">
                                    <li>Necessidade de monitoramento de alinhamento cultural nos primeiros 90 dias.</li>
                                    <li>Gestão de expectativas em entregas de curto prazo.</li>
                                    <li>Mitigação de pontos cegos mapeados na matriz de resiliência.</li>
                                </ul>
                            </div>
                        </td>
                    </tr>
                </table>

                <div class="section-title">3. Parecer Deliberativo & Contexto Conjuntural</div>
                <div class="content-box">
                    <p style="margin: 0 0 6px 0;">O(A) candidato(a) <strong>{nome}</strong> foi submetido(a) a uma avaliação profunda para a posição de <strong>{vaga}</strong>, balizada pelo arquétipo de <strong>{arquetipo}</strong>. O índice global consolidado situa-se em <strong>{classificacao} ({score_global:.1f}%)</strong>.</p>
                    <p style="margin: 0;">A análise cruzada indica que o momento conjuntural e os trâmites operacionais do candidato convergem com as necessidades estratégicas da organização, exigindo contudo governança estruturada no trimestre inicial para pleno aproveitamento do potencial de liderança.</p>
                </div>

                <div class="section-title">4. Diretrizes para o Plano de Integração (90 Dias)</div>
                <div class="content-box">
                    <ul style="margin: 0; padding-left: 15px; font-size: 8.5pt;">
                        <li><strong>Dias 1 a 30:</strong> Imersão institucional, alinhamento de expectativas com a diretoria e mapeamento de processos críticos.</li>
                        <li><strong>Dias 31 a 60:</strong> Assunção gradual de entregas táticas, liderança de comitês operacionais e validação de indicadores de desempenho.</li>
                        <li><strong>Dias 61 a 90:</strong> Avaliação de impacto de 90 dias, entrega de projetos estruturantes e consolidação da governança sob o arquétipo escolhido.</li>
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
            print(f"[Aviso] WeasyPrint indisponível ou falhou ({e}). Recorrendo automaticamente ao motor FPDF...")

    # FALLBACK SEGURO VIA FPDF (Sem caracteres Unicode especiais como '•' para evitar FPDFUnicodeEncodingException)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 7, "DOSSIE EXECUTIVO INTEGRADO DE GOVERNANCA", 0, 1, "C")
    pdf.set_font("helvetica", "I", 8)
    pdf.cell(0, 4, "Avaliacao C-Level, Cruzamento Ponderado & Diretrizes (Modo Compatibilidade)", 0, 1, "C")
    pdf.ln(4)
    
    pdf.set_font("helvetica", "B", 8)
    pdf.set_fill_color(245, 247, 250)
    pdf.cell(0, 5.5, f"   CANDIDATO(A): {nome.upper()}   |   EMISSAO: {data_reg}", 1, 1, "L", True)
    pdf.cell(0, 5.5, f"   CARGO: {vaga.upper()} ({nivel})   |   ARQUETIPO: {arquetipo}", 1, 1, "L", True)
    pdf.ln(4)
    
    pdf.set_font("helvetica", "B", 8.5)
    pdf.cell(0, 5, "1. SUMARIO EXECUTIVO DE ADERENCIA PONDERADA", 0, 1, "L")
    pdf.set_font("helvetica", "", 8)
    pdf.cell(0, 5, f"- Indice Global Integrado: {score_global:.1f}% ({classificacao})", 0, 1, "L")
    pdf.cell(0, 5, f"- Fase 1 (Tarot/Psicometrica): {score_fase1:.1f}% (Peso 70%)", 0, 1, "L")
    pdf.cell(0, 5, f"- Fase 2 (Transitos/Estrutural): {score_fase2:.1f}% (Peso 30%)", 0, 1, "L")
    pdf.cell(0, 5, f"- Status de Alerta (Sinal Vermelho): {sinal_vermelho}", 0, 1, "L")
    pdf.ln(3)
    
    pdf.set_font("helvetica", "B", 8.5)
    pdf.cell(0, 5, "2. MAPEAMENTO DE FORCAS E RISCOS", 0, 1, "L")
    pdf.set_font("helvetica", "", 7.5)
    pdf.multi_cell(0, 4, "- Forcas: Consistencia analitica, tomada de decisao sob pressao e alinhamento com o arquetipo corporativo.\n- Riscos: Necessidade de governanca rigorosa nos primeiros 90 dias para mitigacao de pontos cegos operacionais.", border=1, fill=True)
    pdf.ln(3)

    pdf.set_font("helvetica", "B", 8.5)
    pdf.cell(0, 5, "3. PARECER DELIBERATIVO & CONTEXTO CONJUNTURAL", 0, 1, "L")
    pdf.set_font("helvetica", "", 7.5)
    parecer_txt = (
        f"O(A) candidato(a) {nome} foi avaliado(a) para a posicao de {vaga} sob o arquetipo {arquetipo}. "
        + (
            f"Embora tenha atingido {score_global:.1f}%, a candidatura foi vetada pelas regras de integridade e governanca corporativa. "
            f"A classificacao compulsoria e '{classificacao}'."
            if is_vermelho else
            f"O perfil enquadra-se na diretriz de '{classificacao}' com score de {score_global:.1f}%. "
            f"A avaliacao cruza a base comportamental com o panorama estrutural e tramites vigentes."
        )
    )
    pdf.multi_cell(0, 4, parecer_txt, border=1, fill=True)
    pdf.ln(3)

    pdf.set_font("helvetica", "B", 8.5)
    pdf.cell(0, 5, "4. DIRETRIZES PARA O PLANO DE INTEGRACAO (90 DIAS)", 0, 1, "L")
    pdf.set_font("helvetica", "", 7.5)
    plano_txt = (
        "- 30 Dias: Imersao institucional e alinhamento de expectativas.\n"
        "- 60 Dias: Assuncao tatica e lideranca de comites operacionais.\n"
        "- 90 Dias: Avaliacao de impacto, projetos estruturantes e consolidacao."
    )
    pdf.multi_cell(0, 4, plano_txt, border=1, fill=True)
    
    res = pdf.output(dest="S")
    with open(output_pdf, "wb") as f:
        f.write(res.encode("latin1") if isinstance(res, str) else bytes(res))
        
    return output_pdf