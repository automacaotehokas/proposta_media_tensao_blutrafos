# componentes.py

import streamlit as st
from typing import Dict, List

def render_item_description(index: int, item: Dict, df) -> Dict:
    """
    Renderiza o componente de descrição do item, incluindo selectbox para a descrição
    e campos relacionados como tensões e material.
    """
    descricao_opcoes = [""] + df['descricao'].dropna().unique().tolist()
    item['Descrição'] = st.selectbox(
        f"Descrição do Item {index + 1}:",
        descricao_opcoes,
        index=descricao_opcoes.index(item['Descrição']) if item['Descrição'] in descricao_opcoes else 0
    )

    if item['Descrição']:
        item['ID'] = int(df.loc[df['descricao'] == item['Descrição'], 'id'].values[0])
        item['Produto'] = df.loc[df['descricao'] == item['Descrição'], 'produto'].values[0]
        item['Potência'] = df.loc[df['descricao'] == item['Descrição'], 'potencia_numerica'].values[0]
        item['Potência '] = df.loc[df['descricao'] == item['Descrição'], 'potencia'].values[0]

        tensao_primaria_db = df.loc[df['descricao'] == item['Descrição'], 'tensao_primaria'].values[0]
        tensao_secundaria_db = df.loc[df['descricao'] == item['Descrição'], 'tensao_secundaria'].values[0]

        item['Tensão Primária'] = st.number_input(
            f"Tensão Primária do Item {index + 1}:",
            value=tensao_primaria_db,
            min_value=0
        )
        item['Tensão Secundária'] = st.number_input(
            f"Tensão Secundária do Item {index + 1}:",
            value=tensao_secundaria_db,
            min_value=0
        )

        material_opcoes = [""] + df[df['descricao'] == item['Descrição']]['material'].dropna().unique().tolist()
        item['Material'] = st.selectbox(
            f"Material do Item {index + 1}:",
            material_opcoes,
            index=material_opcoes.index(item['Material']) if item['Material'] in material_opcoes else 0
        )

    return item

def render_item_specifications(index: int, item: Dict) -> Dict:
    """
    Renderiza os componentes de especificações do item como Fator K e IP.
    """
    fator_k_opcoes = [1, 4, 6, 8, 13]
    item['Fator K'] = st.selectbox(
        f"Fator K do Item {index + 1}:",
        fator_k_opcoes,
        index=fator_k_opcoes.index(item['Fator K']) if item['Fator K'] in fator_k_opcoes else 0
    )
    
    ip_opcoes = ['00', '21', '23', '54']
    
    if "IP-54" in item['Descrição']:
        item['IP'] = '54'
        flange_opcoes = [0, 1, 2]
        item['Flange'] = st.selectbox(
            f"Flange {index + 1}:",
            flange_opcoes,
            index=flange_opcoes.index(item['Flange']) if item['Flange'] in flange_opcoes else 0
        )
    else:
        item['IP'] = st.selectbox(
            f"IP do Item {index + 1}:",
            ip_opcoes,
            index=ip_opcoes.index(item['IP']) if item['IP'] in ip_opcoes else 0
        )
        
        if item['IP'] != '00':
            flange_opcoes = [0, 1, 2]
            item['Flange'] = st.selectbox(
                f"Flange {index + 1}:",
                flange_opcoes,
                index=flange_opcoes.index(item['Flange']) if item['Flange'] in flange_opcoes else 0
            )
        else:
            item['Flange'] = 0

    item['Quantidade'] = st.number_input(
        f"Quantidade do Item {index + 1}:",
        min_value=1,
        step=1,
        value=item['Quantidade']
    )

    return item

def render_item_accessories(index: int, item: Dict) -> Dict:
    """
    Renderiza os componentes de acessórios do item em um layout de colunas.
    """
    col1, col2, col3, col4 = st.columns(4)

    opcoes_rele = [
        {"label": "Nenhum", "value": "", "price": 0},
        {"label": "Relé TH104", "value": "TH104", "price": 433.4},
        {"label": "Relé NT935 AD", "value": "NT935_AD", "price": 1248.0},
        {"label": "Relé NT935 ETH", "value": "NT935_ETH", "price": 3515.0}
    ]

    with col1:
        item['Frequencia 50Hz'] = st.checkbox(
            f"Freqüência de 50Hz para o Item {index + 1}",
            value=item['Frequencia 50Hz']
        )
        render_item_taps(index, item)

    with col2:
        item['Blindagem Eletrostática'] = st.checkbox(
            f"Blindagem Eletrostática para o Item {index + 1}",
            value=item['Blindagem Eletrostática']
        )
        render_item_tensoes(index, item)

    with col3:
        item['Ensaios']['Elev. Temperat.'] = st.checkbox(
            f"Elev. Temperat. para o Item {index + 1}",
            value=item['Ensaios']['Elev. Temperat.']
        )
        
        labels_rele = [opcao["label"] for opcao in opcoes_rele]
        indice_inicial = labels_rele.index(item['Rele']) if item['Rele'] in labels_rele else 0
        
        item['Rele'] = st.selectbox(
            "Selecione o tipo de Relé",
            labels_rele,
            index=indice_inicial,
            key=f"rele_{item['ID']}_{index}"
        )
        
        item['Preço Rele'] = next((opcao['price'] for opcao in opcoes_rele if opcao['label'] == item['Rele']), 0)

    with col4:
        item['Ensaios']['Nível de Ruído'] = st.checkbox(
            f"Nível de Ruído para o Item {index + 1}",
            value=item['Ensaios']['Nível de Ruído']
        )

    return item

def render_item_taps(index: int, item: Dict):
    """
    Renderiza os componentes relacionados aos taps do item.
    """
    tap_options = ['nenhum', '2 taps', '3 taps']
    item['Derivações']['taps'] = st.radio(
        f"Configuração de taps para o Item {index + 1}",
        tap_options,
        index=tap_options.index(item['Derivações']['taps']),
        key=f"radio_taps_{index}"
    )

    if item['Derivações']['taps'] == "nenhum":
        item['Taps'] = None
    else:
        item['Taps'] = st.text_input(
            "Escreva os Tap's:",
            value=item.get('Taps', ''),
            key=f"text_taps_{index}"
        )

def render_item_tensoes(index: int, item: Dict):
    """
    Renderiza os componentes relacionados às tensões do item.
    """
    tensoes_options = ['nenhum', '2 tensões', '3 tensões']
    item['Derivações']['tensoes_primarias'] = st.radio(
        f"Configuração de tensões primárias para o Item {index + 1}",
        tensoes_options,
        index=tensoes_options.index(item['Derivações']['tensoes_primarias']),
        key=f"radio_tensoes_{index}"
    )
    
    if item['Derivações']['tensoes_primarias'] == "nenhum":
        item['taps_tensoes'] = None
    else:
        item['taps_tensoes'] = st.text_input(
            "Escreva as tensões primárias:",
            value=item.get('taps_tensoes', ''),
            key=f"text_tensoes_{index}"
        )