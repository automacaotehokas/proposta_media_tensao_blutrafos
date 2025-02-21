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
from decimal import Decimal
from services.document.mt.test import formatar_numero_inteiro_ou_decimal
from utils.formatters import formatar_numero_brasileiro

dotenv.load_dotenv()

def converter_para_float(valor):
    """Converte um valor monetário formatado para float"""
    if isinstance(valor, str):
        # Remove R$, pontos dos milhares e troca vírgula por ponto
        valor = valor.replace('R$ ', '').replace('.', '').replace(',', '.')
    return float(valor)

def selecionar_tipo_proposta():
    """Função para selecionar se é nova revisão ou atualização"""
    params = st.query_params
    
    # Verifica se está rodando no localhost:8501
    if st.get_option('server.port') == 8501:
        revisao_id = os.getenv("ID_REVISAO_TESTE")
    else:
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
    """Exibe uma tabela unificada com itens MT e BT."""
    if 'itens' not in st.session_state:
        st.session_state.itens = {
            'itens_configurados_mt': [],
            'itens_configurados_bt': []
        }

    # Criar DataFrames
    df_mt = pd.DataFrame(st.session_state.itens['itens_configurados_mt'])
    df_bt = pd.DataFrame(st.session_state.itens['itens_configurados_bt'])

    # Preparar dados para exibição
    dfs = []
    if not df_mt.empty:
        # Formatar descrição para MT
        df_mt['Descrição Completa'] = df_mt.apply(
            lambda row: f"{row['Descrição']} | IP: {row['IP']} | Tensão Primária: {row['Tensão Primária']}V | Tensão Secundária: {row['Tensão Secundária']}V", 
            axis=1
        )
        df_mt['tipo'] = 'MT'
        df_mt['origem_index'] = df_mt.index
        # Formatar valores monetários usando formatar_numero_brasileiro
        df_mt['Preço Unitário'] = df_mt['Preço Unitário'].apply(lambda x: f"R$ {formatar_numero_brasileiro(float(x))}")
        df_mt['Preço Total'] = df_mt['Preço Total'].apply(lambda x: f"R$ {formatar_numero_brasileiro(float(x))}")
        dfs.append(df_mt)

    if not df_bt.empty:
        # Formatar descrição para BT
        df_bt['Descrição Completa'] = df_bt.apply(
            lambda row: f"{row['Descrição']} | IP: {row['IP']} | Tensão Primária: {row['Tensão Primária']}V | Tensão Secundária: {row['Tensão Secundária']}V", 
            axis=1
        )
        df_bt['tipo'] = 'BT'
        df_bt['origem_index'] = df_bt.index
        # Formatar valores monetários usando formatar_numero_brasileiro
        df_bt['Preço Unitário'] = df_bt['Preço Unitário'].apply(lambda x: f"R$ {formatar_numero_brasileiro(float(x))}")
        df_bt['Preço Total'] = df_bt['Preço Total'].apply(lambda x: f"R$ {formatar_numero_brasileiro(float(x))}")
        dfs.append(df_bt)

    if not dfs:
        st.info("Nenhum item configurado ainda.")
        return

    df_unified = pd.concat(dfs, ignore_index=True)
    df_unified['index_exibicao'] = df_unified.index + 1

    # Exibir tabela
    cols = st.columns([6, 1, 1, 1])
    with cols[0]:
        st.dataframe(
            df_unified[[
                'index_exibicao', 'tipo', 'Descrição Completa',
                'Quantidade', 'Preço Unitário', 'Preço Total'
            ]].rename(columns={
                'index_exibicao': 'Item',
                'tipo': 'Tipo',
                'Descrição Completa': 'Descrição',
                'Quantidade': 'Quantidade',
                'Preço Unitário': 'Valor Unitário',
                'Preço Total': 'Valor Total'
            }),
            height=400,
            use_container_width=True
        )

    # Botões de Edição/Exclusão
    with cols[1]:
        st.write("")
        for idx, row in df_unified.iterrows():
            if st.button(
                "✏️", 
                key=f"edit_{row['tipo']}_{row['origem_index']}",
                help="Editar item"
            ):
                if row['tipo'] == 'MT':
                    st.session_state.editando_item_mt = {
                        'index': row['origem_index'],
                        'dados': st.session_state.itens['itens_configurados_mt'][row['origem_index']]
                    }
                else:
                    st.session_state.editando_item_bt = {
                        'index': row['origem_index'],
                        'dados': st.session_state.itens['itens_configurados_bt'][row['origem_index']]
                    }
                st.session_state['pagina_atual'] = 'configuracao'
                st.rerun()

    with cols[2]:
        st.write("")
        for idx, row in df_unified.iterrows():
            if st.button(
                "🗑️", 
                key=f"del_{row['tipo']}_{row['origem_index']}",
                help="Excluir item"
            ):
                if row['tipo'] == 'MT':
                    st.session_state.itens['itens_configurados_mt'].pop(row['origem_index'])
                else:
                    st.session_state.itens['itens_configurados_bt'].pop(row['origem_index'])
                st.rerun()

    # Exibir totais
    total_mt = formatar_numero_brasileiro(float(df_mt['Preço Total'].iloc[0].replace('R$ ', '').replace('.', '').replace(',', '.'))) if not df_mt.empty else "0"
    total_bt = formatar_numero_brasileiro(float(df_bt['Preço Total'].iloc[0].replace('R$ ', '').replace('.', '').replace(',', '.'))) if not df_bt.empty else "0"


    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total MT", f"R$ {total_mt}")
    with col2:
        st.metric("Total BT", f"R$ {total_bt}")
    with col3:
        # Convertendo strings para float para soma correta
        total_mt_float = float(total_mt.replace('.', '').replace(',', '.'))
        total_bt_float = float(total_bt.replace('.', '').replace(',', '.'))
        total_geral = total_mt_float + total_bt_float
        # Formatando o total geral usando formatar_numero_brasileiro
        st.metric("Total Geral", f"R$ {formatar_numero_brasileiro(total_geral)}")




    
    # st.divider()

        
        
        
    # total_mt = df_mt['Preço Total'].sum() if not df_mt.empty else 0
    # total_bt = df_bt['Preço Total'].sum() if not df_mt.empty else 0
    
import logging

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

def carregar_dados_revisao(revisao_id: str):
    """Carrega dados de uma revisão existente com tratamento para JSON duplamente codificado"""
    logger = logging.getLogger(__name__)
    logger.info(f"Iniciando carregamento da revisão: {revisao_id}")
    
    conn = DatabaseConfig.get_connection()
    cur = conn.cursor()
    
    try:
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
        
        logger.info(f"Executando query com revisao_id: {revisao_id}")
        cur.execute(query, (revisao_id,))
        resultado = cur.fetchone()
        
        if resultado:
            logger.info("Dados encontrados no banco")
            conteudo, numero_revisao, cliente, proposta, obra, dt_oferta, contato = resultado
            logger.info(f"Número da revisão: {numero_revisao}")
            logger.info(f"Cliente: {cliente}")
            logger.info(f"Proposta: {proposta}")
            
            if conteudo:
                try:
                    # Primeiro decode: converter para string JSON
                    logger.info("Primeiro decode: convertendo dados do banco")
                    logger.info(f"Tipo do conteúdo original: {type(conteudo)}")
                    logger.info(f"Primeiros 100 caracteres do conteúdo: {str(conteudo)[:100]}")
                    
                    if isinstance(conteudo, str):
                        primeiro_decode = json.loads(conteudo)
                        logger.info(f"Tipo após primeiro decode: {type(primeiro_decode)}")
                        logger.info(f"Estrutura após primeiro decode: {list(primeiro_decode.keys()) if isinstance(primeiro_decode, dict) else 'Não é um dicionário'}")
                        
                        # Se ainda é string, precisa de segundo decode
                        if isinstance(primeiro_decode, str):
                            logger.info("Segundo decode necessário")
                            dados = json.loads(primeiro_decode)
                            logger.info(f"Estrutura após segundo decode: {list(dados.keys()) if isinstance(dados, dict) else 'Não é um dicionário'}")
                        else:
                            dados = primeiro_decode
                    else:
                        dados = conteudo

                    logger.info(f"Tipo final dos dados: {type(dados)}")
                    logger.info(f"Chaves disponíveis: {dados.keys() if isinstance(dados, dict) else 'Não é um dicionário'}")

                    # Garante que temos um dicionário
                    if not isinstance(dados, dict):
                        logger.error(f"Dados finais não são um dicionário: {type(dados)}")
                        return False

                    # Inicializa a estrutura de itens
                    logger.info("Inicializando estrutura de itens")
                    st.session_state['itens'] = {
                        'itens_configurados_mt': dados.get('itens_configurados_mt', []),
                        'itens_configurados_bt': dados.get('itens_configurados_bt', [])
                    }
                    
                    # Log detalhado dos itens
                    logger.info(f"Quantidade de itens MT: {len(st.session_state['itens']['itens_configurados_mt'])}")
                    if st.session_state['itens']['itens_configurados_mt']:
                        logger.info(f"Primeiro item MT: {st.session_state['itens']['itens_configurados_mt'][0]}")
                    
                    logger.info(f"Quantidade de itens BT: {len(st.session_state['itens']['itens_configurados_bt'])}")
                    if st.session_state['itens']['itens_configurados_bt']:
                        logger.info(f"Primeiro item BT: {st.session_state['itens']['itens_configurados_bt'][0]}")

                    # Carrega dados iniciais
                    if 'dados_iniciais' in dados:
                        logger.info("Carregando dados iniciais do JSON")
                        st.session_state['dados_iniciais'] = dados['dados_iniciais']
                        logger.info(f"Dados iniciais carregados: {st.session_state['dados_iniciais']}")
                    else:
                        logger.info("Criando dados iniciais a partir do banco")
                        dt = dt_oferta or datetime.now()
                        st.session_state['dados_iniciais'] = {
                            'cliente': cliente,
                            'bt': str(proposta),
                            'obra': obra,
                            'id_proposta': id_proposta,
                            'rev': str(numero_revisao).zfill(2),
                            'dia': dt.strftime('%d'),
                            'mes': dt.strftime('%m'),
                            'ano': dt.strftime('%Y'),
                            'nomeCliente': contato,
                            'email': '',
                            'fone': '',
                            'local_frete': 'São Paulo/SP'
                        }
                        logger.info(f"Dados iniciais criados: {st.session_state['dados_iniciais']}")

                    # Carrega outros dados
                    chaves_para_carregar = [
                        'impostos', 
                        'eventos_pagamento',
                        'prazo_entrega',
                        'desvios'
                    ]
                    
                    logger.info("Carregando outras configurações")
                    for chave in chaves_para_carregar:
                        if chave in dados:
                            st.session_state[chave] = dados[chave]
                            logger.info(f"Carregado {chave}: {st.session_state[chave]}")
                        else:
                            logger.warning(f"Chave {chave} não encontrada nos dados")

                    # Marca como carregado
                    st.session_state['revisao_loaded'] = True
                    st.session_state['revisao_atual'] = revisao_id
                    
                    logger.info("Carregamento concluído com sucesso")
                    logger.info(f"Estado final do session_state: {list(st.session_state.keys())}")
                    return True
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Erro ao decodificar JSON: {e}")
                    logger.error(f"Conteúdo problemático: {conteudo[:200]}")  # Mostra os primeiros 200 caracteres
                    return False
                except Exception as e:
                    logger.error(f"Erro inesperado ao processar dados: {e}")
                    return False
        else:
            logger.error(f"Nenhum resultado encontrado para revisao_id: {revisao_id}")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao carregar revisão: {e}")
        return False
    finally:
        cur.close()
        conn.close()
        logger.info("Conexão com o banco fechada")


def verificar_carregamento(id_revisao):
    """Função auxiliar para verificar o carregamento dos dados"""
    if id_revisao:
        success = carregar_dados_revisao(id_revisao)
        if success:
            logger.info("Verificando dados carregados:")
            
            status = {
                "Itens MT": len(st.session_state.itens.get('itens_configurados_mt', [])),
                "Itens BT": len(st.session_state.itens.get('itens_configurados_bt', [])),
                "Dados Iniciais": 'dados_iniciais' in st.session_state,
                "Impostos": 'impostos' in st.session_state,
                "Eventos": 'eventos_pagamento' in st.session_state,
                "Prazo Entrega": 'prazo_entrega' in st.session_state,
                "Desvios": 'desvios' in st.session_state
            }
            
            for key, value in status.items():
                logger.info(f"{key}: {value}")
            
            return status
        else:
            logger.error("Falha no carregamento dos dados")
            return None
    return None


def inicializar_dados():
    try:
        print("Iniciando função inicializar_dados()")
        
        if not selecionar_tipo_proposta():
            print("Tipo de proposta não selecionado, retornando")
            return
            
        params = st.query_params
        usuario = params.get('usuario')
        print(f"Parâmetros URL: {params}")
        print(f"Usuário encontrado: {usuario}")
        
        if usuario:
            st.session_state['usuario'] = usuario.replace("+", " ")
        else:
            st.session_state['usuario'] = ""
        print(f"Usuário definido na session_state: {st.session_state['usuario']}")

        if st.session_state.get('app_initialized'):
            print("App já inicializado, retornando")
            return

        # Verifica se está rodando no localhost:8501
        if st.get_option('server.port') == 8501:
            id_proposta = os.getenv("ID_PROPOSTA_TESTE")
            id_revisao = os.getenv("ID_REVISAO_TESTE")
            token = os.getenv("TOKEN_TESTE")
        else:
            id_proposta = params.get('id_proposta')
            id_revisao = params.get('id_revisao')
            token = params.get('token')
            
        print(f"ID Proposta carregado: {id_proposta}")
        print(f"ID Revisão carregado: {id_revisao}")
        print(f"Token encontrado: {token}")
        
        st.session_state['id_proposta'] = id_proposta
        st.session_state['token'] = token

        # Se tiver id_revisao, tenta carregar os dados da revisão
        if id_revisao:
            print(f"Tentando carregar dados da revisão: {id_revisao}")
            status = verificar_carregamento(id_revisao)
            if status:
                print(f"Dados da revisão carregados com sucesso: {status}")
                st.session_state['proposta_loaded'] = True
                st.session_state['revisao_loaded'] = True
                st.session_state['app_initialized'] = True
                return
            else:
                print("Falha ao carregar dados da revisão")

        # Se não tiver id_revisao ou falhar o carregamento, carrega dados da proposta
        if id_proposta and not st.session_state.get('proposta_loaded'):
            print("Iniciando carregamento da proposta do banco")
            conn = DatabaseConfig.get_connection()
            try:
                with conn.cursor() as cur:
                    if not st.session_state.get('revisao_numero_definido'):
                        print("Buscando última revisão")
                        cur.execute("""
                            SELECT MAX(CAST(revisao AS INTEGER))
                            FROM revisoes 
                            WHERE id_proposta_id = %s
                        """, (id_proposta,))
                        
                        ultima_revisao = cur.fetchone()[0]
                        print(f"Última revisão encontrada: {ultima_revisao}")
                        proxima_revisao = str(ultima_revisao + 1 if ultima_revisao is not None else 0).zfill(2)
                        print(f"Próxima revisão definida: {proxima_revisao}")
                        
                        print("Buscando dados da proposta")
                        cur.execute("""
                            SELECT proposta, cliente, obra, contato
                            FROM propostas 
                            WHERE id_proposta = %s
                        """, (id_proposta,))
                        
                        resultado = cur.fetchone()
                        print(f"Resultado da busca: {resultado}")
                        if resultado:
                            proposta, cliente, obra, contato = resultado
                            
                            dados_iniciais = {
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
                            print(f"Dados iniciais montados: {dados_iniciais}")
                            
                            st.session_state['dados_iniciais'] = dados_iniciais
                            st.session_state['revisao_numero_definido'] = True
                            st.session_state['proposta_loaded'] = True
            finally:
                conn.close()
                print("Conexão com banco fechada")
        
        st.session_state['app_initialized'] = True
        print("Inicialização concluída com sucesso")
            
    except Exception as e:
        print(f"Erro detalhado na inicialização: {str(e)}")
        st.error(f"Erro ao inicializar dados: {str(e)}")


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
        campos_vazios = [k for k, v in dados.items() if not v and k not in ['id_proposta', 'dia', 'mes', 'ano','comentario','obra']]
        if campos_vazios:
            st.error("Por favor, preencha todos os campos obrigatórios:")
            for campo in campos_vazios:
                st.warning(f"• {campo}")
            return False
        
        st.session_state['configuracao_inicial_completa'] = True
        st.rerun()
    return False

def main():
    """Função principal da aplicação"""
    st.set_page_config(layout="wide")
    st.title("Proposta Automatizada - Transformadores")
    st.markdown("---")
    
    # Verifica se está rodando no localhost:8501
    if st.get_option('server.port') == 8501:
        st.session_state['id_proposta'] = os.getenv("ID_PROPOSTA_TESTE")
        st.session_state['id_revisao'] = os.getenv("ID_REVISAO_TESTE")
    
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