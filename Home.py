import streamlit as st
import pandas as pd
from config_db import conectar_banco
import os  # Função de conexão com o banco de dados

# Função para apagar todos os dados e inserir os novos dados no banco de dados
def atualizar_dados(df):
    conn = conectar_banco()
    cur = conn.cursor()

    # Apaga todos os dados da tabela
    cur.execute("DELETE FROM custos_media_tensao")
    conn.commit()

    # Insere os novos dados
    for index, row in df.iterrows():
        cur.execute("""
            INSERT INTO custos_media_tensao (p_caixa, p_trafo, potencia, preco, perdas, classe, valor_ip_baixo, valor_ip_alto)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (row['p_caixa'], row['p_trafo'], row['potencia'], row['custo'], row['valor'], row['classe'], row['valor_ip_baixo'], row['valor_ip_alto']))
    
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

# Botão "ADM" no canto superior direito
col1, col2 = st.columns([8, 1])  # Layout com o botão no canto direito
with col2:
    if st.button("⚙️ ADM"):
        # Solicita senha para acessar a parte administrativa
        senha_adm = st.text_input("Digite a senha de administração", type="password")

        # Verifica a senha fornecida
        if senha_adm == os.getenv["SENHAADM"]:
            st.success("Acesso concedido à área administrativa.")
            
            # Agora exibe a funcionalidade de upload e atualização de dados
            st.subheader("Atualizar Base de Dados: custos_media_tensao")
            
            # Upload do arquivo Excel
            uploaded_file = st.file_uploader("Escolha o arquivo Excel com a planilha 'atualizacao'", type="xlsx")

            if uploaded_file:
                try:
                    # Leitura do arquivo Excel
                    df = pd.read_excel(uploaded_file, sheet_name='atualizacao')

                    # Exibe os dados carregados para conferência
                    st.write("Dados carregados:")
                    st.dataframe(df)

                    # Verificação de layout
                    expected_columns = ['p_caixa', 'p_trafo', 'potencia', 'custo', 'valor', 'classe', 'valor_ip_baixo', 'valor_ip_alto']
                    if all(col in df.columns for col in expected_columns):
                        # Botão para atualizar os dados no banco de dados
                        if st.button("Atualizar dados"):
                            atualizar_dados(df)
                    else:
                        st.error("A planilha não possui o layout esperado. Verifique as colunas.")
                except Exception as e:
                    st.error(f"Erro ao ler o arquivo: {e}")
        else:
            st.error("Senha incorreta. Tente novamente.")
