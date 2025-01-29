from typing import Dict, Any, Optional, List
from decimal import Decimal
import pandas as pd
from utils.constants import TAX_CONSTANTS,K_FACTOR_PERCENTAGES
from .utils import verificar_regra_aplicacao
import streamlit as st

class CalculoItemMT:
    def __init__(self, item_data: Dict[str, Any], percentuais: float, dados_impostos: Dict[str, Any], acessorios: List[Dict] = None):
        self.item_data = item_data
        self.percentuais = percentuais
        self.dados_impostos = dados_impostos
        self.acessorios = acessorios

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

    def calcular_preco_item(self) -> float:
        """Calcula o preço final do item considerando todos os fatores"""
        # Conversão inicial dos valores para Decimal
        preco_base = Decimal(str(self.item_data['preco']))
        p_trafo = Decimal(str(self.item_data['p_trafo']))
        classe_tensao = self.item_data.get('classe_tensao', '')
        ip_escolhido = self.item_data.get('ip', '00')
        fator_k = self.item_data.get('fator_k', 1)
        valor_acessorios_com_percentuais = Decimal('0')
        
        # Cálculo do preço base ajustado
        preco_base1 = preco_base / (Decimal('1') - p_trafo - Decimal(str(self.percentuais)))

        preco_base_com_percentuais = preco_base1

        st.session_state['preco_trafo'] = float(preco_base1)

        if self.acessorios:
            for acessorio in self.acessorios:
                if acessorio['tipo'] == 'VALOR_FIXO':
                    if acessorio['base_calculo'] == 'PRECO_BASE1':
                        valor_acessorio = Decimal(str(acessorio['valor'])) / (Decimal('1') - Decimal(str(self.percentuais)))
                        valor_acessorios_com_percentuais += valor_acessorio
        
        # Cálculo do adicional IP
        valor_ip_baixo = Decimal(str(self.item_data['valor_ip_baixo']))
        valor_ip_alto = Decimal(str(self.item_data['valor_ip_alto']))
        p_caixa = Decimal(str(self.item_data['p_caixa']))
        
        if ip_escolhido == '00':
            adicional_ip = Decimal('0')
        else:
            adicional_ip = valor_ip_baixo / (Decimal('1') - Decimal(str(self.percentuais)) - p_caixa) if int(ip_escolhido) < 54 else valor_ip_alto / (Decimal('1') - Decimal(str(self.percentuais)) - p_caixa)
        
        # Cálculo do adicional da caixa baseado na classe de tensão
        adicional_caixa_classe = Decimal('0')
        if classe_tensao == "24 kV":
            adicional_caixa_classe = Decimal(str(TAX_CONSTANTS['P_CAIXA_24'])) * adicional_ip
        elif classe_tensao == "36 kV":
            adicional_caixa_classe = Decimal(str(TAX_CONSTANTS['P_CAIXA_36'])) * adicional_ip
        
        # Cálculo do adicional do fator K
        adicional_k = preco_base1 * Decimal(str(K_FACTOR_PERCENTAGES.get(fator_k, 0)))

        if self.acessorios:
            preco_atual = preco_base1 + adicional_ip + adicional_k + adicional_caixa_classe

            for acessorio in self.acessorios:
                if acessorio['tipo'] == 'PERCENTUAL':
                    percentual = Decimal(str(acessorio['percentual'])) / Decimal('100')

                    if acessorio['base_calculo'] == 'PRECO_BASE1':
                        preco_atual += preco_base1 * percentual
                    else:
                        preco_atual += preco_atual * percentual

            preco_base1 = preco_atual

        # Cálculo do preço final
        preco_unitario = int(((preco_base1 + adicional_ip + adicional_k + adicional_caixa_classe) * (Decimal('1') - Decimal('0.12'))) / \
                        (Decimal('1') - (Decimal(str(self.dados_impostos['difal'])) / Decimal('100')) - (Decimal(str(self.dados_impostos['f_pobreza'])) / Decimal('100')) - (Decimal(str(self.dados_impostos['icms'])) / Decimal('100'))))
        
        preco_unitario += valor_acessorios_com_percentuais

        st.write(st.session_state)

        return float(preco_unitario)

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
