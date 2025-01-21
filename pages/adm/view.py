
import streamlit as st
import pandas as pd
import os
from repositories.custos_media_tensao_repository import CustoMediaTensaoRepository

def admin_section():
    """Seção administrativa da aplicação"""
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
        atualizar_base_dados()

def atualizar_base_dados():
    """Interface para atualização da base de dados"""
    st.subheader("Atualizar Base de Dados")
    uploaded_file = st.file_uploader(
        "Escolha o arquivo Excel com a planilha 'atualizacao'", 
        type="xlsx"
    )
    
    if uploaded_file:
        try:
            processar_arquivo_excel(uploaded_file)
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {str(e)}")

def processar_arquivo_excel(uploaded_file):
    """Processa o arquivo Excel carregado"""
    excel_file = pd.ExcelFile(uploaded_file)
    st.write("Abas encontradas no arquivo:", excel_file.sheet_names)
    
    if 'atualizacao' in excel_file.sheet_names:
        df = pd.read_excel(uploaded_file, sheet_name='atualizacao')
        st.write("Dados carregados:")
        st.dataframe(df)
        st.write("Colunas encontradas:", df.columns.tolist())

        expected_columns = [
            'p_caixa', 'p_trafo', 'potencia', 'preco', 'perdas', 
            'classe_tensao', 'valor_ip_baixo', 'valor_ip_alto', 
            'cod_proj_custo', 'descricao', 'potencia_formatada', 
            'cod_proj_caixa'
        ]
        
        if all(col in df.columns for col in expected_columns):
            st.write("Tipos de dados no DataFrame:", df.dtypes)
            if st.button("Atualizar dados"):
                try:
                    CustoMediaTensaoRepository.atualizar_dados(df)
                    st.success("Base de dados atualizada com sucesso!")
                except Exception as e:
                    st.error(f"Erro na atualização: {str(e)}")
        else:
            st.error("A planilha não possui o layout esperado. Verifique as colunas.")
    else:
        st.error("A aba 'atualizacao' não foi encontrada no arquivo enviado.")