import streamlit as st
from typing import Dict, List
import streamlit as st
import pandas as pd

class ComponentsPagamentoEntrega:
    EVENTOS_PADRAO = [
        "Pedido",
        "Faturamento",
        "Contraembarque",
        "Aprovação dos Desenhos",
        "TAF",
        "Entrega do Equipamento"
    ]

    EVENTOS_PREDEFINIDOS = [
        {"percentual": 25, "dias": 20, "evento": "Aprovação dos Desenhos"},
        {"percentual": 25, "dias": 30, "evento": "Aprovação dos Desenhos"},
        {"percentual": 25, "dias": 60, "evento": "Aprovação dos Desenhos"},
        {"percentual": 25, "dias": 0, "evento": "Entrega do Equipamento"}
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
        if 'eventos_pagamento' not in st.session_state:
            st.session_state['eventos_pagamento'] = {}
            
        if 'prazo_entrega' not in st.session_state:
            st.session_state['prazo_entrega'] = {
                'prazo_desenho': 0,
                'prazo_cliente': 0,
                'prazo': {}
            }
        
        # Inicializa eventos MT e BT se não existirem
        if 'eventos_mt' not in st.session_state:
            st.session_state['eventos_mt'] = ComponentsPagamentoEntrega.EVENTOS_PREDEFINIDOS.copy()
        
        if 'eventos_bt' not in st.session_state:
            st.session_state['eventos_bt'] = ComponentsPagamentoEntrega.EVENTOS_PREDEFINIDOS.copy()
        
        # Inicializa os checkboxes "A combinar"
        if 'a_combinar_mt' not in st.session_state:
            st.session_state['a_combinar_mt'] = False
        
        if 'a_combinar_bt' not in st.session_state:
            st.session_state['a_combinar_bt'] = False

    @staticmethod

    def configurar_eventos_pagamento(tipo_produto: str) -> Dict:
        """Configura eventos de pagamento para um tipo específico de produto"""
        eventos_key = f'eventos_{tipo_produto.lower()}'
        a_combinar_key = f'a_combinar_{tipo_produto.lower()}'
        
        # Inicializa o valor no session_state se não existir
        if a_combinar_key not in st.session_state:
            st.session_state[a_combinar_key] = False
        
        # Agora usamos o valor do session_state como valor inicial do checkbox
        a_combinar = st.checkbox(
            "A combinar",
            key=a_combinar_key
        )
        
        if not a_combinar:
            eventos = st.session_state[eventos_key]
            eventos_mutaveis = list(eventos)
            
            for i, evento in enumerate(eventos):
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                
                with col1:
                    evento["percentual"] = st.number_input(
                        f"Percentual do evento {i+1}",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(evento["percentual"]),
                        key=f"percentual_{tipo_produto.lower()}_{i}"
                    )
                
                with col2:
                    evento["dias"] = st.number_input(
                        f"Dias do evento {i+1}",
                        min_value=0,
                        value=int(evento["dias"]),
                        key=f"dias_{tipo_produto.lower()}_{i}"
                    )
                
                with col3:
                    evento["evento"] = st.selectbox(
                        f"Evento base {i+1}",
                        ComponentsPagamentoEntrega.EVENTOS_PADRAO,
                        index=ComponentsPagamentoEntrega.EVENTOS_PADRAO.index(evento["evento"]),
                        key=f"evento_{tipo_produto.lower()}_{i}"
                    )
                
                with col4:
                    # Usar um botão com chave única e explícita
                    if st.button("❌", key=f"remove_evento_{tipo_produto}_{i}"):
                        # Remover o evento específico
                        del eventos_mutaveis[i]
                        # Atualizar o session state
                        st.session_state[eventos_key] = eventos_mutaveis
                        st.rerun()
                        
            st.session_state[eventos_key] = eventos_mutaveis

            if st.button("Adicionar Evento", key=f"add_{tipo_produto.lower()}"):
                eventos.append({
                    "percentual": 0,
                    "dias": 0,
                    "evento": ComponentsPagamentoEntrega.EVENTOS_PADRAO[0]
                })
                st.rerun()

            # Validação do total de percentuais
            total_percentual = sum(e["percentual"] for e in eventos)
            if total_percentual != 100:
                st.warning(f"O total dos percentuais deve ser 100%. Atual: {total_percentual}%")
    @staticmethod
    def configurar_prazo_entrega(tipo_produto: str):
        """Configura o prazo de entrega para um tipo específico de produto"""
        prazo_key = f'prazo_{tipo_produto.lower()}'
        
        if prazo_key not in st.session_state['prazo_entrega']:
            st.session_state['prazo_entrega'][prazo_key] = {
                'valor': 0,
                'evento': 'Entrega do Equipamento'
            }
        
        prazo = st.number_input(
            "Prazo de entrega (em dias):",
            min_value=0,
            value=st.session_state['prazo_entrega'][prazo_key]['valor'],
            key=f"prazo_{tipo_produto.lower()}"
        )
        
        evento = st.selectbox(
            "Evento base para prazo:",
            ComponentsPagamentoEntrega.EVENTOS_PADRAO,
            index=ComponentsPagamentoEntrega.EVENTOS_PADRAO.index(
                st.session_state['prazo_entrega'][prazo_key]['evento']
            ),
            key=f"evento_prazo_{tipo_produto.lower()}"
        )
        
        st.session_state['prazo_entrega'][prazo_key] = {
            'valor': prazo,
            'evento': evento
        }