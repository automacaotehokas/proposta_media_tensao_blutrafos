def aplicar_mascara_telefone(telefone: str) -> str:
    """Aplica máscara no número de telefone"""
    telefone = ''.join(filter(str.isdigit, telefone))
    if len(telefone) == 11:
        return f"({telefone[:2]}) {telefone[2:7]}-{telefone[7:]}"
    elif len(telefone) == 10:
        return f"({telefone[:2]}) {telefone[2:6]}-{telefone[6:]}"
    return telefone

def get_meses_pt():
    """Retorna lista de meses em português"""
    return [
        "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", 
        "Junho", "Julho", "Agosto", "Setembro", "Outubro", 
        "Novembro", "Dezembro"
    ]