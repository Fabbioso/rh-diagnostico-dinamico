import os
import re
from typing import Tuple, Dict, Any, Optional

try:
    import google.generativeai as genai
    GENAI_DISPONIVEL = True
except ImportError:
    GENAI_DISPONIVEL = False

# Custos referenciais de API (Gemini 3.8/Flash) e conversão cambial
PRECO_POR_MILHAO_INPUT_USD = 0.075
PRECO_POR_MILHAO_OUTPUT_USD = 0.30
TAXA_CAMBIO_USD_BRL = 5.80

def configurar_gemini(api_key: Optional[str] = None) -> bool:
    """Configura o client da API do Google Gemini a partir do argumento ou variável de ambiente."""
    chave = api_key or os.environ.get("GEMINI_API_KEY")
    if not chave or not GENAI_DISPONIVEL:
        return False
    try:
        genai.configure(api_key=chave)
        return True
    except Exception as e:
        print(f"[ERRO AI] Falha ao configurar Gemini: {e}")
        return False

def obter_modelo_ativo() -> str:
    """Seleciona o modelo Gemini mais recente e ativo disponível na API."""
    try:
        modelos_validos = [
            m.name.replace("models/", "")
            for m in genai.list_models()
            if "generateContent" in m.supported_generation_methods
        ]
        for candidato in ["gemini-3.8-flash", "gemini-flash-latest", "gemini-2.5-flash", "gemini-1.5-flash"]:
            if candidato in modelos_validos:
                return candidato
        return modelos_validos[0] if modelos_validos else "gemini-3.8-flash"
    except Exception:
        return "gemini-3.8-flash"

def _calcular_telemetria(input_tokens: int, output_tokens: int) -> Dict[str, Any]:
    """Calcula métricas de consumo de tokens e custos em USD e BRL."""
    custo_in = (input_tokens / 1_000_000.0) * PRECO_POR_MILHAO_INPUT_USD
    custo_out = (output_tokens / 1_000_000.0) * PRECO_POR_MILHAO_OUTPUT_USD
    custo_total_usd = custo_in + custo_out
    custo_total_brl = custo_total_usd * TAXA_CAMBIO_USD_BRL
    total_tokens = input_tokens + output_tokens

    return {
        "tokens_in": input_tokens,
        "tokens_out": output_tokens,
        "tokens_total": total_tokens,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "custo_usd": custo_total_usd,
        "custo_brl": custo_total_brl,
        "custo_formatado": f"${custo_total_usd:.6f} USD (R$ {custo_total_brl:.4f})",
    }

def gerar_analise_fase1(
    candidato_nome: str,
    cargo: str,
    nivel: str,
    arquetipo: str,
    dados_casas: Dict[int, Dict[str, Any]],
    classificacao_formal: str = "Não Recomendado",
    sinal_vermelho: bool = False,
    modelo_nome: Optional[str] = None,
) -> Tuple[bool, str, Dict[str, Any]]:
    """Gera o laudo analítico e situacional da Fase 1 com alto rigor executivo."""
    if not configurar_gemini():
        return False, "Chave da API GEMINI_API_KEY não configurada ou biblioteca indisponível.", {}

    try:
        nome_modelo = modelo_nome or obter_modelo_ativo()
        model = genai.GenerativeModel(nome_modelo)

        bloco_casas = []
        for i in range(1, 9):
            info = dados_casas.get(i, {})
            nome = info.get("nome", f"Casa {i}")
            c_cent = info.get("central", "Não informada")
            c_neg = info.get("negativa", "Não informada")
            c_pos = info.get("positiva", "Não informada")
            nota = info.get("nota", 3)
            bloco_casas.append(
                f"Casa {i} ({nome}) - Nota atribuída: {nota}/5\n"
                f"  - Arcana Central: {c_cent}\n"
                f"  - Ponto de Tensão (Negativa): {c_neg}\n"
                f"  - Recurso de Alavancagem (Positiva): {c_pos}"
            )
        bloco_casas_str = "\n".join(bloco_casas)

        prompt = rf"""
Atue como Especialista Sênior em Avaliação Psicométrica Executiva, Governança Corporativa e Seleção Estratégica de Talentos.
Analise a matriz de 8 competências (Fase 1 - Tarot Comportamental Estruturado) para o seguinte profissional:

CANDIDATO: {candidato_nome}
CARGO PRETENDIDO: {cargo} ({nivel})
ARQUÉTIPO CORPORATIVO DA POSIÇÃO: {arquetipo}
CLASSIFICAÇÃO FORMAL DO SISTEMA: {classificacao_formal}
SINAL VERMELHO ATIVO: {'SIM' if sinal_vermelho else 'NÃO'}

DIRETRIZ MANDATÓRIA DE GOVERNANÇA:
O Parecer Final DEVE refletir obrigatoriamente a CLASSIFICAÇÃO FORMAL DO SISTEMA ({classificacao_formal}). É terminantemente proibido alterar ou suavizar este veredito. Se a classificação for 'Não Recomendado' ou houver Sinal Vermelho ativo, fundamente tecnicamente a contraindicação com base nos riscos de conduta, integridade ou desestabilização operacional mapeados.

MATRIZ DAS 8 CASAS:
{bloco_casas_str}

DIRETRIZES DE ESTILO E REDAÇÃO (SENIOR EXECUTIVE PROSE):
1. Redija com prosa executiva corporativa, densa, analítica e fundamentada em situações reais da rotina de trabalho da função.
2. Não utilize clichês esotéricos, termos místicos ou linguagem de adivinhação. Trate os arcanos estritamente como arquétipos analíticos de comportamento e padrões de tomada de decisão.
3. É TERMINANTEMENTE PROIBIDO o uso de LaTeX (não use cifrões, barras invertidas, comandos matemáticos ou blocos de código). Use texto puro para números e percentuais.

ESTRUTURA DE RESPOSTA OBRIGATÓRIA:
Para que o motor de geração documental processe o relatório, preserve rigorosamente as marcações abaixo para cada uma das 8 casas:

### [CASA X: NOME DA COMPETÊNCIA]
CARTA CENTRAL: [Nome da Carta] - [Diagnóstico situacional denso de 2 a 3 linhas sobre a manifestação central desta competência na rotina operacional do cargo]
CARTA NEGATIVA: [Nome da Carta] - [Diagnóstico de vulnerabilidade de 2 a 3 linhas indicando o ponto de atrito, risco de estresse ou falha processual sob cobrança]
CARTA POSITIVA: [Nome da Carta] - [Diagnóstico de potencial integrador de 2 a 3 linhas indicando o recurso prático de alavancagem técnica ou comportamental]
RESUMO DA LEITURA: [Síntese executiva direta de 2 linhas consolidando o prognóstico para a tabela do laudo]

Ao final das 8 casas, inclua a seção conclusiva:
CONCLUSÃO E RECOMENDAÇÃO FINAL
PARECER FINAL: {classificacao_formal}
JUSTIFICATIVA EXECUTIVA: [Elabore um parecer denso e aprofundado de 6 a 10 linhas, articulado em três eixos:
1. Aderência Arquétipo-Cargo: Alinhamento entre as competências demonstradas, a senioridade ({nivel}) e os desafios reais de {cargo} sob a ótica de {arquetipo}.
2. Riscos Comportamentais e Operacionais: Impacto direto de competências com notas baixas (<= 2) na dinâmica da equipe, prazos e integridade de processos.
3. Parecer e Governança: Veredito corporativo sustentando a recomendação ou veto, apontando condições mandatórias (caso avance) ou fatores de descarte sumário.]
Forças principais: [Competências de destaque com notas]
Focos de ressalva: [Competências críticas ou com baixa pontuação]
"""
        response = model.generate_content(prompt)
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
    modelo_nome: Optional[str] = None,
) -> Tuple[bool, str, Dict[str, Any]]:
    """Gera a Deliberação Executiva Integrada (Fase 3) consolidando os motores analíticos."""
    if not configurar_gemini():
        return False, "Chave da API GEMINI_API_KEY não configurada ou biblioteca indisponível.", {}

    try:
        nome_modelo = modelo_nome or obter_modelo_ativo()
        model = genai.GenerativeModel(nome_modelo)

        status_veto = "ATIVADO (VETO DE GOVERNANÇA MANDATÓRIO)" if sinal_vermelho else "INATIVO (EM CONFORMIDADE)"

        prompt = rf"""
Atue como Diretor Executivo de Recursos Humanos e Membro do Comitê de Governança e Seleção Executiva.
Redija o Parecer de Deliberação Executiva Integrado (Dossiê Master de Avaliação) para a seguinte candidatura:

CANDIDATO: {candidato_nome}
CARGO: {cargo} ({nivel})
ARQUÉTIPO EXIGIDO: {arquetipo}
ÍNDICE GLOBAL INTEGRADO: {indice_global:.1f}%
CLASSIFICAÇÃO CONSOLIDADA: {classificacao}
STATUS DO SINAL VERMELHO: {status_veto}
ADERÊNCIA FASE 1 (COMPORTAMENTAL): {aderencia_f1:.1f}%
ADERÊNCIA FASE 2 (ESTRUTURAL / TRÂNSITOS): {aderencia_f2:.1f}%
PRINCIPAIS FORÇAS IDENTIFICADAS: {pontos_fortes}
PONTOS DE ATENÇÃO / RESSALVAS: {pontos_atencao}

DIRETRIZES DE DELIBERAÇÃO:
1. Redija de 3 a 5 parágrafos coesos, densos e situacionais em alto padrão de governança executiva corporativa.
2. Analise a correlação entre as forças técnicas/estruturais e a sustentabilidade comportamental frente ao arquétipo {arquetipo}.
3. Se houver Sinal Vermelho ativo ou classificação 'Não Recomendado', o parecer deve deliberar pelo veto institucional fundamentado, sem meias-palavras.
4. Para perfis recomendados com ressalvas, especifique ações de mitigação e diretrizes para o Plano de Desenvolvimento Individual (PDI).
5. É TERMINANTEMENTE PROIBIDO o uso de sintaxe LaTeX. Use notação textual limpa.
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
