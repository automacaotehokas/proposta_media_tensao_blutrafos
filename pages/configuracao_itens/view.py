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
from .calculo_item_bt import (
    buscar_cod_caixa_proj,
    buscar_preco_por_potencia,
    calcular_percentuais
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


def exibir_resumo_resultados(itens, tipo='MT'):
    """
    Exibe o resumo dos itens calculados em formato de tabela.
    """
    st.markdown("---")
    st.subheader(f"Resumo dos Itens {tipo} Configurados")
    
    # Cria DataFrame para exibição
    resumo_data = []
    for idx, item in enumerate(itens, 1):
        resumo_data.append({
            'Item': idx,
            'Quantidade': item['Quantidade'],
            'Produto': item['Produto'],
            'Potência': item.get('Potência ', ''),
            'Fator K': item['Fator K'],
            'Tensões': f"{item['Tensão Primária']} V / {item['Tensão Secundária']} V",
            'IP': item['IP'],
            'Preço Unitário': f"R$ {item['Preço Unitário']:,.2f}",
            'Preço Total': f"R$ {item['Preço Total']:,.2f}",
            'IPI': '0%'
        })

    df_resumo = pd.DataFrame(resumo_data)
    st.table(df_resumo)

    # Exibe o valor total
    total = sum(item['Preço Total'] for item in itens)
    st.subheader(f"Valor Total do Fornecimento {tipo}: R$ {total:,.2f}")

def carregar_tensoes_padrao(item: Dict, df: pd.DataFrame, index: int):
    """
    Carrega as tensões padrão para um item se necessário.
    """
    if item['Produto'] == "ATT" and (item.get('Tensão Primária') != 380 or item.get('Tensão Secundária') != 220):
        st.warning(f"As tensões padrão (380V e 220V) não serão carregadas para o Item {index + 1}.")
    else:
        if item['Descrição']:
            descricao_selecionada = df[df['descricao'] == item['Descrição']].iloc[0]
            item['Tensão Primária'] = descricao_selecionada['tensao_primaria']
            item['Tensão Secundária'] = descricao_selecionada['tensao_secundaria']
            st.success(f"Tensões carregadas para o Item {index + 1}!")

            

def pagina_configuracao_MT():
    """Página de configuração para itens de Média Tensão"""
    st.subheader("Configuração de Itens - Média Tensão")
    
    # Renderização dos inputs de impostos
    st.session_state['impostos'] = componentsMT.render_tax_inputs(st.session_state['impostos'])
    
    # Renderização dos componentes MT
    with st.expander("Adicionar Novo Item MT", expanded=True):
        df = CustoMediaTensaoRepository().buscar_todos()
        item_index = len(st.session_state['itens_configurados_mt'])
        item_data = initialize_item()
        percentuais = calcular_percentuais(st.session_state['impostos'])
        componentsMT.render_item_config(item_index, df, item_data, percentuais)
    
    # Renderização do resumo
    

def pagina_configuracao_BT():
    """Página de configuração para itens de Baixa Tensão"""
    st.subheader("Configuração de Itens - Baixa Tensão")
    
    # Renderização dos componentes BT
    with st.expander("Adicionar Novo Item BT", expanded=True):
        ComponenteBT.render_bt_components()
    
    # Exibe o resumo dos resultados automaticamente se houver itens calculados

def pagina_configuracao():
    """Página principal de configuração de itens"""
    st.title("Configuração de Itens")
    
    # Inicializa o session state se necessário
    initialize_session_state()
    
    # Cria as abas para MT e BT
    tab_mt, tab_bt = st.tabs(["Média Tensão", "Baixa Tensão"])
    
    # Conteúdo da aba MT
    with tab_mt:
        pagina_configuracao_MT()
    
    # Conteúdo da aba BT
    with tab_bt:
        pagina_configuracao_BT()
    
        

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
    if 'itens_configurados_mt' not in st.session_state:
        st.session_state['itens_configurados_mt'] = []
    
    if 'itens_configurados_bt' not in st.session_state:
        st.session_state['itens_configurados_bt'] = []
    
    if 'impostos' not in st.session_state:
        st.session_state['impostos'] = {
            'lucro': 5.0,
            'icms': 12.0,
            'frete': 0.0,
            'comissao': 5.0,
            'contribuinte_icms': "Sim",
            'difal': 0.0,
            'f_pobreza': 0.0,
            'local_entrega': st.session_state['dados_iniciais'].get('local_frete', ''),
            'tipo_frete': "CIF"
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
    st.title('Configuração Itens')
    st.markdown("---")
    
    # Validação inicial
    if not validate_initial_data():
        st.error("Por favor, preencha todos os dados iniciais antes de continuar.")
        return
    
    # Inicialização do state
    initialize_session_state()
    
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
    


def update_items_list(quantidade_itens: int):
    """Atualiza a lista de itens baseado na quantidade desejada"""
    while len(st.session_state['itens_configurados_mt']) < quantidade_itens:
        st.session_state['itens_configurados_mt'].append({
            'Item': len(st.session_state['itens_configurados_mt']) + 1,
            'Quantidade': 1,
            'Descrição': "",
            'Potência': None,
            'Tensão Primária': None,
            'Tensão Secundária': "380",
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
    
    while len(st.session_state['itens_configurados_mt']) > quantidade_itens:
        st.session_state['itens_configurados_mt'].pop()


    