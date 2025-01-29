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
