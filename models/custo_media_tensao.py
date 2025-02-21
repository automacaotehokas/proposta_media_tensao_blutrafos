from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

@dataclass
class CustoMediaTensao:
    """Modelo representando a tabela custos_media_tensao"""
    id: int
    potencia: Decimal
    perdas: Optional[str] = None
    classe_tensao: Optional[str] = None
    preco: Optional[Decimal] = None
    valor_ip_baixo: Optional[Decimal] = None
    valor_ip_alto: Optional[Decimal] = None
    p_caixa: Optional[Decimal] = None
    p_trafo: Optional[Decimal] = None
    potencia_formatada: Optional[str] = None
    descricao: Optional[str] = None
    cod_proj_custo: Optional[str] = None
    cod_proj_caixa: Optional[str] = None


    @staticmethod
    def from_db_row(row: tuple) -> 'CustoMediaTensao':
        """Cria uma instância a partir de uma linha do banco"""
        return CustoMediaTensao(
            id=row[0],
            potencia=row[1],
            perdas=row[2],
            classe_tensao=row[3],
            preco=row[4],
            valor_ip_baixo=row[5],
            valor_ip_alto=row[6],
            p_caixa=row[7],
            p_trafo=row[8],
            potencia_formatada=row[9],
            descricao=row[10],
            cod_proj_custo=row[11],
            cod_proj_caixa=row[12]
        )