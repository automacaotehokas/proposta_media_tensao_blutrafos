import streamlit as st
from typing import Dict, List
import streamlit as st
import pandas as pd

class ComponentsPagamentoEntrega:
    EVENTOS_PADRAO = [
        "Pedido",
        "Faturamento (Mediante aprovação financeira)",
        "Contra aviso de pronto p/ embarque",
        "Aprovação dos Desenhos",
        "TAF",
        "Entrega do Equipamento"
    ]

    EVENTOS_PREDEFINIDOS = [
        {"percentual": 40, "dias": 0, "evento": "Aprovação dos Desenhos"},
        {"percentual": 30, "dias": 0, "evento": "Contra aviso de pronto p/ embarque"},
        {"percentual": 30, "dias": 28, "evento": "Faturamento (Mediante aprovação financeira)"}
    ]



    EVENTOS_PREDEFINIDOS_BT = [
        {"percentual": 50, "dias": 0, "evento": "Aprovação dos Desenhos"},
        {"percentual": 50, "dias": 28, "evento": "Contra aviso de pronto p/ embarque"},
    ]


# Em components.py, adicione/modifique:
    @staticmethod
    def carregar_tipo_produto(dados: Dict) -> Dict:
        """Carrega os tipos de produtos baseado nos dados dos itens"""
        produtos = {
            'mt': False,
            'bt': False
        }
        
        # Verifica MT
        if dados.get('itens_configurados_mt'):
            for item in dados['itens_configurados_mt']:
                if item.get('Descrição'):
                    produtos['mt'] = True
                    break
        
        # Verifica BT
        if dados.get('itens_configurados_bt'):
            for item in dados['itens_configurados_bt']:
                if item.get('descricao'):
                    produtos['bt'] = True
                    break
        
        return produtos
    @staticmethod
    def criar_input_desvios():
        """
        Cria um sistema de input para desvios com tabela dinâmica.
        Permite adicionar e remover desvios conforme necessário.
        """
        # Inicializa a lista de desvios no session_state se não existir
        if 'desvios' not in st.session_state:
            st.session_state['desvios'] = []
        
        # Inicializa o estado para controlar a limpeza do input
        if 'limpar_desvio' not in st.session_state:
            st.session_state['limpar_desvio'] = False
        
        # Define o valor padrão do input baseado no estado
        valor_padrao = "" if st.session_state['limpar_desvio'] else st.session_state.get('ultimo_desvio', "")
        
        # Container para o input e botão
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Campo de texto para o desvio
            novo_desvio = st.text_input(
                "Digite o desvio:",
                value=valor_padrao,
                key="input_desvio",
                placeholder="Descreva o desvio aqui..."
            )
        
        with col2:
            # Botão para adicionar o desvio
            if st.button("Adicionar Desvio", key="btn_add_desvio"):
                if novo_desvio.strip():  # Verifica se o texto não está vazio
                    # Adiciona o novo desvio à lista com um ID único
                    novo_id = len(st.session_state['desvios'])
                    st.session_state['desvios'].append({
                        'id': novo_id,
                        'texto': novo_desvio
                    })
                    # Marca para limpar o campo no próximo rerun
                    st.session_state['limpar_desvio'] = True
                    st.rerun()
        
        # Reset do estado de limpeza após o rerun
        if st.session_state['limpar_desvio']:
            st.session_state['limpar_desvio'] = False
        
        # Se existem desvios, mostra a tabela
        if st.session_state['desvios']:
            st.write("Desvios cadastrados:")
            
            # Cria uma tabela para mostrar os desvios
            for desvio in st.session_state['desvios']:
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    # Mostra o texto do desvio
                    st.text(desvio['texto'])
                
                with col2:
                    # Botão para excluir o desvio
                    if st.button("Excluir", key=f"excluir_{desvio['id']}"):
                        # Remove o desvio da lista
                        st.session_state['desvios'] = [
                            d for d in st.session_state['desvios'] 
                            if d['id'] != desvio['id']
                        ]
                        st.rerun()



    @staticmethod
    def inicializar_session_state():
        """Inicializa todas as variáveis necessárias no session_state"""
        
        # Inicialização do estado para prazo de fabricação com texto padrão
        if 'prazo_entrega_global' not in st.session_state:
            st.session_state['prazo_entrega_global'] = {
                'prazo_fabricacao': "**Transformadores**: Até 60 dias contados a partir da data da aprovação definitiva dos desenhos + transporte."
            }

        
        if 'eventos_pagamento' not in st.session_state:
            st.session_state['eventos_pagamento'] = {}
            
        if 'prazo_entrega' not in st.session_state:
            st.session_state['prazo_entrega'] = {
                'prazo_desenho': 5,
                'prazo_cliente': 2,
                'prazo': {}
            }
        
        # Inicializa eventos MT e BT se não existirem
        if 'eventos_pagamento' not in st.session_state:
            st.session_state['eventos_pagamento'] = ComponentsPagamentoEntrega.EVENTOS_PREDEFINIDOS.copy()
        

        # Inicializa os checkboxes "A combinar"
        if 'a_combinar' not in st.session_state:
            st.session_state['a_combinar'] = False


    @staticmethod
    def inicializar_session_state_itens():
        """Inicializa todas as variáveis necessárias no session_state"""

        produtos = ComponentsPagamentoEntrega.carregar_tipo_produto(st.session_state['itens'])
        # Garantir que a lista de eventos existe e está inicializada
        if 'eventos_pagamento' not in st.session_state:
            # Se tiver apenas BT, usa os eventos predefinidos de BT
            if produtos['bt'] and not produtos['mt']:
                st.session_state['eventos_pagamento'] = ComponentsPagamentoEntrega.EVENTOS_PREDEFINIDOS_BT.copy()
            # Se tiver MT ou ambos, usa os eventos predefinidos padrão (MT)
            else:
                st.session_state['eventos_pagamento'] = ComponentsPagamentoEntrega.EVENTOS_PREDEFINIDOS.copy()
        # Se a lista estiver vazia, inicializa com os eventos predefinidos
        if len(st.session_state['eventos_pagamento']) == 0:
            if produtos['bt'] and not produtos['mt']:
                st.session_state['eventos_pagamento'] = ComponentsPagamentoEntrega.EVENTOS_PREDEFINIDOS_BT.copy()
            else:
                st.session_state['eventos_pagamento'] = ComponentsPagamentoEntrega.EVENTOS_PREDEFINIDOS.copy()

        
        # Garantir que a flag a_combinar existe
        if 'a_combinar_pagamento' not in st.session_state:
            st.session_state['a_combinar_pagamento'] = False
    
        
        
        # Inicialização do estado para prazo de fabricação com texto padrão
        if 'prazo_entrega_global' not in st.session_state:
            st.session_state['prazo_entrega_global'] = {
                'prazo_fabricacao': "**Transformadores**: Até 60 dias contados a partir da data da aprovação definitiva dos desenhos + transporte."
            }

        
        if 'eventos_pagamento' not in st.session_state:
            st.session_state['eventos_pagamento'] = {}
            
        if 'prazo_entrega' not in st.session_state:
            st.session_state['prazo_entrega'] = {
                'prazo_desenho': 5,
                'prazo_cliente': 2,
                'prazo': {}
            }
        
        # Inicializa eventos MT e BT se não existirem
        if 'eventos_pagamento' not in st.session_state:
            st.session_state['eventos_pagamento'] = ComponentsPagamentoEntrega.EVENTOS_PREDEFINIDOS.copy()
        

        # Inicializa os checkboxes "A combinar"
        if 'a_combinar' not in st.session_state:
            st.session_state['a_combinar'] = False


                


    @staticmethod
    def configurar_eventos_pagamento():
        """
        Configura eventos de pagamento de forma unificada para todos os produtos.
        """
        produtos = ComponentsPagamentoEntrega.carregar_tipo_produto(st.session_state['itens'])
        # Garantir que a lista de eventos existe e está inicializada
        if 'eventos_pagamento' not in st.session_state:
            # Se tiver apenas BT, usa os eventos predefinidos de BT
            if produtos['bt'] and not produtos['mt']:
                st.session_state['eventos_pagamento'] = ComponentsPagamentoEntrega.EVENTOS_PREDEFINIDOS_BT.copy()
            # Se tiver MT ou ambos, usa os eventos predefinidos padrão (MT)
            else:
                st.session_state['eventos_pagamento'] = ComponentsPagamentoEntrega.EVENTOS_PREDEFINIDOS.copy()
        # Se a lista estiver vazia, inicializa com os eventos predefinidos
        if len(st.session_state['eventos_pagamento']) == 0:
            if produtos['bt'] and not produtos['mt']:
                st.session_state['eventos_pagamento'] = ComponentsPagamentoEntrega.EVENTOS_PREDEFINIDOS_BT.copy()
            else:
                st.session_state['eventos_pagamento'] = ComponentsPagamentoEntrega.EVENTOS_PREDEFINIDOS.copy()

        
        # Garantir que a flag a_combinar existe
        if 'a_combinar_pagamento' not in st.session_state:
            st.session_state['a_combinar_pagamento'] = False
        
        a_combinar = st.checkbox(
            "A combinar",
            key='a_combinar_pagamento'
        )
        
        if not a_combinar:
            # Criar um botão de adicionar evento no início
            if st.button("Adicionar Evento"):
                # Criar uma cópia da lista atual
                eventos_atuais = list(st.session_state['eventos_pagamento'])
                # Adicionar novo evento à cópia
                eventos_atuais.append({
                    "percentual": 0,
                    "dias": 0,
                    "evento": ComponentsPagamentoEntrega.EVENTOS_PADRAO[0]
                })
                # Atualizar a lista no session_state
                st.session_state['eventos_pagamento'] = eventos_atuais
                st.rerun()
            
            # Mostrar os eventos existentes
            for i, evento in enumerate(st.session_state['eventos_pagamento']):
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                
                with col1:
                    evento["percentual"] = st.number_input(
                        f"Percentual do evento {i+1}",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(evento["percentual"]),
                        key=f"percentual_evento_{i}"
                    )
                
                with col2:
                    evento["dias"] = st.text_input(
                        f"Dias do evento {i+1}",
                        value=evento["dias"],
                        key=f"dias_evento_{i}"
                    )
                
                with col3:
                    evento["evento"] = st.selectbox(
                        f"Evento base {i+1}",
                        ComponentsPagamentoEntrega.EVENTOS_PADRAO,
                        index=ComponentsPagamentoEntrega.EVENTOS_PADRAO.index(evento["evento"]),
                        key=f"evento_base_{i}"
                    )
                
                with col4:
                    if st.button("❌", key=f"remove_evento_{i}"):
                        eventos_atuais = list(st.session_state['eventos_pagamento'])
                        eventos_atuais.pop(i)
                        st.session_state['eventos_pagamento'] = eventos_atuais
                        st.rerun()

            # Validação do total de percentuais
            total_percentual = sum(e["percentual"] for e in st.session_state['eventos_pagamento'])
            if total_percentual != 100:
                st.warning(f"O total dos percentuais deve ser 100%. Atual: {total_percentual}%")


    
    @staticmethod
    def configurar_prazo_entrega():
        """
        Configura os prazos de entrega para a proposta, incluindo prazos gerais 
        (desenho e cliente) e prazo de fabricação. A função gerencia três tipos
        diferentes de prazos que serão usados na proposta.
        """
        
        # Inicialização dos estados para prazos gerais com valores padrão
        if 'prazo_entrega' not in st.session_state:
            st.session_state['prazo_entrega'] = {
                'prazo_desenho': 5,
                'prazo_cliente': 2
            }
        
        # Inicialização do estado para prazo de fabricação com texto padrão
        if 'prazo_entrega_global' not in st.session_state:
            st.session_state['prazo_entrega_global'] = {
                'prazo_fabricacao': "**Transformadores**: Até 60 dias contados a partir da data da aprovação definitiva dos desenhos + transporte."
            }

        # Seção de Prazos Gerais - Organizada em duas colunas para melhor visualização
        st.subheader("Prazos Gerais")
        col1, col2 = st.columns(2)
        
        # Coluna 1: Input para Prazo de Desenho
        with col1:
            prazo_desenho = st.number_input(
                "Prazo de desenho (em dias):",
                min_value=0,
                value=st.session_state['prazo_entrega']['prazo_desenho'],
                key="prazo_desenho_input"
            )
            st.session_state['prazo_entrega']['prazo_desenho'] = prazo_desenho
        
        # Coluna 2: Input para Prazo de Cliente
        with col2:
            prazo_cliente = st.number_input(
                "Prazo de cliente (em dias):",
                min_value=0,
                value=st.session_state['prazo_entrega']['prazo_cliente'],
                key="prazo_cliente_input"
            )
            st.session_state['prazo_entrega']['prazo_cliente'] = prazo_cliente

        # Seção de Prazo de Fabricação - Usando text_input para permitir descrição detalhada
        st.subheader("Prazo de Fabricação do(s) Produto(s)")
        st.info("Este prazo será aplicado a todos os itens da proposta")
        
        prazo_fabricacao = st.text_input(
            "Prazo de fabricação: ",
            value=st.session_state['prazo_entrega_global']['prazo_fabricacao'],
            key="prazo_fabricacao_global"
        )
        
        # Atualiza o prazo de fabricação no session_state
        st.session_state['prazo_entrega_global']['prazo_fabricacao'] = prazo_fabricacao