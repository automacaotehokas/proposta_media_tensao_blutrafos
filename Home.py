import streamlit as st
import pandas as pd
from io import BytesIO
from config_db import conectar_banco  # Função já existente para conexão com o banco de dados
from PIL import Image

# Configuração da página inicial - deve ser a primeira chamada
st.set_page_config(page_title="Proposta Automatizada - Média Tensão", layout="wide")

# Função para verificar a senha de administração
def autenticar_adm(senha):
    return senha == st.secrets["SENHAADM"]

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
            INSERT INTO custos_media_tensao (p_caixa, p_trafo, potencia, custo, valor, classe, valor_ip_baixo, valor_ip_alto)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (row['p_caixa'], row['p_trafo'], row['potencia'], row['custo'], row['valor'], row['classe'], row['valor_ip_baixo'], row['valor_ip_alto']))
    
    conn.commit()
    cur.close()
    conn.close()
    st.success("Dados atualizados com sucesso!")

# Layout da página principal e botão de ADM no canto superior direito
col1, col2 = st.columns([8, 1])  # Ajuste os valores para mover o botão mais para o lado direito

with col2:
    # Ícone de engrenagem para o botão de ADM
    if st.button("⚙️ ADM"):  # O emoji de engrenagem representa o ícone no botão
        senha_adm = st.text_input("Digite a senha de administração", type="password")

        # Verifica a senha inserida
        if autenticar_adm(senha_adm):
            st.success("Acesso concedido à área administrativa.")

            # Função administrativa: Upload de Excel e atualização dos dados
            st.markdown("---")
            st.subheader("Atualizar Base de Dados: custos_media_tensao")

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
                        # Botão para atualizar os dados no banco de dados
                        if st.button("Atualizar dados"):
                            atualizar_dados(df)
                    else:
                        st.error("A planilha não possui o layout esperado. Verifique as colunas.")
                
                except Exception as e:
                    st.error(f"Erro ao ler o arquivo: {e}")
        else:
            st.error("Senha incorreta. Tente novamente.")

# Conteúdo principal da página após a autenticação
st.image("image1png.png", width=100)  # Adicionando a imagem do logo

# Título e descrição da página
st.title("Proposta Automatizada - Média Tensão")
st.markdown("---")

# Descrição justificada da página
st.markdown(
    """
    <style>
    .justified-text {
        text-align: justify;
    }
    </style>
    <div class="justified-text">
        Bem-vindo à Proposta Automatizada de Média Tensão. Este sistema foi desenvolvido para 
        facilitar o processo de criação de propostas comerciais personalizadas. Com ele, é possível configurar 
        itens técnicos, calcular preços e gerar documentos profissionais de maneira automatizada, otimizando 
        tempo e garantindo precisão nas informações fornecidas aos nossos clientes.
        <br><br>
        Nosso objetivo é proporcionar uma solução eficiente, rápida e segura, integrando todas as etapas do 
        processo de criação de propostas em um único lugar, com a capacidade de armazenar e gerenciar dados de 
        forma centralizada através da integração com o SharePoint.
    </div>
    """, 
    unsafe_allow_html=True
)
