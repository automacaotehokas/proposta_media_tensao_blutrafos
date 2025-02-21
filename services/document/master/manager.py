from typing import Dict
import logging
import docx2pdf
import tempfile
from docx.shared import Pt,RGBColor,Inches
from docx import Document
import os
import dotenv
from shareplum import Site, Office365
from shareplum.site import Version
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

from services.sharepoint.sharepoint_service import SharePoint
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
    def __init__(self, itens: Dict = None):
        load_dotenv()
        self.USERNAME = os.getenv("SHAREPOINT_USER")
        self.PASSWORD = os.getenv("SHAREPOINT_PASSWORD")
        self.SHAREPOINT_URL = os.getenv("SHAREPOINT_URL")
        self.SHAREPOINT_SITE = os.getenv("SHAREPOINT_SITE")
        self.SHAREPOINT_DOC = os.getenv("SHAREPOINT_DOC_LIBRARY")
        
        # Determina qual pasta usar baseado nos produtos configurados
        self.FOLDER_NAME = self._get_folder_name(itens)


    def listar_arquivos(self):
        """
        Lista todos os arquivos na pasta do SharePoint
        """
        try:
            self._folder = self.connect_folder()
            arquivos = self._folder.files
            logging.info(f"Listando arquivos da pasta {self.FOLDER_NAME}:")
            for arquivo in arquivos:
                logging.info(f"- {arquivo['Name']}")
            return arquivos
        except Exception as e:
            logging.error(f"Erro ao listar arquivos: {str(e)}")
            return []

    def _get_folder_name(self, itens: Dict = None) -> str:
        """
        Determina qual pasta do SharePoint usar baseado nos produtos configurados
        """
        try:
            from pages.pagamento_entrega.components import ComponentsPagamentoEntrega
            
            # Se não houver itens, usa BT como padrão
            if not itens:
                logging.info("Sem itens configurados, usando pasta BT como padrão")
                return os.getenv("SHAREPOINT_FOLDER_NAME_BT")

            produtos_configurados = ComponentsPagamentoEntrega.carregar_tipo_produto(itens)
            tem_mt = produtos_configurados.get('mt', False)
            tem_bt = produtos_configurados.get('bt', False)

            # Primeiro verifica se tem os dois tipos de produto
            if tem_mt and tem_bt:
                logging.info("Detectados produtos MT e BT - usando pasta unificada")
                return os.getenv("SHAREPOINT_FOLDER_NAME_UNIFICADO")  # "08 - Propostas Automatizadas Transformadores"
            elif tem_mt:
                logging.info("Detectado apenas produto MT - usando pasta MT")
                return os.getenv("SHAREPOINT_FOLDER_NAME_MT")  # "04 - Propostas Automatizadas Média Tensão"
            elif tem_bt:
                logging.info("Detectado apenas produto BT - usando pasta BT")
                return os.getenv("SHAREPOINT_FOLDER_NAME_BT")  # "06 - Propostas Automatizadas BxBx"
            else:
                # Se não houver nenhum produto configurado, usa MT como fallback
                logging.warning("Nenhum produto MT ou BT detectado - usando pasta BT como fallback")
                return os.getenv("SHAREPOINT_FOLDER_NAME_MT")
                    
        except Exception as e:
            logging.error(f"Erro ao determinar pasta do SharePoint: {str(e)}")
            return os.getenv("SHAREPOINT_FOLDER_NAME_BT")


    def auth(self):
        """Autenticação no SharePoint"""
        self.authcookie = Office365(
            self.SHAREPOINT_URL, 
            username=self.USERNAME, 
            password=self.PASSWORD
        ).GetCookies()
        self.site = Site(
            self.SHAREPOINT_SITE, 
            version=Version.v365, 
            authcookie=self.authcookie
        )
        return self.site

    def connect_folder(self):
        """Conecta à pasta específica no SharePoint"""
        self.auth_site = self.auth()
        # Constrói o caminho completo para a pasta
        self.sharepoint_dir = f"{self.SHAREPOINT_DOC}/{self.FOLDER_NAME}"
        logging.info(f"Tentando acessar pasta: {self.sharepoint_dir}")
        
        try:
            # Tenta acessar a pasta existente
            self.folder = self.auth_site.Folder(self.sharepoint_dir)
            logging.info(f"Conectado com sucesso à pasta: {self.sharepoint_dir}")
            return self.folder
        except Exception as e:
            logging.error(f"Erro ao conectar à pasta {self.sharepoint_dir}: {str(e)}")
            raise Exception(f"Pasta {self.FOLDER_NAME} não encontrada no SharePoint")

    def download_file(self, file_name):
        """
        Baixa um arquivo do SharePoint
        
        Args:
            file_name (str): Nome do arquivo para baixar
            
        Returns:
            str: Caminho do arquivo baixado
        """
        logging.info(f"Tentando baixar arquivo: {file_name}")
        logging.info(f"Da pasta: {self.FOLDER_NAME}")
        
        try:
            self._folder = self.connect_folder()
            file = self._folder.get_file(file_name)
            
            temp_path = os.path.join(tempfile.gettempdir(), file_name)
            
            with open(temp_path, 'wb') as f:
                f.write(file)
                
            logging.info(f"Arquivo baixado com sucesso para: {temp_path}")
            return temp_path
            
        except Exception as e:
            logging.error(f"Erro ao baixar arquivo {file_name}: {str(e)}")
            raise Exception(f"Não foi possível baixar o arquivo {file_name} da pasta {self.FOLDER_NAME}")
        


from docx.shared import Pt, Inches

from docx.shared import Pt, Inches


    

    # Adicionar espaço após todos os prazos
    






class DocumentManager:
    @staticmethod
    def get_template_file(itens: Dict = None):
        """
        Seleciona e obtém o template apropriado baseado nos tipos de produtos configurados
        """
        try:
            # Verifica quais produtos estão configurados
            produtos_configurados = ComponentsPagamentoEntrega.carregar_tipo_produto(itens or {})
            
            # Instancia o SharePoint e lista os arquivos disponíveis
            sp = SharePoint(itens)
            arquivos_disponiveis = sp.listar_arquivos()
            
            # Define o nome do template baseado no tipo de produto
            tem_mt = produtos_configurados.get('mt', False)
            tem_bt = produtos_configurados.get('bt', False)
            
            # Determina qual template usar baseado na combinação de produtos
            if tem_mt and tem_bt:
                # Caso para ambos MT e BT - usa template unificado
                template_name = os.getenv('TEMPLATE_UNIFICADO')  # 'template_unificado_trafo.docx'
                logging.info("Detectados produtos MT e BT - usando template unificado")
            elif tem_mt:
                # Caso apenas MT
                template_name = os.getenv('TEMPLATE_MT')  # 'Template_Proposta_Comercial.docx'
                logging.info("Detectado apenas produto MT")
            else:
                # Caso apenas BT
                template_name = os.getenv('TEMPLATE_BT')  # 'template_baixa_tensao.docx'
                logging.info("Detectado apenas produto BT")
            
            local_template_path = f"/tmp/{template_name}"
            logging.info(f"Procurando template: {template_name}")
            
            # Se o arquivo não existe localmente, faz o download
            if not os.path.exists(local_template_path):
                try:
                    local_template_path = sp.download_file(template_name)
                except Exception as e:
                    logging.error(f"Arquivo {template_name} não encontrado. Arquivos disponíveis na pasta:")
                    for arquivo in arquivos_disponiveis:
                        logging.info(f"- {arquivo['Name']}")
                    raise Exception(f"Template {template_name} não encontrado na pasta {sp.FOLDER_NAME}")
            
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
                'template':os.getenv('TEMPLATE_MT')
            }
        else:
            return {
                'pdf_service': pdf_service_bt,
                'word_service': word_service_bt,
                'word_formatter': word_formatter_bt,
                'word_table': word_tables_bt,
                'template':os.getenv('TEMPLATE_BT')
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
            
    # @staticmethod
    # def gerar_pdf(doc_path: str) -> str:
    #     """
    #     Converte o documento Word em PDF
    #     """
    #     try:
    #         from docx2pdf import convert
    #         pdf_path = doc_path.replace('.docx', '.pdf')
    #         convert(doc_path, pdf_path)
    #         logging.info(f"PDF gerado com sucesso: {pdf_path}")
    #         return pdf_path
    #     except Exception as e:
    #         logging.error(f"Erro ao gerar PDF: {str(e)}")
    #         raise Exception(f"Erro ao gerar PDF: {str(e)}")