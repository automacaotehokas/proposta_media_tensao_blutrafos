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
