"""
Módulo de Constantes, Pesos e Parâmetros de Governança
Sistema de Diagnóstico Corporativo
"""

# Ponderação do Laudo Integrado (Fase 3)
PESO_FASE_1 = 0.70
PESO_FASE_2 = 0.30

# Regras de Veto e Governança (Sinal Vermelho)
NOTA_CRITICA_SINAL_VERMELHO = 2
CASAS_CRITICAS_GOVERNANCA = [7, 8]  # Saúde Psicológica (7) e Confiabilidade/Ética (8)

# Faixas de Deliberação Executiva
FAIXAS_DELIBERACAO = {
    "REPROVADO": {
        "limite_max": 64.99,
        "rotulo": "Não Recomendado",
        "descricao": "Abaixo de 65%: Riscos severos de aderência",
        "cor_hex": "#DC2626",
    },
    "RESSALVAS": {
        "limite_min": 65.0,
        "limite_max": 79.99,
        "rotulo": "Recomendado com Ressalvas",
        "descricao": "Aderência entre 65% e 79%",
        "cor_hex": "#D97706",
    },
    "APROVADO": {
        "limite_min": 80.0,
        "rotulo": "Recomendado",
        "descricao": "Aderência igual ou superior a 80%",
        "cor_hex": "#16A34A",
    },
}

# Nomes padronizados das 8 Competências (Fase 1)
COMPETENCIAS_FASE_1 = [
    "Hard Skills",
    "Soft Skills",
    "Fit Cultural",
    "Desafios",
    "Potencial Futuro",
    "Equilíbrio Emocional",
    "Saúde Psicológica",
    "Confiabilidade e Ética",
]