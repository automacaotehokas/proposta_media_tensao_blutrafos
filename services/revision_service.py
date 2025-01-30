import json
import os
import logging
import sys
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from config.databaseMT import DatabaseConfig
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder


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
    def _inserir_revisao(
        dados: Dict[str, Any],
        id_proposta: str,
        valor: float,
        numero_revisao: int,
        word_path: BytesIO,  
        pdf_path: BytesIO,   
        escopo: str
    ) -> Optional[str]:
        """
        Insere uma nova revisão através da API.
        """
        logger.info(f"""
        Iniciando inserção de revisão via API:
        - ID Proposta: {id_proposta}
        - Valor: {valor}
        - Número Revisão: {numero_revisao}
        - Escopo: {escopo}
        """)

        try:
            # Preparar os dados do formulário
            form_data = {
                'id_proposta': id_proposta,
                'revisao': str(numero_revisao),
                'valor': str(valor),
                'escopo': escopo,
                'tipo': dados.get('tipo', ''),
                'conteudo': json.dumps(dados, default=lambda x: float(x) if isinstance(x, Decimal) else x)
            }

            # Log dos dados antes de enviar
            logger.info(f"Dados do formulário: {form_data}")

            # Adicionar arquivo do buffer
            form_data['arquivo'] = ('proposta.docx', word_path, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')

            # Criar MultipartEncoder para enviar arquivos
            multipart_data = MultipartEncoder(fields=form_data)
            
            # Configurar headers
            headers = {
                'Content-Type': multipart_data.content_type,
                'Accept': 'application/json',
                'Authorization': f'Bearer {dados.get("token")}'  # Mudando de Token para Bearer
            }
            
            logger.info(f"Headers da requisição: {headers}")
            
            # Fazer a requisição POST
            response = requests.post(
                'http://localhost:8000/api/streamlit/inserir_revisao/',
                data=multipart_data,
                headers=headers
            )
            
            logger.info(f"Status code da resposta: {response.status_code}")
            logger.info(f"Headers da resposta: {response.headers}")
            logger.info(f"Conteúdo da resposta: {response.text}")
            
            # Verificar se a requisição foi bem sucedida
            response.raise_for_status()
            
            result = response.json()
            
            if not result.get('success'):
                raise Exception(result.get('error', 'Erro desconhecido ao criar revisão'))
            
            logger.info(f"Revisão criada com sucesso via API: {result}")
            return result.get('revisao', {}).get('id')
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao criar revisão via API: {str(e)}")
            raise Exception(f"Erro ao criar revisão via API: {str(e)}")
        except Exception as e:
            logger.error(f"Erro inesperado ao criar revisão: {str(e)}")
            raise Exception(f"Erro inesperado ao criar revisão: {str(e)}")

    @staticmethod
    def _atualizar_revisao(
        dados: Dict[str, Any],
        valor: float,
        numero_revisao: int,
        word_path: BytesIO,  
        pdf_path: BytesIO,   
        escopo: str,
        revisao_id: str
    ) -> str:
        """
        Atualiza uma revisão existente através da API.
        """
        logger.info(f"""
        Iniciando atualização de revisão via API:
        - ID Revisão: {revisao_id}
        - Valor: {valor}
        - Número Revisão: {numero_revisao}
        - Escopo: {escopo}
        """)

        try:
            # Preparar os dados do formulário
            form_data = {
                'revisao_id': revisao_id,
                'valor': str(valor),
                'escopo': escopo,
                'tipo': dados.get('tipo', ''),
                'conteudo': json.dumps(dados, default=lambda x: float(x) if isinstance(x, Decimal) else x)
            }

            # Adicionar arquivo do buffer
            form_data['arquivo'] = ('proposta.docx', word_path, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')

            # Criar MultipartEncoder para enviar arquivos
            multipart_data = MultipartEncoder(fields=form_data)
            
            # Configurar headers
            headers = {
                'Content-Type': multipart_data.content_type,
                'Authorization': f'Bearer {dados.get("token")}'  # Mudando de Token para Bearer
            }
            
            # Fazer a requisição POST
            response = requests.post(
                'http://localhost:8000/api/streamlit/atualizar_revisao/',
                data=multipart_data,
                headers=headers
            )
            
            # Verificar se a requisição foi bem sucedida
            response.raise_for_status()
            
            result = response.json()
            
            if not result.get('success'):
                raise Exception(result.get('error', 'Erro desconhecido ao atualizar revisão'))
            
            logger.info(f"Revisão atualizada com sucesso via API: {result}")
            return revisao_id
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao atualizar revisão via API: {str(e)}")
            raise Exception(f"Erro ao atualizar revisão via API: {str(e)}")
        except Exception as e:
            logger.error(f"Erro inesperado ao atualizar revisão: {str(e)}")
            raise Exception(f"Erro inesperado ao atualizar revisão: {str(e)}")

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