from typing import Dict, Any, Optional, List
from decimal import Decimal
import pandas as pd
from utils.constants import TAX_CONSTANTS,K_FACTOR_PERCENTAGES
from .utils import verificar_regra_aplicacao
import streamlit as st

def to_decimal(value) -> Decimal:
    """Converte qualquer valor para Decimal de forma segura"""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        return Decimal(value.replace(',', '.'))
    return Decimal('0') 

def calcular_potencia_equivalente(potencia: float, fator_k: int) -> float:
    """Calcula a potência equivalente baseada no fator K"""
    if fator_k <= 5:
        return potencia
        
    return potencia / (
        (-0.000000391396 * fator_k**6) +
        (0.000044437349 * fator_k**5) -
        (0.001966117106 * fator_k**4) +
        (0.040938237195 * fator_k**3) -
        (0.345600795014 * fator_k**2) -
        (1.369407483908 * fator_k) +
        101.826204136368
    ) / 100 * 10000

def calcular_preco_item(item_data: Dict, percentuais: float, dados_impostos: Dict, 
                       acessorios: List[Dict] = None) -> Decimal:
    """Calcula o preço final do item considerando todos os fatores"""
    # Conversão inicial dos valores para Decimal
    preco_base = to_decimal(item_data['preco'])
    p_trafo = to_decimal(item_data['p_trafo'])
    percentuais = to_decimal(percentuais)
    classe_tensao = item_data.get('classe_tensao', '')
    ip_escolhido = item_data.get('ip', '00')
    fator_k = to_decimal(item_data.get('fator_k', 1))
    valor_acessorios_com_percentuais = Decimal('0')
    
    # Cálculo do preço base ajustado
    preco_base1 = preco_base / (Decimal('1') - p_trafo - percentuais)
    preco_base_com_percentuais = preco_base1
    
    st.session_state['preco_trafo'] = preco_base1

    if acessorios:
        for acessorio in acessorios:
            if acessorio['tipo'] == 'VALOR_FIXO':
                if acessorio['base_calculo'] == 'PRECO_BASE1':
                    valor_acessorio = to_decimal(acessorio['valor']) / (Decimal('1') - percentuais)
                    valor_acessorios_com_percentuais += valor_acessorio
    
    # Cálculo do adicional IP
    valor_ip_baixo = to_decimal(item_data['valor_ip_baixo'])
    valor_ip_alto = to_decimal(item_data['valor_ip_alto'])
    p_caixa = to_decimal(item_data['p_caixa'])
    
    if ip_escolhido == '00':
        adicional_ip = Decimal('0')
    else:
        adicional_ip = (valor_ip_baixo if int(ip_escolhido) < 54 else valor_ip_alto) / (Decimal('1') - percentuais - p_caixa)
    
    # Cálculo do adicional da caixa baseado na classe de tensão
    adicional_caixa_classe = Decimal('0')
    if classe_tensao == "24 kV":
        adicional_caixa_classe = to_decimal(TAX_CONSTANTS['P_CAIXA_24']) * adicional_ip
    elif classe_tensao == "36 kV":
        adicional_caixa_classe = to_decimal(TAX_CONSTANTS['P_CAIXA_36']) * adicional_ip
    
    # Cálculo do adicional do fator K
    adicional_k = preco_base1 * to_decimal(K_FACTOR_PERCENTAGES.get(fator_k, 0))

    if acessorios:
        preco_atual = preco_base1 + adicional_ip + adicional_k + adicional_caixa_classe

        for acessorio in acessorios:
            if acessorio['tipo'] == 'PERCENTUAL':
                percentual = to_decimal(acessorio['percentual']) / Decimal('100')

                if acessorio['base_calculo'] == 'PRECO_BASE1':
                    preco_atual += preco_base1 * percentual
                else:
                    preco_atual += preco_atual * percentual

        preco_base1 = preco_atual
    
    # Cálculo do preço final
    difal = to_decimal(dados_impostos['difal']) / Decimal('100')
    f_pobreza = to_decimal(dados_impostos['f_pobreza']) / Decimal('100')
    icms = to_decimal(dados_impostos['icms']) / Decimal('100')
    
    preco_unitario = ((preco_base1 + adicional_ip + adicional_k + adicional_caixa_classe) * 
                      (Decimal('1') - Decimal('0.12'))) / \
                     (Decimal('1') - difal - f_pobreza - icms)
    
    preco_unitario += valor_acessorios_com_percentuais

    return preco_unitario.quantize(Decimal('1')) 


# Função para determinar o percentual do frete
def calcular_percentual_frete(estado, distancia):
    regras = {
        "SC": (2.0, 4.0),
        "RS": (2.5, 4.0),
        "PR": (2.5, 4.0),
        "SP": (2.5, 5.0),
        "MG": (3.0, 5.0),
        "RJ": (4.0, 5.0),
        "ES": (4.0, 5.0),
        "GO": (6.0, 7.0),
        "DF": (6.0, 7.0),
        "MT": (7.0, 8.0),
        "MS": (7.0, 8.0),
        "AL": (7.5, 8.0),
        "BA": (7.5, 8.0),
        "SE": (7.5, 8.0),
        "PB": (8.0, "Orçar"),
        "PE": (8.0, "Orçar"),
        "RN": (8.0, "Orçar"),
        "CE": (9.0, "Orçar"),
        "PI": (9.0, "Orçar"),
        "MA": (9.0, "Orçar"),
        "AC": (10.0, "Orçar"),
        "AM": (10.0, "Orçar"),
        "AP": (10.0, "Orçar"),
        "PA": (10.0, "Orçar"),
        "RO": (10.0, "Orçar"),
        "RR": (10.0, "Orçar"),
        "TO": (10.0, "Orçar"),
    }

    if estado not in regras:
        return "Estado não configurado para cálculo de frete."

    limite_km = 200
    percentuais = regras[estado]

    if distancia <= limite_km:
        return percentuais[0]
    elif isinstance(percentuais[1], float):
        return percentuais[1]
    else:
        return percentuais[1]
 

