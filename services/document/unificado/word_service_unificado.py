from docx import Document
from typing import Dict, List
from io import BytesIO
import os
import logging
from .word_tables_unificado import create_custom_table, create_custom_table_escopo
from ..bt import pdf_service_bt
from ..mt import pdf_service_mt

logger = logging.getLogger(__name__)

def substituir_texto_documento(doc, replacements):
    """
    Substitui o texto no documento Word com base no dicionário de substituições
    """
    def remove_paragraph(paragraph):
        p = paragraph._element
        p.getparent().remove(p)
        paragraph._p = paragraph._element = None

    # Substituir texto em todos os parágrafos do documento
    for paragraph in doc.paragraphs:
        for old_text, new_text in replacements.items():
            if old_text in paragraph.text:
                if old_text == "{{IP}}" and not new_text.strip():
                    remove_paragraph(paragraph)
                    break
                else:
                    inline = paragraph.runs
                    for run in inline:
                        if old_text in run.text:
                            run.text = run.text.replace(old_text, new_text)

    # Substituir texto em todas as tabelas do documento
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for old_text, new_text in replacements.items():
                        if old_text in paragraph.text:
                            if old_text == "{{IP}}" and not new_text.strip():
                                remove_paragraph(paragraph)
                                break
                            else:
                                inline = paragraph.runs
                                for run in inline:
                                    if old_text in run.text:
                                        run.text = run.text.replace(old_text, new_text)

    # Substituir texto no cabeçalho de todas as seções
    for section in doc.sections:
        header = section.header
        for paragraph in header.paragraphs:
            for old_text, new_text in replacements.items():
                if old_text in paragraph.text:
                    if old_text == "{{IP}}" and not new_text.strip():
                        remove_paragraph(paragraph)
                        break
                    else:
                        inline = paragraph.runs
                        for run in inline:
                            if old_text in run.text:
                                run.text = run.text.replace(old_text, new_text)

def inserir_tabelas_word(doc, itens_mt, itens_bt, observacao, replacements):
    """
    Insere as tabelas no documento e realiza substituições de texto para documentos unificados
    """
    logger.info("Iniciando inserção de tabelas em documento unificado")
    
    try:
        # Substituir texto no documento
        substituir_texto_documento(doc, replacements)
        logger.debug("Texto substituído com sucesso")

        # Inserir tabela de preços após o título "Quadro de Preços"
        for i, paragraph in enumerate(doc.paragraphs):
            if "Quadro de Preços" in paragraph.text:
                logger.debug("Encontrado parágrafo 'Quadro de Preços'")
                table = create_custom_table(doc, itens_mt, itens_bt, observacao)
                doc.paragraphs[i+1]._element.addnext(table._element)
                break

        # Inserir tabela de escopo após o título "Escopo de Fornecimento"
        for i, paragraph in enumerate(doc.paragraphs):
            if "Escopo de Fornecimento" in paragraph.text:
                logger.debug("Encontrado parágrafo 'Escopo de Fornecimento'")
                table_escopo = create_custom_table_escopo(doc, itens_mt, itens_bt)
                doc.paragraphs[i+1]._element.addnext(table_escopo._element)
                break

        logger.info("Tabelas inseridas com sucesso")
        return doc

    except Exception as e:
        logger.error(f"Erro ao inserir tabelas: {str(e)}", exc_info=True)
        raise

# def get_template_file(sharepoint):
#     """
#     Obtém o arquivo de template unificado do SharePoint
#     """
#     logger.info("Obtendo arquivo de template unificado")
#     try:
#         local_template_path = "/tmp/Template_Proposta_Comercial_Unificado.docx"
#         if not os.path.exists(local_template_path):
#             template_name = os.getenv('TEMPLATE_UNIFICADO', 'Template_Proposta_Comercial_Unificado.docx')
#             local_template_path = sharepoint.download_file(template_name)
#             logger.debug(f"Template baixado para: {local_template_path}")
#         return local_template_path
#     except Exception as e:
#         logger.error(f"Erro ao obter template: {str(e)}", exc_info=True)
#         raise

def gerar_documento(template_path: str, dados_iniciais: Dict, 
                   impostos: Dict, itens_mt: List[Dict], itens_bt: List[Dict]) -> BytesIO:
    """
    Gera o documento Word unificado com os dados fornecidos
    """
    logger.info("Iniciando geração de documento unificado")
    try:
        # Preparar substituições de texto
        ips_mt = set(str(item['IP']) for item in itens_mt if item['IP'] != '00')
        ips_bt = set(str(item['IP']) for item in itens_bt if item['IP'] != '00')
        todos_ips = ips_mt.union(ips_bt)

        # Construir o dicionário de substituições
        replacements = {
            '{{CLIENTE}}': str(dados_iniciais.get('cliente', '')),
            '{{NOMECLIENTE}}': str(dados_iniciais.get('nomeCliente', '')),
            '{{FONE}}': str(dados_iniciais.get('fone', '')),
            '{{EMAIL}}': str(dados_iniciais.get('email', '')),
            '{{BT}}': str(dados_iniciais.get('bt', '')),
            '{{OBRA}}': str(dados_iniciais.get('obra', ' ')),
            '{{DIA}}': str(dados_iniciais.get('dia', '')),
            '{{MES}}': str(dados_iniciais.get('mes', '')),
            '{{ANO}}': str(dados_iniciais.get('ano', '')),
            '{{REV}}': str(dados_iniciais.get('rev', '')),
            '{{LOCAL}}': str(dados_iniciais.get('local_frete', '')),
            '{{LOCALFRETE}}': str(impostos.get('local_frete_itens', '')),
            '{{ICMS}}': f"{impostos.get('icms', 0):.1f}%",
            '{{IP}}': ', '.join(todos_ips) if todos_ips else '',
            '{obra}': '' if not dados_iniciais.get('obra', '').strip() else 'Obra:'
        }

        # Gerar documento
        buffer = BytesIO()
        doc = Document(template_path)
        doc = inserir_tabelas_word(doc, itens_mt, itens_bt, '', replacements)
        doc.save(buffer)
        buffer.seek(0)
        
        logger.info("Documento unificado gerado com sucesso")
        return buffer

    except Exception as e:
        logger.error(f"Erro ao gerar documento: {str(e)}", exc_info=True)
        raise

# def inserir_titulo_e_imagem(doc, itens_mt, itens_bt):
#     """
#     Insere títulos e imagens para ambos os tipos de produtos
#     """
#     logger.info("Iniciando inserção de títulos e imagens")
#     try:
#         # Encontrar o ponto de inserção
#         ponto_insercao = None
#         for i, paragraph in enumerate(doc.paragraphs):
#             if "A liberação da fabricação ocorrerá imediatamente após o recebimento do pedido de compra." in paragraph.text:
#                 ponto_insercao = paragraph
#                 break

#         if not ponto_insercao:
#             logger.error("Ponto de inserção não encontrado")
#             return doc

#         # Processa itens MT
#         if itens_mt:
#             from pdf_service_mt import inserir_titulo_e_imagem as inserir_mt
#             logger.debug("Processando imagens MT")
#             inserir_mt(doc, itens_mt)

#         # Processa itens BT
#         if itens_bt:
#             from bt.pdf_service_bt import verificar_produto_ip, inserir_titulo_e_imagem as inserir_bt
#             logger.debug("Processando imagens BT")
#             resultados_produtos = verificar_produto_ip(itens_bt)
#             inserir_bt(doc, resultados_produtos)

#         logger.info("Títulos e imagens inseridos com sucesso")
#         return doc

#     except Exception as e:
#         logger.error(f"Erro ao inserir títulos e imagens: {str(e)}", exc_info=True)
#         raise