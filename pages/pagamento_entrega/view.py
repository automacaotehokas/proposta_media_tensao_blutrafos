import streamlit as st
from typing import Dict
from .components import ComponentsPagamentoEntrega

def pagina_configuracao_eventos():
    # Inicialização do session state
    ComponentsPagamentoEntrega.inicializar_session_state()
    st.markdown("---")
    
    # Verifica quais produtos estão configurados
    produtos_configurados = ComponentsPagamentoEntrega.carregar_tipo_produto(st.session_state.get('itens', {}))

    # Seção de Configuração de Eventos de Pagamento e Prazos
    st.header("Configuração de Prazos de entrega")

    # Prazos Gerais
    if produtos_configurados['mt'] or produtos_configurados['bt']:
        st.subheader("Prazos Gerais")
        col1, col2 = st.columns(2)
        
        with col1:
            prazo_desenho = st.number_input(
                "Prazo de desenho (em dias):",
                min_value=0,
                value=st.session_state['prazo_entrega'].get('prazo_desenho', 0),
                key="prazo_desenho_geral"
            )
            st.session_state['prazo_entrega']['prazo_desenho'] = prazo_desenho
        
        with col2:
            prazo_cliente = st.number_input(
                "Prazo de cliente (em dias):",
                min_value=0,
                value=st.session_state['prazo_entrega'].get('prazo_cliente', 0),
                key="prazo_cliente_geral"
            )
            st.session_state['prazo_entrega']['prazo_cliente'] = prazo_cliente

        st.subheader("Prazos por Produto")

        # Prazo MT
        if produtos_configurados['mt']:
            with st.expander("Prazo de Entrega para Transformador de Média Tensão"):
                ComponentsPagamentoEntrega.configurar_prazo_entrega('mt')

        # Prazo BT
        if produtos_configurados['bt']:
            with st.expander("Prazo de Entrega para Transformador de Baixa Tensão"):
                ComponentsPagamentoEntrega.configurar_prazo_entrega('bt')

        st.markdown("---")
        st.header("Configurações de eventos de pagamento")

        # Transformador de Média Tensão
        if produtos_configurados['mt']:
            with st.expander("Configurar eventos de pagamento para Transformador de Média Tensão"):
                ComponentsPagamentoEntrega.configurar_eventos_pagamento('mt')

        # Transformador de Baixa Tensão
        if produtos_configurados['bt']:
            with st.expander("Configurar eventos de pagamento para Transformador de Baixa Tensão"):
                ComponentsPagamentoEntrega.configurar_eventos_pagamento('bt')

        st.markdown("---")
        st.header('Configuração de Desvios')
        ComponentsPagamentoEntrega.criar_input_desvios()
    else:
        st.warning("Nenhum item configurado encontrado. Configure os itens primeiro.")

if __name__ == "__main__":
    pagina_configuracao_eventos()