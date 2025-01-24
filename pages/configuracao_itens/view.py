import streamlit as st
import pandas as pd
from .components import render_tax_inputs, render_item_config
from repositories.custos_media_tensao_repository import CustoMediaTensaoRepository
from utils.constants import TAX_CONSTANTS
from typing import Dict, Any, Optional , List
from utils.constants import VOLTAGE_DEFAULTS

# Abordagem alternativa mais robusta
def calcular_total(df):
    try:
        # Converte para float e soma, tratando valores problemáticos
        valores = pd.to_numeric(df['Preço Total'], errors='coerce')
        return valores.fillna(0).sum()
    except Exception as e:
        print(f"Erro ao calcular total: {e}")
        # Retorna valores brutos para debug
        print("Valores na coluna:", df['Preço Total'].tolist())
        return 0

def formatar_valor_br(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")




def pagina_configuracao():
    st.title('Configuração Itens')
    st.markdown("---")
    
    # Inicialização do state
    if 'itens_configurados' not in st.session_state:
        st.session_state['itens_configurados'] = []
    
    if 'impostos' not in st.session_state:
        st.session_state['impostos'] = {}
    
    # Carregamento dos dados
    df = CustoMediaTensaoRepository.buscar_todos()
    
    # Renderização dos inputs de impostos
    st.session_state['impostos'] = render_tax_inputs(st.session_state['impostos'])
    
    # Configuração da quantidade de itens
    quantidade_itens = st.number_input(
        'Quantidade de Itens:', 
        min_value=1, 
        step=1, 
        value=len(st.session_state['itens_configurados']) or 1
    )
    
    # Atualização da lista de itens
    while len(st.session_state['itens_configurados']) < quantidade_itens:
        st.session_state['itens_configurados'].append({
            'Item': len(st.session_state['itens_configurados']) + 1,
            'Quantidade': 1,
            'Descrição': "",
            'Fator K': 1,
            'IP': '00',
            'Tensão Primária': "380",
            'Tensão Secundária': "220",
            'Preço Unitário': 0.0,
            'Preço Total': 0.0
        })
    
    while len(st.session_state['itens_configurados']) > quantidade_itens:
        st.session_state['itens_configurados'].pop()
    
    # Renderização dos itens
    for i in range(len(st.session_state['itens_configurados'])):
        st.session_state['itens_configurados'][i] = render_item_config(
            i, 
            df, 
            st.session_state['itens_configurados'][i],
            calcular_percentuais(st.session_state['impostos'])
        )
    
    # Renderização do resumo
    render_summary(st.session_state['itens_configurados'])

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

def render_summary(itens: List[Dict[str, Any]]):
    """Renderiza o resumo dos itens configurados"""
    st.subheader("Resumo dos Itens Selecionados")
    
    if not itens:
        st.warning("Nenhum item configurado.")
        return
    
    # Mantém um DataFrame original para cálculos
    resumo_df = pd.DataFrame(itens)
    
    # Cria uma cópia para formatação e display
    display_df = resumo_df.copy()
    
    # Formatação das colunas monetárias para display
    if 'Preço Unitário' in display_df.columns:
        display_df['Preço Unitário'] = display_df['Preço Unitário'].apply(formatar_valor_br)
    
    if 'Preço Total' in display_df.columns:
        display_df['Preço Total'] = display_df['Preço Total'].apply(formatar_valor_br)
    
    # Verificação e formatação da potência
    if 'Potência' in display_df.columns:
        display_df['Potência'] = display_df['Potência'].apply(
            lambda x: f"{x:,.0f} kVA" if pd.notnull(x) else ""
        )
    else:
        display_df['Potência'] = ""
    
    # Verificação e concatenação das tensões
    if 'Tensão Primária' in display_df.columns and 'Tensão Secundária' in display_df.columns:
        display_df['Tensões'] = display_df['Tensão Primária'].astype(str) + "kV" + " / " + display_df['Tensão Secundária'].astype(str) + " V"
    else:
        display_df['Tensões'] = ""
    
    # Seleção e ordenação das colunas para exibição
    colunas_resumo = [
        'Item', 'Quantidade', 'Potência', 'Tensões', 
        'Perdas', 'Fator K', 'IP', 'Preço Unitário', 'Preço Total'
    ]
    
    # Filtragem das colunas existentes no DataFrame
    colunas_existentes = [col for col in colunas_resumo if col in display_df.columns]
    
    # Exibição da tabela resumo
    st.table(display_df[colunas_existentes])
    
    # Cálculo e exibição do total usando o DataFrame original
    if 'Preço Total' in resumo_df.columns:
        total_fornecimento = calcular_total(resumo_df)
        st.subheader(f"Valor Total do Fornecimento: {formatar_valor_br(total_fornecimento)}")
    
    # Armazenamento do resumo no session_state para uso posterior
    st.session_state['resumo_df'] = resumo_df

def initialize_session_state():
    """Inicializa as variáveis necessárias no session_state"""
    if 'itens_configurados' not in st.session_state:
        st.session_state['itens_configurados'] = []
    
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
    try:
        df = CustoMediaTensaoRepository.buscar_todos()
    except Exception as e:
        st.error(f"Erro ao carregar dados do banco: {str(e)}")
        return
    
    # Seção de impostos e taxas
    with st.container():
        st.subheader("Impostos e Taxas")
        st.session_state['impostos'] = render_tax_inputs(st.session_state['impostos'])
    
    st.markdown("---")
    
    # Seção de configuração de itens
    with st.container():
        st.subheader("Configuração dos Itens")
        
        # Input para quantidade de itens
        quantidade_itens = st.number_input(
            'Quantidade de Itens:', 
            min_value=1, 
            step=1, 
            value=len(st.session_state['itens_configurados']) or 1
        )
        
        # Atualização da lista de itens
        update_items_list(quantidade_itens)
        
        # Cálculo dos percentuais
        percentuais = calcular_percentuais(st.session_state['impostos'])
        
        # Renderização de cada item
        for i in range(len(st.session_state['itens_configurados'])):
            with st.container():
                st.session_state['itens_configurados'][i] = render_item_config(
                    i, df, st.session_state['itens_configurados'][i], percentuais
                )
                st.markdown("---")
     
    
    # Seção de resumo
    with st.container():
        render_summary(st.session_state['itens_configurados'])

def update_items_list(quantidade_itens: int):
    """Atualiza a lista de itens baseado na quantidade desejada"""
    while len(st.session_state['itens_configurados']) < quantidade_itens:
        st.session_state['itens_configurados'].append({
            'Item': len(st.session_state['itens_configurados']) + 1,
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
    
    while len(st.session_state['itens_configurados']) > quantidade_itens:
        st.session_state['itens_configurados'].pop()

