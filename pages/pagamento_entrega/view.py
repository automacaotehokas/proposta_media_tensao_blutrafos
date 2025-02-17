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
        # Prazo MT
        if produtos_configurados['mt'] or  produtos_configurados['bt']:
            with st.expander("Prazo de Entrega para Transformadores"):
                ComponentsPagamentoEntrega.configurar_prazo_entrega()

        st.markdown("---")
        st.header("Configurações de eventos de pagamento")
        # Transformador de Média Tensão
        if produtos_configurados:
            with st.expander("Configurar eventos de pagamento para o(s) Transformador(es)"):
                ComponentsPagamentoEntrega.configurar_eventos_pagamento()

        st.markdown("---")
        st.header('Configuração de Desvios')
        ComponentsPagamentoEntrega.criar_input_desvios()

    else:
        st.warning("Nenhum item configurado encontrado. Configure os itens primeiro.")

if __name__ == "__main__":
    pagina_configuracao_eventos()