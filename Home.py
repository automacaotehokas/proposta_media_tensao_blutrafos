import streamlit as st
import pandas as pd
import os
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
from pages.pagamento_entrega.components import ComponentsPagamentoEntrega
import json
from decimal import Decimal

dotenv.load_dotenv()


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)  # Converte Decimal para float
        return super(DecimalEncoder, self).default(obj)
    

def converter_para_float(valor):
    """Converte um valor monetário formatado para float"""
    if isinstance(valor, str):
        # Remove R$, pontos dos milhares e troca vírgula por ponto
        valor = valor.replace('R$ ', '').replace('.', '').replace(',', '.')
    return float(valor)

def selecionar_tipo_proposta():
    """Função para selecionar se é nova revisão ou atualização"""
    params = st.query_params
    
    if os.getenv('ENVIRONMENT') == 'PRODUCTION':
        id_proposta = params.get('id_proposta')
        id_revisao = params.get('id_revisao')
        token = params.get('token')
    else:
        # Ambiente de desenvolvimento ou local
        id_proposta = os.getenv("ID_PROPOSTA_TESTE")
        id_revisao = os.getenv("ID_REVISAO_TESTE")
        token = os.getenv("TOKEN_TESTE")
    
    # Se não tem id_revisao, define automaticamente como nova revisão
    if not id_revisao:
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
                carregar_dados_revisao(st.session_state["id_revisao"])
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

    # Calcular a soma total para MT
    if not df_mt.empty:
        # 1. Converter a coluna 'Preço Total' para float
        total_mt_numeric = df_mt['Preço Total'].str.replace('R$ ', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
        # 2. Somar os valores
        soma_total_mt = total_mt_numeric.sum()
        # 3. Formatar o resultado
        total_mt_formatado = formatar_numero_brasileiro(soma_total_mt)
    else:
        soma_total_mt = 0.0
        total_mt_formatado = formatar_numero_brasileiro(0) # Ou "0,00"

    # Calcular a soma total para BT
    if not df_bt.empty:
        # 1. Converter a coluna 'Preço Total' para float
        total_bt_numeric = df_bt['Preço Total'].str.replace('R$ ', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
        # 2. Somar os valores
        soma_total_bt = total_bt_numeric.sum()
        # 3. Formatar o resultado
        total_bt_formatado = formatar_numero_brasileiro(soma_total_bt)
    else:
        soma_total_bt = 0.0
        total_bt_formatado = formatar_numero_brasileiro(0) # Ou "0,00"

    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total MT", f"R$ {total_mt_formatado}")
    with col2:
        st.metric("Total BT", f"R$ {total_bt_formatado}")
    with col3:
        total_mt_float = float(total_mt_formatado.replace('.', '').replace(',', '.'))
        total_bt_float = float(total_bt_formatado.replace('.', '').replace(',', '.'))
        total_geral = total_mt_float + total_bt_float
        st.metric("Total Geral", f"R$ {formatar_numero_brasileiro(total_geral)}")
    
import logging

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

# Fix 1: Enhance the carregar_dados_revisao function
def carregar_dados_revisao(revisao_id: str):
    """Carrega dados de uma revisão existente com tratamento para JSON duplamente codificado"""
    logger = logging.getLogger(__name__)

    conn = DatabaseConfig.get_connection()
    cur = conn.cursor()
    
    try:
        query = """
            SELECT
                r.conteudo::text,
                r.revisao,
                p.proposta,
                p.obra,
                p.id_proposta,
                c.nome AS contato_nome,
                c.email AS contato_email,
                c.telefone AS contato_telefone,
                cl.nome AS cliente_nome
            FROM revisoes r
            JOIN propostas p ON r.id_proposta_id = p.id_proposta
            LEFT JOIN gerenciadorpropostas_contato c ON p.contato_id_id = c.id_contato
            LEFT JOIN gerenciadorpropostas_cliente cl ON p.cliente_id_id = cl.id_cliente
            WHERE r.id_revisao= %s
        """
        
        cur.execute(query, (revisao_id,))
        resultado = cur.fetchone()
        
        if resultado:
            conteudo, revisao, proposta_num, obra, id_proposta_db, contato_nome, contato_email, contato_telefone, cliente_nome = resultado
            cliente = cliente_nome
            proposta = proposta_num
            contato = contato_nome
            dt_oferta = datetime.now()
            numero_revisao = revisao
            st.session_state['rev_atual']= numero_revisao 
            print("rev atual: ", st.session_state['rev_atual'])
            id_proposta = id_proposta_db
            if conteudo:
                try:
                    if isinstance(conteudo, str):
                        primeiro_decode = json.loads(conteudo)
                        
                        # Se ainda é string, precisa de segundo decode
                        if isinstance(primeiro_decode, str):
                            dados = json.loads(primeiro_decode)
                        else:
                            dados = primeiro_decode
                    else:
                        dados = conteudo
                        
                    # Log dos dados brutos após desserialização
                    logger.info(f"Dados desserializados: {dados}")

                    # Garante que temos um dicionário
                    if not isinstance(dados, dict):
                        return False

                    # Inicializa a estrutura de itens
                    st.session_state['itens'] = {
                        'itens_configurados_mt': dados.get('itens_configurados_mt', []),
                        'itens_configurados_bt': dados.get('itens_configurados_bt', [])
                    }
                    
                    # Log detalhado dos itens
                    if st.session_state['itens']['itens_configurados_mt']:
                        logger.info(f"Primeiro item MT: {st.session_state['itens']['itens_configurados_mt'][0]}")
                    
                    logger.info(f"Quantidade de itens BT: {len(st.session_state['itens']['itens_configurados_bt'])}")
                    if st.session_state['itens']['itens_configurados_bt']:
                        logger.info(f"Primeiro item BT: {st.session_state['itens']['itens_configurados_bt'][0]}")

                    # Preserva os dados originais de dados_iniciais se existirem
                    dados_iniciais_json = dados.get('dados_iniciais', {})
                    
                    # Carrega dados iniciais
                    if 'dados_iniciais' in dados:
                        logger.info("Carregando dados iniciais do JSON")
                        
                        # Verificamos se existem todos os campos necessários no dados_iniciais
                        dt = dt_oferta or datetime.now()

                        dados_iniciais_completos = {
                            'cliente': cliente,
                            'bt': str(proposta),
                            'obra': obra,
                            'id_proposta': id_proposta,  # Agora vem do resultado da consulta
                            'rev': st.session_state['rev_atual'],
                            'dia': dt.strftime('%d'),
                            'mes': dt.strftime('%m'),
                            'ano': dt.strftime('%Y'),
                            'nomeCliente': contato,
                            'local_frete': 'São Paulo/SP',
                            'email': '',
                            'fone': '',
                            'comentario': ''
                        }
                        
                        # Obtemos os valores do JSON
                        for key, value in dados_iniciais_json.items():
                            dados_iniciais_completos[key] = value
                        
                        # Garantimos explicitamente que email e fone existem
                        if 'email' not in dados_iniciais_completos or not dados_iniciais_completos['email']:
                            logger.warning("Campo email vazio ou ausente")
                            if 'email' in dados_iniciais_json:
                                logger.info(f"Email original do JSON: '{dados_iniciais_json['email']}'")
                        else:
                            logger.info(f"Email carregado: '{dados_iniciais_completos['email']}'")
                            
                        if 'fone' not in dados_iniciais_completos or not dados_iniciais_completos['fone']:
                            logger.warning("Campo fone vazio ou ausente")
                            if 'fone' in dados_iniciais_json:
                                logger.info(f"Fone original do JSON: '{dados_iniciais_json['fone']}'")
                        else:
                            logger.info(f"Fone carregado: '{dados_iniciais_completos['fone']}'")
                            
                        # Atribuímos ao session_state
                        st.session_state['dados_iniciais'] = dados_iniciais_completos
                        
                    else:
                        logger.info("Criando dados iniciais a partir do banco")
                        dt = dt_oferta or datetime.now()
                        st.session_state['dados_iniciais'] = {
                            'cliente': cliente,
                            'bt': str(proposta),
                            'obra': obra,
                            'id_proposta': id_proposta,  # Agora vem do resultado da consulta
                             'rev': st.session_state['rev_atual'],
                            'dia': dt.strftime('%d'),
                            'mes': dt.strftime('%m'),
                            'ano': dt.strftime('%Y'),
                            'nomeCliente': contato,
                            'local_frete': 'São Paulo/SP',
                            'email': '',
                            'fone': '',
                            'comentario': ''
                        }
                    
                    logger.info(f"Dados iniciais finais: {st.session_state['dados_iniciais']}")

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
                    return True
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Erro ao decodificar JSON: {e}")
                    logger.error(f"Conteúdo problemático: {conteudo[:200]}")  # Mostra os primeiros 200 caracteres
                    return False
                except Exception as e:
                    logger.error(f"Erro inesperado ao processar dados: {e}")
                    import traceback
                    logger.error(traceback.format_exc())  # Adiciona o stack trace completo
                    return False
        else:
            logger.error(f"Nenhum resultado encontrado para revisao_id: {revisao_id}")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao carregar revisão: {e}")
        import traceback
        logger.error(traceback.format_exc())  # Adiciona o stack trace completo
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


# 1. Adicione esta nova função para salvar dados iniciais no banco


# 2. Modifique a função inicializar_dados para definir a configuração como completa
def inicializar_dados():
    id_proposta = st.session_state['id_proposta']
    id_revisao = st.session_state['id_revisao']
    token = st.session_state['token']

    if 'rev_atual' not in session_state:
        st.session_state['rev_atual'] = '00'

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

        # IMPORTANTE: Verifica se já temos dados carregados de uma revisão
        if id_revisao and st.session_state.get('revisao_loaded'):
            print("Dados de revisão já carregados, pulando inicialização básica")
            # Definir como configurado para ir direto para as páginas
            st.session_state['configuracao_inicial_completa'] = True
            return
            
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
                            SELECT
                                p.ultima_revisao,
                                p.proposta,
                                p.obra,
                                p.id_proposta,
                                c.nome AS contato_nome,
                                c.email AS contato_email,
                                c.telefone AS contato_telefone,
                                cl.nome AS cliente_nome,
                                cl.endereco as local_cliente
                            FROM propostas p
                            LEFT JOIN gerenciadorpropostas_contato c ON p.contato_id_id = c.id_contato
                            LEFT JOIN gerenciadorpropostas_cliente cl ON p.cliente_id_id = cl.id_cliente
                            WHERE p.id_proposta = %s;
                        """, (id_proposta,))
                        
                        resultado = cur.fetchone()
                        print(f"Resultado da busca: {resultado}")
                        if resultado:
                            ultima_revisao, proposta, obra, id_proposta, contato_nome, contato_email, contato_telefone, cliente_nome, local_cliente = resultado
                            # --- LÓGICA DA REVISÃO ---
                            if st.session_state.get('tipo_proposta') == "Nova revisão":
                                print("Tipo: Nova revisão. Calculando próximo número.")
                                cur.execute("""
                                    SELECT MAX(CAST(revisao AS INTEGER))
                                    FROM revisoes
                                    WHERE id_proposta_id = %s
                                """, (id_proposta,))
                                ultima_revisao = cur.fetchone()[0]
                                proxima_revisao_num = ultima_revisao + 1 if ultima_revisao is not None else 0
                                revisao_para_usar = str(proxima_revisao_num).zfill(2)
                                print(f"Última revisão: {ultima_revisao}, Próxima revisão a usar: {revisao_para_usar}")
                                st.session_state['rev']= revisao_para_usar
                            
                            # CORREÇÃO: Se não tiver id_revisao, sempre criar novos dados iniciais
                            if not id_revisao:
                                # Definindo data_hoje ANTES de usá-la
                                data_hoje = datetime.today()
                                
                                from pages.inicial.utils import get_meses_pt
                                meses = get_meses_pt()
                                mes_atual = data_hoje.month
                                
                                dados_iniciais = {
                                    'cliente': cliente_nome,
                                    'bt': proposta,
                                    'obra': obra,
                                    'id_proposta': id_proposta,
                                    'rev': st.session_state['rev_atual'],
                                    'dia': data_hoje.strftime('%d'),
                                    'mes': meses[mes_atual],
                                    'ano': data_hoje.strftime('%Y'),
                                    'nomeCliente': contato_nome,
                                    'local_frete': local_cliente or 'São Paulo/SP',
                                    'email': contato_email or '',  # Usa o email do banco ou string vazia
                                    'fone': contato_telefone or '',   # Usa o telefone do banco ou string vazia
                                    'comentario': ''
                                }
                                print(f"Novos dados iniciais criados para proposta sem revisão: {dados_iniciais}")
                                
                                st.session_state['dados_iniciais'] = dados_iniciais
                                
                                # Inicializa a estrutura de itens vazia para nova revisão
                                st.session_state['itens'] = {
                                    'itens_configurados_mt': [],
                                    'itens_configurados_bt': []
                                }
                                
                                # Define configuração como completa para pular a tela de configuração inicial
                                st.session_state['configuracao_inicial_completa'] = True
                                
                            # Caso tenha id_revisao mas ainda não tenha carregado os dados
                            elif id_revisao and not st.session_state.get('revisao_loaded'):
                                if not carregar_dados_revisao(id_revisao):
                                    # Se falhar o carregamento, cria dados parciais
                                    if 'dados_iniciais' not in st.session_state:
                                        # Definindo data_hoje ANTES de usá-la
                                        data_hoje = datetime.today()
                                        
                                        from pages.inicial.utils import get_meses_pt
                                        meses = get_meses_pt()
                                        mes_atual = data_hoje.month
                                        
                                        st.session_state['dados_iniciais'] = {
                                            'cliente': cliente_nome,
                                            'bt': proposta,
                                            'obra': obra,
                                            'id_proposta': id_proposta,
                                            'rev': st.session_state['rev_atual'],
                                            'dia': data_hoje.strftime('%d'),
                                            'mes': meses[mes_atual],
                                            'ano': data_hoje.strftime('%Y'),
                                            'nomeCliente': contato_nome,
                                            'local_frete': local_cliente or 'São Paulo/SP',
                                            'email': contato_email or '',  # Usa o email do banco ou string vazia
                                            'fone': contato_telefone or '',   # Usa o telefone do banco ou string vazia
                                            'comentario': ''
                                        }
                                        
                                    # Define configuração como completa para pular a tela de configuração inicial
                                    st.session_state['configuracao_inicial_completa'] = True
                                else:
                                    # Se carregou com sucesso, também define como configurado
                                    st.session_state['configuracao_inicial_completa'] = True
                                    
                            st.session_state['revisao_numero_definido'] = True
                            st.session_state['proposta_loaded'] = True
            finally:
                conn.close()
                print("Conexão com banco fechada")
        
        st.session_state['app_initialized'] = True
        print("Cliente nome:" + st.session_state['dados_iniciais']['cliente'])
        print("Inicialização concluída com sucesso")
            
    except Exception as e:
        print(f"Erro detalhado na inicialização: {str(e)}")
        st.error(f"Erro ao inicializar dados: {str(e)}")


def atualizar_numero_revisao_final():
    """
    Busca a última revisão salva no banco para a proposta atual
    e atualiza o st.session_state['dados_iniciais']['rev'] para o próximo número,
    respeitando as condições de 'Nova revisão' vs 'Atualizar revisão'.
    """
    logger.info("Iniciando atualização final do número da revisão.")

    tipo_proposta = st.session_state.get('tipo_proposta')
    id_proposta = st.session_state.get('id_proposta')

    print("Número da revisão até aqui:" ,st.session_state['dados_iniciais']['rev'])

    if  st.session_state['id_revisao'] == '':
        st.session_state['dados_iniciais']['rev'] = '00'
        logger.info("ID da revisão não encontrado, número da revisão definido como '00'.")
        return
    
    # Condição 1: Se for "Atualizar revisão", não faz nada e sai.
    if tipo_proposta == "Atualizar revisão":
        logger.info("Tipo: Atualizar revisão. Número da revisão não será alterado aqui.")
        st.session_state['dados_iniciais']['rev'] = str(st.session_state['rev_atual']).zfill(2)
        return # Sai da função sem modificar

    # Condição 2: Se for "Nova revisão" (e tem id_proposta)
    if tipo_proposta == "Nova revisão":
        if not id_proposta:
            logger.error("ID da proposta não encontrado em session_state para calcular nova revisão.")
            # Define como '00' como fallback se não houver proposta? Ou mantém o que estava?
            # Vamos manter o que estava para evitar inconsistência se a proposta não carregou.
            return

        logger.info(f"Tipo: Nova revisão. Buscando MAX(revisao) para proposta ID: {id_proposta}")
        conn = None
        try:
            conn = DatabaseConfig.get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT MAX(CAST(revisao AS INTEGER))
                    FROM revisoes
                    WHERE id_proposta_id = %s
                """, (id_proposta,))
                ultima_revisao = cur.fetchone()[0]

                # Calcula o próximo número (max + 1 ou 0 se for a primeira)
                proxima_revisao_num = ultima_revisao + 1 if ultima_revisao is not None else 0
                revisao_formatada = str(proxima_revisao_num).zfill(2)

                logger.info(f"Última revisão no DB: {ultima_revisao}. Próxima revisão calculada: {revisao_formatada}")

                # Atualiza o valor em session_state
                st.session_state['dados_iniciais']['rev'] = revisao_formatada
                logger.info(f"Número da revisão em 'dados_iniciais' atualizado para: {revisao_formatada}")

        except psycopg2.Error as db_err:
            logger.error(f"Erro de banco de dados ao buscar última revisão final: {db_err}", exc_info=True)
            # Não atualiza se der erro, mantém o que estava antes
        except Exception as e:
            logger.error(f"Erro geral ao buscar última revisão final: {e}", exc_info=True)
            # Não atualiza se der erro
        finally:
            if conn:
                conn.close()
                logger.info("Conexão com banco fechada (atualizar_numero_revisao_final).")

    # Caso não seja nem "Atualizar" nem "Nova" (ou falte id_proposta em "Nova")
    else:
        logger.warning(f"Tipo de proposta '{tipo_proposta}' não permite atualização do número da revisão ou ID da proposta ausente. Número da revisão não atualizado.")


# 3. Modifique a função main para definir "Configuração de Itens" como página padrão
def main():
    """Função principal da aplicação"""
    st.set_page_config(layout="wide")
    st.title("Proposta Automatizada - Transformadores")
    st.markdown("---")

    
    # Verifica se está rodando em produção
    if os.getenv('ENVIRONMENT') == 'PRODUCTION':
        params = st.query_params
        print("Estamos em produção")
        id_proposta = params.get('id_proposta')
        print(f"ID Proposta: {id_proposta}")
        id_revisao = params.get('id_revisao')
        print(f"ID Revisão: {id_revisao}")
        token = params.get('token')
    else:
        print("Estamos em ambiente de desenvolvimento ou local")
        id_proposta = os.getenv("ID_PROPOSTA_TESTE")
        id_revisao = os.getenv("ID_REVISAO_TESTE")
        token = os.getenv("TOKEN_TESTE")

    st.session_state['id_proposta'] = id_proposta
    st.session_state['id_revisao'] = id_revisao
    st.session_state['token'] = token
    
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
        atualizar_numero_revisao_final()
        
        # Verifica se já completou a configuração inicial
        if st.session_state.get('configuracao_inicial_completa'):
            dados = st.session_state['dados_iniciais']
            if dados.get('cliente'):
                st.success(f" Proposta {dados.get('bt')} - {dados.get('cliente')} - {dados.get('obra')} - Revisão {dados.get('rev')}")
            
            # Sidebar navigation
            st.sidebar.title('Navegação')
            
            # Definindo a página padrão como "Configuração de Itens" se não houver uma página atual
            if 'pagina_atual' not in st.session_state:
                st.session_state['pagina_atual'] = "Configuração de Itens"
                
            selection = st.sidebar.radio(
                "Ir para", 
                ["Configuração de Itens", "Entrega/Pagamento/Desvio", "Resumo", "Administrativo"],
                index=0  # Define o primeiro item (Configuração de Itens) como selecionado por padrão
            )
            
            # Atualiza a página atual
            st.session_state['pagina_atual'] = selection
            
            # Render selected page
            PAGES[selection]()
            
            # Show unified table if there are items
            st.markdown("---")
            exibir_tabela_unificada()


PAGES = {
    "Configuração de Itens": pagina_configuracao,
    "Entrega/Pagamento/Desvio": pagina_configuracao_eventos,
    "Resumo": pagina_resumo,
    "Administrativo": admin_section
}

if __name__ == "__main__":
    load_dotenv()
    
    main()