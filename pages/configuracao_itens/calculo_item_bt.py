# calculo_item_bt.py

from typing import Dict, Any
import streamlit as st
import pandas as pd
from decimal import Decimal
from pages.configuracao_itens.utils import converter_valor_ajustado
from utils.constants import TAX_CONSTANTS

def buscar_cod_caixa_proj(df: pd.DataFrame, id: int) -> Dict[str, Any]:
    """Busca o código de projeto e o código de caixa no DataFrame."""
    item_info = df[df['id'] == id]
    if item_info.empty:
        return None
    
    return {
        'cod_caixa': item_info['cod_caixa'].values[0],
        'proj': item_info['proj'].values[0]
    }

def ajustar_preco_por_derivacoes(preco_encontrado: float, item: Dict) -> float:
    """Ajusta o preço do item com base nas derivações selecionadas."""
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

def calcular_preco_com_impostos(preco_base: float, dados_impostos: Dict[str, Any], percentuais: float) -> Dict[str, float]:
    """Calcula o preço final considerando impostos e percentuais."""
    try:
        # Converter para Decimal para maior precisão
        preco_base_dec = Decimal(str(preco_base))
        percentuais_dec = Decimal(str(percentuais))
        p_trafo = Decimal(str(dados_impostos.get('p_trafo', '0')))

        # Cálculo similar ao MT
        preco_base1 = preco_base_dec / (Decimal('1') - p_trafo - percentuais_dec)
        
        # Salvar preço do transformador no session state
        st.session_state['preco_trafo'] = float(preco_base1)

        # Calcular preços com impostos
        preco_final = preco_base1

        return {
            'preco_base': float(preco_base_dec),
            'preco_com_impostos': float(preco_final)
        }
    except Exception as e:
        st.error(f"Erro no cálculo de impostos: {str(e)}")
        return {
            'preco_base': preco_base,
            'preco_com_impostos': preco_base
        }

def buscar_preco_por_potencia(df: pd.DataFrame, potencia: float, produto: str, 
                             ip: str, tensao_primaria: float, tensao_secundaria: float, 
                             material: str, item: Dict) -> float:
    """Calcula o preço base do item considerando todas as especificações e adicionais."""
    tensao_primaria_padrao = 380
    tensao_secundaria_padrao = 220
    potencia_ajustada = potencia

    if produto == "ATT" and (tensao_primaria != tensao_primaria_padrao or tensao_secundaria != tensao_secundaria_padrao):
        tensao_maior = max(tensao_primaria, tensao_secundaria)
        tensao_menor = min(tensao_primaria, tensao_secundaria)
        potencia_ajustada = (potencia / tensao_maior) * (tensao_maior - tensao_menor)
        st.write(f"Potencia ajustada:{potencia_ajustada}")
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
    
    return preco_encontrado

def calcular_preco_encontrado(
    df: pd.DataFrame,
    preco_base: float, 
    potencia: float, 
    produto: str,
    ip: str,
    tensao_primaria: float,
    tensao_secundaria: float,
    material: str,
    item: Dict[str, Any]
) -> float:
    """
    Calcula o preço de um item encontrado.
    """
    # Lógica de ajuste de tensão para produto ATT
    tensao_primaria_padrao = 380
    tensao_secundaria_padrao = 220
    potencia_ajustada = potencia

    if produto == "ATT" and (tensao_primaria != tensao_primaria_padrao or tensao_secundaria != tensao_secundaria_padrao):
        tensao_maior = max(tensao_primaria, tensao_secundaria)
        tensao_menor = min(tensao_primaria, tensao_secundaria)
        potencia_ajustada = (potencia / tensao_maior) * (tensao_maior - tensao_menor)
        st.write(f"Potencia ajustada:{potencia_ajustada}")
        produto = 'TT'
    
    # Busca preço base na tabela
    df_produto_material = df[(df['produto'] == produto) & (df['material'] == material)]
    if df_produto_material.empty:
        return 0

    df_sorted = df_produto_material.sort_values(by='potencia_numerica', ascending=True)
    potencia_mais_proxima = df_sorted[df_sorted['potencia_numerica'] >= potencia_ajustada].iloc[0]
    preco_trafo = potencia_mais_proxima['preco']
    
    # Cálculo de adicional de caixa para IP
    soma_cx_preco = 0

    adicional_ip = Decimal('0')
    if ip not in ['00', '54']:
        soma_cx_preco = df_sorted.loc[
            df_sorted['potencia_numerica'] == potencia_mais_proxima['potencia_numerica'], 
            'preco_caixa'
        ].sum()
        
    # Incializa variáveis
    adicional_acessorios_percentual = 0
    adicional_acessorios_fixo = 0
    # Ajustes de preço baseados nas características do item
    if item['Frequencia 50Hz']:
        adicional_acessorios_percentual += 0.2

    if item['Blindagem Eletrostática']:
        adicional_acessorios_percentual += 0.3

    # Adiciona preços de acessórios específicos
    adicional_acessorios_fixo += item['Preço Rele']

    if item['Rele'] != "Nenhum":
        adicional_acessorios_fixo += 3 * 51.83

    # Ajustes para ensaios
    if item['Ensaios']['Elev. Temperat.']:
        if potencia_mais_proxima['potencia_numerica'] < 1000:
            adicional_acessorios_fixo += 2910
        elif potencia_mais_proxima['potencia_numerica'] >= 1250:
            adicional_acessorios_fixo += 4807

    if item['Ensaios']['Nível de Ruído']:
        adicional_acessorios_fixo += 1265



    # Ajustes para flanges
    if ip in ['21', '23']:
        if item['Flange'] == 1:
            adicional_ip =  0.3
            st.write("FLANGE 1")
        elif item['Flange'] == 2:
            adicional_ip =  0.5
            st.write("FLANGE 2")
    elif ip == '54':
        if item['Flange'] == 1:
            adicional_ip =  0.8
            st.write("FLANGE 1 IP 54")
        elif item['Flange'] == 2:
            adicional_ip =  1.5
    


    preco_caixa = converter_valor_ajustado(Decimal(str(soma_cx_preco)), Decimal('0'))
    
    # Cálculo do adicional IP como percentual do preço da caixa
    adicional_ip_valor = preco_caixa * Decimal(str(adicional_ip))
    
    # Cálculo do preço unitário
    preco_unitario = (
        converter_valor_ajustado(Decimal(str(preco_trafo)), Decimal('0')) + 
        preco_caixa + 
        adicional_ip_valor + 
        Decimal(str(adicional_acessorios_fixo)) + 
        Decimal(str(adicional_acessorios_percentual))
    )
    
    # Detalhamento do cálculo
    st.markdown("### 📊 Detalhamento do Preço Unitário")
    
    st.write(f"- Percentual Adicional IP: {float(adicional_ip):.2%}")
    st.write(f"- Adicional IP: R$ {float(adicional_ip_valor):.2f}")
    st.write(f"- Adicional Acessórios Fixos: R$ {float(adicional_acessorios_fixo):.2f}")
    st.write(f"- Adicional Acessórios Percentuais: R$ {float(adicional_acessorios_percentual):.2f}")
    
    # Format the unit price in Brazilian currency format
    preco_formatado = f"R$ {float(preco_unitario):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    # Destaque do preço final
    st.markdown(f"### 💰 **Preço Unitário Final:** {preco_formatado}")
    
    return float(preco_unitario)
