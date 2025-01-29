from typing import List, Optional
import pandas as pd
from config.databaseMT import DatabaseConfig
from models.custo_baixa_tensao import CustoBaixaTensao


class CustoBaixaTensaoRepository:
    @staticmethod
    def buscar_todos() -> pd.DataFrame:
        """Busca todos os registros da tabela e retorna como DataFrame"""
        conn = DatabaseConfig.get_connection()
        try:
            query = """
                SELECT 
                    c.id,
                    c.produto,
                    c.potencia,
                    c.potencia_numerica,
                    c.material,
                    c.tensao_primaria,
                    c.tensao_secundaria,
                    c.preco,
                    c.proj,
                    c.modelo_caixa,
                    c.descricao,
                    c.cod_caixa,
                    cx.preco AS preco_caixa  
                FROM 
                    custos_bxbx c
                LEFT JOIN 
                    caixa_bxbx cx ON c.modelo_caixa = cx.modelo
                ORDER BY 
                    c.potencia_numerica ASC;
            """
            df = pd.read_sql(query, conn)
            # Renomeia as colunas para minúsculo
            df.columns = df.columns.str.lower()
            return df
        finally:
            conn.close()
