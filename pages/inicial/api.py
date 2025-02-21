import requests
import streamlit as st
import logging
import os
from dotenv import load_dotenv

load_dotenv()

def buscar_cidades():
    """Busca a lista de cidades da API do IBGE"""
    try:
        url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
        response = requests.get(url)
        response.raise_for_status()
        
        municipios = response.json()
        return [
            f"{municipio['nome']}/{municipio['microrregiao']['mesorregiao']['UF']['sigla']}" 
            for municipio in municipios
        ]
    except Exception as e:
        st.error(f"Erro ao buscar cidades: {e}")
        return []

def distancia_cidade_capital(cidade_estado):
    """Função de placeholder para distância entre cidades"""
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
        
        # Placeholder para distância (sem Google Maps)
        return estado, 0  # Retorna 0 como distância
    except Exception as e:
        return f"Erro ao processar cidade: {e}"
