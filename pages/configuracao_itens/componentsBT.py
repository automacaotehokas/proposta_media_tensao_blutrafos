import streamlit as st
from typing import Dict, List
from repositories.custos_baixa_tensao import CustoBaixaTensaoRepository
from .utils import verificar_campos_preenchidos, converter_valor_ajustado
from .calculo_item_bt import calcular_preco_encontrado
from decimal import Decimal

class ComponenteBT:
    @staticmethod
    def render_bt_components(modo_edicao=False, item_edicao=None):
        """
        Renderiza todos os componentes BT em sequência.
        Args:
            modo_edicao (bool): Define se o componente está em modo de edição
            item_edicao (dict): Item sendo editado, se estiver em modo de edição
        Returns:
            Optional[Dict]: Retorna o item atualizado se estiver em modo de edição e salvo com sucesso
        """
        # Inicializa ou atualiza o item no session state baseado no modo
        if item_edicao and modo_edicao:
            st.session_state['current_bt_item'] = item_edicao
        elif 'current_bt_item' not in st.session_state:
            st.session_state['current_bt_item'] = {
                'id': None,
                'Produto': "",
                'Potência': "",
                'potencia_numerica': None,
                'material': "",
                'Tensão Primária': None,
                'Tensão Secundária': None,
                'preco': None,
                'proj': None,
                'modelo_caixa': None,
                'descricao': "",
                'cod_caixa': None,
                'preco_caixa': None,
                'derivacoes': {
                    'taps': 'nenhum',
                    'tensoes_primarias': 'nenhum'
                },
                'taps': None,
                'taps_tensoes': None,
                'frequencia_50hz': False,
                'blindagem_eletrostatica': False,
                'ensaios': {
                    'elevacao_temperatura': False,
                    'nivel_ruido': False
                },
                'rele': "Nenhum",
                'preco_rele': 0,
                'IP': '00',
                'flange': 0,
                'Quantidade': 1,
                'Fator K': 1,
                'Preço Unitário': 0.0,
                'Preço Total': 0.0,
                'Descrição': ""
            }

        # Obtém o item atual do session state
        item = st.session_state['current_bt_item']
        
        # Carrega os dados do repositório
        df_bt = CustoBaixaTensaoRepository().buscar_todos()

        # Renderiza os componentes principais
        ComponenteBT.render_item_description(0, item, df_bt)
        ComponenteBT.render_item_specifications(0, item)
        ComponenteBT.render_item_accessories(0, item)

        # Calcula o preço se tivermos as informações necessárias
        if item['Produto'] and item['material']:
            try:
                preco_unitario = calcular_preco_encontrado(
                    df=df_bt,
                    preco_base=item['preco'],
                    potencia=item['potencia_numerica'],
                    produto=item['Produto'],
                    ip=item['IP'],
                    tensao_primaria=item['Tensão Primária'],
                    tensao_secundaria=item['Tensão Secundária'],
                    material=item['material'],
                    item={
                        'Frequencia 50Hz': item['frequencia_50hz'],
                        'Blindagem Eletrostática': item['blindagem_eletrostatica'],
                        'Preço Rele': item['preco_rele'],
                        'Rele': item['rele'],
                        'Ensaios': {
                            'Elev. Temperat.': item['ensaios']['elevacao_temperatura'],
                            'Nível de Ruído': item['ensaios']['nivel_ruido']
                        },
                        'Flange': item['flange']
                    }
                )

                # Atualiza os preços no item
                item['Preço Unitário'] = preco_unitario
                item['Preço Total'] = preco_unitario * item['Quantidade']
                item['Descrição'] = item['descricao']

                # Atualiza o session state
                st.session_state['current_bt_item'] = item

            except Exception as e:
                st.error(f"Erro ao calcular preço: {str(e)}")

        # Interface de controle baseada no modo (edição ou criação)
        if modo_edicao:
            # Layout para modo de edição
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button("💾 Salvar Alterações", key="salvar_edicao_bt", type="primary"):
                    # Validação dos campos obrigatórios
                    campos_vazios = verificar_campos_preenchidos(item, campos_obrigatorios=[
                        'descricao',
                        'material',
                        'Tensão Primária',
                        'Tensão Secundária',
                    ])

                    if campos_vazios:
                        st.error(f"Por favor, preencha os seguintes campos: {', '.join(campos_vazios)}")
                        return None
                    
                    # Se a validação passar, atualiza o item na lista principal
                    if 'editando_item_bt' in st.session_state:
                        index = st.session_state.editando_item_bt['index']
                        st.session_state.itens['itens_configurados_bt'][index] = item.copy()
                        del st.session_state.editando_item_bt
                        st.success("Item atualizado com sucesso!")
                        st.rerun()
                    return item
                    
            with col2:
                if st.button("❌ Cancelar Edição", key="cancelar_edicao_bt"):
                    if 'editando_item_bt' in st.session_state:
                        del st.session_state.editando_item_bt
                    st.rerun()
                    
        else:
            # Layout para modo de criação
            if st.button("➕ Adicionar Item BT", key="adicionar_item_bt", type="primary"):
                # Validação dos campos obrigatórios
                campos_vazios = verificar_campos_preenchidos(item, campos_obrigatorios=[
                    'descricao',
                    'material',
                    'Tensão Primária',
                    'Tensão Secundária',
                ])

                if campos_vazios:
                    st.error(f"Por favor, preencha os seguintes campos: {', '.join(campos_vazios)}")
                else:
                    # Inicializa a lista de itens BT se necessário
                    if 'itens_configurados_bt' not in st.session_state['itens']:
                        st.session_state['itens']['itens_configurados_bt'] = []
                    
                    # Adiciona o novo item à lista
                    item_to_add = item.copy()
                    item_to_add['Descrição'] = item['descricao']
                    st.session_state['itens']['itens_configurados_bt'].append(item_to_add)
                    st.success("Item BT adicionado com sucesso!")

                    # Reseta o formulário para um novo item
                    st.session_state['current_bt_item'] = {
                        'id': None,
                        'Produto': "",
                        'Potência': "",
                        'potencia_numerica': None,
                        'material': "",
                        'Tensão Primária': None,
                        'Tensão Secundária': None,
                        'preco': None,
                        'proj': None,
                        'modelo_caixa': None,
                        'descricao': "",
                        'cod_caixa': None,
                        'preco_caixa': None,
                        'derivacoes': {
                            'taps': 'nenhum',
                            'tensoes_primarias': 'nenhum'
                        },
                        'taps': None,
                        'taps_tensoes': None,
                        'frequencia_50hz': False,
                        'blindagem_eletrostatica': False,
                        'ensaios': {
                            'elevacao_temperatura': False,
                            'nivel_ruido': False
                        },
                        'rele': "Nenhum",
                        'preco_rele': 0,
                        'IP': '00',
                        'flange': 0,
                        'Quantidade': 1,
                        'Fator K': 1,
                        'Preço Unitário': 0.0,
                        'Preço Total': 0.0,
                        'Descrição': ""
                    }
                    st.rerun()
    


                
    @staticmethod
    def render_item_description(index: int, item: Dict, df) -> Dict:
        """
        Renderiza o componente de descrição do item.
        """
        descricao_opcoes = [""] + df['descricao'].dropna().unique().tolist()
        item['descricao'] = st.selectbox(
            f"Descrição do Item {index + 1}:",
            descricao_opcoes,
            index=descricao_opcoes.index(item['descricao']) if item['descricao'] in descricao_opcoes else 0,
            key=f'descricao_bt_{index}_{id(item)}'  # Make key unique by adding bt prefix and item id
        )

        if item['descricao']:
            item['id'] = int(df.loc[df['descricao'] == item['descricao'], 'id'].values[0])
            item['Produto'] = df.loc[df['descricao'] == item['descricao'], 'produto'].values[0]
            item['potencia_numerica'] = df.loc[df['descricao'] == item['descricao'], 'potencia_numerica'].values[0]
            item['Potência'] = df.loc[df['descricao'] == item['descricao'], 'potencia'].values[0]
            item['preco'] = df.loc[df['descricao'] == item['descricao'], 'preco'].values[0]
            item['proj'] = df.loc[df['descricao'] == item['descricao'], 'proj'].values[0]
            item['modelo_caixa'] = df.loc[df['descricao'] == item['descricao'], 'modelo_caixa'].values[0]
            item['cod_caixa'] = df.loc[df['descricao'] == item['descricao'], 'cod_caixa'].values[0]
            item['preco_caixa'] = df.loc[df['descricao'] == item['descricao'], 'preco_caixa'].values[0]

            tensao_primaria_db = df.loc[df['descricao'] == item['descricao'], 'tensao_primaria'].values[0]
            tensao_secundaria_db = df.loc[df['descricao'] == item['descricao'], 'tensao_secundaria'].values[0]

            item['Tensão Primária'] = st.number_input(
                f"Tensão Primária do Item {index + 1}:",
                value=float(tensao_primaria_db),
                min_value=0.0,
                key=f"tensao_primaria_{index}_{id(item)}"
            )
            item['Tensão Secundária'] = st.number_input(
                f"Tensão Secundária do Item {index + 1}:",
                value=float(tensao_secundaria_db),
                min_value=0.0,
                key=f"tensao_secundaria_{index}_{id(item)}"
            )

            material_opcoes = [""] + df[df['descricao'] == item['descricao']]['material'].dropna().unique().tolist()
            item['material'] = st.selectbox(
                f"Material do Item {index + 1}:",
                material_opcoes,
                index=material_opcoes.index(item['material']) if item['material'] in material_opcoes else 0,
                key=f"material_{index}_{id(item)}"
            )

        return item

    @staticmethod
    def render_item_specifications(index: int, item: Dict) -> Dict:
        """
        Renderiza os componentes de especificações do item.
        """
        fator_k_opcoes = [1, 4, 6, 8, 13]
        item['Fator K'] = st.selectbox(
            f"Fator K do Item {index + 1}:",
            fator_k_opcoes,
            index=fator_k_opcoes.index(item['Fator K']) if 'Fator K' in item and item['Fator K'] in fator_k_opcoes else 0,
            key=f"fator_k_{index}_{id(item)}"
        )

        ip_opcoes = ['00', '21', '23', '54']

        if "IP-54" in item['descricao']:
            item['IP'] = '54'
            flange_opcoes = [0, 1, 2]
            item['flange'] = st.selectbox(
                f"Flange {index + 1}:",
                flange_opcoes,
                index=flange_opcoes.index(item['flange']) if item['flange'] in flange_opcoes else 0,
                key=f"flange_{index}_{id(item)}"
            )
        else:
            item['IP'] = st.selectbox(
                f"IP do Item {index + 1}:",
                ip_opcoes,
                index=ip_opcoes.index(item['IP']) if item['IP'] in ip_opcoes else 0,
                key=f"ip_{index}_{id(item)}"
            )

            if item['IP'] != '00':
                flange_opcoes = [0, 1, 2]
                item['flange'] = st.selectbox(
                    f"Flange {index + 1}:",
                    flange_opcoes,
                    index=flange_opcoes.index(item['flange']) if item['flange'] in flange_opcoes else 0,
                    key=f"flange_{index}_{id(item)}"
                )
            else:
                item['flange'] = 0

        item['Quantidade'] = st.number_input(
            f"Quantidade do Item {index + 1}:",
            min_value=1,
            step=1,
            value=item['Quantidade'],
            key=f"quantidade_{index}_{id(item)}"
        )

        return item

    @staticmethod
    def render_item_accessories(index: int, item: Dict) -> Dict:
        """
        Renderiza os acessórios para um item BT.
        """
        # Título da seção de acessórios
        st.markdown("### 🔧 Acessórios do Transformador")

        # Cria colunas para organizar os widgets
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("#### 🔲 Configurações")
            # Frequência 50Hz
            item['frequencia_50hz'] = st.checkbox(
                f"Frequência 50Hz: (20% sobre o valor do Transformador)",
                value=item.get('frequencia_50hz', False),
                key=f'frequencia_50hz_{index}_{id(item)}'
            )

            # Blindagem Eletrostática
            item['blindagem_eletrostatica'] = st.checkbox(
                "Blindagem Eletrostática: (30% sobre o valor do Transformador)",
                value=item.get('blindagem_eletrostatica', False),
                key=f'blindagem_eletrostatica_{index}_{id(item)}'
            )

            # Ensaio de Elevação de Temperatura
            elevacao_temp_valor = converter_valor_ajustado(Decimal('2910'), Decimal('0'))
            item['ensaios']['elevacao_temperatura'] = st.checkbox(
                f"Ensaio Elevação Temperatura (R$ {elevacao_temp_valor:.2f})",
                value=item['ensaios'].get('elevacao_temperatura', False),
                key=f'elevacao_temperatura_{index}_{id(item)}'
            )

            # Ensaio de Nível de Ruído
            nivel_ruido_valor = converter_valor_ajustado(Decimal('1265'), Decimal('0'))
            item['ensaios']['nivel_ruido'] = st.checkbox(
                f"Ensaio Nível de Ruído (R$ {nivel_ruido_valor:.2f})",
                value=item['ensaios'].get('nivel_ruido', False),
                key=f'nivel_ruido_{index}_{id(item)}'
            )

        with col2:
            st.markdown("#### 📋 Relé")
            # Seleção de Relé
            rele_options = ["Nenhum", "Relé TH104", "Relé NT935 AD", "Relé NT935 ETH"]
            rele_prices = {
                "Nenhum": 0,
                "Relé TH104": 433.4,
                "Relé NT935 AD": 1248.0,
                "Relé NT935 ETH": 3515.0
            }

            item['rele'] = st.selectbox(
                "Tipo de Relé",
                options=rele_options,
                index=rele_options.index(item.get('rele', "Nenhum")),
                key=f'rele_{index}'
            )
            preco_do_rele = converter_valor_ajustado(Decimal(str(rele_prices[item['rele']])), Decimal('0'))
            # Preço do Relé (se aplicável)
            item['preco_rele'] = rele_prices[item['rele']]
            st.text_input(
                "Preço Relé",
                value=f"R$ {preco_do_rele:.2f}",
                disabled=True,
                key=f'preco_rele_display_{index}_{id(item)}'
            )

        with col3:
            st.markdown("#### 🔢 Taps")
            # Renderiza taps
            ComponenteBT.render_item_taps(index, item)

        with col4:
            st.markdown("#### 🔢 Tensões")
            # Renderiza tensões
            ComponenteBT.render_item_tensoes(index, item)

        # Adiciona um espaçador para melhorar o layout
        st.markdown("---")

        return item

    @staticmethod
    def render_item_taps(index: int, item: Dict):
        """
        Renderiza os componentes relacionados aos taps do item.
        """
        tap_options = ['nenhum', '2 taps', '3 taps']
        item['derivacoes']['taps'] = st.radio(
            f"Configuração de taps para o Item {index + 1}",
            tap_options,
            index=tap_options.index(item['derivacoes']['taps']),
            key=f"radio_taps_{index}_{id(item)}"
        )

        if item['derivacoes']['taps'] == "nenhum":
            item['taps'] = None
        else:
            item['taps'] = st.text_input(
                "Escreva os Tap's:",
                value=item.get('taps', ''),
                key=f"text_taps_{index}_{id(item)}"
            )

    @staticmethod
    def render_item_tensoes(index: int, item: Dict):
        """
        Renderiza os componentes relacionados às tensões do item.
        """
        tensoes_options = ['nenhum', '2 tensões', '3 tensões']
        item['derivacoes']['tensoes_primarias'] = st.radio(
            f"Configuração de tensões primárias para o Item {index + 1}",
            tensoes_options,
            index=tensoes_options.index(item['derivacoes']['tensoes_primarias']),
            key=f"radio_tensoes_{index}_{id(item)}"
        )

        if item['derivacoes']['tensoes_primarias'] == "nenhum":
            item['taps_tensoes'] = None
        else:
            item['taps_tensoes'] = st.text_input(
                "Escreva as tensões primárias:",
                value=item.get('taps_tensoes', ''),
                key=f"text_tensoes_{index}_{id(item)}"
            )