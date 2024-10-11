import os
import streamlit as st


# Configuração da página inicial - deve ser a primeira chamada
st.set_page_config(page_title="Proposta Automatizada - Média Tensão", layout="wide")



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
