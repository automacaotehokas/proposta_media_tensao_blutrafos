import streamlit as st
from msal import ConfidentialClientApplication
import os
from dotenv import load_dotenv

CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
TENANT_ID = os.getenv('AZURE_TENANT_ID')
CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_URI = os.getenv('REDIRECT_URI')
SCOPES = ["User.Read"]

EMAILS_PERMITIDOS = os.getenv('EMAILS_PERMITIDOS', '').split(',')

def init_app():
    return ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET,
    )

def autenticar_usuario():
    # Verifica se o estado de permissão já foi armazenado
    if 'autenticado' in st.session_state:
        if st.session_state['autenticado']:
            return True
        else:
            exibir_mensagem_permissao_negada()
            return False

    app = init_app()
    accounts = app.get_accounts()

    # Tenta autenticar de forma silenciosa se o usuário já estiver logado no navegador
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            email = result['id_token_claims']['preferred_username']
            if email in EMAILS_PERMITIDOS:
                st.session_state['autenticado'] = True
                st.session_state['email'] = email
                return True
            else:
                st.session_state['autenticado'] = False
                exibir_mensagem_permissao_negada()
                return False

    # Verifica se há um código de autorização na URL após o redirecionamento
    query_params = st.query_params
    if "code" in query_params:
        code = query_params["code"][0]
        result = app.acquire_token_by_authorization_code(
            code=code,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )

        if "access_token" in result:
            email = result['id_token_claims']['preferred_username']
            if email in EMAILS_PERMITIDOS:
                st.session_state['autenticado'] = True
                st.session_state['email'] = email
                # Limpa o código da URL após a autenticação
                st.experimental_set_query_params()  # Limpa os parâmetros da URL
                return True
            else:
                st.session_state['autenticado'] = False
                exibir_mensagem_permissao_negada()
                return False
        else:
            st.error("Falha na autenticação. Por favor, tente novamente.")
            st.stop()

    # Se o usuário não estiver autenticado e não tiver sido marcado como sem permissão
    if 'autenticado' not in st.session_state:
        auth_url = app.get_authorization_request_url(
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        st.markdown(f"[Clique aqui para entrar]({auth_url})")
        st.stop()

def verificar_acesso():
    # Chama a função de autenticação e verifica se o usuário tem permissão
    if not autenticar_usuario():
        st.stop()

def exibir_mensagem_permissao_negada():
    st.error("Você não tem permissão para acessar este aplicativo.")
    st.stop()

# Chama a função de verificação de acesso
verificar_acesso()
