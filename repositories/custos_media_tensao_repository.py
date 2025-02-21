from typing import List, Optional
import pandas as pd
from config.databaseMT import DatabaseConfig
from models.custo_media_tensao import CustoMediaTensao

class CustoMediaTensaoRepository:
    @staticmethod
    def buscar_todos() -> List[CustoMediaTensao]:
        """Busca todos os registros da tabela"""
        conn = DatabaseConfig.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, potencia, perdas, classe_tensao, preco,
                           valor_ip_baixo, valor_ip_alto, p_caixa, p_trafo,
                           potencia_formatada, descricao, cod_proj_custo, cod_proj_caixa
                    FROM custos_media_tensao
                    ORDER BY potencia ASC
                """)
                results = cur.fetchall()
                return [CustoMediaTensao.from_db_row(row) for row in results]
        finally:
            conn.close()

    @staticmethod
    def atualizar_dados(df: pd.DataFrame) -> None:
        """Atualiza os dados da tabela com os dados do DataFrame"""
        conn = DatabaseConfig.get_connection()
        try:
            with conn.cursor() as cur:
                # Limpa a tabela
                cur.execute("DELETE FROM custos_media_tensao")

                # Insere os novos dados
                for _, row in df.iterrows():
                    cur.execute("""
                        INSERT INTO custos_media_tensao (
                            p_caixa, p_trafo, potencia, preco, perdas,
                            classe_tensao, valor_ip_baixo, valor_ip_alto,
                            cod_proj_custo, descricao, potencia_formatada,
                            cod_proj_caixa
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        row['p_caixa'],
                        row['p_trafo'],
                        row['potencia'],
                        row['preco'],
                        row['perdas'],
                        row['classe_tensao'],
                        row['valor_ip_baixo'],
                        row['valor_ip_alto'],
                        row['cod_proj_custo'],
                        row['descricao'],
                        row['potencia_formatada'],
                        row['cod_proj_caixa']
                    ))
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"Erro ao atualizar dados: {str(e)}")
        finally:
            conn.close()