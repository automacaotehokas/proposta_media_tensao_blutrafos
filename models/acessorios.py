from decimal import Decimal

class Acessorio:
    def __init__(self, id: int, descricao: str, tipo: str, valor: Decimal, 
                 percentual: Decimal, base_calculo: str, regra_aplicacao: str):
        self.id = id
        self.descricao = descricao
        self.tipo = tipo
        self.valor = valor
        self.percentual = percentual
        self.base_calculo = base_calculo
        self.regra_aplicacao = regra_aplicacao
    
    @classmethod
    def from_db_row(cls, row):
        return cls(
            id=row[0],
            descricao=row[1],
            tipo=row[2],
            valor=Decimal(str(row[3])),
            percentual=Decimal(str(row[4])),
            base_calculo=row[5],
            regra_aplicacao=row[6]
        )