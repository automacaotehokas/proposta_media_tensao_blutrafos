import streamlit as st
import pandas as pd
from config_db import conectar_banco
import os
from dotenv import load_dotenv
from pages.Inicial import carregar_cidades


load_dotenv()

def verificar_dados_iniciais():
    dados_iniciais = st.session_state.get('dados_iniciais', {})
    campos_obrigatorios = ['cliente', 'nomeCliente', 'fone', 'email', 'bt', 'obra', 'dia', 'mes', 'ano', 'rev', 'local']

    for campo in campos_obrigatorios:
        if not dados_iniciais.get(campo):
            return False
    return True

@st.cache_data
def buscar_dados():
    conn = conectar_banco()
    query = """
        SELECT id, descricao, potencia, classe_tensao, perdas, preco, p_trafo, valor_ip_baixo, valor_ip_alto, p_caixa
        FROM custos_media_tensao
        ORDER BY potencia ASC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def calcular_preco_total(preco_unit, quantidade):
    return preco_unit * quantidade

if 'itens_configurados' not in st.session_state:
    st.session_state['itens_configurados'] = []

st.title('Configuração Itens')
st.markdown("---")
df = buscar_dados()
icms_base = 12 / 100
irpj_cssl = 2.28 / 100
tkxadmmkt = 3.7 / 100
mocusfixo = 20 / 100
pisconfins = 9.25 / 100
p_caixa_24 = 30 / 100
p_caixa_36 = 50 / 100
valor_ip_baixo = df['valor_ip_baixo'].iloc[0]
valor_ip_alto = df['valor_ip_alto'].iloc[0]
p_caixa = df['p_caixa'].iloc[0]
percentuais_k = {
    1: 0.0,
    4: 0.0502,
    6: 0.0917,
    13: 0.2317,
    20: 0.3359
}

carregar_cidades()

if 'dados_iniciais' not in st.session_state:
    st.session_state['dados_iniciais'] = {}

if 'lucro' not in st.session_state:
    st.session_state['lucro'] = 5.0
if 'icms' not in st.session_state:
    st.session_state['icms'] = 12.0
if 'frete' not in st.session_state:
    st.session_state['frete'] = 5.0
if 'comissao' not in st.session_state:
    st.session_state['comissao'] = 5.0

if 'local_frete_itens' not in st.session_state:
    st.session_state['local_frete_itens'] = st.session_state['dados_iniciais'].get('local_frete', '')

lucro = st.number_input('Lucro (%):', min_value=0.0, max_value=100.0, step=0.1, value=st.session_state['lucro'])
st.session_state['lucro'] = lucro
icms = st.number_input('ICMS (%):', min_value=0.0, max_value=100.0, step=0.1, value=st.session_state['icms'])
st.session_state['icms'] = icms
frete = st.number_input('Frete (%):', min_value=0.0, step=0.1, value=st.session_state['frete'])
st.session_state['frete'] = frete

cidades = st.session_state['cidades']
local_frete_itens = st.selectbox(
    'Local Frete :',
    st.session_state['cidades'],
    index=st.session_state['cidades'].index(st.session_state['local_frete_itens']) if st.session_state['local_frete_itens'] in st.session_state['cidades'] else 0
)
st.session_state['local_frete_itens'] = local_frete_itens

contribuinte_icms = st.radio(
    "O cliente é contribuinte do ICMS?",
    options=["Sim", "Não"],
    index=0 if 'contribuinte_icms' not in st.session_state else 1 if st.session_state['contribuinte_icms'] == "Não" else 0
)
st.session_state['contribuinte_icms'] = contribuinte_icms

if 'difal' not in st.session_state:
    st.session_state['difal'] = 0.0
if 'f_pobreza' not in st.session_state:
    st.session_state['f_pobreza'] = 0.0

if contribuinte_icms == "Sim":
    st.session_state['difal'] = 0.0
    st.session_state['f_pobreza'] = 0.0
else:
    st.session_state['difal'] = st.number_input(
        'DIFAL (%):',
        min_value=0.0,
        value=st.session_state['difal'],
        step=0.1
    )
    st.session_state['f_pobreza'] = st.number_input(
        'F. Pobreza (%):',
        min_value=0.0,
        value=st.session_state['f_pobreza'],
        step=0.1
    )

comissao = st.number_input('Comissão (%):', min_value=0.0, step=0.1, value=st.session_state['comissao'])
st.session_state['comissao'] = comissao

percentuais = (lucro / 100) + (icms_base) + (comissao / 100) + (frete / 100) + irpj_cssl + tkxadmmkt + mocusfixo + pisconfins

quantidade_itens = st.number_input('Quantidade de Itens:', min_value=1, step=1, value=len(st.session_state.get('itens_configurados', [])) or 1)

while len(st.session_state['itens_configurados']) < quantidade_itens:
    
    item_index = len(st.session_state['itens_configurados'])

    st.session_state['itens_configurados'].append({
        'ID': None,
        'Item': item_index + 1,
        'Quantidade': 1,
        'Descrição': "",
        'Potência': None,
        'Tensão Primária': None,
        'Tensão Secundária': 380,
        'Derivações': "13,8/13,2/12,6/12,0/11,4",
        'Fator K': 1,
        'IP': '00',
        'Perdas': None,
        'Preço Unitário': 0.0,
        'Preço Total': 0.0,
        'IPI': 0.0,
        'classe_tensao': None,
        'adicional_caixa_classe': None
    })

while len(st.session_state['itens_configurados']) > quantidade_itens:
    st.session_state['itens_configurados'].pop()

opcoes_ip = ['00', '21', '23', '54']
fator_k_opcoes = [1, 4, 6, 8, 13]

for item in range(len(st.session_state['itens_configurados'])):
    st.subheader(f"Item {item + 1}")

    descricao_opcoes = [""] + df['descricao'].unique().tolist()
    descricao_key = f'descricao_{item}'
    descricao_escolhida = st.selectbox(
        f'Digite ou Selecione a Descrição do Item {item + 1}:',
        descricao_opcoes,
        key=descricao_key,
        index=0 if st.session_state['itens_configurados'][item]['Descrição'] == "" else descricao_opcoes.index(st.session_state['itens_configurados'][item]['Descrição'])
    )

    if descricao_escolhida == "":
        st.warning("Por favor, selecione uma descrição para continuar.")
        st.session_state['itens_configurados'][item]['Preço Total'] = 0.0
        st.session_state['itens_configurados'][item]['Preço Unitário'] = 0.0
        continue

    id_item = df[df['descricao'] == descricao_escolhida]['id'].values[0]
    st.session_state['itens_configurados'][item]['ID'] = id_item
    st.session_state['itens_configurados'][item]['Descrição'] = descricao_escolhida

    detalhes_item = df[df['descricao'] == descricao_escolhida].iloc[0]
    st.session_state['itens_configurados'][item]['Potência'] = detalhes_item['potencia']
    st.session_state['itens_configurados'][item]['Perdas'] = detalhes_item['perdas']
    st.session_state['itens_configurados'][item]['classe_tensao'] = detalhes_item['classe_tensao']

    valor_ip_baixo = detalhes_item['valor_ip_baixo']
    valor_ip_alto = detalhes_item['valor_ip_alto']
    p_caixa = detalhes_item['p_caixa']
    preco_base = detalhes_item['preco']
    p_trafo = detalhes_item['p_trafo']
    
    preco_base1 = preco_base / (1 - p_trafo - percentuais)

    item_index = 0 

    fator_k_escolhido = st.selectbox(
        f'Selecione o Fator K do Item: ',
        fator_k_opcoes,
        key=f'fator_k_{item_index}_unique_key',
        index=fator_k_opcoes.index(st.session_state['itens_configurados'][item]['Fator K'])
    )
    st.session_state['itens_configurados'][item]['Fator K'] = fator_k_escolhido

    ip_escolhido = st.selectbox(
        f'Selecione o IP do Item: ',
        opcoes_ip,
        key=f'ip_{item_index}_unique_key',
        index=opcoes_ip.index(st.session_state['itens_configurados'][item]['IP'])
    )
    st.session_state['itens_configurados'][item]['IP'] = ip_escolhido

    # Pegar a potência do item (a partir da descrição selecionada anteriormente)
    potencia = st.session_state['itens_configurados'][item]['Potência']

    # Inicializa a potência equivalente com a potência original
    potencia_equivalente = potencia

    # Se o Fator K for maior que 5, calcular a potência equivalente
        # Se o Fator K for maior que 5, calcular a potência equivalente
    if fator_k_escolhido > 5:
        potencia_equivalente = potencia / (
            (-0.000000391396 * fator_k_escolhido**6) +
            (0.000044437349 * fator_k_escolhido**5) -
            (0.001966117106 * fator_k_escolhido**4) +
            (0.040938237195 * fator_k_escolhido**3) -
            (0.345600795014 * fator_k_escolhido**2) -
            (1.369407483908 * fator_k_escolhido) +
            101.826204136368
        ) / 100 * 10000  # Ajuste para multiplicar corretamente

        # Arredondar para o valor mais próximo para cima na coluna 'potencia' da base de dados
        potencias_disponiveis = sorted(df['potencia'].values)
        potencia_equivalente = next((p for p in potencias_disponiveis if p >= potencia_equivalente), potencias_disponiveis[-1])

        # Atualizar a potência equivalente no session_state
        st.session_state['itens_configurados'][item]['Potência Equivalente'] = potencia_equivalente

        # Buscar os valores da potência equivalente
        detalhes_item_equivalente = df[df['potencia'] == potencia_equivalente].iloc[0]
        valor_ip_baixo = detalhes_item_equivalente['valor_ip_baixo']
        valor_ip_alto = detalhes_item_equivalente['valor_ip_alto']
        p_caixa = detalhes_item_equivalente['p_caixa']
    else:
        # Usar os valores da potência original se o fator K for <= 5
        valor_ip_baixo = detalhes_item['valor_ip_baixo']
        valor_ip_alto = detalhes_item['valor_ip_alto']
        p_caixa = detalhes_item['p_caixa']

    # Cálculo do adicional IP baseado no IP escolhido e os valores adequados (potência original ou equivalente)
    if ip_escolhido == '00':
        adicional_ip = 0.0
    else:
        adicional_ip = valor_ip_baixo / (1 - percentuais - p_caixa) if int(ip_escolhido) < 54 else valor_ip_alto / (1 - percentuais - p_caixa)

# Atualizar o preço total considerando o adicional IP e demais fatores

    classe_tensao = detalhes_item['classe_tensao']
    adicional_caixa_classe = 0
    if classe_tensao == "24 kV":
        adicional_caixa_classe = p_caixa_24 * adicional_ip
    elif classe_tensao == "36 kV":
        adicional_caixa_classe = p_caixa_36 * adicional_ip
    elif classe_tensao == "15 kV":
        adicional_caixa_classe = 0

    adicional_k = 0
    if fator_k_escolhido in percentuais_k:
        adicional_k = preco_base1 * percentuais_k[fator_k_escolhido]

    preco_unitario = int(((preco_base1 + adicional_ip + adicional_k + adicional_caixa_classe) * (1 - 0.12)) / \
                      (1 - (st.session_state['difal'] / 100) - (st.session_state['f_pobreza'] / 100) - (st.session_state['icms'] / 100)))

    st.session_state['itens_configurados'][item]['Preço Unitário'] = preco_unitario

    # Regras para valores padrão de Tensão Primária, Tensão Secundária e Derivações
    if classe_tensao == "15 kV":
        tensao_primaria_padrao = "13,8"
        derivacoes_padrao = "13,8/13,2/12,6/12,0/11,4kV"
    elif classe_tensao == "24 kV":
        tensao_primaria_padrao = "23,1"
        derivacoes_padrao = "23,1/22,0/20kV"
    elif classe_tensao == "36 kV":
        tensao_primaria_padrao = "34,5"
        derivacoes_padrao = "+/- 2x2,5%"
    else:
        tensao_primaria_padrao = st.session_state['itens_configurados'][item]['Tensão Primária']
        derivacoes_padrao = st.session_state['itens_configurados'][item]['Derivações']

    # Campos de entrada
    tensao_primaria = st.text_input(
        f'Tensão Primária do Item {item + 1}:',
        key=f'tensao_primaria_{item}',
        value=tensao_primaria_padrao,  # Usando o valor padrão baseado na classe
        placeholder="Digite apenas o valor sem unidade"
    )
    tensao_secundaria = st.text_input(
        f'Tensão Secundária do Item {item + 1}:',
        key=f'tensao_secundaria_{item}',
        value=st.session_state['itens_configurados'][item]['Tensão Secundária'],
        placeholder="Digite apenas o valor sem unidade"
    )
    derivacoes = st.text_input(
        f'Derivações do Item {item + 1}:',
        key=f'derivacoes_{item}',
        value=derivacoes_padrao,  # Usando o valor padrão baseado na classe
        placeholder="Digite apenas o valor sem unidade"
    )

    st.session_state['itens_configurados'][item]['Tensão Primária'] = tensao_primaria
    st.session_state['itens_configurados'][item]['Tensão Secundária'] = tensao_secundaria
    st.session_state['itens_configurados'][item]['Derivações'] = derivacoes

    quantidade = st.number_input(
        f'Quantidade para o Item {item + 1}:',
        min_value=1,
        value=st.session_state['itens_configurados'][item]['Quantidade'],
        step=1,
        key=f'qtd_{item}'
    )
    st.session_state['itens_configurados'][item]['Quantidade'] = quantidade

    ipi = st.number_input(f'IPI do Item {item + 1} (%):', min_value=0.0, step=0.1, value=0.0, key=f'ipi_{item}')
    st.session_state['itens_configurados'][item]['IPI'] = ipi

    preco_total = calcular_preco_total(preco_unitario, quantidade)
    st.session_state['itens_configurados'][item]['Preço Total'] = preco_total

    st.markdown("---")

# Mostrar a tabela de resumo
st.subheader("Resumo dos Itens Selecionados")
resumo_df = pd.DataFrame(st.session_state['itens_configurados'])

resumo_df['Potência'] = resumo_df['Potência'].apply(lambda x: f"{x:,.0f} kVA" if x is not None else "")
resumo_df['Tensões'] = resumo_df['Tensão Primária'] + "kV" + " / " + resumo_df['Tensão Secundária'] + " V"
resumo_df = resumo_df[['Item', 'Quantidade', 'Potência', 'Tensões', 'Perdas', 'Fator K', 'IP', 'Preço Unitário', 'Preço Total']]

st.table(resumo_df)

st.session_state['resumo_df'] = resumo_df

st.markdown("---")

total_fornecimento = resumo_df['Preço Total'].sum()
st.subheader(f"Valor Total do Fornecimento: R$ {total_fornecimento:,.2f}")


