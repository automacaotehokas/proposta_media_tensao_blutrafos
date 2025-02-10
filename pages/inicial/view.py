import streamlit as st
from datetime import datetime
from .api import buscar_cidades
from .utils import aplicar_mascara_telefone, get_meses_pt


def carregar_cidades():
    """Carrega e armazena a lista de cidades no session_state"""
    if 'cidades' not in st.session_state:
        st.session_state['cidades'] = buscar_cidades()


def configurar_informacoes():
    """Renderiza e configura a página de informações iniciais"""
    st.title('Dados Iniciais')
    st.markdown("---")
    # Configuração da data
    data_hoje = datetime.today()
    data_selecionada = st.date_input('Data da Proposta:', value=data_hoje)
    meses_pt = get_meses_pt()
    
    # Atualização da data no session_state
    st.session_state['dados_iniciais'].update({
        'dia': data_selecionada.strftime('%d'),
        'mes': meses_pt[data_selecionada.month],
        'ano': data_selecionada.strftime('%Y'),
    })

    # Layout em duas colunas
    col1, col2 = st.columns(2)

    with col1:
        _render_left_column()

    with col2:
        _render_right_column()

def _render_left_column():
    """Renderiza a coluna esquerda do formulário"""
    st.session_state['dados_iniciais'].update({
        'bt': st.text_input('Nº BT:', 
                           st.session_state['dados_iniciais'].get('bt', ''), 
                           autocomplete='off'),
        'rev': st.text_input('Rev:', 
                            st.session_state['dados_iniciais'].get('rev', ''), 
                            autocomplete='off'),
        'cliente': st.text_input('Cliente:', 
                                st.session_state['dados_iniciais'].get('cliente', ''), 
                                autocomplete='off', 
                                placeholder='Digite o nome da empresa'),
        'obra': st.text_input('Obra:', 
                             st.session_state['dados_iniciais'].get('obra', ''), 
                             autocomplete='off'),
    })

def _render_right_column():
    """Renderiza a coluna direita do formulário"""
    st.session_state['dados_iniciais'].update({
        'nomeCliente': st.text_input('Nome do Contato:', 
                                    st.session_state['dados_iniciais'].get('nomeCliente', ''), 
                                    autocomplete='off', 
                                    placeholder='Digite o nome do contato dentro da empresa'),
        'email': st.text_input('E-mail do Contato:', 
                              st.session_state['dados_iniciais'].get('email', ''), 
                              autocomplete='off'),
    })

    # Local Frete
    local_frete = st.selectbox(
        'Local Frete:',
        st.session_state['cidades'],
        index=st.session_state['cidades'].index(st.session_state['dados_iniciais']['local_frete']) 
        if st.session_state['dados_iniciais']['local_frete'] in st.session_state['cidades'] 
        else 3829
    )
    st.session_state['dados_iniciais']['local_frete'] = local_frete

    # Telefone com máscara
    st.text_input(
        'Telefone do Contato:', 
        value=st.session_state['dados_iniciais'].get('fone', ''), 
        max_chars=15, 
        autocomplete='off', 
        key='fone_raw', 
        on_change=lambda: _atualizar_telefone(),
        placeholder="Digite sem formação, exemplo: 47999998888"
    )

def _atualizar_telefone():
    """Atualiza o telefone no session_state aplicando a máscara"""
    telefone = st.session_state['fone_raw']
    st.session_state['dados_iniciais']['fone'] = aplicar_mascara_telefone(telefone)


def pagina_inicial():
    configurar_informacoes()
    st.write(st.session_state)

