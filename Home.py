import streamlit as st
import pandas as pd
import os
import json
from dotenv import load_dotenv
from repositories.custos_media_tensao_repository import CustoMediaTensaoRepository
from pages.inicial.view import carregar_cidades
from config.databaseMT import DatabaseConfig
from pages.pagamento_entrega.view import pagina_configuracao_eventos
from pages.configuracao_itens.view import pagina_configuracao
from pages.resumo.view import pagina_resumo
from pages.adm.view import admin_section
from datetime import datetime
import dotenv
from streamlit.components.v1 import html as components_html

dotenv.load_dotenv()

def selecionar_tipo_proposta():
    """Função para selecionar se é nova revisão ou atualização"""
    params = st.query_params
    # revisao_id = params.get("id_revisao")
    revisao_id = os.getenv("ID_REVISAO_TESTE")
    
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
    """Exibe uma tabela unificada com itens MT e BT."""
    if 'itens' not in st.session_state:
        st.session_state.itens = {'itens_configurados_mt': [], 'itens_configurados_bt': []}
    
    # Criar DataFrames para MT e BT
    df_mt = pd.DataFrame(st.session_state['itens']['itens_configurados_mt'])
    df_bt = pd.DataFrame(st.session_state['itens']['itens_configurados_bt'])
 
    # Verificar se há itens configurados
    if df_mt.empty and df_bt.empty:
        st.info("Nenhum item configurado ainda.")
        return
 
    # Preparar os DataFrames
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
    df_unified['index_exibicao'] = range(1, len(df_unified) + 1)

    # Criar colunas para exibição
    df_display = pd.DataFrame({
        'Item': df_unified['index_exibicao'],
        'Tipo': df_unified['tipo'],
        'Descrição': df_unified['descricao'],
        'Quantidade': df_unified['quantidade'],
        'Valor Unitário': df_unified['valor_unit'].apply(lambda x: f"R$ {x:,.2f}"),
        'Valor Total': df_unified['valor_total'].apply(lambda x: f"R$ {x:,.2f}"),
    })

    # Criar coluna de botões usando st.columns
    cols = st.columns([7, 1])  # 7 para a tabela, 1 para os botões
    
    with cols[0]:
        st.dataframe(
            df_display,
            hide_index=True,
            height=400,
            use_container_width=True
        )
    
    with cols[1]:
        st.write("")  # Espaço para alinhar com o cabeçalho da tabela
        for idx, row in df_unified.iterrows():
            if st.button("🗑️", key=f"delete_{row['tipo']}_{row['origem_index']}"):
                if row['tipo'] == 'MT':
                    st.session_state['itens']['itens_configurados_mt'].pop(int(row['origem_index']))
                else:
                    st.session_state['itens']['itens_configurados_bt'].pop(int(row['origem_index']))
                st.rerun()

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
                
                # Inicializar a estrutura de itens se não existir
                if 'itens' not in st.session_state:
                    st.session_state.itens = {
                        'itens_configurados_mt': [],
                        'itens_configurados_bt': []
                    }
                
                # Carregar dados na nova estrutura
                if 'itens_configurados_mt' in dados:
                    st.session_state.itens['itens_configurados_mt'] = dados['itens_configurados_mt']
                elif 'itens_configurados' in dados:  # Compatibilidade com dados antigos
                    st.session_state.itens['itens_configurados_mt'] = dados['itens_configurados']
                
                if 'itens_configurados_bt' in dados:
                    st.session_state.itens['itens_configurados_bt'] = dados['itens_configurados_bt']
                
                # Carregar outros dados
                for key in ['configuracoes_itens', 'impostos', 'dados_iniciais']:
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
                
                # Inicializar itens vazios
                st.session_state.itens = {
                    'itens_configurados_mt': [],
                    'itens_configurados_bt': []
                }
            
            st.session_state['revisao_loaded'] = True
            st.session_state['revisao_atual'] = revisao_id
            
        cur.close()
        conn.close()
        
    except Exception as e:
        st.error(f"Erro ao carregar revisão: {str(e)}")
        raise e

def inicializar_dados():
    """Inicia os dados da proposta com base nos parâmetros da URL"""
    try:
        if not selecionar_tipo_proposta():
            return
            
        params = st.query_params
        
        # Se já foi inicializado, mantém os dados existentes
        if st.session_state.get('app_initialized'):
            return

        # id_revisao = params.get('id_revisao')
        id_revisao = os.getenv("ID_REVISAO_TESTE")
        st.session_state['id_revisao'] = id_revisao

        # id_proposta = params.get('id_proposta')   
        id_proposta = os.getenv("ID_PROPOSTA_TESTE")    
        st.session_state['id_proposta'] = id_proposta

        token = os.getenv("TOKEN_TESTE")
        st.session_state['token'] = token

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


def configurar_dados_iniciais():
    """Configura os dados iniciais necessários"""
    dados = st.session_state['dados_iniciais']
    
    st.subheader("Configure os dados iniciais")
    col1, col2 = st.columns(2)
    
    with col1:
        dados['bt'] = st.text_input('Nº BT:', dados.get('bt', ''), autocomplete='off')
        dados['cliente'] = st.text_input('Cliente:', dados.get('cliente', ''), 
                                       autocomplete='off', placeholder='Digite o nome da empresa')
        dados['obra'] = st.text_input('Obra:', dados.get('obra', ''), autocomplete='off')
        dados['rev'] = st.text_input('Rev:', dados.get('rev', ''), autocomplete='off')
    
    with col2:
        dados['nomeCliente'] = st.text_input('Nome do Contato:', dados.get('nomeCliente', ''),
                                           autocomplete='off', placeholder='Digite o nome do contato')
        dados['email'] = st.text_input('E-mail do Contato:', dados.get('email', ''), autocomplete='off')
        fone = st.text_input('Telefone do Contato:', dados.get('fone', ''),
                           max_chars=15, autocomplete='off',
                           placeholder="Digite sem formação, exemplo: 47999998888")
        from pages.inicial.utils import aplicar_mascara_telefone
        dados['fone'] = aplicar_mascara_telefone(fone)
        dados['local_frete'] = st.selectbox('Local Frete:', st.session_state['cidades'])
    
    # Data atual
    from datetime import datetime
    from pages.inicial.utils import get_meses_pt
    data_hoje = datetime.today()
    dados.update({
        'dia': data_hoje.strftime('%d'),
        'mes': get_meses_pt()[data_hoje.month],
        'ano': data_hoje.strftime('%Y'),
    })
    
    if st.button("Continuar", type="primary"):
        # Verifica campos obrigatórios
        campos_vazios = [k for k, v in dados.items() if not v and k not in ['id_proposta', 'dia', 'mes', 'ano','comentario']]
        if campos_vazios:
            st.error("Por favor, preencha todos os campos obrigatórios:")
            for campo in campos_vazios:
                st.warning(f"• {campo}")
            return False
        
        st.session_state['configuracao_inicial_completa'] = True
        st.rerun()
    return False
    
    return True

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
        
        # Verifica se já completou a configuração inicial
        if st.session_state.get('configuracao_inicial_completa'):
            dados = st.session_state['dados_iniciais']
            if dados.get('cliente'):
                st.success(f" Proposta {dados.get('bt')} - {dados.get('cliente')} - {dados.get('obra')}")
            
            # Sidebar navigation
            st.sidebar.title('Navegação')
            selection = st.sidebar.radio("Ir para", ["Configuração de Itens", "Entrega/Pagamento/Desvio", "Resumo", "Administrativo"])
            
            # Render selected page
            PAGES[selection]()
            
            # Show unified table if there are items
            st.markdown("---")
            exibir_tabela_unificada()
        else:
            configurar_dados_iniciais()

PAGES = {
    "Configuração de Itens": pagina_configuracao,
    "Entrega/Pagamento/Desvio": pagina_configuracao_eventos,
    "Resumo": pagina_resumo,
    "Administrativo": admin_section
}

if __name__ == "__main__":
    load_dotenv()
    main()
