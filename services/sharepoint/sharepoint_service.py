# services/sharepoint/sharepoint_service.py
import os
import tempfile
from shareplum import Site, Office365
from shareplum.site import Version
from dotenv import load_dotenv
import logging

class SharePoint:
    def __init__(self):
        load_dotenv()  # Carrega as variáveis de ambiente
        self.USERNAME = os.getenv("SHAREPOINT_USER")
        self.PASSWORD = os.getenv("SHAREPOINT_PASSWORD")
        self.SHAREPOINT_URL = os.getenv("SHAREPOINT_URL")
        self.SHAREPOINT_SITE = os.getenv("SHAREPOINT_SITE")
        self.SHAREPOINT_DOC = os.getenv("SHAREPOINT_DOC_LIBRARY")
        self.FOLDER_NAME = os.getenv("SHAREPOINT_FOLDER_NAME")

    def auth(self):
        """Autenticação no SharePoint"""
        self.authcookie = Office365(
            self.SHAREPOINT_URL, 
            username=self.USERNAME, 
            password=self.PASSWORD
        ).GetCookies()
        self.site = Site(
            self.SHAREPOINT_SITE, 
            version=Version.v365, 
            authcookie=self.authcookie
        )
        return self.site
    
    def listar_arquivos(self):
        """
        Lista todos os arquivos na pasta do SharePoint
        """
        try:
            self._folder = self.connect_folder()
            arquivos = self._folder.files
            logging.info(f"Pasta atual: {self.FOLDER_NAME}")
            logging.info("Arquivos disponíveis:")
            for arquivo in arquivos:
                logging.info(f"- {arquivo['Name']}")
            return arquivos
        except Exception as e:
            logging.error(f"Erro ao listar arquivos: {str(e)}")
            return []

    def connect_folder(self):
        """Conecta à pasta específica no SharePoint"""
        self.auth_site = self.auth()
        self.sharepoint_dir = '/'.join([self.SHAREPOINT_DOC, self.FOLDER_NAME])
        self.folder = self.auth_site.Folder(self.sharepoint_dir)
        return self.folder

    def download_file(self, file_name):
        """
        Baixa um arquivo do SharePoint
        
        Args:
            file_name (str): Nome do arquivo para baixar
            
        Returns:
            str: Caminho do arquivo baixado
        """
        self._folder = self.connect_folder()
        file = self._folder.get_file(file_name)
        
        # Usa o diretório temporário do sistema
        temp_path = os.path.join(tempfile.gettempdir(), file_name)
        
        # Salva o arquivo localmente
        with open(temp_path, 'wb') as f:
            f.write(file)
        
        return temp_path