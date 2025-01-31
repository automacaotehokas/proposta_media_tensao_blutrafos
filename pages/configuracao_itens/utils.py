from decimal import Decimal
import streamlit as st
from utils.constants import TAX_CONSTANTS, K_FACTOR_PERCENTAGES
from typing import Dict, Any, Optional, List

def verificar_regra_aplicacao(regra: str, potencia: float) -> bool:
    if '≥' in regra:
        min_val = float(regra.replace('≥', '').replace('kVA', ''))
        return potencia >= min_val
    elif '≤' in regra:
        max_val = float(regra.replace('≤', '').replace('kVA', ''))
        return potencia <= max_val
    return True

def calcular_valor_acessorio_com_percentuais(valor_acessorio: float, percentuais: float) -> float:
    return valor_acessorio / (1 - Decimal(percentuais))

def verificar_campos_preenchidos(dicionario,campos_obrigatorios):
    campos_vazios = []
    def verificar_valor(valor, caminho=""):
        if isinstance(valor, dict):
            for chave, val in valor.items():
                novo_caminho = f"{caminho}.{chave}" if caminho else chave
                verificar_valor(val, novo_caminho)
        elif caminho in campos_obrigatorios:  # só verifica campos obrigatórios
            if valor is None or (isinstance(valor, str) and valor.strip() == ""):
                campos_vazios.append(caminho)
    
    verificar_valor(dicionario)
    return campos_vazios

def calcular_percentuais(impostos: Dict[str, float]) -> float:
    """Calcula os percentuais totais baseados nos impostos"""
    return (
        (impostos.get('lucro', 0) / 100) + 
        TAX_CONSTANTS['ICMS_BASE'] + 
        (impostos.get('comissao', 0) / 100) + 
        (impostos.get('frete', 0) / 100) + 
        TAX_CONSTANTS['IRPJ_CSSL'] + 
        TAX_CONSTANTS['TKXADMMKT'] + 
        TAX_CONSTANTS['MOCUSFIXO'] + 
        TAX_CONSTANTS['PISCONFINS']
    )


def converter_valor_ajustado(
    valor: Decimal,  
    parametro_adicional: Decimal
) -> Decimal:
    """
    Converte o valor usando a fórmula de ajuste de percentuais e base de cálculo.
    
    Parâmetros:
    - valor: Valor original a ser convertido
    - parametro_adicional: Parâmetro adicional a ser subtraído do denominador
    
    Retorna:
    - Valor convertido e ajustado
    """
    # Carrega os impostos diretamente do session_state
    impostos = st.session_state['impostos']
    
    # Converte os valores para Decimal
    icms = Decimal(str(impostos['icms'])) / Decimal('100')
    difal = Decimal(str(impostos['difal'])) / Decimal('100')
    f_pobreza = Decimal(str(impostos['f_pobreza'])) / Decimal('100')
    
    # Calcula os percentuais totais
    percentuais = calcular_percentuais(impostos)
    
    # Primeiro termo: ajuste do valor pelos percentuais
    denominador1 = Decimal('1') - Decimal(percentuais) - Decimal(parametro_adicional)
    primeiro_termo = valor / denominador1
    
    # Segundo termo: conversão de base de cálculo
    numerador2 = Decimal('1') - Decimal('0.12')
    denominador2 = Decimal('1') - icms - difal - f_pobreza
    resultado_parte2 = numerador2 / denominador2
    
    # Cálculo final
    valor_convertido = primeiro_termo * resultado_parte2
    
    return valor_convertido

def renderizar_memorial_calculo_conversao(
    valor: Decimal,
    parametro_adicional: Decimal,
    impostos: dict = None
) -> None:
    """
    Renderiza um expander com o memorial de cálculos detalhado.
    
    Parâmetros:
    - valor: Valor original a ser convertido
    - parametro_adicional: Parâmetro adicional a ser subtraído do denominador
    - impostos: Dicionário de impostos (opcional, usa session_state se não fornecido)
    """
    # Usa impostos do session_state se não fornecidos
    if impostos is None:
        impostos = st.session_state['impostos']
    
    # Converte os valores para Decimal
    icms = Decimal(str(impostos['icms'])) / Decimal('100')
    difal = Decimal(str(impostos['difal'])) / Decimal('100')
    f_pobreza = Decimal(str(impostos['f_pobreza'])) / Decimal('100')
    
    # Calcula os percentuais totais
    percentuais = calcular_percentuais(impostos)
    
    # Cria um expander para o memorial de cálculos
    with st.expander("Memorial de Cálculos - Conversão de Valor"):
        st.markdown("### Detalhamento da Conversão de Valor")
        
        st.markdown(f"**Valor original:** R$ {float(valor):.2f}")
        st.markdown(f"**Percentuais totais:** {float(percentuais):.4f}")
        st.markdown(f"**Parâmetro adicional:** {float(parametro_adicional):.4f}")
        
        # Primeiro termo: ajuste do valor pelos percentuais
        denominador1 = Decimal('1') - Decimal(percentuais) - Decimal(parametro_adicional)
        primeiro_termo = valor / denominador1
        
        st.markdown("#### Primeiro Termo: Ajuste pelos Percentuais")
        st.markdown(f"- Denominador 1 (1 - Percentuais - Param. Adicional): {float(denominador1):.4f}")
        st.markdown(f"- Primeiro Termo (Valor / Denominador 1): R$ {float(primeiro_termo):.2f}")
        st.markdown(f"- Fórmula: {float(valor):.2f} / (1 - {float(percentuais):.4f} - {float(parametro_adicional):.4f})")
        
        # Segundo termo: conversão de base de cálculo
        st.markdown("#### Segundo Termo: Conversão de Base de Cálculo")
        st.markdown(f"- ICMS Base: {float(Decimal('0.12')):.4f}")
        st.markdown(f"- ICMS: {float(icms):.4f}")
        st.markdown(f"- DIFAL: {float(difal):.4f}")
        st.markdown(f"- F. Pobreza: {float(f_pobreza):.4f}")
        
        numerador2 = Decimal('1') - Decimal('0.12')
        denominador2 = Decimal('1') - icms - difal - f_pobreza
        resultado_parte2 = numerador2 / denominador2
        
        st.markdown(f"- Numerador 2 (1 - ICMS Base): {float(numerador2):.4f}")
        st.markdown(f"- Denominador 2 (1 - ICMS - DIFAL - F. Pobreza): {float(denominador2):.4f}")
        st.markdown(f"- Resultado Parte 2: {float(resultado_parte2):.4f}")
        st.markdown(f"- Fórmula: (1 - 0.12) / (1 - {float(icms):.4f} - {float(difal):.4f} - {float(f_pobreza):.4f})")
        
        # Cálculo final
        valor_convertido = primeiro_termo * resultado_parte2
        
        st.markdown("#### Resultado Final")
        st.markdown(f"**Valor Convertido:** R$ {float(valor_convertido):.2f}")
        st.markdown(f"- Cálculo: R$ {float(primeiro_termo):.2f} * {float(resultado_parte2):.4f}")
