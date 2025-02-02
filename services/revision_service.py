import requests
import os
import logging
import json
from typing import Dict, Optional, Any, Union, List
from datetime import datetime
import numpy as np
import pandas as pd
import streamlit as st
from requests.exceptions import RequestException
from decimal import Decimal

class ApiError(Exception):
    """Custom exception for API-related errors"""
    pass

def configure_logger(name: str) -> logging.Logger:
    """
    Configura e retorna um logger com saída para console e arquivo
    
    :param name: Nome do logger
    :return: Logger configurado
    """
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler = logging.FileHandler(
        os.path.join(log_dir, f'{name}.log'), 
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.handlers.clear()
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

class DataConverter:
    """Classe auxiliar para conversão de dados"""
    
    @staticmethod
    def convert_numpy(obj: Union[np.integer, np.floating, np.ndarray]) -> Union[int, float, list]:
        """Converte tipos numpy para tipos Python nativos"""
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        if isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    @staticmethod
    def convert_pandas(obj: Union[pd.Series, pd.DataFrame]) -> Union[list, dict]:
        """Converte tipos pandas para tipos Python nativos"""
        try:
            if isinstance(obj, pd.Series):
                return obj.astype(str).tolist()
            if isinstance(obj, pd.DataFrame):
                return obj.astype(str).to_dict(orient='records')
        except Exception as e:
            logging.warning(f"Erro na conversão de dados pandas: {e}")
            if isinstance(obj, pd.Series):
                return obj.tolist()
            if isinstance(obj, pd.DataFrame):
                return obj.to_dict(orient='records')
        return obj

class StreamlitApiService:
    def __init__(self, base_url=None):
        self.base_url = base_url or os.getenv('API_BASE_URL', 'http://localhost:8000')
        self.token = 'token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMyIsInVzZXJuYW1lIjoicHJvY2Vzc29zQGJsdXRyYWZvcy5jb20uYnIiLCJleHAiOjE3Mzg1MDU5NTV9.BClc7QQ9AI_gp3GQ7oiyTYs0czaJ35j6F4yqRvz_Wyw'
        self.logger = configure_logger('StreamlitApiService')
        self.converter = DataConverter()
        self._update_itens_totais()
        
        self.logger.info(f"StreamlitApiService inicializado com base_url: {self.base_url}")
            
    def _update_itens_totais(self) -> None:
            """Updates the combined items from both MT and BT session states"""
            self.itens_totais = (
                st.session_state.get('itens', {}).get('itens_configurados_mt', []) + 
                st.session_state.get('itens', {}).get('itens_configurados_bt', [])
            )
    

    def _prepare_headers(self) -> Dict[str, str]:
        """Prepara os cabeçalhos para requisição"""
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': f'Token {self.token.split("=")[-1]}'  # Extrai o token JWT
        }
        return headers

    def _convert_to_serializable(self, obj: Any) -> Any:
        """Converte objetos para tipos serializáveis JSON"""
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj

        numpy_result = self.converter.convert_numpy(obj)
        if numpy_result != obj:
            return numpy_result

        pandas_result = self.converter.convert_pandas(obj)
        if pandas_result != obj:
            return pandas_result

        if isinstance(obj, dict):
            return {
                str(k): self._convert_to_serializable(v)
                for k, v in obj.items()
                if v is not None
            }

        if isinstance(obj, list):
            return [
                self._convert_to_serializable(item)
                for item in obj
                if item is not None
            ]

        if hasattr(obj, '__bool__'):
            return bool(obj)

        try:
            return str(obj)
        except Exception as e:
            self.logger.warning(f"Não foi possível converter objeto do tipo {type(obj)}: {e}")
            return None

    def _make_request(self, method: str, endpoint: str, data: Dict) -> Dict:
        """
        Realiza requisição HTTP para a API
        
        :param method: Método HTTP ('GET', 'POST', etc)
        :param endpoint: Endpoint da API
        :param data: Dados a serem enviados
        :return: Resposta da API
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            # Adiciona o token como query parameter
            if '?' in url:
                url += f"&{self.token}"
            else:
                url += f"?{self.token}"
            
            serialized_data = json.dumps(data, ensure_ascii=False)
            self.logger.info(f"Enviando requisição para {url}")
            self.logger.info(f"Payload: {serialized_data}")
            
            response = requests.request(
                method=method,
                url=url,
                data=serialized_data,
                headers=self._prepare_headers()
            )
            
            # Log detalhado do erro para status codes de erro
            if response.status_code >= 400:
                self.logger.error(f"Erro na requisição: {response.status_code}")
                self.logger.error(f"Cabeçalhos de resposta: {response.headers}")
                self.logger.error(f"Conteúdo da resposta: {response.text}")
                response.raise_for_status()
            
            return response.json()
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Erro de serialização JSON: {e}")
            self.logger.error(f"Dados problemáticos: {data}")
            raise ApiError(f"Erro ao serializar dados: {str(e)}")
            
        except RequestException as e:
            self.logger.error(f"Erro na requisição HTTP: {e}")
            if hasattr(e, 'response'):
                self.logger.error(f"Conteúdo da resposta: {e.response.text}")
            raise ApiError(f"Erro na comunicação com a API: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Erro inesperado: {e}")
            raise ApiError(f"Erro inesperado: {str(e)}")

    def verificar_dados_completos(self) -> bool:
        """
        Verifica se todos os campos obrigatórios estão preenchidos nos dados iniciais
        e se há usinas configuradas corretamente
        
        :return: True se todos os campos obrigatórios estiverem preenchidos, False caso contrário
        """
        dados_iniciais = st.session_state.get('dados_iniciais', {})
        itens = int(st.session_state.get('valor_totalizado'))

        campos_obrigatorios = [
            'cliente', 'bt', 'dia', 'mes', 'ano', 'rev'
        ]

        for campo in campos_obrigatorios:
            if not dados_iniciais.get(campo):
                st.error(f"Campo obrigatório não preenchido: {campo}")
                return False

        if itens <= 0:
            st.error("É necessário cadastrar pelo menos uma item para a proposta")
            return False

        return True

    def somar_potencias_transformadores(self,itens_configurados_bt, itens_configurados_mt):
        soma_potencia = 0
        
        # Soma potências BT
        for item in itens_configurados_bt:
            if "potencia_numerica" in item:
                soma_potencia += item["potencia_numerica"]
      
        
        # Soma potências MT
        for item in itens_configurados_mt:
            if "Potência" in item:
                # Remove 'Decimal(' and ')' and convert to float
                potencia_str = str(item["Potência"]).replace("Decimal('", "").replace("')", "")
                try:
                    potencia = float(potencia_str)
                    soma_potencia += potencia
                except ValueError:
                    continue
        
        return f"{soma_potencia/1000:.3f} mVA"

    def inserir_revisao(self, 
                       comentario: str,
                       usuario: str,
                       id_proposta: str, 
                       escopo: str, 
                       valor: float, 
                       numero_revisao: int, 
                       dados: Dict) -> Dict:
        """
        Insere uma nova revisão via API do Django
        
        :param id_proposta: UUID da proposta
        :param escopo: Descrição do escopo
        :param valor: Valor da proposta
        :param numero_revisao: Número da revisão
        :param dados: Dicionário com dados da revisão
        :return: Resposta da API
        """
        itens_mt = st.session_state.get('itens', {}).get('itens_configurados_mt', [])
        itens_bt = st.session_state.get('itens', {}).get('itens_configurados_bt', [])

        def get_preco_total(item):
            preco_total_keys = ['Preço Total', 'Preço_Total', 'preco_total', 'valor_total']
            for key in preco_total_keys:
                if key in item:
                    try:
                        # Convert Decimal to float
                        value = item[key]
                        if isinstance(value, Decimal):
                            return float(value)
                        return float(value)
                    except (TypeError, ValueError):
                        continue
            return 0.0

        valor_mt = sum(get_preco_total(item) for item in itens_mt)
        valor_bt = sum(get_preco_total(item) for item in itens_bt)


        dados_serializaveis = self._convert_to_serializable(dados)
        
        payload = {
            'id_proposta': str(id_proposta),
            'escopo': str(escopo),
            'valor': round(valor, 2),
            'valor_mt': round(valor_mt, 2),
            'valor_bt': round(valor_bt, 2),
            'numero_revisao': int(numero_revisao),
            'conteudo': dados_serializaveis,
            'comentario': comentario,
            'usuario': usuario
        }
        
        return self._make_request('POST', '/api/streamlit/inserir_revisao/', payload)

    def atualizar_revisao(self, 
                          comentario: str,
                          usuario: str,
                          id_proposta: str, 
                          id_revisao: str, 
                          escopo: str, 
                          valor: float, 
                          dados: Dict) -> Dict:
        """
        Atualiza uma revisão existente via API do Django
        
        :param id_proposta: UUID da proposta
        :param id_revisao: ID da revisão
        :param escopo: Novo escopo
        :param valor: Novo valor
        :param dados: Dicionário com dados da revisão
        :return: Resposta da API
        """
        itens_mt = st.session_state.get('itens', {}).get('itens_configurados_mt', [])
        itens_bt = st.session_state.get('itens', {}).get('itens_configurados_bt', [])

        def get_preco_total(item):
            preco_total_keys = ['Preço Total', 'Preço_Total', 'preco_total', 'valor_total']
            for key in preco_total_keys:
                if key in item:
                    try:
                        # Convert Decimal to float
                        value = item[key]
                        if isinstance(value, Decimal):
                            return float(value)
                        return float(value)
                    except (TypeError, ValueError):
                        continue
            return 0.0

        valor_mt = sum(get_preco_total(item) for item in itens_mt)
        valor_bt = sum(get_preco_total(item) for item in itens_bt)

        dados_serializaveis = self._convert_to_serializable(dados)
        
        payload = {
            'id_proposta': str(id_proposta),
            'id_revisao': str(id_revisao),
            'escopo': str(escopo),
            'valor': round(valor, 2),
            'valor_mt': round(valor_mt, 2),
            'valor_bt': round(valor_bt, 2),
            'conteudo': dados_serializaveis,
            'comentario': comentario,
            'usuario': usuario
        }
        
        return self._make_request('POST', '/api/streamlit/atualizar_revisao/', payload)

    def salvar_revisao_banco(self) -> bool:
        """
        Salva ou atualiza a revisão no banco de dados
        
        :return: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            # Log todos os itens no session_state

            self.logger.info(f"Itens MT: {st.session_state.get('itens', {}).get('itens_configurados_mt')}")
            self.logger.info(f"Itens BT: {st.session_state.get('itens', {}).get('itens_configurados_bt')}")
            
            
            itens_mt = st.session_state.get('itens', {}).get('itens_configurados_mt', [])
            itens_bt = st.session_state.get('itens', {}).get('itens_configurados_bt', [])
            if not self.verificar_dados_completos():
                return False

            dados_revisao = {
                'itens_configurados_mt': st.session_state.get('itens', {}).get('itens_configurados_mt', []),
                'itens_configurados_bt': st.session_state.get('itens', {}).get('itens_configurados_bt', []),
                'dados_iniciais': st.session_state.get('dados_iniciais', {}),
                'impostos': st.session_state.get('impostos', {}),
                'eventos_mt': st.session_state.get('eventos_mt', {}),
                'eventos_bt': st.session_state.get('eventos_bt', {}),
                'prazo_entrega': st.session_state.get('prazo_entrega', {}),
                'desvios': st.session_state.get('desvios', {})
            }

            self._update_itens_totais()

            valor_total = sum(
                float(item.get('Preço Total', 0.0))
                for item in self.itens_totais
            )

            escopo = self.somar_potencias_transformadores(st.session_state.get('itens', {}).get('itens_configurados_bt', []),
                                                          st.session_state.get('itens', {}).get('itens_configurados_mt', []))

            is_nova_revisao = st.session_state.get('tipo_proposta') == "Nova revisão"
            
            try:
                # Serialização robusta com conversão de tipos e log
                def custom_serializer(obj):
                    if isinstance(obj, (Decimal, np.number)):
                        return float(obj)
                    if hasattr(obj, 'isoformat'):  # Para objetos datetime
                        return obj.isoformat()
                    if isinstance(obj, bool):
                        return obj  # Mantém valores booleanos
                    self.logger.warning(f"Não foi possível serializar: {type(obj)} - {obj}")
                    return str(obj)

                # Converte dados para JSON e imprime para debug
                json_str = json.dumps(dados_revisao, default=custom_serializer, ensure_ascii=False)
                self.logger.info(f"JSON gerado: {json_str}")

                # Tenta parsear o JSON para garantir que é válido
                dados_serializados = json.loads(json_str)

                if is_nova_revisao:
                    resultado = self.inserir_revisao(
                        comentario=st.session_state.get('comentario_revisao', ''),
                        usuario=st.session_state.get('usuario', ''),
                        id_proposta=st.session_state['id_proposta'],
                        escopo=escopo,
                        valor=valor_total,
                        numero_revisao=int(st.session_state['dados_iniciais']['rev']),
                        dados=dados_serializados
                    )
                    st.session_state['id_revisao'] = resultado.get('id')
                    st.success("Nova revisão inserida com sucesso!")
                else:
                    resultado = self.atualizar_revisao(
                        comentario=st.session_state.get('comentario_revisao', ''),
                        usuario=st.session_state.get('usuario', ''),
                        id_proposta=st.session_state['id_proposta'],
                        id_revisao=st.session_state.get('id_revisao') or os.getenv('ID_REVISAO_TESTE'),
                        escopo=escopo,
                        valor=valor_total,
                        dados=dados_serializados
                    )
                    st.success("Revisão atualizada com sucesso!")

                st.session_state['dados_salvos'] = True
                return True

            except json.JSONDecodeError as e:
                self.logger.error(f"Erro de decodificação JSON: {e}")
                st.error(f"Erro de serialização: {e}")
                return False
            except ApiError as e:
                st.error(f"Erro na comunicação com a API: {str(e)}")
                return False
                
        except Exception as e:
            st.error(f"Erro inesperado ao processar dados: {str(e)}")
            return False