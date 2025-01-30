import streamlit as st
from typing import Dict, Any
import pandas as pd
from .calculo_item_mt import CalculoItemMT
from utils.constants import get_default_voltage_values, ACESSORIOS_FIXOS , ACESSORIOS_PERCENTUAIS
from pages.inicial.api import distancia_cidade_capital
from .utils import calcular_valor_acessorio_com_percentuais
from repositories.custos_media_tensao_repository import CustoMediaTensaoRepository
from .utils import verificar_campos_preenchidos




class componentsMT:
    def render_tax_inputs(dados_impostos: Dict[str, Any]) -> Dict[str, Any]:
        """Renderiza os campos de entrada para impostos"""
        st.sidebar.header("Configuração de Impostos")

        # Inicializar session_state para o frete
        if 'frete_value' not in st.session_state:
            st.session_state['frete_value'] = dados_impostos.get('frete', 5.0)
        
        # Inicializa o tipo_frete no session_state se não existir
        if 'tipo_frete' not in st.session_state:
            st.session_state['tipo_frete'] = dados_impostos.get('tipo_frete', "CIF")

        # Valores básicos
        lucro = st.sidebar.number_input('Lucro (%):', 
                            min_value=0.0, 
                            max_value=100.0, 
                            step=0.1, 
                            value=dados_impostos.get('lucro', 5.0))
        
        icms = st.sidebar.number_input('ICMS (%):', 
                            min_value=0.0, 
                            max_value=100.0, 
                            step=0.1, 
                            value=dados_impostos.get('icms', 12.0))
        
        comissao = st.sidebar.number_input('Comissão (%):', 
                                min_value=0.0, 
                                step=0.1, 
                                value=dados_impostos.get('comissao', 5.0))

        # Callback para atualizar o valor do frete quando o tipo muda
        def on_tipo_frete_change():
            if st.session_state.select_tipo_frete == "FOB":
                st.session_state.frete_value = 0.0

        # Usar session_state para manter o tipo de frete
        tipo_frete = st.sidebar.selectbox(
            'Tipo de Frete:',
            ["FOB","CIF"],
            key='select_tipo_frete',
            on_change=on_tipo_frete_change,
            index=0 if st.session_state['tipo_frete'] == "FOB" else 1
        )
        st.session_state['tipo_frete'] = tipo_frete

        # Input do frete usando session_state
        frete = st.sidebar.number_input(
            'Frete (%):', 
            min_value=0.0, 
            step=0.1, 
            value=st.session_state.frete_value,
            key='frete_input'
        )
        
        # Atualiza o valor no session_state quando o usuário muda manualmente
        st.session_state.frete_value = frete
        st.session_state['local_entrega'] ="São Paulo/SP"

        if tipo_frete == "CIF":
            local_entrega = st.sidebar.selectbox(
                'Local de Entrega:', 
                st.session_state['cidades'], 
                key='select_local_entrega',
                index=st.session_state['cidades'].index(st.session_state['local_entrega'])
            )
            st.session_state['local_entrega'] = local_entrega

            if st.sidebar.button("Calcular Frete", key='btn_calcular_frete'):
                with st.spinner('Calculando frete...'):
                    resultado = distancia_cidade_capital(local_entrega)
                    if isinstance(resultado, tuple):
                        estado, distancia = resultado
                        percentual_frete = CalculoItemMT().calcular_percentual_frete(estado, distancia)
                        
                        if isinstance(percentual_frete, (int, float)) or (isinstance(percentual_frete, str) and percentual_frete.replace('.', '').isdigit()):
                            percentual_frete = float(percentual_frete)
                            st.session_state.frete_value = percentual_frete
                            frete = percentual_frete
                            st.success(f"Frete calculado: {percentual_frete:.1f}%")
                            st.rerun()

                        else:
                            st.warning(f"Frete para esta localidade precisa ser orçado. Por favor, entre em contato com o setor comercial.")
                    else:
                        st.error("Erro ao calcular distância")
        else:
            local_entrega = None

        contribuinte_icms = st.sidebar.radio(
            "O cliente é contribuinte do ICMS?",
            options=["Sim", "Não"],
            index=0 if dados_impostos.get('contribuinte_icms') != "Não" else 1
        )
        
        # Campos condicionais baseados na escolha do contribuinte
        difal = f_pobreza = 0.0
        if contribuinte_icms == "Não":
            difal = st.sidebar.number_input('DIFAL (%):', 
                                min_value=0.0, 
                                value=dados_impostos.get('difal', 0.0),
                                step=0.1)
            f_pobreza = st.sidebar.number_input('F. Pobreza (%):', 
                                    min_value=0.0,
                                    value=dados_impostos.get('f_pobreza', 0.0),
                                    step=0.1)
        
        return {
            'lucro': lucro,
            'icms': icms,
            'frete': frete,
            'comissao': comissao,
            'contribuinte_icms': contribuinte_icms,
            'difal': difal,
            'f_pobreza': f_pobreza,
            'tipo_frete': tipo_frete,
            'local_entrega': local_entrega if tipo_frete == "CIF" else None
        }

    def render_item_config(item_index: int, df: pd.DataFrame, item_data: Dict[str, Any], 
                        percentuais: float) -> Dict[str, Any]:
        

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
        st.subheader("Acessórios")
        
        acessorios_selecionados = []
        potencia = detalhes_item.get('potencia', 0)

        # Recuperar acessórios salvos anteriormente
        acessorios_salvos = item_data.get('acessorios', [])

        col1, col2 = st.columns(2)

        with col1:
            st.write("#### Valores Fixos")
            for acessorio in ACESSORIOS_FIXOS:
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

                valor_acessorio_com_percentuais = calcular_valor_acessorio_com_percentuais(acessorio['valor'], percentuais)
                
                # Verificar se este acessório estava selecionado anteriormente
                checkbox_key = f"acessorio_fixo_{item_index}_{acessorio['descricao']}"
                default_value = any(
                    ac['tipo'] == 'VALOR_FIXO' and ac['descricao'] == acessorio['descricao']
                    for ac in acessorios_salvos
                )
                
                if checkbox_key not in st.session_state:
                    st.session_state[checkbox_key] = default_value
                
                if st.checkbox(
                    f"{acessorio['descricao']} (+R$ {valor_acessorio_com_percentuais:,.2f})",
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
            st.write("#### Valores Percentuais")
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

        # Calcula os preços usando CalculoItemMT
        if 'dados_impostos' not in st.session_state:
            st.session_state['dados_impostos'] = {
                'difal': 0,
                'f_pobreza': 0,
                'icms': 0
            }

        calculo = CalculoItemMT(
            item_data=item_data, 
            percentuais=percentuais,
            dados_impostos=st.session_state['dados_impostos'],
            acessorios=acessorios_selecionados
        )
        preco_unitario = calculo.calcular_preco_item()
        preco_total = preco_unitario * quantidade

        item_data['Preço Unitário'] = preco_unitario
        item_data['Preço Total'] = preco_total

        # Exibe os preços calculados
        st.markdown("---")
        st.write(f"**Preço Unitário:** R$ {preco_unitario:,.2f}")
        st.write(f"**Preço Total:** R$ {preco_total:,.2f}")


        item = st.session_state['current_mt_item'] = {
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
                    'valor_unit': 0.0,
                    'valor_total': 0.0
                }
        

        # Remova esta parte que está recriando o item
# item = st.session_state['current_mt_item'] = { ... }

# Substitua o código do botão por:
        if st.button("Adicionar Item MT"):
            campos_vazios = verificar_campos_preenchidos(item, campos_obrigatorios=[
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