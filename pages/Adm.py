import streamlit as st
import pandas as pd
import psycopg2
from io import BytesIO
from sqlalchemy import create_engine
import openpyxl

# Função para conectar ao banco de dados
def get_db_connection():
    conn = psycopg2.connect(
        host=st.secrets["DB_HOST"],
        database=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        port=st.secrets["DB_PORT"]
    )
    return conn

# Função para apagar todos os dados da tabela custos_media_tensao
def apagar_dados():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM custos_media_tensao")
    conn.commit()
    cur.close()
    conn.close()
    st.success("Todos os dados foram apagados da tabela 'custos_media_tensao'.")

# Função para inserir os dados no banco de dados
def inserir_dados(df):
    engine = create_engine(f"postgresql+psycopg2://{st.secrets['DB_USER']}:{st.secrets['DB_PASSWORD']}@{st.secrets['DB_HOST']}:{st.secrets['DB_PORT']}/{st.secrets['DB_NAME']}")
    df.to_sql('custos_media_tensao', engine, if_exists='replace', index=False)
    st.success("Dados inseridos com sucesso na tabela 'custos_media_tensao'.")

# Interface do Streamlit
st.title("Atualizar Base de Dados: custos_media_tensao")

# Botão para apagar os dados da tabela
if st.button("Apagar todos os dados da tabela"):
    apagar_dados()

# Campo para inserir a senha do arquivo Excel
senha = st.text_input("Digite a senha para desbloquear o arquivo Excel (se necessário)", type="password")

# Upload do arquivo Excel
uploaded_file = st.file_uploader("Escolha o arquivo Excel com a planilha 'atualizacao'", type="xlsx")

if uploaded_file:
    try:
        # Leitura do arquivo Excel com senha
        if senha:
            # Se a senha for fornecida, tenta abrir o arquivo protegido
            with BytesIO(uploaded_file.read()) as f:
                excel_file = pd.read_excel(f, sheet_name='atualizacao', engine='openpyxl', password=senha)
        else:
            # Caso contrário, abre normalmente
            excel_file = pd.read_excel(uploaded_file, sheet_name='atualizacao', engine='openpyxl')

        # Exibindo os dados carregados para conferência
        st.write("Dados carregados:")
        st.dataframe(excel_file)

        # Verificação de layout
        expected_columns = ['p_caixa', 'p_trafo', 'potencia', 'custo', 'valor', 'classe', 'valor_ip_baixo', 'valor_ip_alto']
        if all(col in excel_file.columns for col in expected_columns):
            # Inserção dos dados no banco de dados
            if st.button("Inserir dados no banco de dados"):
                inserir_dados(excel_file)
        else:
            st.error("A planilha não possui o layout esperado. Verifique as colunas.")
    
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
