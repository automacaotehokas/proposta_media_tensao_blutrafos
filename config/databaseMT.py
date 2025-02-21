# config/database.py
import psycopg2
import os
from dotenv import load_dotenv

class DatabaseConfig:
    @staticmethod
    def get_connection():
        """Retorna uma conexão com o banco de dados"""
        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                database=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                port=os.getenv("DB_PORT"),
                options="-c client_encoding=UTF8"
            )
            return conn
        except Exception as e:
            raise Exception(f"Erro ao conectar ao banco de dados: {str(e)}")
