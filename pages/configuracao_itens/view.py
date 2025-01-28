import streamlit as st
import pandas as pd
from .componentsMT import render_tax_inputs, render_item_config
from repositories.custos_media_tensao_repository import CustoMediaTensaoRepository
from repositories.custos_baixa_tensao import CustoBaixaTensaoRepository
from utils.constants import TAX_CONSTANTS
from typing import Dict, Any, Optional , List
from utils.constants import VOLTAGE_DEFAULTS
import streamlit as st
import pandas as pd
from typing import List, Dict
from componentsBT import (
    render_item_description,
    render_item_specifications,
    render_item_accessories
)
from calculo_item_bt import (
    buscar_cod_caixa_proj,
    buscar_preco_por_potencia,
    calcular_percentuais
)

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

def exibir_resumo_resultados():
    """
    Exibe o resumo dos itens calculados em formato de tabela.
    """
    st.markdown("---")
    st.subheader("Resumo dos Itens Configurados")
    
    # Cria DataFrame para exibição
    resumo_data = []
    for idx, item in enumerate(st.session_state['itens_configurados'], 1):
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
    total = sum(item['Preço Total'] for item in st.session_state['itens_configurados'])
    st.subheader(f"Valor Total do Fornecimento: R$ {total:,.2f}")

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

def pagina_configuracao_BT():
    """
    Renderiza a página de configuração de transformadores de baixa tensão com cálculos automáticos.
    Os cálculos são realizados à medida que os valores são inseridos, eliminando a necessidade
    de um botão específico para calcular.
    """
    st.title("Configuração de Transformadores de Baixa Tensão")

    # Inicialização do session state para itens
    if 'itens_configurados' not in st.session_state:
        st.session_state['itens_configurados'] = []

    # Carregamento dos dados
    df = CustoBaixaTensaoRepository.buscar_todos()

    # Input para quantidade de itens
    quantidade_itens = st.number_input(
        'Quantidade de Itens:',
        min_value=1,
        step=1,
        value=len(st.session_state['itens_configurados']) or 1
    )

    # Ajusta a lista de itens conforme a quantidade
    while len(st.session_state['itens_configurados']) < quantidade_itens:
        st.session_state['itens_configurados'].append(initialize_item())

    # Renderiza cada item e calcula automaticamente
    for index, item in enumerate(st.session_state['itens_configurados']):
        st.subheader(f"Item {index + 1}")
        
        # Renderiza os componentes do item
        item = render_item_description(index, item, df)
        item = render_item_specifications(index, item)
        item = render_item_accessories(index, item)

        # Realiza os cálculos automaticamente se tivermos todas as informações necessárias
        if item['Material'] and item['Descrição']:
            percentuais = calcular_percentuais()
            
            # Verifica e carrega tensões se necessário
            if not item['Tensão Primária'] or not item['Tensão Secundária']:
                carregar_tensoes_padrao(item, df, index)

            # Calcula os preços
            codigos = buscar_cod_caixa_proj(df, item['ID'])
            item['cod_caixa'] = codigos['cod_caixa']
            item['cod_proj'] = codigos['proj']
            
            item['Preço Base'] = buscar_preco_por_potencia(
                df,
                item['Potência'],
                item['Produto'],
                item['IP'],
                item['Tensão Primária'],
                item['Tensão Secundária'],
                item['Material'],
                item
            )
            
            item['Preço Unitário'] = int(item['Preço Base']) / (1 - percentuais)
            item['Preço Total'] = item['Quantidade'] * item['Preço Unitário']

            # Exibe os valores calculados para este item
            with st.expander(f"Valores calculados para Item {index + 1}", expanded=False):
                st.write(f"Preço Base: R$ {item['Preço Base']:,.2f}")
                st.write(f"Preço Unitário: R$ {item['Preço Unitário']:,.2f}")
                st.write(f"Preço Total: R$ {item['Preço Total']:,.2f}")

        # Botão para excluir item
        if st.button(f"Excluir Item {index + 1}"):
            del st.session_state['itens_configurados'][index]
            st.rerun()

        st.markdown("---")

    # Exibe o resumo dos resultados automaticamente se houver itens calculados
    if any(item.get('Preço Total', 0) > 0 for item in st.session_state['itens_configurados']):
        exibir_resumo_resultados()

def pagina_configuracao():
    checkbox_type = st.session_state['configuracao']
    if checkbox_type not in st.session_state:
        st.session_state[checkbox_type] = 'MT'

    st.checkbox("Opções de itens: ", ['MT', 'BT', 'BT-MT'], key='opcoes_itens' , index = ['MT', 'BT', 'BT-MT'].index )
    if st.session_state['opcoes_itens'] == 'MT':
        pagina_configuracao_MT()
    elif st.session_state['configuracao'] == 'BT':
        pagina_configuracao_BT()
    elif st.session_state['opcoes_itens'] == 'BT-MT':
        pagina_configuracao_MT()
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

def render_summary(itens: List[Dict[str, Any]]):
    """Renderiza o resumo dos itens configurados"""
    st.subheader("Resumo dos Itens Selecionados")
    
    if not itens:
        st.warning("Nenhum item configurado.")
        return
    
    resumo_df = pd.DataFrame(itens)
    
    # Verificação e formatação da potência
    if 'Potência' in resumo_df.columns:
        resumo_df['Potência'] = resumo_df['Potência'].apply(
            lambda x: f"{x:,.0f} kVA" if pd.notnull(x) else ""
        )
    else:
        resumo_df['Potência'] = ""
    
    # Verificação e concatenação das tensões
    if 'Tensão Primária' in resumo_df.columns and 'Tensão Secundária' in resumo_df.columns:
        resumo_df['Tensões'] = resumo_df['Tensão Primária'].astype(str) + "kV" + " / " + resumo_df['Tensão Secundária'].astype(str) + " V"
    else:
        resumo_df['Tensões'] = ""
    
    # Seleção e ordenação das colunas para exibição
    colunas_resumo = [
        'Item', 'Quantidade', 'Potência', 'Tensões', 
        'Perdas', 'Fator K', 'IP', 'Preço Unitário', 'Preço Total'
    ]
    
    # Filtragem das colunas existentes no DataFrame
    colunas_existentes = [col for col in colunas_resumo if col in resumo_df.columns]
    
    # Exibição da tabela resumo
    st.table(resumo_df[colunas_existentes])
    
    # Cálculo e exibição do total
    if 'Preço Total' in resumo_df.columns:
        total_fornecimento = resumo_df['Preço Total'].sum()
        st.subheader(f"Valor Total do Fornecimento: R$ {total_fornecimento:,.2f}")
    
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

