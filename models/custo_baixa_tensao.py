from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
 
@dataclass
class CustoBaixaTensao:
    """Modelo representando a tabela custos_bxbx"""
    id: int
    produto: Optional[str] = None
    potencia: Optional[str] = None
    potencia_numerica: Optional[Decimal] = None
    material: Optional[str] = None
    tensao_primaria: Optional[int] = None
    tensao_secundaria: Optional[int] = None
    preco: Optional[float] = None
    proj: Optional[str] = None
    modelo_caixa: Optional[str] = None
    descricao: Optional[str] = None
    cod_caixa: Optional[str] = None
 
    @staticmethod
    def from_db_row(row: tuple) -> 'CustoBaixaTensao':
        """Cria uma instância a partir de uma linha do banco"""
        return CustoBaixaTensao(
            id=row[0],
            produto=row[1],
            potencia=row[2],
            potencia_numerica=row[3],
            material=row[4],
            tensao_primaria=row[5],
            tensao_secundaria=row[6],
            preco=row[7],
            proj=row[8],
            modelo_caixa=row[9],
            descricao=row[10],
            cod_caixa=row[11]
        )