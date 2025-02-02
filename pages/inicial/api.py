import requests
import streamlit as st
import logging
import os
from dotenv import load_dotenv

# # Attempt to import googlemaps with fallback
# try:
#     from googlemaps import Client
# except ImportError:
#     logging.warning("googlemaps package not found. Attempting alternative import.")
#     try:
#         import googlemaps as Client
#     except ImportError:
#         logging.error("Could not import googlemaps. Functionality will be limited.")
#         Client = None

load_dotenv()

# Add logging for API key debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# # Validate API key and create client
# API_KEY = os.getenv("API_KEY")

# if not API_KEY:
#     logger.error("Google Maps API key is missing. Please set the API_KEY in your .env file.")
#     st.error("Google Maps functionality is disabled due to missing API key.")
#     gmaps = None
# elif Client is None:
#     logger.error("Google Maps client could not be created.")
#     st.error("Google Maps functionality is unavailable.")
#     gmaps = None
# else:
#     try:
#         gmaps = Client(key=API_KEY)
#         logger.info("Google Maps client initialized successfully.")
#     except Exception as e:
#         logger.error(f"Error initializing Google Maps client: {e}")
#         st.error(f"Google Maps initialization failed: {e}")
#         gmaps = None

def buscar_cidades():
    """Busca a lista de cidades da API do IBGE"""
    url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
    response = requests.get(url)
    if response.status_code == 200:
        return sorted([
            f"{cidade['nome']}/{cidade['microrregiao']['mesorregiao']['UF']['sigla']}" 
            for cidade in response.json()
        ])
    return []

#     # st.error(f"Erro ao conectar com a API: {e}")    
#     # return []
    
# # # Função para calcular distância
# # def distancia_cidade_capital(cidade_estado):
# #     if gmaps is None:
# #         st.error("Google Maps functionality is not available.")
# #         return None
    
#     capitais = {
#         "SC": "Florianópolis",
#         "RS": "Porto Alegre",
#         "PR": "Curitiba",
#         "SP": "São Paulo",
#         "MG": "Belo Horizonte",
#         "RJ": "Rio de Janeiro",
#         "ES": "Vitória",
#         "GO": "Goiânia",
#         "DF": "Brasília",
#         "MT": "Cuiabá",
#         "MS": "Campo Grande",
#         "AL": "Maceió",
#         "BA": "Salvador",
#         "SE": "Aracaju",
#         "PB": "João Pessoa",
#         "PE": "Recife",
#         "RN": "Natal",
#         "CE": "Fortaleza",
#         "PI": "Teresina",
#         "MA": "São Luís",
#         "AC": "Rio Branco",
#         "AM": "Manaus",
#         "AP": "Macapá",
#         "PA": "Belém",
#         "RO": "Porto Velho",
#         "RR": "Boa Vista",
#         "TO": "Palmas",
#     }

#     try:
#         cidade, estado = cidade_estado.split("/")
#         estado = estado.strip()
#         if estado not in capitais:
#             return f"Estado da cidade '{cidade}' não encontrado."

#         capital = capitais[estado]
#         directions_result = gmaps.directions(f"{cidade}, {estado}", capital, mode="driving")
#         distancia = directions_result[0]["legs"][0]["distance"]["value"] / 1000  # Distância em km
#         return estado, distancia
#     except Exception as e:
#         return f"Erro ao calcular a distância: {e}"
