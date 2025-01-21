from dotenv import load_dotenv
import os

load_dotenv()

# Configurações do banco de dados
DATABASE = {
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'port': os.getenv('DB_PORT')
}

# Outras configurações
ADMIN_PASSWORD = os.getenv('SENHAADM')

SHAREPOINT_CONFIG = {
    'site_url': os.getenv('SHAREPOINT_SITE'),
    'client_id': os.getenv('SHAREPOINT_CLIENT_ID'),
    'client_secret': os.getenv('SHAREPOINT_CLIENT_SECRET')
}