import streamlit as st
import logging
from services.revision_service import RevisionService
from .components import (
    render_dados_iniciais, render_variaveis, 
    render_itens_configurados, render_botoes_download
)

from services.document.master.manager import DocumentManager
from config.databaseMT import DatabaseConfig
from services.sharepoint.sharepoint_service import SharePoint


def is_ultima_revisao(id_proposta: str, id_revisao: str) -> bool:
   conn = DatabaseConfig.get_connection()
   try:
       with conn.cursor() as cur:
           cur.execute("""
               SELECT id_revisao = (
                   SELECT id_revisao 
                   FROM revisoes
                   WHERE id_proposta_id = %s
                   ORDER BY revisao DESC, dt_revisao DESC
                   LIMIT 1
               ) as is_latest
               FROM revisoes 
               WHERE id_revisao = %s
           """, (id_proposta, id_revisao))
           result = cur.fetchone()
           return result[0] if result else False
   finally:
       conn.close()

def verificar_dados_completos():
    """Verifica se todos os dados necessários estão preenchidos"""
    dados_iniciais = st.session_state.get('dados_iniciais', {})

    campos_obrigatorios = [
        'cliente', 'nomeCliente', 'fone', 'email', 'bt', 
        'dia', 'mes', 'ano', 'rev', 'local_frete'
    ]

    return all(dados_iniciais.get(campo) for campo in campos_obrigatorios)

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
                    st.session_state['itens']['itens_configurados_mt'])
    st.markdown("---")

    # Adicionar campo de comentários
    st.markdown("### Comentários da Revisão")
    if 'dados_iniciais' in st.session_state:
        st.session_state['dados_iniciais']['comentario'] = st.text_area(
            "Insira um comentário para esta revisão:",
            value=st.session_state['dados_iniciais'].get('comentario', ''),
            key='comentario_revisao'
        )

    # Botão de confirmação
    dados_completos = verificar_dados_completos()
    st.write("O botão abaixo estará disponível após o preenchimento de todos os dados")

    if st.button("Confirmar", type="primary", use_container_width=True):
        # Função para gerar documentos de forma independente
        def gerar_documentos_independente():
            try:
                # Verifica se todos os dados necessários estão presentes
                if not verificar_dados_completos():
                    st.error("Por favor, preencha todos os campos obrigatórios antes de gerar os documentos.")
                    return False

                # Busca o escopo do transformador
                escopo = RevisionService.buscar_escopo_transformador(
                    st.session_state.get('itens_configurados', [])
                )

                # Inicializa o gerenciador de documentos
                doc_manager = DocumentManager()
                
                # Recupera dados necessários do session_state
                dados_iniciais = st.session_state['dados_iniciais']
                itens = st.session_state['itens']
                impostos = st.session_state['impostos']
                
                # Gera o documento Word
                output_path = doc_manager.gerar_documentos(
                    itens=itens,
                    observacao=dados_iniciais.get('comentario', ''),
                    replacements={
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
                        '{{IP}}': ', '.join(set(str(item['IP']) for item in itens.get('itens_configurados_bt', []) 
                                        if item['IP'] != '00')),
                        '{obra}': '' if not dados_iniciais.get('obra', '').strip() else 'Obra:'
                    }
                )
                
                # Prepara os nomes dos arquivos
                bt = dados_iniciais['bt']
                rev = dados_iniciais['rev']
                output_filename_word = f"Proposta Blutrafos nº BT {bt}-Rev{rev}.docx"
                pdf_filename = f"Resumo_Proposta_BT_{bt}-Rev{rev}_EXTRATO.pdf"
                
                # Lê o arquivo Word em memória
                with open(output_path, 'rb') as word_file:
                    buffer_word = word_file.read()
                
                # Prepara a conexão com o banco de dados
                conn = DatabaseConfig.get_connection()
                cur = conn.cursor()
                pdf_path = "bola azul"

                try:
                    # Calcula o valor total dos itens
                    valor_total = sum(float(item['Preço Total']) for item in st.session_state.get('itens_configurados', []))
                    
                    # Salva a revisão no banco de dados
                    if st.session_state['tipo_proposta'] == "Atualizar revisão":
                        RevisionService._atualizar_revisao(
                            cur=cur,
                            dados={
                                'configuracoes_itens': st.session_state.get('configuracoes_itens', {}),
                                'impostos': st.session_state.get('impostos', {}),
                                'itens_configurados': st.session_state.get('itens_configurados', []),
                                'dados_iniciais': st.session_state.get('dados_iniciais', {})
                            },
                            valor=valor_total,
                            numero_revisao=int(st.session_state['dados_iniciais']['rev']),
                            word_path=output_filename_word,
                            pdf_path=pdf_filename,
                            escopo=escopo,
                            revisao_id=st.session_state['id_revisao']
                        )
                    else:
                        RevisionService._inserir_revisao(
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
                            pdf_path=pdf_filename,
                            escopo=escopo
                        )

                    conn.commit()

                    # Atualiza o session_state com os buffers e nomes dos arquivos
                    st.session_state.update({
                        'buffer_word': buffer_word,
                        'output_filename_word': output_filename_word,
                        'buffer_pdf': "bola azul",
                        'pdf_filename': pdf_filename,
                        'downloads_gerados': True
                    })

                    st.success("Documentos gerados com sucesso.")
                    return True

                except Exception as e:
                    st.error(f"Erro ao salvar revisão: {str(e)}")
                    return False

            except Exception as e:
                st.error(f"Erro ao gerar documentos: {str(e)}")
                return False

        # Chama a função de geração de documentos
        gerar_documentos_independente()

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