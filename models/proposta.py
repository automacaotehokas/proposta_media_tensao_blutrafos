# models/proposta.py
from dataclasses import dataclass
from typing import Optional
from decimal import Decimal
from datetime import date
import uuid

@dataclass
class Proposta:
    """Modelo representando uma proposta"""
    id_proposta: str
    proposta: int
    dt_oferta: date
    cliente: str
    uf: str
    obra: str
    contato: str
    agente: str
    tipo: str
    escopo: str
    valor: Decimal
    chance: str
    estagio: str
    canal: str
    tipo_solar: str
    cabo_marca: str
    cabo_valor: Decimal
    estrutura_marca: str
    estrutura_modelo: str
    estrutura_valor: Decimal
    inversor_marca: str
    inversor_potencia: str
    inversor_quantidade: int
    inversor_valor: Decimal
    modulo_marca: str
    modulo_potencia: str
    modulo_quantidade: int
    modulo_valor: Decimal
    obs_solar: str

    @staticmethod
    def create_new(dados_iniciais: dict) -> 'Proposta':
        """Cria uma nova proposta com dados básicos"""
        novo_id = str(uuid.uuid4())
        local_frete = dados_iniciais.get('local_frete', 'São Paulo/SP')
        uf = local_frete.split('/')[-1] if '/' in local_frete else 'SP'
        
        print("Criando nova proposta com ID:", novo_id)  # Debug
        
        return Proposta(
            id_proposta=novo_id,
            proposta=int(dados_iniciais.get('bt', 0)),
            dt_oferta=date.today(),
            cliente=dados_iniciais.get('cliente', ''),
            uf=uf,
            obra=dados_iniciais.get('obra', ''),
            contato=dados_iniciais.get('nomeCliente', ''),
            agente='Sistema',  # Valor padrão
            tipo='MEDIA TENSAO',
            escopo='Transformador',
            valor=Decimal('0'),
            chance='NOVO',
            estagio='NOVO',
            canal='DIRETO',
            tipo_solar='',
            cabo_marca='',
            cabo_valor=Decimal('0'),
            estrutura_marca='',
            estrutura_modelo='',
            estrutura_valor=Decimal('0'),
            inversor_marca='',
            inversor_potencia='',
            inversor_quantidade=0,
            inversor_valor=Decimal('0'),
            modulo_marca='',
            modulo_potencia='',
            modulo_quantidade=0,
            modulo_valor=Decimal('0'),
            obs_solar=''
        )