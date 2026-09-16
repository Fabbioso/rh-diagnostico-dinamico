import os
from fpdf import FPDF

def gerar_laudo_fase3_pdf(
    c_nome, c_vaga, c_nivel, arq_ativo_ficha, 
    perc_t1, perc_t2, indice_global, classificacao, 
    sinal_vermelho, texto_conclusao_f3, mandala_dados, dados_tabela_f1,
    output_pdf="Ficha_Avaliacao_Fase3.pdf"
):
    """
    Gera o PDF da Ficha de Avaliação Integrada (Fase 3) utilizando FPDF,
    com tratamento seguro de conversão de tipos para evitar erros de formatação (ValueError).
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Cabeçalho do Laudo
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "FICHA DE AVALIACAO INTEGRADA E PONDERADA (FASE 3)", 0, 1, "C")
    pdf.set_font("helvetica", "I", 8.5)
    pdf.cell(0, 5, "Governança Final, Cruzamento de Tarot & Astrologia", 0, 1, "C")
    pdf.ln(5)
    
    # Bloco de Identificação
    pdf.set_font("helvetica", "B", 8)
    pdf.set_fill_color(245, 247, 250)
    pdf.cell(0, 6, f"   CANDIDATO(A): {str(c_nome or 'Candidato').upper()}", 1, 1, "L", True)
    pdf.cell(0, 6, f"   VAGA / CARGO: {str(c_vaga or 'Não informada').upper()} ({str(c_nivel or 'Executivo')})  |  ARQUETIPO: {str(arq_ativo_ficha or 'Geral')}", 1, 1, "L", True)
    pdf.ln(5)
    
    # Resumo de Indicadores com Conversão Segura
    p1 = float(perc_t1 or 0)
    p2 = float(perc_t2 or 0)
    ig = float(indice_global or 0)

    pdf.set_font("helvetica", "B", 9)
    pdf.cell(0, 6, "RESUMO DOS INDICADORES GLOBAIS", 0, 1, "L")
    pdf.set_font("helvetica", "", 8.5)
    pdf.cell(0, 6, f"- Fase 1 (Tarot): {p1:.1f}%", 0, 1, "L")
    pdf.cell(0, 6, f"- Fase 2 (Trânsitos): {p2:.1f}%", 0, 1, "L")
    pdf.cell(0, 6, f"- Índice Global Integrado: {ig:.1f}% ({str(classificacao or 'Avaliado')})", 0, 1, "L")
    pdf.cell(0, 6, f"- Sinal Vermelho: {str(sinal_vermelho or 'Não')}", 0, 1, "L")
    pdf.ln(5)
    
    # Detalhamento das 8 Casas / Tabela com Tratamento de Float Seguro
    if dados_tabela_f1 and isinstance(dados_tabela_f1, list):
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(0, 6, "DETALHAMENTO DAS 8 CASAS / DIMENSOES", 0, 1, "L")
        pdf.set_font("helvetica", "B", 8)
        pdf.set_fill_color(226, 232, 240)
        
        # Cabeçalhos da Tabela
        pdf.cell(100, 6, " Dimensão / Casa", 1, 0, "L", True)
        pdf.cell(40, 6, " Configuração", 1, 0, "C", True)
        pdf.cell(50, 6, " Nota Base", 1, 1, "C", True)
        
        pdf.set_font("helvetica", "", 8)
        for d_val in dados_tabela_f1:
            raw_nota = d_val.get('nota_base', 0)
            try:
                nota_val = float(raw_nota)
            except (TypeError, ValueError):
                nota_val = 0.0
                
            casa_nome = str(d_val.get('casa', 'Casa'))
            cfg_nome = str(d_val.get('configuracao', 'N/A'))
            
            pdf.cell(100, 5.5, f" {casa_nome}", 1, 0, "L")
            pdf.cell(40, 5.5, f"{cfg_nome}", 1, 0, "C")
            pdf.cell(50, 5.5, f"{nota_val:.1f}/5", 1, 1, "C")
        pdf.ln(5)
        
    # Parecer Técnico e Deliberativo
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(0, 6, "PARECER TECNICO DINAMICO & CONJUNTURAL", 0, 1, "L")
    pdf.set_font("helvetica", "", 8)
    texto_final = str(texto_conclusao_f3 or "Avaliação executiva concluída com cruzamento ponderado de dados e diretrizes de governança.")
    pdf.multi_cell(0, 4.5, texto_final, border=1, fill=True)
    
    # Gravação e retorno dos bytes binários do PDF
    pdf_bytes = bytes(pdf.output())
    try:
        with open(output_pdf, "wb") as f:
            f.write(pdf_bytes)
    except Exception:
        pass

    return pdf_bytes