import streamlit as st
import pandas as pd
import os
from config_db import conectar_banco  # Função de conexão com o banco de dados
from dotenv import load_dotenv

load_dotenv()
# Função para apagar todos os dados e inserir os novos dados no banco de dados
def atualizar_dados(df):
    conn = conectar_banco()
    cur = conn.cursor()

    # Apaga todos os dados da tabela
    cur.execute("DELETE FROM custos_media_tensao")
    conn.commit()

    # Insere os novos dados com as colunas corretas e colunas formatadas
    for index, row in df.iterrows():

        cur.execute("""
            INSERT INTO custos_media_tensao (p_caixa, p_trafo, potencia, preco, perdas, classe_tensao, valor_ip_baixo, valor_ip_alto,cod_proj_custo,descricao, potencia_formatada,cod_proj_caixa)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s , %s , %s)
        """, (row['p_caixa'], row['p_trafo'], row['potencia'], row['preco'], row['perdas'], row['classe_tensao'], row['valor_ip_baixo'], row['valor_ip_alto'],row['cod_proj_custo'], row['descricao'], row['potencia_formatada'],row['cod_proj_caixa']))
    conn.commit()
    cur.close()
    conn.close()
    st.success("Dados atualizados com sucesso!")

# Interface da página principal (Home)
st.title("Proposta Automatizada - Média Tensão")
st.markdown("---")

# Descrição na página Home
st.markdown("""
    Bem-vindo à Proposta Automatizada de Média Tensão. Este sistema foi desenvolvido para facilitar
    o processo de criação de propostas comerciais personalizadas. Com ele, você pode configurar
    itens técnicos, calcular preços e gerar documentos de forma automatizada.
    """)
st.markdown("---")

# Cria o estado de autenticação se ainda não existir
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

# Verifica se o usuário está autenticado
if not st.session_state['autenticado']:
    st.subheader("Área Administrativa:")

    # Campo para digitar a senha
    senha_adm = st.text_input("Digite a senha de administração", type="password")
    
    # Botão para verificar a senha
    if st.button("Verificar senha"):
        senha_correta = os.getenv("SENHAADM")  # Usando os.getenv para acessar a variável de ambiente

        if senha_adm == senha_correta:
            st.session_state['autenticado'] = True  # Marca como autenticado
            st.success("Acesso concedido à área administrativa.")
        else:
            st.error("Senha incorreta. Tente novamente.")

if st.session_state['autenticado']:
    st.subheader("Atualizar Base de Dados")
    
    uploaded_file = st.file_uploader("Escolha o arquivo Excel com a planilha 'atualizacao'", type="xlsx")
    
    if uploaded_file:
        try:
            # Verifica as abas disponíveis no arquivo
            excel_file = pd.ExcelFile(uploaded_file)
            st.write("Abas encontradas no arquivo:", excel_file.sheet_names)
            
            # Certifica-se de que a aba 'atualizacao' está presente
            if 'atualizacao' in excel_file.sheet_names:
                df = pd.read_excel(uploaded_file, sheet_name='atualizacao')
                
                # Exibe os dados carregados para conferência
                st.write("Dados carregados:")
                st.dataframe(df)

                # Exibe as colunas encontradas
                st.write("Colunas encontradas no arquivo:", df.columns.tolist())

                # Verificação de layout
                expected_columns = ['p_caixa', 'p_trafo', 'potencia', 'preco', 'perdas', 'classe_tensao', 'valor_ip_baixo', 'valor_ip_alto', 'cod_proj_custo', 'descricao', 'potencia_formatada', 'cod_proj_caixa']
                if all(col in df.columns for col in expected_columns):
                    # Verifica os tipos de dados no DataFrame
                    st.write("Tipos de dados no DataFrame:", df.dtypes)

                    # Botão para atualizar os dados no banco de dados
                    if st.button("Atualizar dados"):
                        atualizar_dados(df)
                else:
                    st.error("A planilha não possui o layout esperado. Verifique as colunas.")
            else:
                st.error("A aba 'atualizacao' não foi encontrada no arquivo enviado.")
        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {e}")
