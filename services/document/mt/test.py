# services/document/word_tables.py
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from typing import Dict, List, Any

import streamlit as st
import logging
logger = logging.getLogger(__name__)


def formatar_numero_inteiro_ou_decimal(valor):
    """
    Converte um número para inteiro se for um número inteiro,
    ou mantém uma casa decimal substituindo . por , se tiver casa decimal.
    Aceita números tanto com ponto quanto com vírgula como separador decimal.
    
    Exemplos:
    1000.00 -> 1000     (remove decimais zero)
    125.5 -> 125,5      (converte ponto para vírgula)
    125.50 -> 125       (remove decimais zero)
    112,5 -> 112,5      (mantém formato com vírgula)
    """
    try:
        # Primeiro convertemos para string para garantir que podemos manipular o texto
        valor_str = str(valor)
        
        # Se o número já veio com vírgula, convertemos para ponto para fazer o cálculo
        valor_padronizado = valor_str.replace(',', '.')
        
        # Agora podemos converter para float com segurança
        valor_float = float(valor_padronizado)
        
        # Se for um número inteiro
        if valor_float.is_integer():
            return str(int(valor_float))
        
        # Se tiver casa decimal, formatamos com uma casa e usamos vírgula
        return f"{valor_float:.1f}".replace('.', ',')
    
    except (ValueError, TypeError):
        return str(valor)   
    
print(formatar_numero_inteiro_ou_decimal(1000.00))  # Saída: "1000"
print(formatar_numero_inteiro_ou_decimal(125.5))    # Saída: "125,5"
print(formatar_numero_inteiro_ou_decimal("112,5"))  # Saída: "112,5"
print(formatar_numero_inteiro_ou_decimal(125.50))   # Saída: "125"
print(formatar_numero_inteiro_ou_decimal(3.0))

def formatar_numero_brasileiro(valor):
    """
    Converte um número para o formato brasileiro de moeda.
    Exemplo: 10000000.50 -> '10.000.000,50'
    """
    try:
        # Converte para float para garantir formato correto
        valor = float(valor)
        # Usa format para separar milhares com ponto e usar vírgula para decimais
        return f"{valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return '0,00'