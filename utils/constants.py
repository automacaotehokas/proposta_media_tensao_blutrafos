from typing import Dict

TAX_CONSTANTS = {
    'ICMS_BASE': 12 / 100,
    'IRPJ_CSSL': 2.28 / 100,
    'TKXADMMKT': 3.7 / 100,
    'MOCUSFIXO': 20 / 100,
    'PISCONFINS': 9.25 / 100,
    'P_CAIXA_24': 30 / 100,
    'P_CAIXA_36': 50 / 100
}

VOLTAGE_DEFAULTS = {
    "15 kV": {
        "nbi": "95kV",
        "tensao_primaria": "13,8",
        "derivacoes": "13,8/13,2/12,6/12,0/11,4kV"
    },
    "24 kV": {
        "nbi": "125kV",
        "tensao_primaria": "23,1",
        "derivacoes": "23,1/22,0/20kV"
    },
    "36 kV": {
        "nbi": "150kV",
        "tensao_primaria": "34,5",
        "derivacoes": "+/- 2x2,5%"
    }
}

K_FACTOR_PERCENTAGES = {
    1: 0.0,
    4: 0.0502,
    6: 0.0917,
    13: 0.2317,
    20: 0.3359
}

def get_default_voltage_values(classe_tensao: str) -> Dict[str, str]:
    """
    Retorna os valores padrão de tensão baseados na classe.
    
    Args:
        classe_tensao (str): A classe de tensão (ex: "15 kV", "24 kV", "36 kV")
        
    Returns:
        Dict[str, str]: Dicionário com valores padrão de tensão para a classe
    """
    return VOLTAGE_DEFAULTS.get(classe_tensao, {
        "tensao_primaria": "",
        "derivacoes": "",
        "nbi": "0"
    })


ACESSORIOS_FIXOS = [
    {"descricao": "Conjunto de 3 Buchas Plug-in", "valor": 1459},
    {"descricao": "Sensor PT - 100", "valor": 51},
    {"descricao": "Rele: TH104", "valor": 433, "regra": "≥ 75kVA"},
    {"descricao": "Rele: NT935 AD", "valor": 1248},
    {"descricao": "Rele: NT935 ETH", "valor": 3515},
    {"descricao": "Kit VF p/ TT de 15kVA a 3000kVA", "valor": 4744},
    {"descricao": "Flange AT até 15KV (s/ Barramento)", "valor": 563},
    {"descricao": "Flange BT até 800V (s/ Barramento)", "valor": 511},
    {"descricao": "Elevação de Temperatura", "valor": 2910, "regra": "≤ 1000kVA"},
    {"descricao": "Elevação de Temperatura", "valor": 4807, "regra": "≥ 1250kVA"},
    {"descricao": "Tensão Suportável Nominal de Impulso", "valor": 3542},
    {"descricao": "Nível de Tensão de Rádio Interferência", "valor": 3795},
    {"descricao": "Nível de Ruído", "valor": 1265},
    {"descricao": "Descarga", "valor": 1500}
]

ACESSORIOS_PERCENTUAIS = [
    {"descricao": "Barra Aluminio p/ Flange", "percentual": 3.5, "base_calculo": "PRECO_BASE1"},
    {"descricao": "Frequência de 50Hz", "percentual": 20.0, "base_calculo": "PRECO_TOTAL"},
    {"descricao": "Trafo Religável com +1 Tensão de MT", "percentual": 20.0, "base_calculo": "PRECO_TOTAL"},
    {"descricao": "Duplo Secundário", "percentual": 20.0, "base_calculo": "PRECO_TOTAL"},
    {"descricao": "Para tap's até 10,2kV", "percentual": 3.5, "base_calculo": "PRECO_TOTAL"},
    {"descricao": "Blindagem Eletrostática", "percentual": 2.5, "base_calculo": "PRECO_TOTAL"}
]