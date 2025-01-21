import streamlit as st
from services.document.word_service import WordDocumentService
from services.document.pdf_service import PDFDocumentService
from services.revision_service import RevisionService
from .components import (
    render_dados_iniciais, render_variaveis, 
    render_itens_configurados, render_botoes_download
)

from config.database import DatabaseConfig
from services.sharepoint.sharepoint_service import SharePoint

def verificar_dados_completos():
    """Verifica se todos os dados necessários estão preenchidos"""
    dados_iniciais = st.session_state.get('dados_iniciais', {})
    itens_configurados = st.session_state.get('itens_configurados', [])

    campos_obrigatorios = [
        'cliente', 'nomeCliente', 'fone', 'email', 'bt', 
        'dia', 'mes', 'ano', 'rev', 'local_frete'
    ]

    return all(dados_iniciais.get(campo) for campo in campos_obrigatorios) and itens_configurados

def pagina_resumo():
    """Renderiza a página de resumo"""
    st.title("Resumo")
    st.markdown("---")

    if 'dados_iniciais' not in st.session_state:
        st.error("Por favor, preencha os dados iniciais antes de gerar o documento.")
        return

    # Renderiza as seções da página
    render_dados_iniciais(st.session_state['dados_iniciais'])
    st.markdown("---")


    
    render_variaveis(st.session_state['impostos'], 
                    st.session_state['itens_configurados'])
    st.markdown("---")

    # Adicionar campo de comentários
    st.markdown("### Comentários da Revisão")
    if 'dados_iniciais' in st.session_state:
        st.session_state['dados_iniciais']['comentario'] = st.text_area(
            "Insira um comentário para esta revisão:",
            value=st.session_state['dados_iniciais'].get('comentario', ''),
            key='comentario_revisao'
        )
    
    render_itens_configurados(st.session_state.get('resumo_df'))

    # Botão de confirmação
    dados_completos = verificar_dados_completos()
    st.write("O botão abaixo estará disponível após o preenchimento de todos os dados")

    if st.button('Confirmar', disabled=not dados_completos, key='btn_salvar'):
        try:
            if dados_completos:
                # Gerar documentos
                sharepoint = SharePoint()
                template_path = WordDocumentService.get_template_file(sharepoint)
                
                # Documento Word
                buffer_word = WordDocumentService.gerar_documento(
                    template_path=template_path,
                    dados_iniciais=st.session_state['dados_iniciais'],
                    impostos=st.session_state['impostos'],
                    itens_configurados=st.session_state['itens_configurados']
                )

                buffer_pdf = PDFDocumentService.gerar_pdf(
                    dados_iniciais=st.session_state['dados_iniciais'],
                    impostos=st.session_state['impostos'],
                    itens_configurados=st.session_state['itens_configurados']
                )

                if buffer_word and buffer_pdf:
                    # Prepara os nomes dos arquivos
                    bt = st.session_state['dados_iniciais']['bt']
                    rev = st.session_state['dados_iniciais']['rev']
                    output_filename_word = f"Proposta Blutrafos nº BT {bt}-Rev{rev}.docx"
                    pdf_filename = f"Resumo_Proposta_BT_{bt}-Rev{rev}_EXTRATO.pdf"

                                        # Obter a conexão com o banco de dados
                    conn = DatabaseConfig.get_connection()

                    # Criar um cursor a partir da conexão
                    cur = conn.cursor()

                    # Salvar a revisão
                    try:
                        if st.session_state['tipo_proposta'] == "Atualizar revisão":
                            valor_total = sum(float(item['Preço Total']) for item in st.session_state.get('itens_configurados', []))
                            RevisionService._atualizar_revisao(
                                cur=cur,
                                dados={
                                    'configuracoes_itens': st.session_state.get('configuracoes_itens', {}),
                                    'impostos': st.session_state.get('impostos', {}),
                                    'itens_configurados': st.session_state.get('itens_configurados', []),
                                    'dados_iniciais': st.session_state.get('dados_iniciais', {})
                                },
                                valor=valor_total,
                                numero_revisao=st.session_state['dados_iniciais']['rev'],
                                word_path=output_filename_word,
                                pdf_path=output_filename_word,
                                revisao_id=st.session_state['id_revisao']
                            )

                            conn.commit()
                            
                            # Adicionar atualização do session_state aqui também
                            st.session_state.update({
                                'buffer_word': buffer_word,
                                'output_filename_word': output_filename_word,
                                'buffer_pdf': buffer_pdf,
                                'pdf_filename': pdf_filename,
                                'downloads_gerados': True
                            })
                            
                            st.success("Revisão atualizada com sucesso no banco de dados.")
                        else:
                            valor_total = sum(float(item['Preço Total']) for item in st.session_state.get('itens_configurados', []))
                            
                            result = RevisionService._inserir_revisao(
                                cur=cur,
                                dados={
                                    'configuracoes_itens': st.session_state.get('configuracoes_itens', {}),
                                    'impostos': st.session_state.get('impostos', {}),
                                    'itens_configurados': st.session_state.get('itens_configurados', []),
                                    'dados_iniciais': st.session_state.get('dados_iniciais', {})
                                },
                                id_proposta=st.session_state['id_proposta'],
                                valor=valor_total,
                                numero_revisao=int(st.session_state['dados_iniciais']['rev']),
                                word_path=output_filename_word,
                                pdf_path=pdf_filename
                            )

                            conn.commit()
                            if result:
                                st.success("Revisão salva com sucesso no banco de dados.")
                            
                            # Armazenar os buffers e nomes dos arquivos no session_state
                            st.session_state.update({
                                'buffer_word': buffer_word,
                                'output_filename_word': output_filename_word,
                                'buffer_pdf': buffer_pdf,
                                'pdf_filename': pdf_filename,
                                'downloads_gerados': True
                            })


                    except Exception as e:
                        st.error(f"Erro ao salvar revisão: {str(e)}")
                        st.stop()

                    st.success("Documentos gerados com sucesso.")
                else:
                    st.error("Erro ao gerar os documentos.")
            else:
                st.error("Por favor, preencha todos os campos obrigatórios antes de gerar os documentos.")

        except Exception as e:
            st.error(f"Erro ao processar documentos: {str(e)}")

    # Exibir os botões de download se os documentos foram gerados
    if st.session_state.get('downloads_gerados'):
        render_botoes_download(
            output_filename_word=st.session_state['output_filename_word'],
            pdf_filename=st.session_state['pdf_filename'],
            buffer_word=st.session_state['buffer_word'],
            buffer_pdf=st.session_state['buffer_pdf']
        )
    else:
        st.warning("Aperte no botão acima para gerar os documentos.")

def validar_dados():
    """Valida se os dados necessários estão presentes"""
    if not st.session_state.get('itens_configurados'):
        st.error('Nenhum item configurado!')
        return False
        
    if not st.session_state.get('dados_iniciais'):
        st.error('Dados iniciais não preenchidos!')
        return False
        
    if not st.session_state.get('dados_iniciais').get('id_proposta'):
        st.error('ID da proposta não encontrado!')
        return False
    
    return True

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    
    # Inicialização do session_state para impostos
    if 'impostos' not in st.session_state:
        st.session_state['impostos'] = {}
    
    dadosimpostos = st.session_state['impostos']
    for key in ['local_frete', 'icms', 'contribuinte_icms', 'lucro', 
                'frete', 'local_frete_itens', 'difal', 'f_pobreza', 'comissao']:
        if key not in dadosimpostos:
            dadosimpostos[key] = 0.0 if 'f' in key or 'c' in key else ''
    
