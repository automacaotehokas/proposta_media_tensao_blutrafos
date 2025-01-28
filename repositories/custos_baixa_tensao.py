from typing import List, Optional
import pandas as pd
from proposta_media_tensao_blutrafos.config.databaseMT import DatabaseConfig
from models.custo_baixa_tensao import CustoBaixaTensao


class CustoBaixaTensaoRepository:
    @staticmethod
    def buscar_todos() -> List[CustoBaixaTensao]:
        """Busca todos os registros da tabela"""
        conn = DatabaseConfig.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        c.*, 
                        cx.preco AS preco_caixa  
                    FROM 
                        custos_bxbx c
                    LEFT JOIN 
                        caixa_bxbx cx ON c.modelo_caixa = cx.modelo
                    ORDER BY 
                        potencia_numerica ASC;
                """)
                results = cur.fetchall()
                return [CustoBaixaTensao.from_db_row(row) for row in results]
        finally:
            conn.close()
