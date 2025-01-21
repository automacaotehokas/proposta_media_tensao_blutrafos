# repositories/revisao_repository.py
from typing import List, Optional
from config.database import DatabaseConfig
from models.revisao import Revisao
import json

class RevisaoRepository:
    @staticmethod
    def buscar_por_id(revisao_id: str) -> Optional[Revisao]:
        """Busca uma revisão pelo ID"""
        conn = DatabaseConfig.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id_revisao, id_proposta_id, valor, conteudo,
                           revisao, dt_revisao, comentario, arquivo, arquivo_pdf
                    FROM revisoes
                    WHERE id_revisao = %s
                """, (revisao_id,))
                row = cur.fetchone()
                return Revisao.from_db_row(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def salvar_revisao(revisao: Revisao) -> str:
        """Salva ou atualiza uma revisão"""
        conn = DatabaseConfig.get_connection()
        try:
            with conn.cursor() as cur:
                if revisao.id_revisao:
                    # Atualização
                    cur.execute("""
                        UPDATE revisoes
                        SET conteudo = %s,
                            valor = %s,
                            revisao = %s,
                            dt_revisao = NOW(),
                            comentario = %s,
                            arquivo = %s,
                            arquivo_pdf = %s
                        WHERE id_revisao = %s
                        RETURNING id_revisao
                    """, (
                        json.dumps(revisao.conteudo),
                        revisao.valor,
                        revisao.revisao,
                        revisao.comentario,
                        revisao.arquivo,
                        revisao.arquivo_pdf,
                        revisao.id_revisao
                    ))
                else:
                    # Inserção
                    cur.execute("""
                        INSERT INTO revisoes (
                            id_revisao, id_proposta_id, valor, conteudo,
                            revisao, dt_revisao, comentario, arquivo, arquivo_pdf
                        ) VALUES (
                            gen_random_uuid(), %s, %s, %s, %s, NOW(), %s, %s, %s
                        )
                        RETURNING id_revisao
                    """, (
                        revisao.id_proposta_id,
                        revisao.valor,
                        json.dumps(revisao.conteudo),
                        revisao.revisao,
                        revisao.comentario,
                        revisao.arquivo,
                        revisao.arquivo_pdf
                    ))
                
                result = cur.fetchone()
                conn.commit()
                return result[0]
        except Exception as e:
            conn.rollback()
            raise Exception(f"Erro ao salvar revisão: {str(e)}")
        finally:
            conn.close()