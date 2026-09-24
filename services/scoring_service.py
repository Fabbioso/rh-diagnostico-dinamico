import random
from typing import Dict, Any, Tuple, List

def sortear_cartas_fase1(
    lista_cartas: List[str],
    definicoes_casas: Dict[int, Any]
) -> Dict[int, Dict[str, Any]]:
    """
    Executa o sorteio metodológico das tríades de cartas (Central, Negativa, Positiva)
    para as 8 casas comportamentais, garantindo cartas não repetidas por casa.
    """
    resultado_casas = {}
    baralho = list(lista_cartas)
    
    for num_casa in range(1, 9):
        amostra = random.sample(baralho, 3)
        nome_casa = definicoes_casas.get(num_casa, {}).get("nome", f"Casa {num_casa}")
        
        # Nota padrão ou calculada pelas regras metodológicas
        nota_padrao = random.choice([3, 4, 4, 5]) if num_casa in [1, 8] else random.choice([2, 3, 3, 4])
        
        resultado_casas[num_casa] = {
            "nome": nome_casa,
            "central": amostra[0],
            "negativa": amostra[1],
            "positiva": amostra[2],
            "nota": nota_padrao
        }
    return resultado_casas

def calcular_pontuacao_fase1(dados_casas: Dict[int, Dict[str, Any]]) -> Tuple[float, float, str]:
    """
    Calcula a soma das notas (escala de 8 a 40) e a respetiva aderência percentual (0 a 100%).
    Retorna: (pontos_obtidos, aderencia_percentual, classificacao_fase1)
    """
    total_pontos = sum(float(c.get("nota", 3)) for c in dados_casas.values())
    max_possivel = 40.0
    aderencia = (total_pontos / max_possivel) * 100.0
    
    if aderencia >= 80.0:
        classificacao = "Recomendado com Destaque"
    elif aderencia >= 65.0:
        classificacao = "Recomendado com Ressalvas"
    else:
        classificacao = "Não Recomendado"
        
    return total_pontos, aderencia, classificacao

def calcular_pontuacao_fase2(
    casas_astrologicas: Dict[int, Dict[str, Any]],
    pesos_arquetipo: Dict[str, float]
) -> Tuple[float, float, str]:
    """
    Aplica os pesos do arquétipo corporativo ativo e os moduladores de trânsito planetário
    sobre as 12 casas astrológicas.
    Retorna: (capacidade_estrutural, aderencia_fase2, diagnostico_fase2)
    """
    soma_ponderada = 0.0
    soma_pesos = 0.0
    
    for i in range(1, 13):
        info = casas_astrologicas.get(i, {})
        nota = float(info.get("nota", 4.0))
        peso_base = float(pesos_arquetipo.get(f"C{i}", 1.0))
        
        soma_ponderada += (nota * peso_base)
        soma_pesos += (5.0 * peso_base)
        
    capacidade_estrutural = soma_ponderada
    aderencia = (soma_ponderada / soma_pesos * 100.0) if soma_pesos > 0 else 0.0
    
    if aderencia >= 80.0:
        diagnostico = "Alta Sinergia / Prontidão Imediata"
    elif aderencia >= 65.0:
        diagnostico = "Sinergia Moderada / Ajustes de Integração Requeridos"
    else:
        diagnostico = "Baixa Sinergia / Desalinhamento Estrutural"
        
    return capacidade_estrutural, aderencia, diagnostico

def calcular_indice_global_integrado(
    aderencia_f1: float,
    aderencia_f2: float,
    notas_fase1: Dict[int, Dict[str, Any]],
    peso_f1: float = 0.70,
    peso_f2: float = 0.30
) -> Tuple[float, str, bool, str]:
    """
    Consolida o cruzamento analítico da Fase 3:
    - Pondera Tarot (70%) e Astrologia (30%).
    - Avalia a regra mandatória de Sinal Vermelho (ex: Casa 8 Ética < 3 ou Casa 7 Psíquica < 2).
    Retorna: (indice_global, classificacao_final, sinal_vermelho_ativo, motivo_sinal)
    """
    indice_global = (aderencia_f1 * peso_f1) + (aderencia_f2 * peso_f2)
    
        # Verificação de Sinal Vermelho por Dimensão Crítica de Governança
    sinal_vermelho = False
    motivos = []

    n6 = float(notas_fase1.get(6, {}).get("nota", 3))
    n7 = float(notas_fase1.get(7, {}).get("nota", 3))
    n8 = float(notas_fase1.get(8, {}).get("nota", 3))

    if n8 < 3.0:
        sinal_vermelho = True
        motivos.append("Confiabilidade e Ética (Nota abaixo de 3.0)")

    if n7 < 2.0:
        sinal_vermelho = True
        motivos.append("Saúde Psicológica e Estabilidade (Nota abaixo de 2.0)")

    if n6 < 2.0:
        sinal_vermelho = True
        motivos.append("Equilíbrio e Resiliência Operacional (Nota abaixo de 2.0)")

    motivo_vermelho = f"Veto Mandatório de Governança: {', '.join(motivos)}." if sinal_vermelho else ""
        
    if sinal_vermelho:
        classificacao = "Não Recomendado (Veto de Governança)"
    elif indice_global >= 80.0:
        classificacao = "Recomendado com Destaque (Alta Sinergia Integrada)"
    elif indice_global >= 65.0:
        classificacao = "Recomendado com Ressalvas (Aderência entre 65% e 79%)"
    else:
        classificacao = "Não Recomendado (Desalinhamento Global)"
        
    return indice_global, classificacao, sinal_vermelho, motivo_vermelho