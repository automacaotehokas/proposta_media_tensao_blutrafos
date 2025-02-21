from docx import Document
from typing import Dict, List
from io import BytesIO
from .word_tables_mt import inserir_tabelas_word, substituir_texto_documento
from .test import formatar_numero_inteiro_ou_decimal
import os
import streamlit as st


@staticmethod
def get_template_file(sharepoint):
    """Obtém o arquivo de template do SharePoint"""
    local_template_path = "/tmp/Template_Proposta_Comercial.docx"
    if not os.path.exists(local_template_path):
        template_name = 'Template_Proposta_Comercial.docx'
        local_template_path = sharepoint.download_file(template_name)
    return local_template_path


@staticmethod
def gerar_documento(template_path: str, dados_iniciais: Dict, 
                   impostos: Dict, itens_configurados: List[Dict]) -> BytesIO:
    """Gera o documento Word com os dados fornecidos"""
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
        '{{ICMS}}': f"{formatar_numero_inteiro_ou_decimal(impostos.get('icms', 0))}%",
        '{{IP}}': ', '.join(set(str(item['IP']) for item in itens_configurados 
                              if item['IP'] != '00')),
        '{{DIFAL}}': f"{formatar_numero_inteiro_ou_decimal(impostos.get('difal', 0))}" if impostos.get('difal', 0) > 0 else '',
        '{obra}': '' if not dados_iniciais.get('obra', '').strip() else 'Obra:',
        '{{RESPONSAVEL}}': st.session_state.get('usuario', ''),
        '{{GARANTIA}}': '12',
        '{{VALIDADE}}': '07',
        
    }

    buffer = BytesIO()
    doc = Document(template_path)
    doc = inserir_tabelas_word(doc, itens_configurados, '', replacements)
    doc = substituir_texto_documento(doc, replacements)
    doc.save(buffer)
    buffer.seek(0)
    return buffer