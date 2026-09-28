import pytest
from app import classificar_arquétipo_manual


@pytest.mark.parametrize(
    ("cargo", "arquetipo_esperado"),
    [
        ("Diretor Financeiro", "Governança, Compliance e Riscos"),
        ("Diretora Financeira", "Governança, Compliance e Riscos"),
        ("Gerente de Operações", "Operações, Processos e Manutenção"),
        ("Consultor Comercial", "Comercial, Negócios e Relacionamento"),
        ("Consultora Comercial", "Comercial, Negócios e Relacionamento"),
        ("Engenheiro de Produção", "Operações, Processos e Manutenção"),
        ("Engenheira de Produção", "Operações, Processos e Manutenção"),
        ("Auditor de Riscos", "Governança, Compliance e Riscos"),
        ("Auditora de Riscos", "Governança, Compliance e Riscos"),
        ("Analista de TI", "Inovação, Estratégia e Expansão"),
        ("", "Padrão / Geral"),
        ("   ", "Padrão / Geral"),
    ],
)
def test_classificar_arquetipo_genero(cargo, arquetipo_esperado):
    arquetipo, pesos = classificar_arquétipo_manual(cargo)
    assert arquetipo == arquetipo_esperado
    assert isinstance(pesos, dict)
    assert len(pesos) == 12
