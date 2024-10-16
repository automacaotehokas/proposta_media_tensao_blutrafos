import streamlit as st
import pandas as pd
import psycopg2
from io import BytesIO
from sqlalchemy import create_engine

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

# Upload do arquivo Excel
uploaded_file = st.file_uploader("Escolha o arquivo Excel com a planilha 'atualizacao'", type="xlsx")

if uploaded_file:
    try:
        # Leitura do arquivo Excel
        df = pd.read_excel(uploaded_file, sheet_name='atualizacao')

        # Exibindo os dados carregados para conferência
        st.write("Dados carregados:")
        st.dataframe(df)

        # Verificação de layout
        expected_columns = ['p_caixa', 'p_trafo', 'potencia', 'custo', 'valor', 'classe', 'valor_ip_baixo', 'valor_ip_alto']
        if all(col in df.columns for col in expected_columns):
            # Inserção dos dados no banco de dados
            if st.button("Inserir dados no banco de dados"):
                inserir_dados(df)
        else:
            st.error("A planilha não possui o layout esperado. Verifique as colunas.")
    
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
