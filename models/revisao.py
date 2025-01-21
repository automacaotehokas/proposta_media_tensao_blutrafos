from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import json

@dataclass
class Revisao:
    """Modelo representando uma revisão de proposta"""
    id_revisao: str
    id_proposta_id: str
    valor: float
    conteudo: Dict[str, Any]
    revisao: int
    dt_revisao: datetime
    comentario: Optional[str] = None
    arquivo: Optional[str] = None
    arquivo_pdf: Optional[str] = None

    @staticmethod
    def from_db_row(row: tuple) -> 'Revisao':
        """Cria uma instância a partir de uma linha do banco"""
        return Revisao(
            id_revisao=row[0],
            id_proposta_id=row[1],
            valor=row[2],
            conteudo=json.loads(row[3]) if row[3] else {},
            revisao=row[4],
            dt_revisao=row[5],
            comentario=row[6],
            arquivo=row[7],
            arquivo_pdf=row[8]
        )