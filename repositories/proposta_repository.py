# repositories/proposta_repository.py
from typing import Optional
from proposta_media_tensao_blutrafos.config.databaseMT import DatabaseConfig
from models.proposta import Proposta
import uuid
from datetime import date

class PropostaRepository:
    @staticmethod
    def criar_proposta(proposta: Proposta) -> str:
        """Cria uma nova proposta no banco de dados"""
        conn = DatabaseConfig.get_connection()
        try:
            with conn.cursor() as cur:
                # Debug dos valores
                print("Valores da proposta:", {
                    'id_proposta': proposta.id_proposta,
                    'proposta': proposta.proposta,
                    'dt_oferta': proposta.dt_oferta,
                    'cliente': proposta.cliente,
                    'uf': proposta.uf,
                    'obra': proposta.obra,
                    'contato': proposta.contato,
                    'agente': proposta.agente,
                    'tipo': proposta.tipo,
                    'escopo': proposta.escopo,
                    'valor': proposta.valor,
                    'chance': proposta.chance,
                    'estagio': proposta.estagio,
                    'canal': proposta.canal,
                    'tipo_solar': proposta.tipo_solar,
                    'cabo_marca': proposta.cabo_marca,
                    'cabo_valor': proposta.cabo_valor,
                    'estrutura_marca': proposta.estrutura_marca,
                    'estrutura_modelo': proposta.estrutura_modelo,
                    'estrutura_valor': proposta.estrutura_valor,
                    'inversor_marca': proposta.inversor_marca,
                    'inversor_potencia': proposta.inversor_potencia,
                    'inversor_quantidade': proposta.inversor_quantidade,
                    'inversor_valor': proposta.inversor_valor,
                    'modulo_marca': proposta.modulo_marca,
                    'modulo_potencia': proposta.modulo_potencia,
                    'modulo_quantidade': proposta.modulo_quantidade,
                    'modulo_valor': proposta.modulo_valor,
                    'obs_solar': proposta.obs_solar
                })

                cur.execute("""
                    INSERT INTO propostas (
                        id_proposta, proposta, dt_oferta, cliente, uf, obra,
                        contato, agente, tipo, escopo, valor, chance, estagio,
                        canal, tipo_solar, cabo_marca, cabo_valor, estrutura_marca,
                        estrutura_modelo, estrutura_valor, inversor_marca,
                        inversor_potencia, inversor_quantidade, inversor_valor,
                        modulo_marca, modulo_potencia, modulo_quantidade,
                        modulo_valor, obs_solar
                    ) VALUES (
                        %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) RETURNING id_proposta::text;
                """, (
                    str(proposta.id_proposta),
                    proposta.proposta,
                    proposta.dt_oferta,
                    proposta.cliente,
                    proposta.uf,
                    proposta.obra,
                    proposta.contato,
                    proposta.agente,
                    proposta.tipo,
                    proposta.escopo,
                    proposta.valor,
                    proposta.chance,
                    proposta.estagio,
                    proposta.canal,
                    proposta.tipo_solar,
                    proposta.cabo_marca,
                    proposta.cabo_valor,
                    proposta.estrutura_marca,
                    proposta.estrutura_modelo,
                    proposta.estrutura_valor,
                    proposta.inversor_marca,
                    proposta.inversor_potencia,
                    proposta.inversor_quantidade,
                    proposta.inversor_valor,
                    proposta.modulo_marca,
                    proposta.modulo_potencia,
                    proposta.modulo_quantidade,
                    proposta.modulo_valor,
                    proposta.obs_solar
                ))
                result = cur.fetchone()
                conn.commit()
                return str(result[0])
        except Exception as e:
            conn.rollback()
            print(f"Erro na query: {str(e)}")  # Debug
            raise
        finally:
            conn.close()