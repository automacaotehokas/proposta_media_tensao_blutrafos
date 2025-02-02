from typing import Dict
import logging
import docx2pdf
import tempfile
from docx.shared import Pt,RGBColor
from docx import Document
import os
import dotenv
from shareplum import Site, Office365
from shareplum.site import Version
from dotenv import load_dotenv
import streamlit as st
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
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
        


def inserir_desvios(doc):
    """
    Insere os desvios no documento Word logo após o parágrafo que menciona alterações na proposta.
    Os desvios são formatados consistentemente com o resto do documento e inseridos em ordem.
    """
    # Procura o parágrafo de referência sobre alterações
    paragrafo_inicial = None
    texto_referencia = "repassadas de forma a objetivar o equilíbrio do contrato."
    
    for paragraph in doc.paragraphs:
        if texto_referencia in paragraph.text:
            paragrafo_inicial = paragraph
            break
    
    if not paragrafo_inicial:
        raise ValueError("Parágrafo de referência sobre alterações não encontrado no documento")

    # Começamos a inserir após o parágrafo de referência
    ultimo_paragrafo = paragrafo_inicial
    
    # Verifica se existem desvios para inserir
    if 'desvios' in st.session_state and st.session_state['desvios']:
        
        # Insere cada desvio como um item com bullet point
        for desvio in st.session_state['desvios']:
            p_desvio = doc.add_paragraph(style='Bullet')
            run_desvio = p_desvio.add_run(desvio['texto'])
            run_desvio.font.name = 'Calibri Light'
            run_desvio.font.size = Pt(11)
            ultimo_paragrafo._element.addnext(p_desvio._element)
            ultimo_paragrafo = p_desvio
        
        # Adiciona um espaço após a lista de desvios
        p_espaco = doc.add_paragraph()
        ultimo_paragrafo._element.addnext(p_espaco._element)

def inserir_prazo_entrega(doc):
    """
    Insere os prazos de entrega no documento Word abaixo do parágrafo inicial existente.
    A função localiza o parágrafo que contém o texto introdutório dos prazos e adiciona
    os novos prazos logo após ele.
    """
    # Procurar o parágrafo inicial que contém o texto sobre os prazos
    paragrafo_inicial = None
    for paragraph in doc.paragraphs:
        if "A partir destes eventos, consideramos os seguintes prazos:" in paragraph.text:
            paragrafo_inicial = paragraph
            break
    
    if not paragrafo_inicial:
        raise ValueError("Texto inicial dos prazos não encontrado no documento")

    # Começamos com o parágrafo inicial como nosso ponto de referência
    ultimo_paragrafo = paragrafo_inicial

    # Inserir prazo de desenho se existir
    if 'prazo_desenho' in st.session_state['prazo_entrega']:
        valor_desenho = st.session_state['prazo_entrega']['prazo_desenho']
        p_desenho = doc.add_paragraph(style='Bullet')
        texto_desenho = f"Desenhos para aprovação: Até {valor_desenho} dias úteis contados a partir da data de efetivação das etapas a e b, listadas acima."
        run_desenho = p_desenho.add_run(texto_desenho)
        run_desenho.font.name = 'Calibri Light'
        run_desenho.font.size = Pt(11)
        ultimo_paragrafo._element.addnext(p_desenho._element)
        ultimo_paragrafo = p_desenho

    # Inserir prazo de cliente se existir
    if 'prazo_cliente' in st.session_state['prazo_entrega']:
        valor_cliente = st.session_state['prazo_entrega']['prazo_cliente']
        p_cliente = doc.add_paragraph(style='Bullet')
        texto_cliente = f"Prazo para aprovação dos desenhos pelo cliente: Até {valor_cliente} dias úteis contados a partir da data de envio dos desenhos para aprovação. Se o tempo de aprovação for maior que informado, o prazo de entrega será obrigatoriamente renegociado"
        run_cliente = p_cliente.add_run(texto_cliente)
        run_cliente.font.name = 'Calibri Light'
        run_cliente.font.size = Pt(11)
        ultimo_paragrafo._element.addnext(p_cliente._element)
        ultimo_paragrafo = p_cliente

    prazo_entrega= st.session_state['prazo_entrega']
    # Inserir prazo MT se existir
    if 'prazo_mt' in prazo_entrega:
        try:
            dados = prazo_entrega['prazo_mt']
            valor = dados.get('valor')
            evento = dados.get('evento')
            if valor and evento:
                p_produto = doc.add_paragraph(style='Bullet')
                texto_produto = f"Transformador de Média Tensão a Seco: Até {valor} dias, contados a partir da data do evento de {evento}."
                run_produto = p_produto.add_run(texto_produto)
                run_produto.font.name = 'Calibri Light'
                run_produto.font.size = Pt(11)
                ultimo_paragrafo._element.addnext(p_produto._element)
                ultimo_paragrafo = p_produto
                logger.debug(f"Prazo MT inserido: {valor} dias, evento: {evento}")
        except Exception as e:
            logger.error(f"Erro ao inserir prazo MT: {str(e)}")

    # Inserir prazo BT se existir
    if 'prazo_bt' in prazo_entrega:
        try:
            dados = prazo_entrega['prazo_bt']
            valor = dados.get('valor')
            evento = dados.get('evento')
            if valor and evento:
                p_produto = doc.add_paragraph(style='Bullet')
                texto_produto = f"Transformador de Baixa Tensão: Até {valor} dias, contados a partir da data do evento de {evento}."
                run_produto = p_produto.add_run(texto_produto)
                run_produto.font.name = 'Calibri Light'
                run_produto.font.size = Pt(11)
                ultimo_paragrafo._element.addnext(p_produto._element)
                ultimo_paragrafo = p_produto
                logger.debug(f"Prazo BT inserido: {valor} dias, evento: {evento}")
        except Exception as e:
            logger.error(f"Erro ao inserir prazo BT: {str(e)}")
            
    # Adicionar espaço após todos os prazos
    p_espaco = doc.add_paragraph()
    ultimo_paragrafo._element.addnext(p_espaco._element)


def inserir_eventos_pagamento(doc, eventos_pagamento, produtos_configurados):
    logger.info("Iniciando inserção de texto de pagamento")
    
    # Encontrar o parágrafo "Condições de Pagamento"
    index = None
    for i, paragraph in enumerate(doc.paragraphs):
        if "Condições de Pagamento" in paragraph.text:
            index = i
            break
    
    if index is None:
        logger.error("Não foi encontrado o parágrafo 'Condições de Pagamento'")
        raise ValueError("Não foi encontrado o parágrafo 'Condições de Pagamento'")
    
    logger.info(f"Parágrafo 'Condições de Pagamento' encontrado no índice: {index}")
        # Adicionar um parágrafo vazio para criar espaço

    # Verificar quais tipos de transformadores existem
    tem_mt = produtos_configurados.get('mt', False)
    tem_bt = produtos_configurados.get('bt', False)
    logger.info(f"Transformadores encontrados - MT: {tem_mt}, BT: {tem_bt}")
    
    # Função auxiliar para criar título
    def criar_titulo(texto):
        logger.debug(f"Criando título: {texto}")
        p = doc.add_paragraph()
        run = p.add_run(f"{texto}:\n")
        run.bold = True
        run.font.size = Pt(12)
        run.font.name = 'Verdana'
        run.font.color.rgb = RGBColor(0, 84, 60)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(8)
        return p
    
    # Função auxiliar para processar eventos
    def processar_eventos(dados, index_atual):
        logger.info("Iniciando processamento de eventos")
        # Verificar se a_combinar está definido no nível do produto
        a_combinar_produto = False
        logger.info(f"A combinar: {a_combinar_produto}")
        
        if a_combinar_produto:
            logger.debug("Adicionando 'A combinar'")
            p_evento = doc.add_paragraph(style='Bullet')
            p_evento.add_run("A combinar")
            p_evento.alignment = WD_ALIGN_PARAGRAPH.LEFT
            doc.paragraphs[index_atual]._element.addnext(p_evento._element)
            return index_atual + 1
        else:
            eventos_ordenados = sorted(dados, key=lambda x: x['percentual'], reverse=True)
            logger.info(f"Número de eventos a processar: {len(eventos_ordenados)}")
            
            for evento in eventos_ordenados:
                percentual = int(evento['percentual'])
                dias = evento['dias']
                evento_texto = evento['evento']
                
                dias_texto = "com o(a)" if dias == 0 else f"{dias} Dias da"
                
                logger.debug(f"Adicionando evento: {percentual}% - {dias_texto} {evento_texto}")
                p_evento = doc.add_paragraph(style='Bullet')
                p_evento.add_run(f"{percentual}% - {dias_texto} {evento_texto}")
                p_evento.alignment = WD_ALIGN_PARAGRAPH.LEFT
                
                doc.paragraphs[index_atual]._element.addnext(p_evento._element)
                index_atual += 1
            return index_atual
    
    index_atual = index
    
    try:
        # Processar eventos de média tensão
        if tem_mt:
            logger.info("Processando eventos de média tensão")
            # Criar título MT
            p_mt = criar_titulo("Transformador de Média Tensão a Seco")
            doc.paragraphs[index_atual]._element.addnext(p_mt._element)
            index_atual += 1
            
            # Processar eventos MT
            index_atual = processar_eventos(eventos_pagamento['eventos_mt'], index_atual)
            logger.info("Eventos MT processados com sucesso")
            
            # Adicionar espaço entre MT e BT se necessário
            if tem_bt:
                logger.debug("Adicionando espaço entre MT e BT")
                doc.add_paragraph()
                index_atual += 1
        
        # Processar eventos de baixa tensão
        if tem_bt:
            logger.info("Processando eventos de baixa tensão")
            # Criar título BT
            p_bt = criar_titulo("Transformador de Baixa Tensão")
            doc.paragraphs[index_atual]._element.addnext(p_bt._element)
            index_atual += 1
            
            # Processar eventos BT
            index_atual = processar_eventos(eventos_pagamento['eventos_bt'], index_atual)
            logger.info("Eventos BT processados com sucesso")
        
        # Adicionar espaço após todos os eventos
        logger.debug("Adicionando espaços finais")
        doc.add_paragraph()
        doc.add_paragraph()
        
        logger.info("Inserção de texto de pagamento concluída com sucesso")
        
    except Exception as e:
        logger.error(f"Erro durante a inserção de texto de pagamento: {str(e)}", exc_info=True)
        raise

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
            



    @staticmethod
    def gerar_documentos(itens: Dict, observacao: str,):
        """
        Gera documentos baseado no tipo de produto (MT, BT ou unificado)
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
            
            # Define nome do arquivo de saída baseado nos tipos de produtos
            if tem_mt and tem_bt:
                output_filename = "proposta_unificada.docx"
            else:
                output_filename = f"proposta_{'mt' if tem_mt else 'bt'}.docx"
                
            output_path = os.path.join(output_dir, output_filename)
            
            try:
                # 5. Determinar serviços baseado no tipo de produto
                if tem_mt and tem_bt:
                    # Caso unificado
                    from services.document.unificado import word_tables_unificado
                    
                    # Separar itens MT e BT
                    itens_mt = itens.get('itens_configurados_mt', [])
                    itens_bt = itens.get('itens_configurados_bt', [])
                    
                    # Preparar dados iniciais
                    dados_iniciais = st.session_state['dados_iniciais']
                    impostos = st.session_state['impostos']
                    # Usar funções unificadas
                    logging.info("Iniciando processamento unificado...")
                    
                    # Gerar documento
                    buffer_documento = word_tables_unificado.gerar_documento(
                        template_path, 
                        dados_iniciais,
                        impostos,       
                        itens_mt, 
                        itens_bt)
                    
                    # Salvar o documento do buffer
                    with open(output_path, 'wb') as f:
                        f.write(buffer_documento.getvalue())
                    
                else:
                    # Casos individuais (MT ou BT)
                    if tem_mt:
                        pdf_service = pdf_service_mt
                        word_service = word_service_mt
                        items_key = 'itens_configurados_mt'
                    else:
                        pdf_service = pdf_service_bt
                        word_service = word_service_bt
                        items_key = 'itens_configurados_bt'
                    
                    doc = Document(template_path)
                    itens_configurados = itens.get(items_key, [])
                    
                    # Inserir tabelas
                    logging.info("Iniciando inserção de tabelas...")
                    word_service.inserir_tabelas_word(
                        doc,
                        itens_configurados=itens_configurados,
                        observacao=observacao
                    )

                    # Inserir eventos de pagamento, desvios e prazos
                    inserir_eventos_pagamento(doc, st.session_state, produtos_configurados)
                    inserir_desvios(doc)
                    inserir_prazo_entrega(doc)
                    
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
                
            except AttributeError as e:
                logging.error(f"Erro ao acessar função dos serviços: {str(e)}")
                raise Exception(f"Função necessária não encontrada: {str(e)}")
                
            except Exception as e:
                logging.error(f"Erro durante o processamento do documento: {str(e)}")
                raise
                
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