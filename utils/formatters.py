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