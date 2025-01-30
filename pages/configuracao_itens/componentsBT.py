# componentes.py

import streamlit as st
from typing import Dict, List
from repositories.custos_baixa_tensao import CustoBaixaTensaoRepository
from .utils import verificar_campos_preenchidos


class ComponenteBT:

    
    @staticmethod
    def render_bt_components():
        """
        Renderiza todos os componentes BT em sequência.
        """
        # Inicializa o item se não existir no session state
        if 'current_bt_item' not in st.session_state:
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
                'Preço Total': 0.0
            }
    


        item = st.session_state['current_bt_item']
        df_bt = CustoBaixaTensaoRepository().buscar_todos()

        # Renderiza cada componente
        ComponenteBT.render_item_description(0, item, df_bt)
        ComponenteBT.render_item_specifications(0, item)
        ComponenteBT.render_item_accessories(0, item)
        # Botão para adicionar o item
        

        if st.button("Adicionar Item BT"):
            campos_vazios = verificar_campos_preenchidos(item, campos_obrigatorios=[
                'descricao',
                'material',
                'tensao_primaria',
                'tensao_secundaria',
            ])
            
            if campos_vazios:
                st.error(f"Por favor, preencha os seguintes campos: {', '.join(campos_vazios)}")
            else:  # Se não houver campos vazios, prossegue com a adição
                # Garante que a lista existe
                if 'itens_configurados_bt' not in st.session_state['itens']:
                    st.session_state['itens']['itens_configurados_bt'] = []
                # Adiciona o item
                st.session_state['itens']['itens_configurados_bt'].append(item.copy())
                st.success("Item BT adicionado com sucesso!")
                
                # Reseta o item atual
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
                    'Preço Unitário': 0,
                    'Preço Total': 0
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
            index=descricao_opcoes.index(item['descricao']) if item['descricao'] in descricao_opcoes else 0
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
                min_value=0.0
            )
            item['Tensão Secundária'] = st.number_input(
                f"Tensão Secundária do Item {index + 1}:",
                value=float(tensao_secundaria_db),
                min_value=0.0
            )

            material_opcoes = [""] + df[df['descricao'] == item['descricao']]['material'].dropna().unique().tolist()
            item['material'] = st.selectbox(
                f"Material do Item {index + 1}:",
                material_opcoes,
                index=material_opcoes.index(item['material']) if item['material'] in material_opcoes else 0
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
            index=fator_k_opcoes.index(item['Fator K']) if 'Fator K' in item and item['Fator K'] in fator_k_opcoes else 0
        )
        
        ip_opcoes = ['00', '21', '23', '54']
        
        if "IP-54" in item['descricao']:
            item['IP'] = '54'
            flange_opcoes = [0, 1, 2]
            item['flange'] = st.selectbox(
                f"Flange {index + 1}:",
                flange_opcoes,
                index=flange_opcoes.index(item['flange']) if item['flange'] in flange_opcoes else 0
            )
        else:
            item['IP'] = st.selectbox(
                f"IP do Item {index + 1}:",
                ip_opcoes,
                index=ip_opcoes.index(item['IP']) if item['IP'] in ip_opcoes else 0
            )
            
            if item['IP'] != '00':
                flange_opcoes = [0, 1, 2]
                item['flange'] = st.selectbox(
                    f"Flange {index + 1}:",
                    flange_opcoes,
                    index=flange_opcoes.index(item['flange']) if item['flange'] in flange_opcoes else 0
                )
            else:
                item['flange'] = 0

        item['Quantidade'] = st.number_input(
            f"Quantidade do Item {index + 1}:",
            min_value=1,
            step=1,
            value=item['Quantidade']
        )

        return item

    @staticmethod
    def render_item_accessories(index: int, item: Dict) -> Dict:
        """
        Renderiza os componentes de acessórios do item.
        """
        col1, col2, col3, col4 = st.columns(4)

        opcoes_rele = [
            {"label": "Nenhum", "value": "", "price": 0},
            {"label": "Relé TH104", "value": "TH104", "price": 433.4},
            {"label": "Relé NT935 AD", "value": "NT935_AD", "price": 1248.0},
            {"label": "Relé NT935 ETH", "value": "NT935_ETH", "price": 3515.0}
        ]

        with col1:
            item['frequencia_50hz'] = st.checkbox(
                f"Freqüência de 50Hz para o Item {index + 1}",
                value=item['frequencia_50hz']
            )

        with col2:
            item['blindagem_eletrostatica'] = st.checkbox(
                f"Blindagem Eletrostática para o Item {index + 1}",
                value=item['blindagem_eletrostatica']
            )

        with col3:
            item['ensaios']['elevacao_temperatura'] = st.checkbox(
                f"Elev. Temperat. para o Item {index + 1}",
                value=item['ensaios']['elevacao_temperatura']
            )
            
            labels_rele = [opcao["label"] for opcao in opcoes_rele]
            indice_inicial = labels_rele.index(item['rele']) if item['rele'] in labels_rele else 0
            
            item['rele'] = st.selectbox(
                "Selecione o tipo de Relé",
                labels_rele,
                index=indice_inicial,
                key=f"rele_{item['id']}_{index}"
            )
            
            item['preco_rele'] = next((opcao['price'] for opcao in opcoes_rele if opcao['label'] == item['rele']), 0)

        with col4:
            item['ensaios']['nivel_ruido'] = st.checkbox(
                f"Nível de Ruído para o Item {index + 1}",
                value=item['ensaios']['nivel_ruido']
            )

        ComponenteBT.render_item_taps(index, item)
        ComponenteBT.render_item_tensoes(index, item)

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
            key=f"radio_taps_{index}_main"
        )

        if item['derivacoes']['taps'] == "nenhum":
            item['taps'] = None
        else:
            item['taps'] = st.text_input(
                "Escreva os Tap's:",
                value=item.get('taps', ''),
                key=f"text_taps_{index}_main"
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
            key=f"radio_tensoes_{index}_main"
        )
        
        if item['derivacoes']['tensoes_primarias'] == "nenhum":
            item['taps_tensoes'] = None
        else:
            item['taps_tensoes'] = st.text_input(
                "Escreva as tensões primárias:",
                value=item.get('taps_tensoes', ''),
                key=f"text_tensoes_{index}_main"
            )