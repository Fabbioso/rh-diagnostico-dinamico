import os
from typing import Dict, Any, Tuple, Optional
import google.generativeai as genai

# Tabela referencial de custo por milhão de tokens (ex: Gemini 1.5 Flash)
PRECO_INPUT_POR_MILHAO = 0.075   # USD
PRECO_OUTPUT_POR_MILHAO = 0.30   # USD

def configurar_gemini(api_key: Optional[str] = None) -> bool:
    """Configura o cliente do Gemini a partir do argumento ou variável de ambiente."""
    chave = api_key or os.environ.get("GEMINI_API_KEY")
    if not chave:
        return False
    try:
        genai.configure(api_key=chave)
        return True
    except Exception as e:
        print(f"[ERRO AI] Falha ao configurar Gemini: {e}")
        return False

def obter_modelo_ativo() -> str:
    try:
        modelos_validos = [
            m.name.replace("models/", "")
            for m in genai.list_models()
            if "generateContent" in m.supported_generation_methods
        ]
        for candidato in ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-flash-latest"]:
            if candidato in modelos_validos:
                return candidato
        return modelos_validos[0] if modelos_validos else "gemini-3.8-flash"
    except Exception:
        return "gemini-3.8-flash"

def _calcular_telemetria(input_tokens: int, output_tokens: int) -> Dict[str, Any]:
    """Calcula estatísticas de uso e estimativa de custo."""
    custo_input = (input_tokens / 1_000_000) * PRECO_INPUT_POR_MILHAO
    custo_output = (output_tokens / 1_000_000) * PRECO_OUTPUT_POR_MILHAO
    custo_total = custo_input + custo_output
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "custo_usd": custo_total,
        "custo_formatado": f"${custo_total:.6f} USD"
    }

def gerar_analise_fase1(
    candidato_nome: str,
    cargo: str,
    nivel: str,
    arquetipo: str,
    dados_casas: Dict[int, Dict[str, Any]],
    modelo_nome: Optional[str] = None
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Gera a análise qualitativa comportamental das 8 casas de Tarot para a Fase 1.
    Retorna: (sucesso: bool, texto_analise: str, telemetria: dict)
    """
    try:
        modelo_final = modelo_nome or obter_modelo_ativo()
        model = genai.GenerativeModel(modelo_final)
        
        # Montagem do prompt executivo
        detalhe_casas = []
        for c_num, c_dados in dados_casas.items():
            detalhe_casas.append(
                f"- Casa {c_num} ({c_dados.get('nome', '')}): Nota {c_dados.get('nota', 3)}/5 | "
                f"Central: {c_dados.get('central', '')} | Negativa: {c_dados.get('negativa', '')} | Positiva: {c_dados.get('positiva', '')}"
            )
        bloco_casas_str = "\n".join(detalhe_casas)

        prompt = f"""
    Atue como um Especialista Sênior em Recursos Humanos, Governança Corporativa e Avaliação Psicométrica.
    Analise os resultados da Fase 1 (Tarot Comportamental - 8 Casas) para o profissional abaixo:

    CANDIDATO: {candidato_nome}
    CARGO PRETENDIDO: {cargo} ({nivel})
    ARQUÉTIPO CORPORATIVO: {arquetipo}

    MATRIZ DAS 8 CASAS:
    {bloco_casas_str}

    REGRAS OBRIGATÓRIAS DE FORMATAÇÃO:
    Para que o sistema processe o laudo, você DEVE estruturar o texto estritamente seguindo o padrão abaixo para CADA UMA das 8 competências (substituindo o número e os dados):

    ### [CASA X: NOME DA COMPETÊNCIA]
    CARTA CENTRAL: [Nome da Carta] - [Análise detalhada de 2 a 3 linhas da influência central]
    CARTA NEGATIVA: [Nome da Carta] - [Análise detalhada de 2 a 3 linhas do ponto de tensão ou desafio]
    CARTA POSITIVA: [Nome da Carta] - [Análise detalhada de 2 a 3 linhas do recurso integrador ou força]
    RESUMO DA LEITURA: [Síntese executiva de 2 a 3 linhas sobre a competência para a tabela do laudo]

    Ao final das 8 casas, inclua a seção conclusiva com:
    CONCLUSÃO E RECOMENDAÇÃO FINAL
    PARECER FINAL: [Recomendado com Destaque / Recomendado com Ressalvas / Não Recomendado]
    JUSTIFICATIVA EXECUTIVA: [Parecer executivo detalhado conectando o arquétipo às competências avaliadas]
    Forças principais: [Competências com melhores notas]
    Focos de ressalva: [Competências que exigem acompanhamento]
    """
        response = model.generate_content(prompt)
        
        # Telemetria estimada de tokens
        input_tokens = model.count_tokens(prompt).total_tokens
        output_tokens = model.count_tokens(response.text).total_tokens if hasattr(response, 'text') else 0
        telemetria = _calcular_telemetria(input_tokens, output_tokens)
        
        return True, response.text, telemetria
    except Exception as e:
        return False, f"Falha na geração da análise via Gemini: {str(e)}", {}

def gerar_deliberacao_fase3(
    candidato_nome: str,
    cargo: str,
    nivel: str,
    arquetipo: str,
    aderencia_f1: float,
    aderencia_f2: float,
    indice_global: float,
    classificacao: str,
    sinal_vermelho: bool,
    pontos_fortes: str = "",
    pontos_atencao: str = "",
    modelo_nome: Optional[str] = None
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Gera a Deliberação Executiva e Parecer Integrado da Fase 3 cruzando Tarot e Trânsitos.
    Retorna: (sucesso: bool, parecer_executivo: str, telemetria: dict)
    """
    try:
        modelo_final = modelo_nome or obter_modelo_ativo()
        model = genai.GenerativeModel(modelo_final)
        
        prompt = f"""
Atue como Diretor Executivo de Recursos Humanos e Governança Corporativa.
Elabore o Parecer de Deliberação Executiva Integrado do Dossiê Master de Recrutamento.

DADOS DA AVALIAÇÃO INTEGRADA:
- Candidato(a): {candidato_nome}
- Cargo / Nível: {cargo} ({nivel})
- Arquétipo Corporativo: {arquetipo}
- Aderência Fase 1 (Tarot Comportamental): {aderencia_f1:.1f}%
- Aderência Fase 2 (Estrutural & Trânsitos): {aderencia_f2:.1f}%
- Índice Global Integrado: {indice_global:.1f}%
- Classificação Final: {classificacao}
- Sinal Vermelho Ativo: {'SIM (Impedimento ético/psíquico)' if sinal_vermelho else 'NÃO (Bases preservadas)'}
- Principais Forças Identificadas: {pontos_fortes}
- Pontos de Atenção / Ressalvas: {pontos_atencao}

DIRETRIZES DO PARECER:
- Redija entre 3 e 5 parágrafos coesos e densos.
- Avalie a consonância do perfil frente ao arquétipo organizacional exigido.
- Se houver ressalvas, aponte recomendações concretas de acompanhamento ou PDI (Plano de Desenvolvimento Individual).
- Finalize com uma deliberação inequívoca de adequação ou não adequação corporativa ao cargo.
"""
        response = model.generate_content(prompt)
        
        input_tokens = model.count_tokens(prompt).total_tokens
        output_tokens = model.count_tokens(response.text).total_tokens if hasattr(response, 'text') else 0
        telemetria = _calcular_telemetria(input_tokens, output_tokens)
        
        return True, response.text, telemetria
    except Exception as e:
        print(f"[ERRO AI] Falha na geração da deliberação integrada: {e}")
        texto_fallback = (
            f"Com base na avaliação das competências comportamentais e estruturais, o candidato {candidato_nome} "
            f"apresenta índice global consolidado de {indice_global:.1f}%, enquadrando-se na classificação de {classificacao}. "
            f"Os pilares avaliados demonstram alinhamento funcional com os requisitos de governança do arquétipo {arquetipo}, "
            f"sendo recomendada a implementação de Plano de Desenvolvimento Individual (PDI) para acompanhamento dos pontos mapeados."
        )
        return False, texto_fallback, {"custo_formatado": "$0.000000 USD", "total_tokens": 0}