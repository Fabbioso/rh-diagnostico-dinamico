import pytest

from app import inferir_nivel


@pytest.mark.parametrize(
    ("cargo", "nivel_esperado"),
    [
        ("Diretor Financeiro", "Diretor"),
        ("Diretora Financeira", "Diretor"),
        ("Gerente de Contas", "Gerente"),
        ("Gerente Geral", "Gerente"),
        ("Coordenador de RH", "Coordenador"),
        ("Coordenadora de Marketing", "Coordenador"),
        ("Supervisor de Logística", "Supervisor"),
        ("Supervisora de Logística", "Supervisor"),
        ("Consultor Comercial", "Especialista"),
        ("Consultora Técnica", "Especialista"),
        ("Estagiário de Direito", "Assistente"),
        ("Estagiária de TI", "Assistente"),
        ("Analista de Suporte", "Analista"),
        ("", ""),
        ("   ", ""),
    ],
)
def test_inferir_nivel(cargo, nivel_esperado):
    assert inferir_nivel(cargo) == nivel_esperado
