import streamlit as st
from io import BytesIO
from backup.Resumo import gerar_pdf  # Suponha que 'Resumo' seja o módulo onde a função gerar_pdf está definida

# Configuração dos dados de exemplo
st.session_state['dados_iniciais'] = {
    'bt': '001',
    'rev': 'A',
    'cliente': 'Cliente Exemplo',
    'nomeCliente': 'Nome do Cliente',
    'fone': '1234-5678',
    'email': 'cliente@exemplo.com',
    'obra': 'Obra Exemplo',
    'dia': '09',
    'mes': '12',
    'ano': '2024',
    'local_frete': 'São Paulo'
}

st.session_state['contribuinte_icms'] = 'Contribuinte Exemplo'
st.session_state['lucro'] = 10.0
st.session_state['icms'] = 18.0
st.session_state['frete'] = 3.0
st.session_state['comissao'] = 5.0
st.session_state['difal'] = 2.0
st.session_state['f_pobreza'] = 0.5
st.session_state['local_frete_itens'] = 'São Paulo'

st.session_state['itens_configurados'] = [
    {'Potência': '15 kVA', 'IP': '00', 'Descrição': 'Item Exemplo 1', 'Fator K': 1.0, 'Quantidade': 5, 'Preço Unitário': 100.00},
    {'Potência': '30 kVA', 'IP': '21', 'Descrição': 'Item Exemplo 2', 'Fator K': 1.2, 'Quantidade': 3, 'Preço Unitário': 150.00},
    # Adicione mais itens conforme necessário
]

# Função para mapear potência para código de projeto de caixa
def get_mapping_code(potencia):
    mapping = {
        "15 kVA": "0013.0760.000",
        "30 kVA": "0013.0480.000",
        "45 kVA": "0013.0480.000",
        "75 kVA": "0013.0896.000",
        "112.5 kVA": "0013.0735.000",
        "150 kVA": "0013.0735.000",
        "225 kVA": "0013.0478.000",
        "300 kVA": "0013.0613.000",
        "500 kVA": "0013.0606.000",
        "750 kVA": "0013.0922.000",
        "1000 kVA": "0013.1182.000",
        "1250 kVA": "0013.0639.000",
        "1500 kVA": "0013.0643.000",
        "2000 kVA": "0013.0805.000",
        "2500 kVA": "0013.0725.000",
        "3000 kVA": "0013.1074.000",
        "3500 kVA": "Não especificado",
        "4000 kVA": "0013.0679.000",
        "5000 kVA": "Não especificado",
        "6000 kVA": "Não especificado",
    }
    return mapping.get(potencia, "Não especificado")

# Chamada à função gerar_pdf
pdf_buffer = gerar_pdf()

if pdf_buffer:
    # Verifica o código do item para cada configuração de item
    for item in st.session_state['itens_configurados']:
        potencia_item = item.get('Potência', '')
        # Obtém o código correspondente para a potência
        codigo_item = get_mapping_code(potencia_item)
        st.write(f"Código para potência {potencia_item}: {codigo_item}")

    # Salva o PDF em um arquivo
    output_path = 'teste.pdf'
    with open(output_path, 'wb') as f:
        f.write(pdf_buffer.getvalue())
    st.success(f"PDF gerado com sucesso! Você pode encontrá-lo em {output_path}.")
else:
    st.error("Falha na geração do PDF.")
