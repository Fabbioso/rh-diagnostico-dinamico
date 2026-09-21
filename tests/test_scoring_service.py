from services.scoring_service import (
    calcular_indice_global_integrado,
    calcular_pontuacao_fase1,
)


def notas_fase1(nota=3):
    return {indice: {"nota": nota} for indice in range(1, 9)}


def test_calcular_pontuacao_fase1():
    total, aderencia, classificacao = calcular_pontuacao_fase1(notas_fase1(4))

    assert total == 32.0
    assert aderencia == 80.0
    assert classificacao == "Recomendado com Destaque"


def test_calcular_indice_global_integrado_ponderacao():
    indice, classificacao, sinal_vermelho, motivo = calcular_indice_global_integrado(
        70.0,
        80.0,
        notas_fase1(3),
    )

    assert indice == 73.0
    assert classificacao.startswith("Recomendado com Ressalvas")
    assert sinal_vermelho is False
    assert motivo == ""


def test_sinal_vermelho_gatilhos():
    _, _, sinal_seguro, _ = calcular_indice_global_integrado(80.0, 80.0, notas_fase1(3))
    assert sinal_seguro is False

    notas_etica_critica = notas_fase1(3)
    notas_etica_critica[8] = {"nota": 2.9}
    _, classificacao_etica, sinal_etica, motivo_etica = calcular_indice_global_integrado(
        80.0,
        80.0,
        notas_etica_critica,
    )
    assert sinal_etica is True
    assert "Veto de Governança" in classificacao_etica
    assert "Confiabilidade e Ética" in motivo_etica

    notas_psiquica_critica = notas_fase1(3)
    notas_psiquica_critica[7] = {"nota": 1.9}
    _, _, sinal_psiquica, motivo_psiquica = calcular_indice_global_integrado(
        80.0,
        80.0,
        notas_psiquica_critica,
    )
    assert sinal_psiquica is True
    assert "Saúde Psicológica" in motivo_psiquica
