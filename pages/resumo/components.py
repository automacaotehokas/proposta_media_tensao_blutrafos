import streamlit as st
from typing import Dict, List, Any

def render_dados_iniciais(dados: Dict[str, Any]):
    """Renderiza a seção de dados iniciais"""
    st.subheader("Dados Iniciais")
    campos = [
        ('Cliente', 'cliente'),
        ('Nome do Contato', 'nomeCliente'),
        ('Telefone', 'fone'),
        ('Email', 'email'),
        ('BT', 'bt'),
        ('Obra', 'obra'),
        ('Data', lambda d: f"{d.get('dia')}/{d.get('mes')}/{d.get('ano')}"),
        ('Revisão', 'rev'),
        ('Local', 'local_frete')
    ]
    
    for label, key in campos:
        value = key(dados) if callable(key) else dados.get(key, '')
        st.write(f"**{label}:**", value)

def render_variaveis(impostos: Dict[str, Any], itens: List[Dict[str, Any]]):
    """Renderiza a seção de variáveis e percentuais"""
    st.subheader("Resumo das Variáveis")
    
    # Variáveis principais
    campos = [
        ('Contribuinte', 'contribuinte_icms', ''),
        ('Lucro', 'lucro', '%'),
        ('ICMS', 'icms', '%'),
        ('Frete', 'frete', '%'),
        ('Comissão', 'comissao', '%'),
        ('DIFAL', 'difal', '%'),
        ('F.pobreza', 'f_pobreza', '%'),
        ('Local Frete', 'local_frete_itens', '')
    ]
    
    for label, key, suffix in campos:
        value = impostos.get(key, 0)
        if isinstance(value, (int, float)) and suffix == '%':
            st.write(f"**{label}:** {value:.2f}{suffix}")
        else:
            st.write(f"**{label}:** {value}{suffix}")
    
    # Percentuais por item
    voltage_class_percentage = {
        "15 kV": 0,
        "24 kV": 30,
        "36 kV": 50
    }
    
    for idx, item in enumerate(itens, start=1):
        classe_tensao = item.get('classe_tensao', '')
        percentual = voltage_class_percentage.get(classe_tensao, 'Não especificado')
        if item.get('IP') == "00":
            percentual = 0
        st.write(f"**% Caixa Item {idx}:** {percentual}%")

def render_itens_configurados(resumo_df):
    """Renderiza a tabela de itens configurados"""
    st.subheader("Itens Configurados")
    if resumo_df is not None:
        # Remove colunas desnecessárias
        colunas_excluir = ['Tensões', 'Derivações', 'Tensão Primária', 
                          'Tensão Secundária', 'Preço Total']
        df_display = resumo_df.drop(columns=colunas_excluir, errors='ignore')
        st.table(df_display)
    else:
        st.write("Nenhum item configurado.")

def render_botoes_download(output_filename_word, pdf_filename, buffer_word, buffer_pdf):
    """Renderiza os botões de download dos documentos"""
    st.markdown("### Documentos Gerados:")
    
    # Documento Word
    col1, col2 = st.columns([6,1])
    with col1:
        st.write(f"📄 {output_filename_word}")
    with col2:
        st.download_button(
            label="⬇️",
            data=buffer_word,
            file_name=output_filename_word,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    # Documento PDF
    col1, col2 = st.columns([6,1])
    with col1:
        st.write(f"📄 {pdf_filename}")
    with col2:
        st.download_button(
            label="⬇️",
            data=buffer_pdf,
            file_name=pdf_filename,
            mime="application/pdf"
        )