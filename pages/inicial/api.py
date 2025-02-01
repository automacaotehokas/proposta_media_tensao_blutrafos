import requests
import streamlit as st
from googlemaps import Client
from dotenv import load_dotenv  
import os

load_dotenv()

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

    # st.error(f"Erro ao conectar com a API: {e}")    
    # return []
    
API_KEY = os.getenv("API_KEY")
gmaps = Client(key=API_KEY)

# Função para calcular distância
def distancia_cidade_capital(cidade_estado):
    capitais = {
        "SC": "Florianópolis",
        "RS": "Porto Alegre",
        "PR": "Curitiba",
        "SP": "São Paulo",
        "MG": "Belo Horizonte",
        "RJ": "Rio de Janeiro",
        "ES": "Vitória",
        "GO": "Goiânia",
        "DF": "Brasília",
        "MT": "Cuiabá",
        "MS": "Campo Grande",
        "AL": "Maceió",
        "BA": "Salvador",
        "SE": "Aracaju",
        "PB": "João Pessoa",
        "PE": "Recife",
        "RN": "Natal",
        "CE": "Fortaleza",
        "PI": "Teresina",
        "MA": "São Luís",
        "AC": "Rio Branco",
        "AM": "Manaus",
        "AP": "Macapá",
        "PA": "Belém",
        "RO": "Porto Velho",
        "RR": "Boa Vista",
        "TO": "Palmas",
    }

    try:
        cidade, estado = cidade_estado.split("/")
        estado = estado.strip()
        if estado not in capitais:
            return f"Estado da cidade '{cidade}' não encontrado."

        capital = capitais[estado]
        directions_result = gmaps.directions(f"{cidade}, {estado}", capital, mode="driving")
        distancia = directions_result[0]["legs"][0]["distance"]["value"] / 1000  # Distância em km
        return estado, distancia
    except Exception as e:
        return f"Erro ao calcular a distância: {e}"

