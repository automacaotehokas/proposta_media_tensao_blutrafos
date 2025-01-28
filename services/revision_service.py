import json
from typing import Dict, Any, Optional, Tuple, List
from decimal import Decimal
from config.database import DatabaseConfig
from io import BytesIO
from pathlib import Path
import logging
import sys
from datetime import datetime
from pathlib import Path

# Cria diretório de logs se não existir
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configura o formato do log
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        # Handler para console
        logging.StreamHandler(sys.stdout),
        # Handler para arquivo
        logging.FileHandler(
            filename=f"logs/app_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
    ]
)

# Configuração do logger específico
logger = logging.getLogger(__name__)

def atualizar_proposta(id_proposta: str, escopo: str, valor: float, ultima_revisao: int, id_revisao: str = None) -> None:
    """
    Atualiza os dados da proposta com a última revisão.
    """
    logger.info(f"""
    Iniciando atualização da proposta:
    - ID: {id_proposta}
    - Escopo: {escopo}
    - Valor: {valor}
    - Última Revisão: {ultima_revisao}
    - ID Revisão (se fornecido): {id_revisao}
    """)

    try:
        conn = DatabaseConfig.get_connection()
        cur = conn.cursor()

        # Se não foi fornecido id_revisao, busca ele
        if not id_revisao:
            logger.info(f"Buscando ID da revisão mais recente para proposta {id_proposta} e revisão {ultima_revisao}")
            cur.execute("""
                SELECT id_revisao::text 
                FROM revisoes 
                WHERE id_proposta_id = %s::uuid AND revisao = %s
                ORDER BY dt_revisao DESC
                LIMIT 1
            """, (id_proposta, ultima_revisao))
            
            resultado = cur.fetchone()
            
            if not resultado:
                logger.error(f"Nenhuma revisão encontrada para proposta {id_proposta} com revisão {ultima_revisao}")
                return

            id_revisao = resultado[0]

        logger.info(f"ID da revisão para atualização: {id_revisao}")

        # Log dos valores antes da atualização
        cur.execute("""
            SELECT escopo, valor, ultima_revisao
            FROM propostas 
            WHERE id_proposta = %s::uuid
        """, (id_proposta,))
        valores_antigos = cur.fetchone()
        if valores_antigos:
            logger.info(f"""
            Valores atuais da proposta antes da atualização:
            - Escopo: {valores_antigos[0]}
            - Valor: {valores_antigos[1]}
            - Última Revisão: {valores_antigos[2]}
            """)

        # Log da query de atualização
        query = """
            UPDATE propostas 
            SET 
                escopo = %s, 
                valor = %s, 
                ultima_revisao = %s
            WHERE id_proposta = %s::uuid
            RETURNING id_proposta, escopo, valor, ultima_revisao
        """
        
        logger.info(f"""
        Executando query de atualização com parâmetros:
        - Escopo: {escopo}
        - Valor: {valor}
        - Última Revisão: {ultima_revisao}
        - ID Proposta: {id_proposta}
        """)

        cur.execute(query, (
            escopo, 
            valor, 
            ultima_revisao, 
            id_proposta
        ))

        resultado_update = cur.fetchone()
        if resultado_update:
            logger.info(f"""
            Proposta atualizada com sucesso:
            - ID: {resultado_update[0]}
            - Novo Escopo: {resultado_update[1]}
            - Novo Valor: {resultado_update[2]}
            - Nova Última Revisão: {resultado_update[3]}
            """)
        else:
            logger.warning("Nenhuma linha foi atualizada na tabela propostas")

        conn.commit()
        logger.info("Commit realizado com sucesso")
        
        # Verificação final
        cur.execute("""
            SELECT escopo, valor, ultima_revisao
            FROM propostas 
            WHERE id_proposta = %s::uuid
        """, (id_proposta,))
        valores_novos = cur.fetchone()
        if valores_novos:
            logger.info(f"""
            Valores finais da proposta após atualização:
            - Escopo: {valores_novos[0]}
            - Valor: {valores_novos[1]}
            - Última Revisão: {valores_novos[2]}
            """)
        
        cur.close()
        conn.close()
        logger.info("Conexão fechada com sucesso")

    except Exception as e:
        logger.error(f"Erro ao atualizar proposta: {str(e)}")
        logger.exception("Stacktrace completo:")
        raise

def is_ultima_revisao(id_proposta: str, numero_revisao: int) -> bool:
    """
    Verifica se o número da revisão é maior que todas as outras revisões da proposta.
    
    Args:
        id_proposta: UUID da proposta
        numero_revisao: Número da revisão a ser verificada
    
    Returns:
        bool: True se for a maior revisão, False caso contrário
    """
    conn = DatabaseConfig.get_connection()
    try:
        with conn.cursor() as cur:
            # Busca a maior revisão da proposta
            cur.execute("""
                SELECT MAX(revisao) as maior_revisao
                FROM revisoes
                WHERE id_proposta_id = %s::uuid;
            """, (id_proposta,))
            
            result = cur.fetchone()
            if not result or result[0] is None:
                logger.info(f"Nenhuma revisão encontrada para proposta {id_proposta}. Esta será a primeira.")
                return True
                
            maior_revisao = result[0]
            eh_maior = numero_revisao >= maior_revisao
            
            logger.info(f"""
                Verificando se revisão {numero_revisao} é a maior:
                - Maior revisão encontrada: {maior_revisao}
                - Nova revisão: {numero_revisao}
                - É a maior? {eh_maior}
            """)
            
            return eh_maior

    except Exception as e:
        logger.error(f"Erro ao verificar última revisão: {e}")
        return False
    finally:
        conn.close()

class RevisionService:
    @staticmethod
    def buscar_escopo_transformador(itens: List[Dict[str, Any]]) -> str:
        """
        Calcula a potência total dos transformadores em MVA, considerando a quantidade de cada item.
        
        Para cada item, multiplica sua potência pela sua quantidade e soma todos os resultados.
        Por exemplo:
        Item 1: 500 kVA × 2 unidades = 1000 kVA
        Item 2: 750 kVA × 3 unidades = 2250 kVA
        Total: 3250 kVA = 3,250 MVA
        """
        try:
            # Soma o produto da potência pela quantidade para cada item
            potencia_total = sum(
                float(item.get('Potência', 0)) * float(item.get('Quantidade', 0))
                for item in itens
            ) / 1000  # Converte de kVA para MVA
            
            # Formata com 3 casas decimais e substitui ponto por vírgula
            potencia_formatada = f"{potencia_total:.3f}".replace('.', ',')
            return f"{potencia_formatada} MVA"

        except (ValueError, TypeError) as e:
            logger.error(f"Erro ao calcular escopo do transformador: {e}")
            return "0,000 MVA"

    @staticmethod
    def _atualizar_revisao(
        cur,
        dados: Dict[str, Any],
        valor: float,
        numero_revisao: int,
        word_path: str,
        pdf_path: str,
        escopo: str,
        revisao_id: str
    ) -> Optional[str]:
        """
        Update an existing revision in the database.
        """
        logger.info(f"""
        Iniciando atualização de revisão:
        - ID Revisão: {revisao_id}
        - Valor: {valor}
        - Número Revisão: {numero_revisao}
        - Word Path: {word_path}
        - PDF Path: {pdf_path}
        - Escopo: {escopo}
        """)

        try:
            logger.info("Preparando dados para atualização da revisão...")
            json_dados = json.dumps(dados, default=lambda x: float(x) if isinstance(x, Decimal) else x)
            logger.info("Dados JSON preparados com sucesso")

            logger.info("Executando query de UPDATE na tabela revisoes...")
            cur.execute("""
                UPDATE revisoes 
                SET conteudo = %s::jsonb, 
                    valor = %s,
                    revisao = %s,
                    dt_revisao = NOW(),
                    comentario = 'Revisão Atualizada',
                    arquivo = %s,
                    arquivo_pdf = %s,
                    escopo = %s
                WHERE id_revisao = %s
                RETURNING id_revisao, id_proposta_id;
            """, (json_dados, valor, numero_revisao, word_path, pdf_path, escopo, revisao_id))
            
            result = cur.fetchone()
            logger.info(f"Resultado do UPDATE: {result}")

            if result:
                revisao_id, id_proposta = str(result[0]), str(result[1])
                logger.info(f"Revisão atualizada com sucesso. ID: {revisao_id}, ID Proposta: {id_proposta}")
                
                logger.info(f"Verificando se revisão {numero_revisao} é a mais recente...")
                if is_ultima_revisao(id_proposta, numero_revisao):
                    logger.info(f"Revisão {numero_revisao} é a mais recente. Atualizando proposta...")
                    atualizar_proposta(
                        id_proposta=id_proposta,
                        escopo=escopo,
                        valor=valor,
                        ultima_revisao=numero_revisao
                    )
                else:
                    logger.info(f"Revisão {revisao_id} não é a mais recente. Proposta não será atualizada.")

                return revisao_id
            
            logger.warning("Nenhuma revisão foi atualizada")
            return None

        except Exception as e:
            logger.error(f"Erro ao atualizar revisão {revisao_id}: {e}")
            logger.exception("Stacktrace completo:")
            raise Exception(f"Erro ao atualizar revisão: {str(e)}")

    @staticmethod
    def _inserir_revisao(
        cur,
        dados: Dict[str, Any],
        id_proposta: str,
        valor: float,
        numero_revisao: int,
        word_path: str,
        pdf_path: str,
        escopo: str
    ) -> Optional[str]:
        """
        Insere ou atualiza uma revisão no banco de dados.
        """
        logger.info(f"""
        Iniciando inserção/atualização de revisão:
        - ID Proposta: {id_proposta}
        - Valor: {valor}
        - Número Revisão: {numero_revisao}
        - Word Path: {word_path}
        - PDF Path: {pdf_path}
        - Escopo: {escopo}
        """)

        try:
            logger.info("Verificando se já existe uma revisão com este número...")
            cur.execute("""
            SELECT id_revisao::text
            FROM revisoes
            WHERE id_proposta_id = %s::uuid AND revisao = %s;
            """, (id_proposta, numero_revisao))

            existing_revision = cur.fetchone()
            logger.info(f"Resultado da busca por revisão existente: {existing_revision}")

            if existing_revision:
                logger.info("Encontrada revisão existente. Buscando última versão...")
                cur.execute("""
                SELECT id_revisao::text 
                FROM revisoes 
                WHERE id_proposta_id = %s::uuid AND revisao = %s
                ORDER BY dt_revisao DESC
                LIMIT 1
                """, (id_proposta, numero_revisao))
                
                ultima_revisao = cur.fetchone()
                revisao_id = str(ultima_revisao[0]) if ultima_revisao else str(existing_revision[0])
                
                logger.info(f"Encontrada revisão {revisao_id} com número {numero_revisao}, chamando atualização...")
                return RevisionService._atualizar_revisao(
                    cur=cur,
                    dados=dados,
                    valor=valor,
                    numero_revisao=numero_revisao,
                    word_path=word_path,
                    pdf_path=pdf_path,
                    escopo=escopo,
                    revisao_id=revisao_id
                )

            logger.info("Verificando se é a próxima revisão válida...")
            cur.execute("""
            SELECT MAX(revisao)
            FROM revisoes
            WHERE id_proposta_id = %s::uuid;
            """, (id_proposta,))
            
            result = cur.fetchone()
            ultima_revisao = result[0] if result and result[0] is not None else -1
            proxima_revisao = ultima_revisao + 1
            
            logger.info(f"Última revisão: {ultima_revisao}, Próxima revisão: {proxima_revisao}")

            if numero_revisao != proxima_revisao:
                logger.error(f"Tentativa inválida: revisão {numero_revisao} ≠ próxima revisão {proxima_revisao}")
                raise Exception(f"Não é possível criar a revisão {numero_revisao}. A próxima revisão deve ser {proxima_revisao}")

            logger.info(f"Preparando dados para nova revisão {numero_revisao}...")
            dados_para_salvar = {
                'itens_configurados': dados.get('itens_configurados', []),
                'impostos': dados.get('impostos', {}),
                'dados_iniciais': dados.get('dados_iniciais', {}),
                'configuracoes_itens': dados.get('configuracoes_itens', {})
            }

            comentario = ('Revisão Inicial' if numero_revisao == 0 
                        else dados.get('dados_iniciais', {}).get('comentario', ''))
            
            logger.info("Inserindo nova revisão no banco...")
            cur.execute("""
                INSERT INTO revisoes (
                    id_revisao, id_proposta_id, valor, conteudo, revisao,
                    dt_revisao, comentario, arquivo, arquivo_pdf, escopo
                )
                VALUES (
                    gen_random_uuid(), %s::uuid, %s, %s, %s,
                    NOW(), %s, %s, %s, %s
                )
                RETURNING id_revisao;
            """, (
                id_proposta,
                valor,
                json.dumps(dados_para_salvar, default=lambda x: float(x) if isinstance(x, Decimal) else x),
                numero_revisao,
                comentario,
                word_path,
                pdf_path,
                escopo
            ))
            
            result = cur.fetchone()
            revisao_id = str(result[0]) if result else None
            logger.info(f"Nova revisão criada com ID: {revisao_id}")

            if not revisao_id:
                logger.error(f"Falha ao inserir revisão {numero_revisao}")
                return None
            
            logger.info(f"Verificando necessidade de atualizar proposta (última revisão: {ultima_revisao})")
            # Dentro da função _inserir_revisao, onde faz a chamada para atualizar_proposta
            if revisao_id and (is_ultima_revisao(id_proposta, numero_revisao) or ultima_revisao in {0,'00'}):
                logger.info("Chamando atualização da proposta...")
                atualizar_proposta(
                    id_proposta=id_proposta,
                    escopo=escopo,
                    valor=valor,
                    ultima_revisao=numero_revisao,
                    id_revisao=revisao_id  # Passa o ID da revisão que acabamos de criar
                )
            else:
                logger.info(f"Revisão {numero_revisao} não é a mais recente. Proposta não será atualizada.")

            return revisao_id

        except Exception as e:
            logger.error(f"Erro ao inserir revisão: {e}")
            logger.exception("Stacktrace completo:")
            raise Exception(f"Erro ao inserir revisão: {str(e)}")

    @staticmethod
    def _salvar_arquivos(bt: str, rev: int, files: Dict[str, BytesIO]) -> Tuple[str, str]:
        """
        Save word and pdf files to disk.
        """
        base_path = Path("media/propostas")
        base_path.mkdir(parents=True, exist_ok=True)

        word_filename = f"proposta_{bt}_rev{rev}.docx"
        pdf_filename = f"proposta_{bt}_rev{rev}.pdf"
        
        word_path = f"propostas/{word_filename}"
        pdf_path = f"propostas/{pdf_filename}"

        full_word_path = base_path / word_filename
        full_pdf_path = base_path / pdf_filename

        try:
            if 'word' in files:
                full_word_path.write_bytes(files['word'].getvalue())

            if 'pdf' in files:
                full_pdf_path.write_bytes(files['pdf'].getvalue())

            return word_path, pdf_path
        except Exception as e:
            logger.error(f"Error saving files: {e}")
            raise