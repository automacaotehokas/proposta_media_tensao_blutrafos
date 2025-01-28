from typing import List
from proposta_media_tensao_blutrafos.config.databaseMT import DatabaseConfig
from models.acessorios import Acessorio

class AcessorioRepository:
    @staticmethod
    def buscar_todos() -> List[Acessorio]:
        conn = DatabaseConfig.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, descricao, valor, percentual, tipo,
                           regra_aplicacao, base_calculo
                    FROM acessorios_transformador
                    ORDER BY tipo, descricao
                """)
                return [Acessorio(*row) for row in cur.fetchall()]
        finally:
            conn.close()