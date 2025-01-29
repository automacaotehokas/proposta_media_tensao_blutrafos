import streamlit as st
import pandas as pd
import os
import json
from dotenv import load_dotenv
from repositories.custos_media_tensao_repository import CustoMediaTensaoRepository
from pages.inicial.view import carregar_cidades
from config.databaseMT import DatabaseConfig
from pages.inicial.view import pagina_inicial
from pages.configuracao_itens.view import pagina_configuracao
from pages.resumo.view import pagina_resumo
from pages.adm.view import admin_section
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder

def selecionar_tipo_proposta():
    """Função para selecionar se é nova revisão ou atualização"""
    params = st.query_params
    revisao_id = params.get("id_revisao")
    
    # Se não tem id_revisao, define automaticamente como nova revisão
    if not revisao_id:
        if 'tipo_proposta' not in st.session_state:
            st.session_state['tipo_proposta'] = "Nova revisão"
            st.session_state['tipo_proposta_selecionado'] = True
        return True
    
    # Se tem id_revisao, mostra a seleção visual
    if 'tipo_proposta_selecionado' not in st.session_state:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.write("## Selecione o tipo de revisão")
            tipo = st.radio(
                "Escolha uma opção:",
                ["Nova revisão", "Atualizar revisão"],
                label_visibility="collapsed"
            )
            if st.button("Continuar"):
                st.session_state['tipo_proposta'] = tipo
                st.session_state['tipo_proposta_selecionado'] = True
                st.rerun()
        return False
    return True


 
def exibir_tabela_unificada():
    """
    Exibe uma tabela unificada com itens MT e BT, permitindo ordenação e exclusão.
    """
    if 'itens' not in st.session_state:
        st.session_state.itens = []
    if 'itens_configurados_mt' not in st.session_state.itens:
        st.session_state.itens_configurados_mt = []
    if 'itens_configurados_bt' not in st.session_state.itens:
        st.session_state.itens_configurados_bt = []
 
    # Criar DataFrames para MT e BT
    df_mt = pd.DataFrame(st.session_state['itens']['itens_configurados_mt'])
    df_bt = pd.DataFrame(st.session_state['itens']['itens_configurados_bt'])
 
    # Verificar se há itens configurados
    if df_mt.empty and df_bt.empty:
        st.info("Nenhum item configurado ainda.")
        return
 
    # Adicionar coluna de tipo e índice original
    if not df_mt.empty:
        df_mt['tipo'] = 'MT'
        df_mt['origem_index'] = range(len(df_mt))
        df_mt = df_mt.rename(columns={
            'Descrição': 'descricao',
            'Quantidade': 'quantidade',
            'Preço Unitário': 'valor_unit',
            'Preço Total': 'valor_total'
        })
 
    if not df_bt.empty:
        df_bt['tipo'] = 'BT'
        df_bt['origem_index'] = range(len(df_bt))
        df_bt = df_bt.rename(columns={
            'Descrição': 'descricao',
            'Quantidade': 'quantidade',
            'Preço Unitário': 'valor_unit',
            'Preço Total': 'valor_total'
        })
 
    # Concatenar os DataFrames
    df_unified = pd.concat([df_mt, df_bt], ignore_index=True)
 
    # Adicionar coluna para ordenação
    df_unified['index_exibicao'] = range(1, len(df_unified) + 1)  # Começa do 1
    # Criar o dataframe para exibição com AgGrid
    gb = GridOptionsBuilder.from_dataframe(df_unified[['index_exibicao', 'tipo', 'descricao', 'quantidade', 'valor_unit', 'valor_total']])
    # Configurar colunas
    gb.configure_column('index_exibicao', 
                       header='Ordem',
                       editable=True,
                       type=["numericColumn", "numberColumnFilter", "customNumericFormat"],
                       valueFormatter="data.index_exibicao")
    gb.configure_column('tipo', header='Tipo', editable=False)
    gb.configure_column('descricao', header='Descrição', editable=False)
    gb.configure_column('quantidade', header='Quantidade', editable=False)
    gb.configure_column('valor_unit', 
                       header='Valor Unitário',
                       editable=False,
                       valueFormatter="'R$ ' + data.valor_unit.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})")
    gb.configure_column('valor_total',
                       header='Valor Total',
                       editable=False,
                       valueFormatter="'R$ ' + data.valor_total.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})")
    gb.configure_grid_options(
        rowDragManaged=True,
        animateRows=True,
        enableRangeSelection=True,
        enableCellChangeFlash=True
    )
    grid_response = AgGrid(
        df_unified,
        gridOptions=gb.build(),
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=True,
        theme='streamlit'
    )
    # Se houve mudança na ordem
    if grid_response['data'] is not None:
        new_df = pd.DataFrame(grid_response['data'])
        # Verifica se houve alteração nos índices
        if not new_df['index_exibicao'].equals(df_unified['index_exibicao']):
            # Ordena pelo novo índice
            new_df = new_df.sort_values('index_exibicao')
            # Atualizar os session states com a nova ordem
            mt_items = []
            bt_items = []
            for _, row in new_df.iterrows():
                if row['tipo'] == 'MT':
                    mt_items.append(st.session_state.itens_configurados_mt[int(row['origem_index'])])
                else:
                    bt_items.append(st.session_state.itens_configurados_bt[int(row['origem_index'])])
            # Atualiza as listas no session state
            st.session_state.itens_configurados_mt = mt_items
            st.session_state.itens_configurados_bt = bt_items
            # Removido st.rerun() daqui pois já existe no componentsMT
    # Exibir totais
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        total_mt = df_mt['valor_total'].sum() if not df_mt.empty else 0
        st.metric("Total MT", f"R$ {total_mt:,.2f}")
    with col2:
        total_bt = df_bt['valor_total'].sum() if not df_bt.empty else 0
        st.metric("Total BT", f"R$ {total_bt:,.2f}")
    with col3:
        total_geral = total_mt + total_bt
        st.metric("Total Geral", f"R$ {total_geral:,.2f}")
    # Botões de excluir com confirmação
    for idx, row in df_unified.iterrows():
        col1, col2 = st.columns([4, 1])
        with col1:
            st.text(f"{row['tipo']} - {row['descricao']}")
        with col2:
            if st.button('🗑️', key=f'del_{idx}'):
                if 'item_to_delete' not in st.session_state:
                    st.session_state.item_to_delete = None
                st.session_state.item_to_delete = (row['tipo'], int(row['origem_index']))
                st.rerun()
    # Confirmação de exclusão
    if hasattr(st.session_state, 'item_to_delete') and st.session_state.item_to_delete:
        tipo, idx = st.session_state.item_to_delete
        st.warning(f"Confirma a exclusão do item {tipo}?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sim"):
                if tipo == 'MT' and idx < len(st.session_state.itens.itens_configurados_mt):
                    st.session_state.itens.itens_configurados_mt.pop(idx)
                elif tipo == 'BT' and idx < len(st.session_state.itens.itens_configurados_bt):
                    st.session_state.itens.itens_configurados_bt.pop(idx)
                st.session_state.item_to_delete = None
                st.rerun()
        with col2:
            if st.button("Não"):
                st.session_state.item_to_delete = None
                st.rerun()

def carregar_dados_revisao(revisao_id: str):
    """Carrega dados de uma revisão existente"""
    try:
        conn = DatabaseConfig.get_connection()
        cur = conn.cursor()
        
        query = """
            SELECT 
                r.conteudo::text, 
                r.revisao, 
                p.cliente, 
                p.proposta, 
                p.obra,
                p.dt_oferta,
                p.contato
            FROM revisoes r 
            JOIN propostas p ON r.id_proposta_id = p.id_proposta 
            WHERE r.id_revisao = %s
        """
        
        cur.execute(query, (revisao_id,))
        resultado = cur.fetchone()
        
        if resultado:
            conteudo_json, numero_revisao, cliente, proposta, obra, dt_oferta, contato = resultado
            
            if conteudo_json:
                dados = json.loads(conteudo_json)
                for key in ['configuracoes_itens', 'impostos', 
                          'itens_configurados', 'dados_iniciais']:
                    if key in dados:
                        st.session_state[key] = dados[key]
            else:
                dt = dt_oferta or datetime.now()
                st.session_state['dados_iniciais'] = {
                    'cliente': cliente,
                    'bt': str(proposta),
                    'obra': obra,
                    'rev': str(numero_revisao).zfill(2),
                    'dia': dt.strftime('%d'),
                    'mes': dt.strftime('%m'),
                    'ano': dt.strftime('%Y'),
                    'nomeCliente': contato,
                    'email': '',
                    'fone': '',
                    'local_frete': 'São Paulo/SP'
                }
            
            st.session_state['revisao_loaded'] = True
            st.session_state['revisao_atual'] = revisao_id
            
        cur.close()
        conn.close()
        
    except Exception as e:
        st.error(f"Erro ao carregar dados da revisão: {str(e)}")

def inicializar_dados():
    """
    Inicializa dados da proposta baseado nos parâmetros da URL.
    O número da revisão é definido apenas uma vez no início.
    """
    try:
        if not selecionar_tipo_proposta():
            return
            
        params = st.query_params
        
        # Se já foi inicializado, mantém os dados existentes
        if st.session_state.get('app_initialized'):
            return

        id_revisao = params.get('id_revisao')
        st.session_state['id_revisao'] = id_revisao

        id_proposta = params.get('id_proposta')       
        st.session_state['id_proposta'] = id_proposta

        if id_revisao:
            # Carrega dados da revisão existente
            carregar_dados_revisao(id_revisao)
            
            # Calcula próxima revisão APENAS se for nova revisão e primeira inicialização
            if (st.session_state.get('tipo_proposta') == "Nova revisão" and 
                not st.session_state.get('revisao_numero_definido')):
                conn = DatabaseConfig.get_connection()
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT MAX(CAST(revisao AS INTEGER))
                            FROM revisoes 
                            WHERE id_proposta_id = (
                                SELECT id_proposta_id 
                                FROM revisoes 
                                WHERE id_revisao = %s
                            )
                        """, (id_revisao,))
                        
                        ultima_revisao = cur.fetchone()[0]
                        proxima_revisao = str(ultima_revisao + 1 if ultima_revisao is not None else 0).zfill(2)
                        st.session_state['dados_iniciais']['rev'] = proxima_revisao
                        st.session_state['revisao_numero_definido'] = True
                finally:
                    conn.close()
            
        elif id_proposta and not st.session_state.get('proposta_loaded'):
            conn = DatabaseConfig.get_connection()
            try:
                with conn.cursor() as cur:
                    # Busca a última revisão se ainda não foi definida
                    if not st.session_state.get('revisao_numero_definido'):
                        cur.execute("""
                            SELECT MAX(CAST(revisao AS INTEGER))
                            FROM revisoes 
                            WHERE id_proposta_id = %s
                        """, (id_proposta,))
                        
                        ultima_revisao = cur.fetchone()[0]
                        proxima_revisao = str(ultima_revisao + 1 if ultima_revisao is not None else 0).zfill(2)
                        
                        # Busca dados da proposta
                        cur.execute("""
                            SELECT 
                                proposta,
                                cliente,
                                obra,
                                contato
                            FROM propostas 
                            WHERE id_proposta = %s
                        """, (id_proposta,))
                        
                        resultado = cur.fetchone()
                        if resultado:
                            proposta, cliente, obra, contato = resultado
                            
                            st.session_state['dados_iniciais'] = {
                                'cliente': cliente,
                                'bt': proposta,
                                'obra': obra,
                                'id_proposta': id_proposta,
                                'rev': proxima_revisao,
                                'dia': st.session_state.get('dia', ''),
                                'mes': st.session_state.get('mes', ''),
                                'ano': st.session_state.get('ano', ''),
                                'nomeCliente': contato,
                                'email': '',
                                'fone': '',
                                'local_frete': 'São Paulo/SP'
                            }
                            
                            st.session_state['revisao_numero_definido'] = True
                            st.session_state['proposta_loaded'] = True
            finally:
                conn.close()
        
        st.session_state['app_initialized'] = True
            
    except Exception as e:
        st.error(f"Erro ao inicializar dados: {str(e)}")
        print(f"Erro detalhado: {str(e)}")


def main():
    """Função principal da aplicação"""
    st.set_page_config(layout="wide")
    st.title("Proposta Automatizada - Transformadores")
    st.markdown("---")
    
    if selecionar_tipo_proposta():
        carregar_cidades()
        
        st.session_state.setdefault('dados_iniciais', {
            'cliente': '',
            'bt': '',
            'obra': '',
            'id_proposta': '',
            'rev': '00',
            'dia': '',
            'mes': '',
            'ano': '',
            'nomeCliente': '',
            'email': '',
            'fone': '',
            'local_frete': 'São Paulo/SP'
        })

        inicializar_dados()
        
        if 'dados_iniciais' in st.session_state:
            st.info(f"""
            Cliente: {st.session_state['dados_iniciais'].get('cliente')}
            Proposta: {st.session_state['dados_iniciais'].get('bt')}
            Obra: {st.session_state['dados_iniciais'].get('obra')}
            """)
        else:
            st.markdown("""
            Bem-vindo à Proposta Automatizada de Média Tensão. Este sistema foi desenvolvido para facilitar
            o processo de criação de propostas comerciais personalizadas. Com ele, você pode configurar
            itens técnicos, calcular preços e gerar documentos de forma automatizada.
            """)


        st.sidebar.title('Navegação')
        selection = st.sidebar.radio("Ir para", list(PAGES.keys()))
        page = PAGES[selection]
        page()
        
        st.markdown("---")

        exibir_tabela_unificada()
        
        ### Configuração das páginas
PAGES = {
    "Inicial": pagina_inicial,
    "Configuração de Itens": pagina_configuracao,
    "Resumo": pagina_resumo,
    "Administrativo": admin_section
}

if __name__ == "__main__":
    load_dotenv()
    main()
