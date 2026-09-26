import pytest
from reports.gerar_pdf_fase1 import gerar_ficha_pdf_fase1
from core.constants import COMPETENCIAS_FASE_1

def _criar_dados_casas_mock():
    dados = []
    for i, nome in enumerate(COMPETENCIAS_FASE_1, start=1):
        dados.append({
            "pos": i,
            "nome": nome,
            "central": "O Mago",
            "negativa": "A Torre",
            "positiva": "O Sol",
            "nota": 4 if i % 2 == 0 else 3,
            "desc_central": f"Capacidade de iniciativa e estruturação em {nome}.",
            "desc_negativa": f"Atenção a rupturas e sobrecargas pontuais em {nome}.",
            "desc_positiva": f"Clareza e vitalidade operacional em {nome}.",
            "resumo": f"Perfil equilibrado com foco em entregas táticas para {nome}."
        })
    return dados

def test_gerar_ficha_pdf_fase1_fluxo_padrao():
    dados_casas = _criar_dados_casas_mock()
    texto_ia = (
        "JUSTIFICATIVA EXECUTIVA: O candidato apresenta solidez técnica e maturidade executiva.\n"
        "FORÇAS PRINCIPAIS: Hard Skills e Potencial Futuro.\n"
        "FOCOS DE RESSALVA: Desafios operacionais."
    )
    
    pdf_bytes = gerar_ficha_pdf_fase1(
        c_nome="Fabio Oliveira",
        c_vaga="Gerente Operacional",
        c_nivel="Sênior",
        total_pts=28.0,
        perc_t1=70.0,
        classif="Recomendado",
        sinal_vermelho_val=False,
        texto_ia_doc=texto_ia,
        dados_casas=dados_casas,
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")

def test_gerar_ficha_pdf_fase1_veto_governanca():
    dados_casas = _criar_dados_casas_mock()
    texto_ia = "JUSTIFICATIVA EXECUTIVA: Risco crítico identificado em integridade institucional."

    pdf_bytes = gerar_ficha_pdf_fase1(
        c_nome="Candidato Teste",
        c_vaga="Analista de Compliance",
        c_nivel="Pleno",
        total_pts=16.0,
        perc_t1=40.0,
        classif="Não Recomendado",
        sinal_vermelho_val=True,
        texto_ia_doc=texto_ia,
        dados_casas=dados_casas,
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")
