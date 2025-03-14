import streamlit as st
import pandas as pd
from .componentsMT import componentsMT
from repositories.custos_media_tensao_repository import CustoMediaTensaoRepository
from repositories.custos_baixa_tensao import CustoBaixaTensaoRepository
from utils.constants import TAX_CONSTANTS
from typing import Dict, Any, Optional , List
from utils.constants import VOLTAGE_DEFAULTS
import streamlit as st
import pandas as pd

from typing import List, Dict
from .componentsBT import ComponenteBT
from ..pagamento_entrega.components import ComponentsPagamentoEntrega
from .calculo_item_bt import (
    buscar_cod_caixa_proj,
    buscar_preco_por_potencia
)


# Abordagem alternativa mais robusta
def calcular_total(df):
    try:
        # Converte para float e soma, tratando valores problemáticos
        valores = pd.to_numeric(df['preco_total'], errors='coerce')
        return valores.fillna(0).sum()
    except Exception as e:
        print(f"Erro ao calcular total: {e}")
        # Retorna valores brutos para debug
        print("Valores na coluna:", df['preco_total'].tolist())
        return 0

def formatar_valor_br(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")




def initialize_item() -> Dict:
    """
    Inicializa um novo item com valores padrão.
    """


    return {
        'ID': None,
        'Produto': "",
        'Descrição': "",
        'Potência': None,
        'Fator K': 1,
        'IP': '00',
        'Preço Unitário': 0.0,
        'Preço Total': 0.0,
        'Quantidade': 1,
        'Tensão Primária': None,
        'Tensão Secundária': None,
        'Material': None,
        'Conector': "Nenhum",
        'Frequencia 50Hz': False,
        'Blindagem Eletrostática': False,
        'Rele': "Nenhum",
        'Sensor PT - 100': 0,
        'Ensaios': {
            'Elev. Temperat.': False,
            'Nível de Ruído': False,
            'Flange': 0
        },
        'cod_caixa': None,
        'cod_proj': None,
        'Derivações': {
            'taps': 'nenhum',
            'tensoes_primarias': 'nenhum'
        },
        'taps_tensoes': None,
        'Taps': None
    }



            

def pagina_configuracao_MT():
    """Página de configuração para itens de Média Tensão"""
    st.subheader("Configuração de Itens - Média Tensão")
    
    # Renderização dos inputs de impostos
    st.session_state['impostos'] = componentsMT.render_tax_inputs(st.session_state['impostos'])
    
    # Renderização dos componentes MT
    with st.expander("Adicionar Novo Item MT", expanded=False):
        df = CustoMediaTensaoRepository().buscar_todos()
        item_index = len(st.session_state['itens']['itens_configurados_mt'])
        item_data = initialize_item()
        percentuais = calcular_percentuais(st.session_state['impostos'])

        componentsMT.render_item_config(item_index, df, item_data)

    ComponentsPagamentoEntrega.inicializar_session_state_itens()
    
    # Renderização do resumo
    

def pagina_configuracao_BT():
    """Página de configuração para itens de Baixa Tensão"""
    st.subheader("Configuração de Itens - Baixa Tensão")
    
    # Renderização dos componentes BT
    with st.expander("Adicionar Novo Item BT", expanded=False):
        ComponenteBT.render_bt_components()
    

def format_bt_values(item):
    """Formata valores numéricos do item BT"""
    numeric_fields = ['preco_unitario', 'preco_total', 'quantidade']
    for field in numeric_fields:
        if field in item:
            item[field] = float(str(item[field]).replace('R$', '').replace('.', '').replace(',', '.').strip())
    return item

def pagina_configuracao():
    """Página principal de configuração de itens"""
    st.title("Configuração de Itens")
    
    
    # Inicializa o session state se necessário
    initialize_session_state()
    
    # Verifica se há um item em edição
    if 'editando_item_mt' in st.session_state:
        item_em_edicao = st.session_state.editando_item_mt
        st.info(f"Editando item MT (ID: {item_em_edicao['index']})")
        # Carrega os dados do item nos campos de configuração
        with st.expander("Editar Item MT", expanded=True):
            df = CustoMediaTensaoRepository().buscar_todos()
            componentsMT.render_item_config(item_em_edicao['index'], df, item_em_edicao['dados'])
            st.session_state['impostos'] = componentsMT.render_tax_inputs(st.session_state['impostos'])
    
    elif 'editando_item_bt' in st.session_state:
        item_em_edicao = st.session_state.editando_item_bt
        st.info(f"Editando item BT (ID: {item_em_edicao['index']})")
        with st.expander("Editar Item BT", expanded=True):
            ComponenteBT.render_bt_components(
                modo_edicao=True,
                item_edicao=item_em_edicao['dados']
            )
            st.session_state['impostos'] = componentsMT.render_tax_inputs(st.session_state['impostos'])
    else:
        # Se não houver item em edição, exibe a interface normal
        n_itens_mt = len(st.session_state['itens']['itens_configurados_mt'])
        n_itens_bt = len(st.session_state['itens']['itens_configurados_bt'])
        n_item_atual = n_itens_mt + n_itens_bt 
        st.subheader(f'Adicionar item {n_item_atual + 1}' )
        
        # Cria as abas para MT e BT
        tab_mt, tab_bt = st.tabs(["Média Tensão Seco", "Baixa Tensão"])
        
        # Conteúdo da aba MT
        with tab_mt:
            pagina_configuracao_MT()
        
        # Conteúdo da aba BT
        with tab_bt:
            pagina_configuracao_BT()
    
    # # Inicializa o session state se necessário
    # initialize_session_state()
    # n_itens_mt = len(st.session_state['itens']['itens_configurados_mt'])
    # n_itens_bt = len(st.session_state['itens']['itens_configurados_bt'])
    # n_item_atual = n_itens_mt + n_itens_bt 
    # st.subheader(f'Adicionar item {n_item_atual + 1}' )
    
        

def calcular_percentuais(impostos: Dict[str, float]) -> float:
    """Calcula os percentuais totais baseados nos impostos"""
    return (
        (impostos['lucro'] / 100) + 
        TAX_CONSTANTS['ICMS_BASE'] + 
        (impostos['comissao'] / 100) + 
        (impostos['frete'] / 100) + 
        TAX_CONSTANTS['IRPJ_CSSL'] + 
        TAX_CONSTANTS['TKXADMMKT'] + 
        TAX_CONSTANTS['MOCUSFIXO'] + 
        TAX_CONSTANTS['PISCONFINS']
    )



def initialize_session_state():
    """Inicializa as variáveis necessárias no session_state"""
    if 'itens' in st.session_state and isinstance(st.session_state['itens'], list):
        # Se for uma lista, remove e recria como dicionário
        del st.session_state['itens']
    
    if 'itens' not in st.session_state:
        st.session_state['itens'] = {
            'itens_configurados_mt': [],
            'itens_configurados_bt': []
        }
    else:
        if 'itens_configurados_mt' not in st.session_state['itens']:
            st.session_state['itens']['itens_configurados_mt'] = []
        if 'itens_configurados_bt' not in st.session_state['itens']:
            st.session_state['itens']['itens_configurados_bt'] = []
    
    if 'impostos' not in st.session_state:
        st.session_state['impostos'] = {
            'lucro': 5.0,
            'icms': 12.0,
            'frete': 4.0,
            'comissao': 5.0,
            'contribuinte_icms': "Sim",
            'difal': 0.0,
            'f_pobreza': 0.0,
            'local_entrega': st.session_state['dados_iniciais'].get('local_frete', ''),
            'tipo_frete': "CIP"
        }
    
    if 'configuracao' not in st.session_state:
        st.session_state['configuracao'] = 'MT'

def validate_initial_data() -> bool:
    """Valida se os dados iniciais necessários estão presentes"""
    dados_iniciais = st.session_state.get('dados_iniciais', {})
    campos_obrigatorios = [
        'cliente', 'nomeCliente', 'fone', 'email', 'bt', 
        'obra', 'dia', 'mes', 'ano', 'rev', 'local'
    ]
    
    for campo in campos_obrigatorios:
        if not dados_iniciais.get(campo):
            return False
    return True

def get_default_voltage_values(classe_tensao: str) -> Dict[str, str]:
    """Retorna os valores padrão de tensão baseados na classe"""
    return VOLTAGE_DEFAULTS.get(classe_tensao, {
        "tensao_primaria": "",
        "derivacoes": "",
        "nbi": "0"
    })

def configuracao_itens_page():
    """Página principal de configuração de itens"""
    st.write(st.session_state)
    # Inicialização do state
    initialize_session_state()

    st.title('Configuração Itens')
    st.markdown("---")
    
    # Validação inicial
    if not validate_initial_data():
        st.error("Por favor, preencha todos os dados iniciais antes de continuar.")
        return
    


    # Carregamento dos dados do banco

    
    # Seção de impostos e taxas
    with st.container():
        st.subheader("Impostos e Taxas")
        st.session_state['impostos'] = componentsMT.render_tax_inputs(st.session_state['impostos'])
    
    st.markdown("---")
    
    # Seção de configuração de itens
    with st.container():
        st.subheader("Configuração dos Itens")
        
        # Input para quantidade de itens
        
        
        # Cálculo dos percentuais
        percentuais = calcular_percentuais(st.session_state['impostos'])
    

def render_impostos(dados_impostos: Dict[str, Any]) -> None:
    """Renderiza os campos de entrada para impostos"""
    st.sidebar.header("Configuração de Impostos")

    # Inicializar impostos no session_state se não existirem
    if 'impostos' not in st.session_state:
        st.session_state['impostos'] = {
            'lucro': dados_impostos.get('lucro', 5.0),
            'icms': dados_impostos.get('icms', 12.0),
            'frete': dados_impostos.get('frete', 4.0),
            'comissao': dados_impostos.get('comissao', 5.0),
            'difal': dados_impostos.get('difal', 0.0),
            'f_pobreza': dados_impostos.get('f_pobreza', 0.0),
            'tipo_frete': dados_impostos.get('tipo_frete', "CIP"),
            'local_frete': dados_impostos.get('local_frete', 'São Paulo/SP')
        }

    # Valores básicos
    st.session_state['impostos']['lucro'] = st.sidebar.number_input('Lucro (%):', 
                        min_value=0.0, 
                        max_value=100.0, 
                        step=0.1, 
                        value=st.session_state['impostos']['lucro'],
                        key='input_lucro')
    
    st.session_state['impostos']['icms'] = st.sidebar.number_input('ICMS (%):', 
                        min_value=0.0, 
                        max_value=100.0, 
                        step=0.1, 
                        value=st.session_state['impostos']['icms'],
                        key='input_icms')
    
    st.session_state['impostos']['comissao'] = st.sidebar.number_input('Comissão (%):', 
                            min_value=0.0, 
                            step=0.1, 
                            value=st.session_state['impostos']['comissao'],
                            key='input_comissao')

    # Callback para atualizar o valor do frete quando o tipo muda
    def on_tipo_frete_change():
        if st.session_state.select_tipo_frete == "FOB":
            st.session_state['impostos']['frete'] = 0.0
            st.session_state['impostos']['tipo_frete'] = "FOB"
        else:
            st.session_state['impostos']['tipo_frete'] = "CIP"

    # Usar session_state para manter o tipo de frete
    tipo_frete = st.sidebar.selectbox(
        'Tipo de Frete:', 
        ["FOB","CIP"],
        key='select_tipo_frete',
        on_change=on_tipo_frete_change,
        index=0 if st.session_state['impostos']['tipo_frete'] == "FOB" else 1
    )
    
    # Adicionar o selectbox de local_frete logo abaixo do tipo_frete
    local_frete = st.sidebar.selectbox(
        'Local Frete:',
        st.session_state['cidades'],
        index=st.session_state['cidades'].index(st.session_state['dados_iniciais']['local_frete']) 
        if st.session_state['dados_iniciais']['local_frete'] in st.session_state['cidades'] 
        else 3829,
        key='select_local_frete'
    )
    
    # Atualizar o valor no session_state
    st.session_state['impostos']['local_frete'] = local_frete
    # Também atualizar o valor nos dados_iniciais para consistência
    st.session_state['dados_iniciais']['local_frete'] = local_frete

    # Input do frete
    st.session_state['impostos']['frete'] = st.sidebar.number_input(
        'Frete (%):', 
        min_value=0.0, 
        step=0.1, 
        value=st.session_state['impostos']['frete'],
        key='input_frete',
        disabled=tipo_frete=="FOB"
    )

    contribuinte_icms = st.sidebar.radio(
        "O cliente é contribuinte do ICMS?",
        options=["Sim", "Não"],
        index=0 if dados_impostos.get('contribuinte_icms') != "Não" else 1,
        key='radio_contribuinte'
    )

    st.session_state['impostos']['contribuinte_icms'] = contribuinte_icms
    
    # Campos condicionais baseados na escolha do contribuinte
    if contribuinte_icms == "Não":
        st.session_state['impostos']['difal'] = st.sidebar.number_input('DIFAL (%):', 
                            min_value=0.0, 
                            value=st.session_state['impostos']['difal'],
                            step=0.1,
                            key='input_difal')
        
        st.session_state['impostos']['f_pobreza'] = st.sidebar.number_input('F. Pobreza (%):', 
                                min_value=0.0,
                                value=st.session_state['impostos']['f_pobreza'],
                                step=0.1,
                                key='input_f_pobreza')
    else:
        st.session_state['impostos']['difal'] = 0.0
        st.session_state['impostos']['f_pobreza'] = 0.0
