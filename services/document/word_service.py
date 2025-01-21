from docx import Document
from typing import Dict, List
from io import BytesIO
from services.document.word_tables import inserir_tabelas_word
import os

class WordDocumentService:
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
            '{{ICMS}}': f"{impostos.get('icms', 0):.1f}%",
            '{{IP}}': ', '.join(set(str(item['IP']) for item in itens_configurados 
                                  if item['IP'] != '00')),
            '{obra}': '' if not dados_iniciais.get('obra', '').strip() else 'Obra:'
        }

        buffer = BytesIO()
        doc = Document(template_path)
        doc = inserir_tabelas_word(doc, itens_configurados, '', replacements)
        doc.save(buffer)
        buffer.seek(0)
        return buffer