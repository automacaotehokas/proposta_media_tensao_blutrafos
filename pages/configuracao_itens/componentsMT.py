import streamlit as st
from typing import Dict, Any
import pandas as pd
from .calculo_item_mt import CalculoItemMT
from utils.constants import get_default_voltage_values, ACESSORIOS_FIXOS , ACESSORIOS_PERCENTUAIS
from pages.inicial.api import distancia_cidade_capital
from .utils import calcular_valor_acessorio_com_percentuais
from repositories.custos_media_tensao_repository import CustoMediaTensaoRepository
from .utils import verificar_campos_preenchidos,calcular_percentuais,converter_valor_ajustado





class componentsMT:
    def render_tax_inputs(dados_impostos: Dict[str, Any]) -> Dict[str, Any]:
        """Renderiza os campos de entrada para impostos"""
        # Agora usa a função do view.py
        from .view import render_impostos
        render_impostos(dados_impostos)
        return st.session_state['impostos']

    def render_item_config(item_index: int, df: pd.DataFrame, item_data: Dict[str, Any]
                        ) -> Dict[str, Any]:
        

        # Converte df em um Dataframe
        df = pd.DataFrame(df)

        # Seleção da descrição
        descricao_opcoes = [""] + df['descricao'].unique().tolist()
        descricao_escolhida = st.selectbox(
            f'Digite ou Selecione a Descrição do Item {item_index + 1}:',
            descricao_opcoes,
            key=f'descricao_{item_index}',
            index=0 if item_data['Descrição'] == "" else descricao_opcoes.index(item_data['Descrição'])
        )
        
        if not descricao_escolhida:
            st.warning("Por favor, selecione uma descrição para continuar.")
            return item_data
            
        # Detalhes do item baseado na descrição
        detalhes_item = df[df['descricao'] == descricao_escolhida].iloc[0]

        # Atualiza os dados do item com os detalhes do DataFrame
        item_data.update({
            'Descrição': descricao_escolhida,
            'classe_tensao': detalhes_item['classe_tensao'],
            'Perdas': detalhes_item['perdas'],
            'Potência': detalhes_item['potencia'],
            'cod_proj_custo': detalhes_item['cod_proj_custo'],
            'cod_proj_caixa': detalhes_item['cod_proj_caixa'],
            'preco': float(detalhes_item['preco']),
            'p_trafo': float(detalhes_item['p_trafo']),
            'valor_ip_baixo': float(detalhes_item['valor_ip_baixo']),
            'valor_ip_alto': float(detalhes_item['valor_ip_alto']),
            'p_caixa': float(detalhes_item['p_caixa'])
        })

        cod_proj_custo = detalhes_item['cod_proj_custo']
        
        # Seleção de Fator K e IP
        fator_k_opcoes = [1, 4, 6, 8, 13]
        opcoes_ip = ['00', '21', '23', '54']
        
        fator_k = st.selectbox(
            f'Selecione o Fator K do Item:',
            fator_k_opcoes,
            key=f'fator_k_{item_index}',
            index=fator_k_opcoes.index(item_data['Fator K'])
        )
        item_data['Fator K'] = fator_k
        
        ip = st.selectbox(
            f'Selecione o IP do Item:',
            opcoes_ip,
            key=f'ip_{item_index}',
            index=opcoes_ip.index(item_data['IP'])
        )
        item_data['IP'] = ip
        
        # Campos de tensão
        tensao_primaria = st.text_input(
            f'Tensão Primária do Item {item_index + 1}:',
            value=get_default_voltage_values(detalhes_item['classe_tensao'])['tensao_primaria'],
            key=f'tensao_primaria_{item_index}'
        )
        item_data['Tensão Primária'] = tensao_primaria
        
        tensao_secundaria = st.text_input(
            f'Tensão Secundária do Item {item_index + 1}:',
            value=item_data['Tensão Secundária'] if item_data['Tensão Secundária'] else "",
            key=f'tensao_secundaria_{item_index}'
        )
        item_data['Tensão Secundária'] = tensao_secundaria
        
        derivacoes = st.text_input(
            f'Derivações do Item {item_index + 1}:',
            value=get_default_voltage_values(detalhes_item['classe_tensao'])['derivacoes'],
            key=f'derivacoes_{item_index}'
        )
        item_data['Derivações'] = derivacoes
        
        quantidade = st.number_input(
            f'Quantidade para o Item {item_index + 1}:',
            min_value=1,
            value=item_data['Quantidade'],
            step=1,
            key=f'qtd_{item_index}'
        )
        item_data['Quantidade'] = quantidade

        st.markdown("---")
        
        
        
        acessorios_selecionados = []
        potencia = detalhes_item.get('potencia', 0)

        # Recuperar acessórios salvos anteriormente
        acessorios_salvos = item_data.get('acessorios', [])

        percentuais = calcular_percentuais(st.session_state['impostos'])
        col1, col2, col3 = st.columns(3)

        with col1:
            st.write("#### 🔧 Acessórios - Valores Fixos")
            for acessorio in ACESSORIOS_FIXOS[:len(ACESSORIOS_FIXOS)//2]:
                # Verifica regras de potência se existirem
                if "regra" in acessorio:
                    if "≥" in acessorio["regra"]:
                        min_val = float(acessorio["regra"].replace("≥", "").replace("kVA", ""))
                        if potencia < min_val:
                            continue
                    elif "≤" in acessorio["regra"]:
                        max_val = float(acessorio["regra"].replace("≤", "").replace("kVA", ""))
                        if potencia > max_val:
                            continue

                # Verificar se este acessório estava selecionado anteriormente
                checkbox_key = f"acessorio_fixo_{item_index}_{acessorio['descricao']}"
                default_value = any(
                    ac['tipo'] == 'VALOR_FIXO' and ac['descricao'] == acessorio['descricao']
                    for ac in acessorios_salvos
                )
                
                if checkbox_key not in st.session_state:
                    st.session_state[checkbox_key] = default_value
                
                if st.checkbox(
                    f"{acessorio['descricao']} (+R$ {acessorio['valor']:,.2f})",
                    key=checkbox_key,
                    value=st.session_state[checkbox_key]
                ):
                    acessorios_selecionados.append({
                        "tipo": "VALOR_FIXO",
                        "descricao": acessorio["descricao"],
                        "valor": acessorio["valor"],
                        "base_calculo": "PRECO_BASE1"
                    })

        with col2:
            st.write("#### 🔧 Acessórios - Valores Fixos")
            for acessorio in ACESSORIOS_FIXOS[len(ACESSORIOS_FIXOS)//2:]:
                # Mesma lógica da coluna anterior
                if "regra" in acessorio:
                    if "≥" in acessorio["regra"]:
                        min_val = float(acessorio["regra"].replace("≥", "").replace("kVA", ""))
                        if potencia < min_val:
                            continue
                    elif "≤" in acessorio["regra"]:
                        max_val = float(acessorio["regra"].replace("≤", "").replace("kVA", ""))
                        if potencia > max_val:
                            continue

                # Verificar se este acessório estava selecionado anteriormente
                checkbox_key = f"acessorio_fixo_{item_index}_{acessorio['descricao']}"
                default_value = any(
                    ac['tipo'] == 'VALOR_FIXO' and ac['descricao'] == acessorio['descricao']
                    for ac in acessorios_salvos
                )
                
                if checkbox_key not in st.session_state:
                    st.session_state[checkbox_key] = default_value
                
                if st.checkbox(
                    f"{acessorio['descricao']} (+R$ {acessorio['valor']:,.2f})",
                    key=checkbox_key,
                    value=st.session_state[checkbox_key]
                ):
                    acessorios_selecionados.append({
                        "tipo": "VALOR_FIXO",
                        "descricao": acessorio["descricao"],
                        "valor": acessorio["valor"],
                        "base_calculo": "PRECO_BASE1"
                    })

        with col3:
            st.write("#### 🔧 Acessórios - Valores Percentuais")
            for acessorio in ACESSORIOS_PERCENTUAIS:
                base = "preço total" if acessorio["base_calculo"] == "PRECO_TOTAL" else "preço base"
                
                # Verificar se este acessório estava selecionado anteriormente
                checkbox_key = f"acessorio_perc_{item_index}_{acessorio['descricao']}"
                default_value = any(
                    ac['tipo'] == 'PERCENTUAL' and ac['descricao'] == acessorio['descricao']
                    for ac in acessorios_salvos
                )
                
                if checkbox_key not in st.session_state:
                    st.session_state[checkbox_key] = default_value
                
                if st.checkbox(
                    f"{acessorio['descricao']} (+{acessorio['percentual']}% sobre {base})",
                    key=checkbox_key,
                    value=st.session_state[checkbox_key]
                ):
                    acessorios_selecionados.append({
                        "tipo": "PERCENTUAL",
                        "descricao": acessorio["descricao"],
                        "percentual": acessorio["percentual"],
                        "base_calculo": acessorio["base_calculo"]
                    })

        # Atualiza os acessórios no item_data
        item_data['acessorios'] = acessorios_selecionados

        calculo = CalculoItemMT(
            item_data=item_data, 
            acessorios=acessorios_selecionados
        )
        preco_unitario = calculo.calcular_preco_item()
        preco_total = preco_unitario * quantidade

        item_data['Preço Unitário'] = preco_unitario
        item_data['Preço Total'] = preco_total

        # Exibe os preços calculados
        st.markdown("---")



        if st.button("Adicionar Item MT"):
            campos_vazios = verificar_campos_preenchidos(item_data, campos_obrigatorios=[
                'descricao',  # Note as maiúsculas, conforme usado no item_data
                'tensao_primaria',
                'tensao_secundaria',
                'derivacoes'
            ])
            if campos_vazios:
                st.error(f"Por favor, preencha os seguintes campos: {', '.join(campos_vazios)}")
            else:
                if 'itens' not in st.session_state:
                    st.session_state['itens'] = {
                        'itens_configurados_mt': [],
                        'itens_configurados_bt': []
                    }
                
                # Adiciona o item_data que já contém todos os valores calculados
                st.session_state['itens']['itens_configurados_mt'].append(item_data.copy())
                st.success("Item MT adicionado com sucesso!")
                
                # Reseta o item atual
                st.session_state['current_mt_item'] = {
                    'Descrição': "",
                    'Fator K': 1,
                    'IP': '00',
                    'Tensão Primária': None,
                    'Tensão Secundária': None,
                    'Derivações': None,
                    'Quantidade': 1,
                    'classe_tensao': None,
                    'Perdas': None,
                    'Potência': None,
                    'cod_proj_custo': None,
                    'cod_proj_caixa': None,
                    'preco': 0.0,
                    'p_trafo': 0.0,
                    'valor_ip_baixo': 0.0,
                    'valor_ip_alto': 0.0,
                    'p_caixa': 0.0,
                    'acessorios': [],
                    'Preço Unitário': 0.0,
                    'Preço Total': 0.0
                }
                st.rerun()

        return item_data