import streamlit as st
import pandas as pd
import os
import json
from backup.config_db import conectar_banco
from dotenv import load_dotenv

def inicializar_dados():
    # Pegar parâmetros da URL
    params = st.query_params
    
    # Se é uma nova proposta
    if all(key in params for key in ['id_proposta', 'cliente', 'bt', 'obra']):
        if 'dados_iniciais' not in st.session_state:
            st.session_state['dados_iniciais'] = {
                'cliente': params.get('cliente', ''),  # Não precisa mais do [0]
                'bt': params.get('bt', ''),
                'obra': params.get('obra', ''),
                'id_proposta': params.get('id_proposta', ''),
                'rev': params.get('rev', '00'),
                'dia': st.session_state.get('dia', ''),
                'mes': st.session_state.get('mes', ''),
                'ano': st.session_state.get('ano', ''),
                'nomeCliente': '',
                'email': '',
                'fone': ''
            }
    
    # Se é uma edição de revisão
    revisao_id = params.get("revisao_id")
    if revisao_id and 'loaded' not in st.session_state:
        carregar_dados_revisao(revisao_id)

        
def carregar_dados_revisao(revisao_id):
    try:
        conn = conectar_banco()
        cur = conn.cursor()
        
        # Buscar dados da revisão
        cur.execute("""
            SELECT r.conteudo, p.cliente, p.proposta, p.obra 
            FROM revisao r 
            JOIN proposta p ON r.id_proposta = p.id_proposta 
            WHERE r.id_revisao = %s
        """, (revisao_id,))
        
        resultado = cur.fetchone()
        if resultado:
            conteudo_json, cliente, proposta, obra = resultado
            
            # Carregar dados do JSON para o session_state
            if conteudo_json:
                dados = json.loads(conteudo_json)
                for key in ['configuracoes_itens', 'impostos', 'itens_configurados', 'dados_iniciais']:
                    if key in dados:
                        st.session_state[key] = dados[key]
            
            st.session_state['loaded'] = True
        
        cur.close()
        conn.close()
        
    except Exception as e:
        st.error(f"Erro ao carregar dados da revisão: {str(e)}")

def admin_section():
    """Função para a seção administrativa"""
    if 'autenticado' not in st.session_state:
        st.session_state['autenticado'] = False

    if not st.session_state['autenticado']:
        st.subheader("Área Administrativa:")
        senha_adm = st.text_input("Digite a senha de administração", type="password")
        
        if st.button("Verificar senha"):
            senha_correta = os.getenv("SENHAADM")
            if senha_adm == senha_correta:
                st.session_state['autenticado'] = True
                st.success("Acesso concedido à área administrativa.")
            else:
                st.error("Senha incorreta. Tente novamente.")

    if st.session_state['autenticado']:
        st.subheader("Atualizar Base de Dados")
        uploaded_file = st.file_uploader("Escolha o arquivo Excel com a planilha 'atualizacao'", type="xlsx")
        
        if uploaded_file:
            processar_arquivo_excel(uploaded_file)

def atualizar_dados(df):
    """
    Atualiza os dados da tabela custos_media_tensao com os novos dados do DataFrame.
    
    Args:
        df (pandas.DataFrame): DataFrame contendo os novos dados a serem inseridos
    """
    try:
        conn = conectar_banco()
        cur = conn.cursor()

        # Apaga todos os dados da tabela
        cur.execute("DELETE FROM custos_media_tensao")
        conn.commit()

        # Insere os novos dados com as colunas corretas e colunas formatadas
        for index, row in df.iterrows():
            cur.execute("""
                INSERT INTO custos_media_tensao (
                    p_caixa, 
                    p_trafo, 
                    potencia, 
                    preco, 
                    perdas, 
                    classe_tensao, 
                    valor_ip_baixo, 
                    valor_ip_alto,
                    cod_proj_custo,
                    descricao, 
                    potencia_formatada,
                    cod_proj_caixa
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['p_caixa'], 
                row['p_trafo'], 
                row['potencia'], 
                row['preco'], 
                row['perdas'], 
                row['classe_tensao'], 
                row['valor_ip_baixo'], 
                row['valor_ip_alto'],
                row['cod_proj_custo'], 
                row['descricao'], 
                row['potencia_formatada'],
                row['cod_proj_caixa']
            ))

        conn.commit()
        st.success("Dados atualizados com sucesso!")

    except Exception as e:
        st.error(f"Erro ao atualizar dados: {str(e)}")
        # Fazer rollback em caso de erro
        if conn:
            conn.rollback()
    
    finally:
        # Garantir que a conexão seja sempre fechada
        if cur:
            cur.close()
        if conn:
            conn.close()

def processar_arquivo_excel(uploaded_file):
    """Função para processar o arquivo Excel carregado"""
    try:
        excel_file = pd.ExcelFile(uploaded_file)
        st.write("Abas encontradas no arquivo:", excel_file.sheet_names)
        
        if 'atualizacao' in excel_file.sheet_names:
            df = pd.read_excel(uploaded_file, sheet_name='atualizacao')
            st.write("Dados carregados:")
            st.dataframe(df)
            st.write("Colunas encontradas no arquivo:", df.columns.tolist())

            expected_columns = ['p_caixa', 'p_trafo', 'potencia', 'preco', 'perdas', 
                              'classe_tensao', 'valor_ip_baixo', 'valor_ip_alto', 
                              'cod_proj_custo', 'descricao', 'potencia_formatada', 
                              'cod_proj_caixa']
            
            if all(col in df.columns for col in expected_columns):
                st.write("Tipos de dados no DataFrame:", df.dtypes)
                if st.button("Atualizar dados"):
                    atualizar_dados(df)
            else:
                st.error("A planilha não possui o layout esperado. Verifique as colunas.")
        else:
            st.error("A aba 'atualizacao' não foi encontrada no arquivo enviado.")
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")

def main():
    st.title("Proposta Automatizada - Média Tensão")
    st.markdown("---")
    
    # Inicializar dados se necessário
    inicializar_dados()
    
    # Se estiver editando uma revisão, mostrar informações
    if 'dados_iniciais' in st.session_state:
        st.info(f"""
        Cliente: {st.session_state['dados_iniciais'].get('cliente')}
        Proposta: {st.session_state['dados_iniciais'].get('bt')}
        Obra: {st.session_state['dados_iniciais'].get('obra')}
        """)
    else:
        # Descrição padrão
        st.markdown("""
        Bem-vindo à Proposta Automatizada de Média Tensão. Este sistema foi desenvolvido para facilitar
        o processo de criação de propostas comerciais personalizadas. Com ele, você pode configurar
        itens técnicos, calcular preços e gerar documentos de forma automatizada.
        """)
    
    st.markdown("---")
    
    # Seção administrativa
    admin_section()

if __name__ == "__main__":
    load_dotenv()
    main()