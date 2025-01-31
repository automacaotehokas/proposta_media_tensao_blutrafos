from docx import Document  # Importação específica
from typing import Dict, List, Optional
import logging
from io import BytesIO
# Importações de serviços
from services.document.mt import word_tables_mt
from services.document.bt import word_tables_bt
from services.document.mt.word_tables_mt import substituir_texto_documento
logger = logging.getLogger(__name__)

def inserir_tabelas_separadas(
    doc: Document, 
    itens_mt: Optional[List[Dict]] = None, 
    itens_bt: Optional[List[Dict]] = None, 
    observacao: str = "",
    replacements: Optional[Dict] = None
) -> Document:
    """
    Insere tabelas de MT e BT separadamente no documento Word
    """
    # Validar e preparar argumentos
    itens_mt = itens_mt or []
    itens_bt = itens_bt or []
    replacements = replacements or {}
    
    # Validar entrada
    if not itens_mt and not itens_bt:
        logger.warning("Nenhum item de MT ou BT fornecido. Nenhuma tabela será inserida.")
        return doc

    # Tabela de preços MT
    if itens_mt:
        logger.info(f"Processando itens MT: {len(itens_mt)} itens")
        
        # Localizar o parágrafo marcador de forma mais flexível
        paragrafos_encontrados = [p for p in doc.paragraphs if "QUADRO_PRECOS_MT" in str(p.text)]
        logger.info(f"Parágrafos encontrados para MT: {len(paragrafos_encontrados)}")
        
        if paragrafos_encontrados:
            paragraph = paragrafos_encontrados[0]
            
            try:
                # Criar tabela de MT
                result = word_tables_mt.inserir_tabelas_word(
                    doc,
                    itens_configurados=itens_mt,
                    observacao="",
                    replacements=replacements
                )
                
                # Neste caso, result é o próprio documento
                logger.info("Tabela MT inserida com sucesso")
            
            except Exception as e:
                logger.error(f"Erro ao criar tabela MT: {str(e)}", exc_info=True)

    # Tabela de preços BT
    if itens_bt:
        logger.info(f"Processando itens BT: {len(itens_bt)} itens")
        
        paragrafos_encontrados = [p for p in doc.paragraphs if "QUADRO_PRECOS_BT" in str(p.text)]
        logger.info(f"Parágrafos encontrados para BT: {len(paragrafos_encontrados)}")
        
        if paragrafos_encontrados:
            try:
                # Criar tabela de BT
                result = word_tables_bt.create_custom_table(
                    doc,
                    itens_configurados=itens_bt,
                    observacao=""
                )
                replacements=replacements
                # Neste caso, result é uma tabela
                logger.info("Tabela BT inserida com sucesso")
            
            except Exception as e:
                logger.error(f"Erro ao criar tabela BT: {str(e)}", exc_info=True)

    return doc
    # Tabela de escopo
    # if itens_mt or itens_bt:
    #     from services.document.mt import word_tables_mt
    #     for i, paragraph in enumerate(doc.paragraphs):
    #         if "Escopo de Fornecimento" in paragraph.text:
    #             logger.info("Inserindo tabela de escopo unificada")
                
    #             # Usar função de escopo MT (assumindo que é a mesma para MT e BT)
    #             tabela_escopo = word_tables_mt.create_custom_table_escopo(
    #                 doc, 
    #                 itens_mt + itens_bt
    #             )
    #             doc.paragraphs[i+1]._element.addnext(tabela_escopo._element)
    #             break

    


logger = logging.getLogger(__name__)


def substituir_texto_documento_1(doc, replacements):
    """
    Substitui texto no documento Word mantendo sua estrutura original.
    
    Args:
        doc: Documento Word (objeto Document)
        replacements: Dicionário com as substituições a serem feitas
        
    Returns:
        Document: Documento Word com as substituições realizadas
    """
    if not doc:
        raise ValueError("Documento não pode ser None")
        
    logger.info("Iniciando substituições com: %s", replacements)
    
    # Função auxiliar para substituir texto em um parágrafo
    def substituir_em_paragrafo(paragraph):
        # Obtém todo o texto do parágrafo
        texto_completo = ''.join(run.text for run in paragraph.runs)
        texto_modificado = texto_completo
        
        # Realiza todas as substituições necessárias
        for old_text, new_text in replacements.items():
            if old_text in texto_completo:
                texto_modificado = texto_modificado.replace(old_text, str(new_text))
                logger.info(f"Substituindo '{old_text}' por '{new_text}'")
                logger.info(f"Texto antes: {texto_completo}")
                logger.info(f"Texto depois: {texto_modificado}")
        
        # Se houve alteração, atualiza o texto no documento
        if texto_modificado != texto_completo:
            # Limpa todos os runs
            for run in paragraph.runs:
                run.text = ""
            # Coloca todo o texto modificado
            paragraph.add_run(texto_modificado)
    
    # Processa cada tipo de conteúdo do documento
    # 1. Corpo do documento
    logger.info("Processando corpo do documento")
    for paragraph in doc.paragraphs:
        substituir_em_paragrafo(paragraph)
    
    # 2. Cabeçalhos e rodapés
    logger.info("Processando cabeçalhos e rodapés")
    for section in doc.sections:
        # Cabeçalho
        header = section.header
        for paragraph in header.paragraphs:
            substituir_em_paragrafo(paragraph)
        
        # Rodapé
        footer = section.footer
        for paragraph in footer.paragraphs:
            substituir_em_paragrafo(paragraph)
    
    # 3. Tabelas
    logger.info("Processando tabelas")
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    substituir_em_paragrafo(paragraph)
    
    # Verifica o resultado final
    logger.info("Verificando resultado final")
    for paragraph in doc.paragraphs:
        logger.info(f"Parágrafo após substituições: {paragraph.text}")
    
    # Verifica também os cabeçalhos, rodapés e tabelas
    for section in doc.sections:
        for paragraph in section.header.paragraphs:
            logger.info(f"Cabeçalho após substituições: {paragraph.text}")
        for paragraph in section.footer.paragraphs:
            logger.info(f"Rodapé após substituições: {paragraph.text}")
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    logger.info(f"Célula após substituições: {paragraph.text}")
    
    return doc
                            
def gerar_documento(template_path, dados_iniciais, impostos, itens_mt, itens_bt):
    logger.info("Iniciando geração de documento unificado")
    
    doc = Document(template_path)
    if not doc:
        raise ValueError("Falha ao carregar template")

    # Criar replacements
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
        '{{LOCALFRETE}}': str(impostos.get('local_entrega', '')),
        '{{ICMS}}': f"{impostos.get('icms', 0):.1f}",
        '{{IP}}': '',  # Será preenchido depois com valores de MT e BT
        '{obra}': '' if not dados_iniciais.get('obra', '').strip() else 'Obra',
        ##################################### novas variaveis
        '{{VALOR_TOTAL}}': f"{impostos.get('valor_total', 0):.2f}", ######### criar uma função para obter o valor total de tudo, ja tenho na HOME.PY
        '{{TRANSPORTE}}': 'O transporte de equipamentos será realizado no formato CIF.' if impostos.get('tipo_frete', '') == 'CIF' else 'O transporte de equipamentos será realizado no formato FOB.'
    }

    logger.info("Aplicando substituições de texto")
    doc = substituir_texto_documento(doc, replacements)
    logger.info(f"Após substituições. Primeiro parágrafo: {doc.paragraphs[0].text if doc.paragraphs else 'Vazio'}")
    logger.info("Inserindo tabelas")
    doc = inserir_tabelas_separadas(doc, itens_mt, itens_bt, "", replacements)
    logger.info(f"Após tabelas. Primeiro parágrafo: {doc.paragraphs[0].text if doc.paragraphs else 'Vazio'}")
    buffer = BytesIO()
    doc.save(buffer)
    logger.info("Verificando conteúdo do buffer antes de retornar")
    buffer.seek(0)
    doc_final = Document(BytesIO(buffer.getvalue()))
    logger.info(f"Documento final. Primeiro parágrafo: {doc_final.paragraphs[0].text if doc_final.paragraphs else 'Vazio'}")
    return buffer
