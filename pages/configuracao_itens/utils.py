from decimal import Decimal

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