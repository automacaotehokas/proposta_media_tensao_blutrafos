# calculo_item.py

from typing import Dict, Any
import streamlit as st
import pandas as pd

def buscar_cod_caixa_proj(df: pd.DataFrame, id: int) -> Dict[str, Any]:
    """
    Busca o código de projeto e o código de caixa no DataFrame.
    """
    item_info = df[df['id'] == id]
    if item_info.empty:
        return None
    
    return {
        'cod_caixa': item_info['cod_caixa'].values[0],
        'proj': item_info['proj'].values[0]
    }

def ajustar_preco_por_derivacoes(preco_encontrado: float, item: Dict) -> float:
    """
    Ajusta o preço do item com base nas derivações selecionadas.
    """
    derivacoes = item['Derivações']
    multiplicador = 1.0

    if derivacoes['taps'] == '2 taps':
        multiplicador = max(multiplicador, 1.3)
    elif derivacoes['taps'] == '3 taps':
        multiplicador = max(multiplicador, 1.5)

    if derivacoes['tensoes_primarias'] == '2 tensões':
        multiplicador = max(multiplicador, 1.3)
    elif derivacoes['tensoes_primarias'] == '3 tensões':
        multiplicador = max(multiplicador, 1.5)

    return preco_encontrado * multiplicador

def buscar_preco_por_potencia(df: pd.DataFrame, potencia: float, produto: str, 
                             ip: str, tensao_primaria: float, tensao_secundaria: float, 
                             material: str, item: Dict) -> float:
    """
    Calcula o preço base do item considerando todas as especificações e adicionais.
    """
    tensao_primaria_padrao = 380
    tensao_secundaria_padrao = 220
    potencia_ajustada = potencia

    if produto == "ATT" and (tensao_primaria != tensao_primaria_padrao or tensao_secundaria != tensao_secundaria_padrao):
        tensao_maior = max(tensao_primaria, tensao_secundaria)
        tensao_menor = min(tensao_primaria, tensao_secundaria)
        potencia_ajustada = (potencia / tensao_maior) * (tensao_maior - tensao_menor)
        produto = 'TT'
    
    df_produto_material = df[(df['produto'] == produto) & (df['material'] == material)]
    if df_produto_material.empty:
        return 0

    df_sorted = df_produto_material.sort_values(by='potencia_numerica', ascending=True)
    potencia_mais_proxima = df_sorted[df_sorted['potencia_numerica'] >= potencia_ajustada].iloc[0]
    preco_encontrado = potencia_mais_proxima['preco']
    
    # Calcular adicionais
    soma_cx_preco = 0
    if ip not in ['00', '54']:
        soma_cx_preco = df_sorted.loc[
            df_sorted['potencia_numerica'] == potencia_mais_proxima['potencia_numerica'], 
            'preco_caixa'
        ].sum()

    preco_encontrado += soma_cx_preco

    # Aplicar ajustes de preço baseados nas características do item
    if item['Frequencia 50Hz']:
        preco_encontrado *= 1.2

    if item['Blindagem Eletrostática']:
        preco_encontrado *= 1.03

    preco_encontrado += item['Preço Rele']

    if item['Rele'] != "Nenhum":
        preco_encontrado += 3 * 51.83

    # Ajustes para ensaios
    if item['Ensaios']['Elev. Temperat.']:
        if potencia_mais_proxima['potencia_numerica'] < 1000:
            preco_encontrado += 2910
        elif potencia_mais_proxima['potencia_numerica'] >= 1250:
            preco_encontrado += 4807

    if item['Ensaios']['Nível de Ruído']:
        preco_encontrado += 1265

    # Ajustes para flanges
    if ip in ['21', '23']:
        if item['Flange'] == 1:
            preco_encontrado += soma_cx_preco * 0.3
        elif item['Flange'] == 2:
            preco_encontrado += soma_cx_preco * 0.5
    elif ip == '54':
        if item['Flange'] == 1:
            preco_encontrado *= 1.8
        elif item['Flange'] == 2:
            preco_encontrado *= 2.1
    
    return ajustar_preco_por_derivacoes(preco_encontrado, item)

def calcular_percentuais() -> float:
    """
    Calcula os percentuais totais aplicados ao preço.
    """
    icms_base = 0.12
    irpj_cssl = 0.0228
    tkxadmmkt = 0.037
    mocusfixo = 0.20
    pisconfins = 0.0925
    
    return (
        (st.session_state['impostos']['lucro'] / 100)
        + icms_base
        + (st.session_state['impostos']['comissao'] / 100)
        + (st.session_state['impostos']['frete'] / 100)
        + irpj_cssl
        + tkxadmmkt
        + mocusfixo
        + pisconfins
    )