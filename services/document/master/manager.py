from typing import Dict
import logging
import docx2pdf
import tempfile
from docx.shared import Pt, RGBColor, Inches
from docx import Document
import os
import dotenv
from dotenv import load_dotenv
import streamlit as st
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from ..utils import document_functions
from ..unificado import word_tables_unificado

# Importações dos serviços MT
from services.document.mt import (
    pdf_service_mt,
    word_service_mt,
    word_formatter_mt,
    word_tables_mt
)

from services.document.bt import (
    pdf_service_bt,
    word_service_bt,
    word_formatter_bt,
    word_tables_bt
)

from pages.pagamento_entrega.components import ComponentsPagamentoEntrega
import tempfile

from pages.pagamento_entrega.components import ComponentsPagamentoEntrega
import logging

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)
dotenv.load_dotenv()


class SharePoint:
    """
    Classe mantida para compatibilidade, mas agora usa templates locais
    """
    def __init__(self, itens: Dict = None):
        load_dotenv()
        # Mantém as variáveis de ambiente mas não as usa mais
        self.USERNAME = os.getenv("SHAREPOINT_USER")
        self.PASSWORD = os.getenv("SHAREPOINT_PASSWORD")
        self.SHAREPOINT_URL = os.getenv("SHAREPOINT_URL")
        self.SHAREPOINT_SITE = os.getenv("SHAREPOINT_SITE")
        self.SHAREPOINT_DOC = os.getenv("SHAREPOINT_DOC_LIBRARY")
        
        # Determina qual pasta usar baseado nos produtos configurados
        self.FOLDER_NAME = self._get_folder_name(itens)
        
        # Define o diretório base dos templates
        self.TEMPLATES_DIR = os.path.join(os.getcwd(), "output", "templates")
        os.makedirs(self.TEMPLATES_DIR, exist_ok=True)

    def listar_arquivos(self):
        """
        Lista todos os arquivos na pasta local de templates
        """
        try:
            arquivos = []
            if os.path.exists(self.TEMPLATES_DIR):
                for filename in os.listdir(self.TEMPLATES_DIR):
                    if filename.endswith('.docx'):
                        arquivos.append({'Name': filename})
                        
            logging.info(f"Listando arquivos da pasta local {self.TEMPLATES_DIR}:")
            for arquivo in arquivos:
                logging.info(f"- {arquivo['Name']}")
            return arquivos
        except Exception as e:
            logging.error(f"Erro ao listar arquivos: {str(e)}")
            return []

    def _get_folder_name(self, itens: Dict = None) -> str:
        """
        Determina qual tipo de template usar baseado nos produtos configurados
        """
        try:
            from pages.pagamento_entrega.components import ComponentsPagamentoEntrega
            
            # Se não houver itens, usa BT como padrão
            if not itens:
                logging.info("Sem itens configurados, usando template BT como padrão")
                return "BT"

            produtos_configurados = ComponentsPagamentoEntrega.carregar_tipo_produto(itens)
            tem_mt = produtos_configurados.get('mt', False)
            tem_bt = produtos_configurados.get('bt', False)

            # Verifica se tem os dois tipos de produto
            if tem_mt and tem_bt:
                logging.info("Detectados produtos MT e BT - usando template unificado")
                return "UNIFICADO"
            elif tem_mt:
                logging.info("Detectado apenas produto MT - usando template MT")
                return "MT"
            elif tem_bt:
                logging.info("Detectado apenas produto BT - usando template BT")
                return "BT"
            else:
                logging.warning("Nenhum produto MT ou BT detectado - usando template BT como fallback")
                return "BT"
                    
        except Exception as e:
            logging.error(f"Erro ao determinar tipo de template: {str(e)}")
            return "BT"

    def auth(self):
        """Método mantido para compatibilidade - não faz nada"""
        logging.info("Método auth() chamado - usando templates locais")
        return None

    def connect_folder(self):
        """Método mantido para compatibilidade - não faz nada"""
        logging.info(f"Método connect_folder() chamado - usando pasta local: {self.TEMPLATES_DIR}")
        return None

    def download_file(self, file_name):
        """
        'Baixa' (copia) um arquivo da pasta local de templates
        
        Args:
            file_name (str): Nome do arquivo para copiar
            
        Returns:
            str: Caminho do arquivo local
        """
        logging.info(f"Buscando arquivo local: {file_name}")
        logging.info(f"Na pasta: {self.TEMPLATES_DIR}")
        
        try:
            local_path = os.path.join(self.TEMPLATES_DIR, file_name)
            
            if not os.path.exists(local_path):
                raise FileNotFoundError(f"Arquivo {file_name} não encontrado em {self.TEMPLATES_DIR}")
            
            # Cria uma cópia temporária para manter compatibilidade
            temp_path = os.path.join(tempfile.gettempdir(), file_name)
            
            with open(local_path, 'rb') as source:
                with open(temp_path, 'wb') as dest:
                    dest.write(source.read())
                    
            logging.info(f"Arquivo copiado com sucesso para: {temp_path}")
            return temp_path
            
        except Exception as e:
            logging.error(f"Erro ao acessar arquivo {file_name}: {str(e)}")
            raise Exception(f"Não foi possível acessar o arquivo {file_name} em {self.TEMPLATES_DIR}")


class DocumentManager:
    @staticmethod
    def get_template_file(itens: Dict = None):
        """
        Seleciona e obtém o template apropriado baseado nos tipos de produtos configurados
        """
        try:
            # Verifica quais produtos estão configurados
            produtos_configurados = ComponentsPagamentoEntrega.carregar_tipo_produto(itens or {})
            
            # Instancia o SharePoint (que agora usa arquivos locais)
            sp = SharePoint(itens)
            arquivos_disponiveis = sp.listar_arquivos()
            
            # Define o nome do template baseado no tipo de produto
            tem_mt = produtos_configurados.get('mt', False)
            tem_bt = produtos_configurados.get('bt', False)
            
            # Determina qual template usar baseado na combinação de produtos
            if tem_mt and tem_bt:
                template_name = os.getenv('TEMPLATE_UNIFICADO', 'template_unificado_trafo.docx')
                logging.info("Detectados produtos MT e BT - usando template unificado")
            elif tem_mt:
                template_name = os.getenv('TEMPLATE_MT', 'Template_Proposta_Comercial.docx')
                logging.info("Detectado apenas produto MT")
            else:
                template_name = os.getenv('TEMPLATE_BT', 'template_baixa_tensao.docx')
                logging.info("Detectado apenas produto BT")
            
            # Caminho direto para o template local
            local_template_path = os.path.join(sp.TEMPLATES_DIR, template_name)
            logging.info(f"Procurando template: {local_template_path}")
            
            # Verifica se o arquivo existe
            if not os.path.exists(local_template_path):
                logging.error(f"Template {template_name} não encontrado. Templates disponíveis:")
                for arquivo in arquivos_disponiveis:
                    logging.info(f"- {arquivo['Name']}")
                raise FileNotFoundError(
                    f"Template {template_name} não encontrado em {sp.TEMPLATES_DIR}. "
                    f"Por favor, certifique-se de que o arquivo existe nesta pasta."
                )
            
            return local_template_path
        
        except Exception as e:
            logging.error(f"Erro ao obter template: {str(e)}")
            raise

    @staticmethod
    def get_document_services(produtos_configurados: Dict):
        """
        Retorna os serviços apropriados baseado nos produtos configurados
        """
        if produtos_configurados['mt']:
            return {
                'pdf_service': pdf_service_mt,
                'word_service': word_service_mt,
                'word_formatter': word_formatter_mt,
                'word_table': word_tables_mt,
                'template': os.getenv('TEMPLATE_MT', 'Template_Proposta_Comercial.docx')
            }
        else:
            return {
                'pdf_service': pdf_service_bt,
                'word_service': word_service_bt,
                'word_formatter': word_formatter_bt,
                'word_table': word_tables_bt,
                'template': os.getenv('TEMPLATE_BT', 'template_baixa_tensao.docx')
            }

    def gerar_documentos(itens: Dict, observacao: str):
        """
        Gera documentos baseado no tipo de produto (MT, BT ou unificado)
        
        Args:
            itens: Dicionário contendo configurações dos itens
            observacao: String com observações a serem incluídas
        """
        try:
            # 1. Identificar tipos de produtos
            produtos_configurados = ComponentsPagamentoEntrega.carregar_tipo_produto(itens)
            tem_mt = produtos_configurados.get('mt', False)
            tem_bt = produtos_configurados.get('bt', False)
            logging.info(f"Tipos de produtos identificados - MT: {tem_mt}, BT: {tem_bt}")
            
            # 2. Obter template correto
            template_path = DocumentManager.get_template_file(itens)
            logging.info(f"Template carregado: {template_path}")
            
            # 3. Preparar diretório de saída
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            
            # 4. Definir nome do arquivo baseado nos tipos de produtos
            if tem_mt and tem_bt:
                output_filename = "proposta_unificada.docx"
            else:
                output_filename = f"proposta_{'mt' if tem_mt else 'bt'}.docx"
                
            output_path = os.path.join(output_dir, output_filename)
            
            # 5. Processar o documento
            if tem_mt and tem_bt:
                # Separar itens MT e BT
                itens_mt = itens.get('itens_configurados_mt', [])
                itens_bt = itens.get('itens_configurados_bt', [])
                
                # Preparar dados iniciais
                dados_iniciais = st.session_state['dados_iniciais']
                impostos = st.session_state['impostos']
                
                # Gerar documento unificado
                logging.info("Iniciando processamento unificado...")
                buffer_documento = word_tables_unificado.gerar_documento(
                    template_path, 
                    dados_iniciais,
                    impostos,       
                    itens_mt, 
                    itens_bt
                )
                
                # Salvar o documento do buffer
                with open(output_path, 'wb') as f:
                    f.write(buffer_documento.getvalue())
                
            else:
                # Configurar serviços baseado no tipo de produto
                if tem_mt:
                    pdf_service = pdf_service_mt
                    word_service = word_service_mt
                    items_key = 'itens_configurados_mt'
                else:
                    pdf_service = pdf_service_bt
                    word_service = word_service_bt
                    items_key = 'itens_configurados_bt'
                
                # Criar documento
                try:
                    doc = Document(template_path)
                except Exception as e:
                    raise ValueError(f"Falha ao carregar template: {str(e)}")
                
                itens_configurados = itens.get(items_key, [])
                
                # Inserir tabelas
                logging.info("Iniciando inserção de tabelas...")
                word_service.inserir_tabelas_word(
                    doc,
                    itens_configurados=itens_configurados,
                    observacao=observacao
                )

                # Processar eventos de pagamento
                eventos_pagamento = []
                if 'eventos_pagamento' in st.session_state:
                    eventos_temp = st.session_state.eventos_pagamento
                    if isinstance(eventos_temp, list):
                        eventos_pagamento = eventos_temp
                    elif hasattr(eventos_temp, '__iter__'):
                        eventos_pagamento = list(eventos_temp)

                # Validar e processar eventos de pagamento
                eventos_validados = []
                for evento in eventos_pagamento:
                    if isinstance(evento, dict) and all(key in evento for key in ['percentual', 'dias', 'evento']):
                        evento_processado = {
                            'percentual': float(str(evento['percentual']).replace(',', '.')),
                            'dias': str(evento['dias']),
                            'evento': str(evento['evento'])
                        }
                        eventos_validados.append(evento_processado)
                
                logging.info(f"Processando {len(eventos_validados)} eventos de pagamento")
                document_functions.inserir_eventos_pagamento(doc, eventos_validados, produtos_configurados)
                
                # Inserir informações adicionais
                document_functions.inserir_desvios(doc)
                document_functions.inserir_prazo_entrega(doc)
                
                # Processar imagens específicas
                if tem_mt:
                    if hasattr(pdf_service_mt, 'inserir_titulo_e_imagem'):
                        pdf_service_mt.inserir_titulo_e_imagem(doc, itens_configurados)
                else:
                    resultados_produtos = pdf_service_bt.verificar_produto_ip(itens_configurados)
                    if hasattr(pdf_service_bt, 'inserir_titulo_e_imagem'):
                        pdf_service_bt.inserir_titulo_e_imagem(doc, resultados_produtos)
                
                # Salvar documento
                doc.save(output_path)
            
            logging.info(f"Documento gerado com sucesso: {output_path}")
            return output_path
            
        except Exception as e:
            logging.error(f"Erro ao gerar documentos: {str(e)}")
            raise Exception(f"Erro ao gerar documentos: {str(e)}")