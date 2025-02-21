# Python Built-in
import json
import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

# Django Core
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Max, Sum, Count, Q
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.template.loader import render_to_string
from django.utils.timezone import now
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

# Third Party
import msal
import openpyxl
from openpyxl.styles import Alignment
from rest_framework.decorators import APIView
from rest_framework.response import Response
from rest_framework.views import APIView

# Local
from .config import DEFAULT_COLUMNS
from .forms import PropostaForm, RevisarForm, ComentarForm
from .graph_helpers import get_user_data, get_user_groups
from .models import (
    AGENTES,
    CANAL,
    ESTAGIOS_ABERTOS,
    Comentario,
    CustomUser,
    Proposta,
    Revisao,
    User,
    UserPreference,
    UserProfile,
)
from .utils import format_date, format_decimal

from .graph_helpers import get_user_data

# Setup Logging
logger = logging.getLogger(__name__)

###########################
#USUÁRIO E AUTENTIFICAÇÃO
###########################

@login_required
def update_profile_image(request):
    if request.method == 'POST' and request.FILES.get('profile_image'):
        try:
            # Salva a nova imagem
            request.user.profile_image = request.FILES['profile_image']
            request.user.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'No image provided'})

def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(settings.LOGIN_REDIRECT_URL)
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def create_new_user(backend, user, response, *args, **kwargs):
    """Função personalizada para criar um novo usuário no Django se não existir."""
    if not user:
        try:
            # Verifica se o usuário já existe
            user = User.objects.get(username=response.get('preferred_username', ''))
        except User.DoesNotExist:
            # Cria o usuário se não existir
            user = User.objects.create_user(
                username=response.get('preferred_username', ''),
                email=response.get('email', ''),
                first_name=response.get('given_name', ''),
                last_name=response.get('family_name', ''),
            )
    return user

@login_required
def minha_conta(request):
    user = request.user
    context = {
        'user': user,
        'URLSUPORTE': settings.URLSUPORTE,
        'page_title': 'Minha Conta'
    }
    return render(request, 'gerenciadorpropostas/minha_conta.html', context)

def azure_login(request):
    msal_app = msal.ConfidentialClientApplication(
        settings.AZURE_APP_ID,
        authority=f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}",
        client_credential=settings.AZURE_APP_SECRET,
    )
    
    # Configurar a URL de redirecionamento no Azure Portal
    redirect_uri = request.build_absolute_uri('/callback').replace('127.0.0.1', 'localhost')

    # Gerar e armazenar o estado na sessão
    state = str(uuid.uuid4())
    request.session['azure_state'] = state

    # Verificar se o estado foi armazenado corretamente na sessão
    if request.session.get('azure_state') != state:
        logger.error(f"Erro ao salvar o estado na sessão: {state}")
        return HttpResponseBadRequest("Falha na sessão")

    logger.debug(f"State armazenado na sessão: {state}")

    # Gerar URL de autorização
    auth_url = msal_app.get_authorization_request_url(
        scopes=["User.Read"],
        redirect_uri=redirect_uri,
        state=state
    )
    
    return redirect(auth_url)

def azure_callback(request):
    # Verifica se há erro na resposta do Azure
    if "error" in request.GET:
        logger.error(f"Erro de autenticação: {request.GET['error_description']}")
        return HttpResponseBadRequest("Erro na autenticação")
    
    # Recupera o estado da resposta e da sessão
    state = request.GET.get("state")
    stored_state = request.session.get('azure_state')
    
    # Valida o estado
    if state != stored_state:
        logger.error(f"State inválido detectado. Esperado: {stored_state}, Recebido: {state}")
        return HttpResponseBadRequest("Invalid state")
    
    logger.debug(f"State validado: {state}")

    msal_app = msal.ConfidentialClientApplication(
        settings.AZURE_APP_ID,
        authority=f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}",
        client_credential=settings.AZURE_APP_SECRET,
    )
    
    # Configura o URI de redirecionamento
    redirect_uri = request.build_absolute_uri('/callback').replace('127.0.0.1', 'localhost')

    # Adquirir o token de acesso utilizando o código de autorização
    token = msal_app.acquire_token_by_authorization_code(
        request.GET["code"],
        scopes=["User.Read"],
        redirect_uri=redirect_uri
    )
    
    # Verificar se houve erro ao obter o token
    if "error" in token:
        logger.error(f"Erro ao obter token: {token['error_description']}")
        return HttpResponseBadRequest("Erro ao obter token")
    
    # Obter os dados do usuário via Microsoft Graph
    graph_data = get_user_data(token["access_token"])

    # Tentativa de encontrar o usuário no banco de dados
    try:
        # Encontrar o usuário existente com base no azure_id
        user = CustomUser.objects.get(azure_id=graph_data["id"])
        
        # Atualizar os dados do usuário com informações do Azure AD
        user.username = graph_data["userPrincipalName"]
        user.email = graph_data["userPrincipalName"]
        user.first_name = graph_data.get("givenName", "")
        user.last_name = graph_data.get("surname", "")
        user.department = graph_data.get("department", "")
        user.job_title = graph_data.get("jobTitle", "")
        user.save()
        
        logger.info(f"Usuário existente atualizado: {user.username}")

    except CustomUser.DoesNotExist:
        # Criar um novo usuário caso não exista
        user = CustomUser.objects.create_user(
            azure_id=graph_data["id"],
            username=graph_data["userPrincipalName"],
            email=graph_data["userPrincipalName"],
            first_name=graph_data.get("givenName", ""),
            last_name=graph_data.get("surname", ""),
            department=graph_data.get("department", ""),
            job_title=graph_data.get("jobTitle", "")
        )
        
        logger.info(f"Novo usuário criado: {user.username}")

    # Realizar login do usuário no Django
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    
    return redirect('propostas')


###########################
#VIEWS PARA MODELO DE PROPOSTAS
###########################

@require_GET
def get_model_choices(request):
    """"
    Função para obter os choices do modelo de proposta
    """
    from .models import (
        AGENTES, UF_BRASIL, CATEGORIAS, ESTAGIO, CANAL,
        SOLAR_CHOICES, INVERSOR_CHOICES, POTENCIA_INVERSOR_CHOICES,
        MODULO_CHOICES, POTENCIA_MODULO_CHOICES, ESTRUTURA_MARCA_CHOICES,
        ESTRUTURA_MODELO_CHOICES, CABOS_CHOICES, CHANCE, CustomUser
    )
    
    # Obtém os usuários do CustomUser
    usuarios = CustomUser.objects.all()
    usuarios_dict = {str(user.id): user.get_full_name() or user.username for user in usuarios}
    
    choices = {
        'agentes': dict(AGENTES),
        'uf': dict(UF_BRASIL),
        'categorias': dict(CATEGORIAS),
        'estagio': dict(ESTAGIO),
        'canal': dict(CANAL),
        'solar': dict(SOLAR_CHOICES),
        'inversor_marca': dict(INVERSOR_CHOICES),
        'inversor_potencia': dict(POTENCIA_INVERSOR_CHOICES),
        'modulo_marca': dict(MODULO_CHOICES),
        'modulo_potencia': dict(POTENCIA_MODULO_CHOICES),
        'estrutura_marca': dict(ESTRUTURA_MARCA_CHOICES),
        'estrutura_modelo': dict(ESTRUTURA_MODELO_CHOICES),
        'cabo_marca': dict(CABOS_CHOICES),
        'chance': dict(CHANCE),
        'usuarios': usuarios_dict  # Adiciona os usuários ao dicionário de choices
    }
    
    return JsonResponse(choices)

class PropostaStateView(APIView):
    def get(self, request, id_proposta):
        try:
            # Buscar a proposta
            proposta = get_object_or_404(Proposta, id_proposta=id_proposta)
            
            # Buscar a última revisão
            ultima_revisao = Revisao.objects.filter(
                id_proposta=proposta
            ).order_by('-revisao').first()
            
            # Preparar dados para retorno
            data = {
                'proposta_id': str(proposta.id_proposta),
                'cliente': proposta.cliente,
                'bt': proposta.proposta,
                'obra': proposta.obra,
                'nova_revisao': (ultima_revisao.revisao + 1) if ultima_revisao else 0
            }
            
            return Response(data)
            
        except Exception as e:
            return Response({"error": str(e)}, status=400)

@login_required
def get_proposta_details(request, proposta_id):
    """
    captura os detalhes da proposta para mostrar em um modal ou button

    """
    try:
        proposta = get_object_or_404(Proposta, id_proposta=proposta_id)
        
        data = {
            'proposta': proposta.proposta,
            'cliente': proposta.cliente,
            'tipo': proposta.tipo,
            'obra': proposta.obra,
            'valor': float(proposta.valor),
            'estagio': proposta.estagio,
            'canal': proposta.get_canal_display(),
            'chance': proposta.chance,
            'ultima_revisao': proposta.ultima_revisao,
            'contato': proposta.contato,
            'uf': proposta.uf,
            'agente': proposta.get_agente_display(),
            'dt_oferta': proposta.dt_oferta.strftime('%Y-%m-%d') if proposta.dt_oferta else None,
            'last': proposta.last.strftime('%Y-%m-%d') if proposta.last else None,
            'next': proposta.next.strftime('%Y-%m-%d') if proposta.next else None,
            'tipo_solar': proposta.tipo_solar,
            'inversor_marca': proposta.inversor_marca,
            'modulo_marca': proposta.modulo_marca,
            'estrutura_marca': proposta.estrutura_marca,
            'escopo': proposta.escopo,
        }
        
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@login_required
def listar_propostas(request):
    """
    Esta função recebe as preferências do usuário e as passa para o template
    """
    try:
        # Tenta recuperar as preferências do usuário
        user_preference = UserPreference.objects.get(user=request.user)
        filters = user_preference.filters
        columns = user_preference.columns
    except UserPreference.DoesNotExist:
        filters = {}
        columns = {}

    # Cria uma instância do formulário de proposta
    proposta_form = PropostaForm()

    return render(request, 'gerenciadorpropostas/proposta_list.html', {
        'user_id': request.user.id,
        'filters': filters,
        'columns': columns,
        'proposta_form': proposta_form  # Adiciona o formulário ao contexto
    })


@login_required
def get_proposta_edit_modal(request, id_proposta):
    """
    Função para obter o HTML do modal de edição de uma proposta
    """
    try:
        # Busca apenas os campos necessários
        proposta = (Proposta.objects
            .filter(id_proposta=id_proposta)
            .only(
                'proposta',
                'cliente',
                'valor',
                'tipo',
                'escopo',
                'ultima_revisao'
            )
            .first()
        )
        
        if not proposta:
            return JsonResponse({
                'success': False,
                'error': 'Proposta não encontrada'
            }, status=404)

        # Retorna apenas o HTML necessário
        html = render_to_string('propostas/modals/edit_modal.html', {
            'proposta': proposta
        }, request=request)

        return JsonResponse({
            'success': True,
            'html': html
        })
        
    except Exception as e:
        print(f"Erro ao buscar dados para edição: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def get_propostas_data(request):
    """
    Função para obter dados da tabela de propostas, tratamento e ordenação. Além de obter a lógica dos filtros
    """
    try:
        print("=== Starting get_propostas_data ===")
        
        # Verifica se é uma solicitação de valores únicos para os filtros
        if request.POST.get('action') == 'get_unique_values':
            try:
                field_name = request.POST.get('field')
                search_term = request.POST.get('search', '').lower()
                mostrar_fechados = request.POST.get('mostrar_fechados') == 'true'
                
                queryset = Proposta.objects.all()
                
                # Aplica filtro de propostas fechadas/abertas
                if not mostrar_fechados:
                    queryset = queryset.filter(estagio__in=ESTAGIOS_ABERTOS)
                
                # Tratamento especial para campos relacionados
                if field_name in ['controle_interno', 'orcamentista']:
                    users = CustomUser.objects.all()
                    values = [f"{user.first_name} {user.last_name}".strip() 
                             for user in users if user.first_name or user.last_name]
                elif field_name == 'agente':
                    values = [dict(AGENTES).get(value, value) 
                            for value in queryset.values_list(field_name, flat=True).distinct()]
                elif field_name == 'canal':
                    values = [dict(CANAL).get(value, value) 
                            for value in queryset.values_list(field_name, flat=True).distinct()]
                else:
                    # Para campos normais, usa distinct
                    values = queryset.values_list(field_name, flat=True).distinct()
                
                # Filtra e processa os valores
                filtered_values = []
                seen = set()  # Para garantir unicidade
                
                for value in values:
                    if value is None:
                        continue
                    
                    str_value = str(value).strip()
                    if not str_value:  # Ignora strings vazias
                        continue
                    
                    # Verifica se devemos filtrar pelo termo de busca
                    if search_term and search_term not in str_value.lower():
                        continue
                    
                    # Evita duplicatas mesmo com diferenças de capitalização
                    lower_value = str_value.lower()
                    if lower_value not in seen:
                        seen.add(lower_value)
                        filtered_values.append(str_value)
                
                # Ordena os valores
                filtered_values.sort(key=lambda x: x.lower())
                
                print(f"Field: {field_name}, Unique values count: {len(filtered_values)}")
                return JsonResponse({'values': filtered_values})
                
            except Exception as e:
                print(f"Error getting unique values: {str(e)}")
                return JsonResponse({'error': str(e)}, status=500)

        # Processamento normal da tabela
        draw = int(request.POST.get('draw', 1))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        search_value = request.POST.get('search[value]', '')
        mostrar_fechados = request.POST.get('mostrar_fechados') == 'true'
        mostrar_atrasados = request.POST.get('mostrar_atrasados') == 'true'
        mostrar_meus_follows = request.POST.get('mostrar_meus_follows') == 'true'

        # Query base com select_related otimizado
        queryset = Proposta.objects.select_related('controle_interno', 'orcamentista')

        # Aplica filtro de propostas fechadas/abertas
        if not mostrar_fechados:
            queryset = queryset.filter(estagio__in=ESTAGIOS_ABERTOS)

                # Filtro de atrasados
        # Filtro de atrasados
        if mostrar_atrasados:
            today = now().date()
            queryset = queryset.filter(
                Q(next__lt=today) |  # Próxima ação no passado
                Q(next__isnull=True, last__lt=today)  # Sem próxima ação e última atualização no passado
            )

        # Filtro de meus follows
        if mostrar_meus_follows:
            queryset = queryset.filter(controle_interno=request.user)

        # Aplica busca global com otimização
        if search_value:
            queryset = queryset.filter(
                Q(proposta__icontains=search_value) |
                Q(cliente__icontains=search_value) |
                Q(obra__icontains=search_value) |
                Q(contato__icontains=search_value) |
                Q(escopo__icontains=search_value) |
                Q(tipo__icontains=search_value) |
                Q(estagio__icontains=search_value)
            )

        # Processa filtros customizados
        filters = json.loads(request.POST.get('filters', '{}'))
        print("Filtros recebidos:", filters)
        
        for index, filter_data in filters.items():
            print(f"Processando filtro - Índice: {index}, Dados: {filter_data}")
            
            field = get_field_name(int(index))
            if not field:
                print(f"Campo não encontrado para índice {index}")
                continue

            if filter_data['type'] == 'date':
                if filter_data.get('start'):
                    queryset = queryset.filter(**{f"{field}__gte": filter_data['start']})
                if filter_data.get('end'):
                    queryset = queryset.filter(**{f"{field}__lte": filter_data['end']})
            
            elif filter_data['type'] == 'number':
                if filter_data.get('min') is not None:
                    queryset = queryset.filter(**{f"{field}__gte": filter_data['min']})
                if filter_data.get('max') is not None:
                    queryset = queryset.filter(**{f"{field}__lte": filter_data['max']})
            
            elif filter_data['type'] == 'select' and filter_data.get('values'):
                if field in ['controle_interno', 'orcamentista']:
                    # Tratamento especial para campos de usuário
                    names = [name.split() for name in filter_data['values']]
                    q_objects = Q()
                    for name_parts in names:
                        if len(name_parts) >= 2:
                            q_objects |= Q(
                                **{f"{field}__first_name__icontains": name_parts[0],
                                   f"{field}__last_name__icontains": name_parts[-1]}
                            )
                    if q_objects:
                        queryset = queryset.filter(q_objects)
                else:
                    queryset = queryset.filter(**{f"{field}__in": filter_data['values']})

        # Total de registros
        total = Proposta.objects.count()
        total_filtered = queryset.count()

        # Ordenação
        order_column = int(request.POST.get('order[0][column]', 0))
        order_dir = request.POST.get('order[0][dir]', 'desc')
        order_field = get_field_name(order_column)
        if order_dir == 'desc':
            order_field = f'-{order_field}'
        queryset = queryset.order_by(order_field)

        # Paginação
        queryset = queryset[start:start + length]

        # Prepara dados para resposta
        data = []
        for proposta in queryset:
            status = proposta.calcular_status
            if callable(status):
                status = status()

            data.append({
                'DT_RowId': str(proposta.id_proposta),
                'proposta': proposta.proposta,
                'dt_criacao': proposta.dt_criacao.strftime('%Y-%m-%d') if proposta.dt_criacao else '',
                'dt_oferta': proposta.dt_oferta.strftime('%Y-%m-%d') if proposta.dt_oferta else '',
                'ultima_revisao': proposta.ultima_revisao,
                'cliente': proposta.cliente,
                'uf': proposta.uf,
                'obra': proposta.obra,
                'contato': proposta.contato,
                'agente': proposta.get_agente_display(),
                'controle_interno': {'id': str(proposta.controle_interno.id), 'name': f"{proposta.controle_interno.first_name} {proposta.controle_interno.last_name}"} if proposta.controle_interno else None,
                'orcamentista': {'id': str(proposta.orcamentista.id), 'name': f"{proposta.orcamentista.first_name} {proposta.orcamentista.last_name}"} if proposta.orcamentista else None,
                'tipo': proposta.tipo,
                'escopo': proposta.escopo,
                'valor': float(proposta.valor),
                'chance': proposta.chance,
                'estagio': proposta.estagio,
                'canal': proposta.get_canal_display(),
                'last': proposta.last.strftime('%Y-%m-%d') if proposta.last else '',
                'next': proposta.next.strftime('%Y-%m-%d') if proposta.next else '',
                'status': status,
                'tipo_solar': proposta.tipo_solar,
                'inversor_marca': proposta.inversor_marca,
                'inversor_potencia': proposta.inversor_potencia,
                'inversor_quantidade': proposta.inversor_quantidade,
                'inversor_valor': float(proposta.inversor_valor),
                'modulo_marca': proposta.modulo_marca,
                'modulo_potencia': proposta.modulo_potencia,
                'modulo_quantidade': proposta.modulo_quantidade,
                'modulo_valor': float(proposta.modulo_valor),
                'estrutura_marca': proposta.estrutura_marca,
                'estrutura_modelo': proposta.estrutura_modelo,
                'estrutura_valor': float(proposta.estrutura_valor),
                'cabo_marca': proposta.cabo_marca,
                'cabo_valor': float(proposta.cabo_valor),
                'obs_solar': proposta.obs_solar,
                'dt_prev_fechamento': proposta.dt_prev_fechamento.strftime('%Y-%m-%d') if proposta.dt_prev_fechamento else ''
            })

        response_data = {
            'draw': draw,
            'recordsTotal': total,
            'recordsFiltered': total_filtered,
            'data': data
        }

        return JsonResponse(response_data)

    except Exception as e:
        print(f"=== Critical Error ===")
        print(f"Error type: {type(e)}")
        print(f"Error message: {str(e)}")
        print(f"Error line number: {e.__traceback__.tb_lineno}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)
    

def get_field_name(index):
    """Mapeia o índice da coluna para o nome do campo no modelo proposta"""
    fields = {
    0: 'proposta',
    1: 'dt_criacao',
    2: 'dt_oferta',
    3: 'ultima_revisao',
    4: 'cliente',
    5: 'uf',
    6: 'obra',
    7: 'contato',
    8: 'agente',
    9: 'controle_interno',
    10: 'orcamentista',
    11: 'tipo',
    12: 'escopo',
    13: 'valor',
    14: 'chance',
    15: 'estagio',
    16: 'canal',
    17: 'last',
    18: 'next',
    19: 'dt_prev_fechamento',
    20: 'status',
    21: 'tipo_solar',
    22: 'inversor_marca',
    23: 'inversor_potencia',
    24: 'inversor_quantidade',
    25: 'inversor_valor',
    26: 'modulo_marca',
    27: 'modulo_potencia',
    28: 'modulo_quantidade',
    29: 'modulo_valor',
    30: 'estrutura_marca',
    31: 'estrutura_modelo',
    32: 'estrutura_valor',
    33: 'cabo_marca',
    34: 'cabo_valor',
    35: 'obs_solar'
}
    return fields.get(index)

@login_required
def get_proposta_data_row(request, id_proposta):
    """ Obtem os dados no modelo proposta para uma única linha, para fins de atualização mais eficiente, atualmente é utilizado os dados do CACHE,porém para funcionalidades posteriores serão utilizados os dados do banco de dados """
    try:
        proposta = Proposta.objects.get(id_proposta=id_proposta)
        
        # Função helper para formatação segura de valores monetários
        def format_decimal(value):
            try:
                if value is None:
                    return 0.0
                return float(value)
            except (ValueError, TypeError):
                return 0.0
                
        # Função helper para formatação segura de datas
        def format_date(date_value):
            try:
                if date_value:
                    return date_value.strftime('%Y-%m-%d')
                return ''
            except (ValueError, TypeError, AttributeError):
                return ''

        data = {
            'proposta': proposta.proposta,
            'dt_criacao': format_date(proposta.dt_criacao),
            'dt_oferta': format_date(proposta.dt_oferta),
            'ultima_revisao': proposta.ultima_revisao or 0,
            'cliente': proposta.cliente or '',
            'uf': proposta.uf or '',
            'obra': proposta.obra or '',
            'contato': proposta.contato or '',
            'agente': proposta.get_agente_display() or '',
            'controle_interno': {'id': str(proposta.controle_interno.id), 'name': f"{proposta.controle_interno.first_name} {proposta.controle_interno.last_name}"} if proposta.controle_interno else None,
            'orcamentista': {'id': str(proposta.orcamentista.id), 'name': f"{proposta.orcamentista.first_name} {proposta.orcamentista.last_name}"} if proposta.orcamentista else None,
            'tipo': proposta.tipo or '',
            'escopo': proposta.escopo or '',
            'valor': format_decimal(proposta.valor),
            'chance': proposta.chance or '',
            'estagio': proposta.estagio or '',
            'canal': proposta.get_canal_display() or '',
            'last': format_date(proposta.last),
            'next': format_date(proposta.next),
            'status': proposta.calcular_status,  # Removido os parênteses pois é uma property
            'tipo_solar': proposta.tipo_solar or '',
            'inversor_marca': proposta.inversor_marca or '',
            'inversor_potencia': proposta.inversor_potencia or '',
            'inversor_quantidade': proposta.inversor_quantidade or 0,
            'inversor_valor': format_decimal(proposta.inversor_valor),
            'modulo_marca': proposta.modulo_marca or '',
            'modulo_potencia': proposta.modulo_potencia or '',
            'modulo_quantidade': proposta.modulo_quantidade or 0,
            'modulo_valor': format_decimal(proposta.modulo_valor),
            'estrutura_marca': proposta.estrutura_marca or '',
            'estrutura_modelo': proposta.estrutura_modelo or '',
            'estrutura_valor': format_decimal(proposta.estrutura_valor),
            'cabo_marca': proposta.cabo_marca or '',
            'cabo_valor': format_decimal(proposta.cabo_valor),
            'obs_solar': proposta.obs_solar or '',
            'dt_prev_fechamento': format_date(proposta.dt_prev_fechamento)
        }
        
        return JsonResponse(data)
        
    except Proposta.DoesNotExist:
        return JsonResponse({
            'error': 'Proposta não encontrada'
        }, status=404)
    except Exception as e:
        import traceback
        print("Erro ao buscar dados da proposta:", traceback.format_exc())
        return JsonResponse({
            'error': f'Erro ao buscar dados da proposta: {e}'
        }, status=500)

@login_required
def save_user_preferences(request):
    """Salva preferências do usuário logado"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método não permitido'})
        
    try:
        data = json.loads(request.body)
        
        # Validação dos dados
        if not isinstance(data, dict):
            raise ValueError("Formato de dados inválido")
            
        # Obtém preferência existente ou cria nova
        preference, created = UserPreference.objects.get_or_create(
            user=request.user
        )
        
        # Verifica se é uma solicitação de limpeza de filtros
        is_clear_request = data.get('is_clear_request', False)
        
        # Atualiza apenas os campos fornecidos
        if is_clear_request:
            # Se for uma solicitação de limpeza, reseta os filtros
            preference.filters = {}
        elif 'filters' in data:
            # Caso contrário, atualiza com os novos filtros
            preference.filters = data['filters']
        
        if 'columns' in data:
            preference.columns = data['columns']
            
        preference.save()
        
        return JsonResponse({
            'success': True,
            'filters': preference.filters,
            'columns': preference.columns,
            'is_clear_request': is_clear_request
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def get_user_preferences(request):
    """Obtem preferências do usuário logado"""
    try:
        preference = UserPreference.objects.get(user=request.user)
        return JsonResponse({
            'success': True,
            'filters': preference.filters,
            'columns': preference.columns
        })
    except UserPreference.DoesNotExist:
        # Retorna preferências padrão em vez de vazio
        return JsonResponse({
            'success': True,
            'filters': {},
            'columns': {col['field']: {'visible': col['visible']} 
                       for col in DEFAULT_COLUMNS}
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def nova_proposta(request):
    """Cria uma nova proposta e comentário associado"""
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'success': False,
            'message': 'Método não permitido'
        }, status=405)

    proposta_form = PropostaForm(request.POST)

    try:
        if not proposta_form.is_valid():
            return JsonResponse({
                'status': 'error',
                'success': False,
                'message': 'Dados inválidos no formulário',
                'errors': proposta_form.errors
            }, status=400)

        # Pega o número da proposta do POST
        numero_proposta = request.POST.get('proposta')
        if not numero_proposta:
            return JsonResponse({
                'status': 'error',
                'success': False,
                'message': 'Número da proposta não fornecido'
            }, status=400)

        numero_original = numero_proposta

        # Verifica se o número já existe e encontra próximo disponível
        while Proposta.objects.filter(proposta=numero_proposta).exists():
            numero_proposta = str(int(numero_proposta) + 1)

        # Salva proposta
        proposta = proposta_form.save(commit=False)
        proposta.estagio = "Em Elaboração"
        proposta.chance = "10%"
        proposta.proposta = numero_proposta
        proposta.save()

        # Prepara resposta de sucesso
        response_data = {
            'status': 'success',
            'success': True,
            'proposta_numero': numero_proposta,  # número da proposta (ex: 810000)
            'id_proposta': str(proposta.id_proposta),  # UUID da proposta
            'message': 'Proposta criada com sucesso!'
        }

        # Se o número foi alterado, adiciona mensagem
        if numero_proposta != numero_original:
            response_data.update({
                'numero_alterado': True,
                'message': f'Proposta criada com sucesso! O número foi ajustado para {numero_proposta} pois o original já estava em uso.'
            })
        else:
            response_data.update({
                'numero_alterado': False,
                'message': 'Proposta criada com sucesso!'
            })

        return JsonResponse(response_data)

    except Exception as e:
        print(f"Erro ao criar proposta: {str(e)}")  # Log para debug
        return JsonResponse({
            'status': 'error',
            'success': False,
            'message': f'Erro ao criar proposta: {str(e)}'
        }, status=400)

def get_next_proposta_number():
    """
    Gera o próximo número de proposta disponível começando de 810000.
    O número será único e sequencial.
    """
    numero_inicial = 80000
    proximo_numero = numero_inicial
    
    # Enquanto existir uma proposta com o número atual, incrementa
    while Proposta.objects.filter(proposta=proximo_numero).exists():
        proximo_numero += 1
    
    return proximo_numero

@require_GET
def get_next_proposta_number_api(request):
    """API endpoint para obter o próximo número de proposta disponível"""
    try:
        next_number = get_next_proposta_number()
        return JsonResponse({'success': True, 'number': next_number})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def editar_proposta(request, id_proposta):
    """Edita uma proposta existente"""
    try:
        proposta = get_object_or_404(Proposta, id_proposta=id_proposta)
        
        if request.method == 'POST':
            # Log dos dados recebidos
            print("Dados recebidos:", request.body.decode('utf-8'))
            
            form_data = json.loads(request.body)
            print("Form data:", form_data)
            
            # Lista todos os campos editáveis
            allowed_fields = [
                'dt_oferta', 'cliente', 'uf', 'obra',
                'contato', 'agente', 'tipo', 'escopo', 'valor',
                'chance', 'estagio', 'canal', 'last', 'next',
                'tipo_solar', 'inversor_marca', 'inversor_potencia',
                'inversor_quantidade', 'inversor_valor', 'modulo_marca',
                'modulo_potencia', 'modulo_quantidade', 'modulo_valor',
                'estrutura_marca', 'estrutura_modelo', 'estrutura_valor',
                'cabo_marca', 'cabo_valor', 'obs_solar', 'dt_prev_fechamento',
                'controle_interno', 'orcamentista'
            ]
            
            # Atualiza os campos
            for field in allowed_fields:
                print(f"Processando campo {field}: {form_data[field]}")
                
                # Tratamento especial para campos de usuário
                if field in ['controle_interno', 'orcamentista']:
                    if form_data[field]:
                        user = CustomUser.objects.filter(id=form_data[field]).first()
                        setattr(proposta, field, user)
                    else:
                        if field == 'orcamentista':  # orcamentista pode ser null
                            setattr(proposta, field, None)
                # Tratamento especial para campos de data
                elif field in ['dt_oferta', 'last', 'next', 'dt_prev_fechamento']:
                    try:
                        if form_data[field] == 'null' or not form_data[field]:
                            print(f"Definindo {field} como None")
                            setattr(proposta, field, None)
                        else:
                            date_value = datetime.strptime(form_data[field], '%Y-%m-%d').date()
                            print(f"Definindo {field} como {date_value}")
                            setattr(proposta, field, date_value)
                    except ValueError as e:
                        print(f"Erro ao processar data {field}: {e}")
                        continue
                # Tratamento especial para campos decimais
                elif field in ['valor', 'inversor_valor', 'modulo_valor', 'estrutura_valor', 'cabo_valor']:
                    try:
                        if form_data[field]:
                            value = Decimal(str(form_data[field]).replace(',', '.'))
                            setattr(proposta, field, value)
                        else:
                            setattr(proposta, field, Decimal('0'))
                    except (ValueError, InvalidOperation):
                        continue
                # Tratamento especial para campos inteiros
                elif field in ['inversor_quantidade', 'modulo_quantidade']:
                    try:
                        if form_data[field]:
                            setattr(proposta, field, int(form_data[field]))
                        else:
                            setattr(proposta, field, 0)
                    except ValueError:
                        continue
                else:
                    setattr(proposta, field, form_data[field] or None)
            
            print("Salvando proposta...")
            proposta.save()
            print("Proposta salva com sucesso!")
            
            # Retorna os dados atualizados no mesmo formato do get_propostas_data
            return JsonResponse({
                'success': True,
                'data': {
                    'dt_oferta': format_date(proposta.dt_oferta) if proposta.dt_oferta else None,
                    'ultima_revisao': proposta.ultima_revisao or 0,
                    'cliente': proposta.cliente or '',
                    'uf': proposta.uf or '',
                    'obra': proposta.obra or '',
                    'contato': proposta.contato or '',
                    'agente': proposta.get_agente_display() or '',
                    'controle_interno': {'id': str(proposta.controle_interno.id), 'name': f"{proposta.controle_interno.first_name} {proposta.controle_interno.last_name}"} if proposta.controle_interno else None,
                    'orcamentista': {'id': str(proposta.orcamentista.id), 'name': f"{proposta.orcamentista.first_name} {proposta.orcamentista.last_name}"} if proposta.orcamentista else None,
                    'tipo': proposta.tipo or '',
                    'escopo': proposta.escopo or '',
                    'valor': format_decimal(proposta.valor),
                    'chance': proposta.chance or '',
                    'estagio': proposta.estagio or '',
                    'canal': proposta.get_canal_display() or '',
                    'last': format_date(proposta.last) if proposta.last else None,
                    'next': format_date(proposta.next) if proposta.next else None,
                    'tipo_solar': proposta.tipo_solar or '',
                    'inversor_marca': proposta.inversor_marca or '',
                    'inversor_potencia': proposta.inversor_potencia or '',
                    'inversor_quantidade': proposta.inversor_quantidade or 0,
                    'inversor_valor': format_decimal(proposta.inversor_valor),
                    'modulo_marca': proposta.modulo_marca or '',
                    'modulo_potencia': proposta.modulo_potencia or '',
                    'modulo_quantidade': proposta.modulo_quantidade or 0,
                    'modulo_valor': format_decimal(proposta.modulo_valor),
                    'estrutura_marca': proposta.estrutura_marca or '',
                    'estrutura_modelo': proposta.estrutura_modelo or '',
                    'estrutura_valor': format_decimal(proposta.estrutura_valor),
                    'cabo_marca': proposta.cabo_marca or '',
                    'cabo_valor': format_decimal(proposta.cabo_valor),
                    'obs_solar': proposta.obs_solar or '',
                    'dt_prev_fechamento': format_date(proposta.dt_prev_fechamento) if proposta.dt_prev_fechamento else None
                }
            })
        
        return JsonResponse({
            'success': False,
            'error': 'Método não permitido'
        }, status=405)
        
    except Exception as e:
        print(f"Erro ao salvar edição: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

class PropostaStateView(APIView):
    """
    View para obter o estado atual de uma proposta.
    """
    def get(self, request, id_proposta):
        try:
            # Buscar a proposta
            proposta = get_object_or_404(Proposta, id_proposta=id_proposta)
            
            # Buscar a última revisão
            ultima_revisao = Revisao.objects.filter(
                id_proposta=proposta
            ).order_by('-revisao').first()
            
            # Preparar dados para retorno
            data = {
                'proposta_id': str(proposta.id_proposta),
                'cliente': proposta.cliente,
                'bt': proposta.proposta,
                'obra': proposta.obra,
                'nova_revisao': (ultima_revisao.revisao + 1) if ultima_revisao else 0
            }
            
            return Response(data)
            
        except Exception as e:
            return Response({"error": str(e)}, status=400)
        

@login_required
def get_proposta_comentarios(request, id_proposta):
    """
    Função para obter comentários de uma proposta
    """
    try:
        proposta = get_object_or_404(Proposta, id_proposta=id_proposta)
        
        # Busca comentários otimizada
        comentarios = (Comentario.objects
            .filter(id_proposta=proposta)
            .order_by('-dt_comentario')
            .only(
                'id_comentario',
                'dt_comentario',
                'comentario',
                'dt_acao'
            )
        )
            
        # Prepara os dados com tratamento de datas
        comentarios_data = [{
            'id_comentario': str(com.id_comentario),
            'dt_comentario': com.dt_comentario.strftime('%d/%m/%y %H:%M:%S') if com.dt_comentario else None,
            'comentario': com.comentario or '',
            'acao': com.dt_acao.strftime('%d/%m/%y') if com.dt_acao else ''
        } for com in comentarios]

        data = {
            'proposta': {
                'proposta': proposta.proposta,
                'cliente': proposta.cliente
            },
            'comentarios': comentarios_data
        }

        return JsonResponse(data)
        
    except Exception as e:
        print(f"Erro ao buscar comentários: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def criar_comentario(request):
    """
    Função para criar um comentário para uma proposta
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método não permitido'})
    
    try:
        print("Dados recebidos:", request.POST)  # Debug
        
        # Validação dos campos obrigatórios
        id_proposta = request.POST.get('id_proposta')
        comentario_texto = request.POST.get('comentario')
        dt_acao = request.POST.get('dt_acao')
        
        if not id_proposta or not comentario_texto:
            return JsonResponse({
                'success': False, 
                'error': 'ID da proposta e comentário são obrigatórios'
            })
        
        # Busca a proposta pelo ID
        try:
            proposta = Proposta.objects.get(id_proposta=id_proposta)
        except Proposta.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'error': f'Proposta com ID {id_proposta} não encontrada'
            })
        
        # Cria o comentário
        comentario = Comentario.objects.create(
            id_proposta=proposta,
            comentario=comentario_texto,
            dt_acao=dt_acao if dt_acao else None,
            dt_comentario=timezone.now()  # Adiciona a data atual do comentário
        )

        # Atualiza os campos next e last da proposta
        if dt_acao:
            # O next é sempre a nova data de ação
            proposta.next = dt_acao
            
            # Pega o comentário com a maior data de ação que seja menor que a nova data
            comentario_anterior = Comentario.objects.filter(
                id_proposta=proposta,
                dt_acao__lt=dt_acao
            ).order_by('-dt_acao').first()

            # Se encontrou um comentário anterior, sua data vira o last
            # Se não encontrou, o last fica como a data atual
            proposta.last = comentario_anterior.dt_acao if comentario_anterior else dt_acao
            proposta.save()
        
        print(f"Comentário salvo com sucesso. ID: {comentario.id_comentario}")
        
        return JsonResponse({
            'success': True,
            'message': 'Comentário criado com sucesso',
            'id': str(comentario.id_comentario)
        })
        
    except Exception as e:
        print("Erro ao salvar comentário:", str(e))
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def editar_revisao(request, id_revisao):
    """Edita uma revisão existente e atualiza a URL do Streamlit"""
    # Busca a revisão pelo ID
    revisao = get_object_or_404(Revisao, id_revisao=id_revisao)

    if request.method == 'POST':
        # Atualiza a revisão com os dados do formulário
        revisao_form = RevisarForm(request.POST, request.FILES, instance=revisao)
        if revisao_form.is_valid():
            revisao_form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': revisao_form.errors})
    else:
        # Preenche o formulário com os dados da revisão
        revisao_form = RevisarForm(instance=revisao)

    # Determina qual URL do Streamlit usar baseado no tipo da proposta
    tipo_proposta = revisao.id_proposta.tipo # Ajuste para o nome do seu campo
    if tipo_proposta == 'S':
        streamlit_url = settings.STREAMLIT_SECO_URL
    elif tipo_proposta == 'B':
        streamlit_url = settings.STREAMLIT_BT_URL
    else:
        streamlit_url = settings.STREAMLIT_SOLAR_URL

    return JsonResponse({
        'revisao_form': revisao_form.data,
        'revisao': revisao.id_revisao,
        'id_proposta': revisao.id_proposta.id_proposta,
        'streamlit_url': streamlit_url
    })

class RevisaoStateView(APIView):
    """
    View para obter o estado atual de uma revisão.
    """
    def get(self, request, id_revisao):
        try:
            revisao = get_object_or_404(Revisao, id_revisao=id_revisao)
            
            # Retorna os dados da revisão
            data = {
                'proposta_id': str(revisao.id_proposta.id_proposta),
                'valor': float(revisao.valor) if revisao.valor else 0,
                'conteudo': revisao.conteudo  # seu campo JSON
            }
            
            return Response(data)
            
        except Exception as e:
            return Response({"error": str(e)}, status=400)

@login_required
def get_proposta_revisoes(request, id_proposta):
    """
    Função para obter revisões de uma proposta e configura a URL do Streamlit
    """
    try:
        print(f"Buscando proposta com ID: {id_proposta}")
        proposta = get_object_or_404(Proposta, id_proposta=id_proposta)
        print(f"Proposta encontrada: {proposta.proposta}")
        
        # Busca revisões otimizada
        print("Buscando revisões...")
        revisoes = (Revisao.objects
            .filter(id_proposta=proposta)
            .order_by('revisao')
            .only(
                'id_revisao',
                'dt_revisao',
                'revisao',
                'valor',
                'comentario',
                'arquivo',
                'acao',
                'arquivo_pdf'
            )
        )
        print(f"Número de revisões encontradas: {revisoes.count()}")
            
        # Prepara os dados com tratamento de datas
        revisoes_data = []
        for rev in revisoes:
            revisao_dict = {
                'id_revisao': str(rev.id_revisao),
                'dt_revisao': rev.dt_revisao.strftime('%Y-%m-%d') if rev.dt_revisao else None,
                'revisao': rev.revisao,
                'valor': float(rev.valor) if rev.valor else 0,
                'comentario': rev.comentario if rev.comentario else '',
                'arquivo': rev.arquivo.url if rev.arquivo else None,
                'acao': rev.acao if rev.acao else '',
                'arquivo_pdf': rev.arquivo_pdf.url if rev.arquivo_pdf else None,
                'is_ultima_revisao': rev.revisao == proposta.ultima_revisao + 1
            }
            revisoes_data.append(revisao_dict)

        # Determina URL do Streamlit
        streamlit_url = {
            'S': settings.STREAMLIT_SECO_URL,
            'B': settings.STREAMLIT_BT_URL
        }.get(proposta.tipo, settings.STREAMLIT_SOLAR_URL)

        data = {
            'proposta': {
                'id_proposta': str(proposta.id_proposta),
                'proposta': proposta.proposta,
                'cliente': proposta.cliente,
                'ultima_revisao': proposta.ultima_revisao or 0,
                'valor': float(proposta.valor) if proposta.valor else 0,
                'tipo': proposta.tipo,
                'escopo': proposta.escopo
            },
            'revisoes': revisoes_data,
            'streamlit_url': streamlit_url
        }

        return JsonResponse(data)
        
    except Exception as e:
        print(f"Erro ao buscar revisões: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def get_revisao_data(request, id_revisao):
    """
    Retorna os dados específicos de uma revisão.
    Usado no processo de edição para obter os dados antigos da revisão.
    """
    try:
        revisao = get_object_or_404(Revisao, id_revisao=id_revisao)
        
        data = {
            'revisao': revisao.revisao,
            'valor': float(revisao.valor) if revisao.valor else 0,
            'comentario': revisao.comentario or ''
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def get_ultima_revisao(request, id_proposta):
    """
    Função para obter dados da última revisão de uma proposta
    """
    try:
        proposta = get_object_or_404(Proposta, id_proposta=id_proposta)
        ultima_revisao = Revisao.objects.filter(id_proposta=proposta).order_by('-revisao').first()
        
        if ultima_revisao:
            # Se existe uma última revisão
            return JsonResponse({
                'success': True,
                'tem_revisoes': True,
                'proxima_revisao': ultima_revisao.revisao + 1,
                'valor_atual': str(ultima_revisao.valor),
                'tipo': proposta.tipo,  # Pega o tipo da proposta atual
                'escopo': proposta.escopo  # Pega o escopo da proposta atual
            })
        else:
            # Se não existe revisão, retorna dados da proposta inicial
            return JsonResponse({
                'success': True,
                'tem_revisoes': False,
                'proxima_revisao': 0,
                'valor_atual': str(proposta.valor),
                'tipo': proposta.tipo,
                'escopo': proposta.escopo
            })
            
    except Exception as e:
        print(f"Erro ao buscar última revisão: {str(e)}")  # Log do erro para debug
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=400)


@login_required
@transaction.atomic
def criar_revisao(request):
    """
    Função para criar uma nova revisão de uma proposta. Contém as regras de negócio para atualização no modelo proposta na coluna valor e ultima_revisao
    """

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método não permitido'})
    
    try:
        id_proposta = request.POST.get('id_proposta')
        proposta = get_object_or_404(Proposta, id_proposta=id_proposta)
        
        # Preparar dados da revisão
        revisao = Revisao(
            id_proposta=proposta,
            revisao=request.POST.get('revisao'),
            valor=request.POST.get('valor'),
            escopo=request.POST.get('escopo')
        )
        
        # Verificar mudanças na proposta
        novo_tipo = request.POST.get('tipo')
        novo_escopo = request.POST.get('escopo')
        mudancas = {}
        
        if novo_tipo and novo_tipo != proposta.tipo:
            mudancas['tipo'] = {'old': proposta.tipo, 'new': novo_tipo}
            proposta.tipo = novo_tipo
            
        if novo_escopo and novo_escopo != proposta.escopo:
            mudancas['escopo'] = {'old': proposta.escopo, 'new': novo_escopo}
            proposta.escopo = novo_escopo
            
        if revisao.valor != proposta.valor:
            mudancas['valor'] = {'old': str(proposta.valor), 'new': str(revisao.valor)}
        
        # Gerar log apenas se houver mudanças
        if mudancas:
            log_mudancas = []
            for campo, valores in mudancas.items():
                log_mudancas.append(f"{campo}: {valores['old']} → {valores['new']}")
            revisao.acao = ' | '.join(log_mudancas)
        
        # Verificar se é a última revisão
        is_ultima_revisao = int(revisao.revisao) == proposta.ultima_revisao + 1
        if is_ultima_revisao:
            proposta.valor = revisao.valor
            proposta.ultima_revisao = revisao.revisao
        
        # Salvar arquivo se fornecido
        if 'arquivo' in request.FILES:
            revisao.arquivo = request.FILES['arquivo']
        
        # Salvar as alterações
        revisao.save()  # Primeiro salva a revisão
        proposta.save()  # Depois salva a proposta com as atualizações
        
        # Preparar resposta
        response_data = {
            'success': True,
            'message': 'Revisão criada com sucesso',
            'revisao': {
                'id': revisao.id_revisao,
                'numero': revisao.revisao,
                'valor': str(revisao.valor),
                'escopo': revisao.escopo,
                'acao': revisao.acao
            },
            'proposta': {
                'id': proposta.id_proposta,
                'valor': str(proposta.valor),
                'ultima_revisao': proposta.ultima_revisao,
                'tipo': proposta.tipo,
                'escopo': proposta.escopo
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Erro ao criar revisão: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Erro ao criar revisão: {str(e)}'
        }, status=500)
    
def gerar_log_mudancas(old_data, new_data):
    """
    Função para capturar a mudança entre revisões e gravar na coluna acao
    """
    mudancas = []
    
    # Verifica mudança no valor
    if old_data['valor'] != new_data['valor']:
        mudancas.append(f"Valor mudado de {formatar_dinheiro(old_data['valor'])} para {formatar_dinheiro(new_data['valor'])}")

    # Verifica mudança no tipo
    if old_data['tipo'] != new_data['tipo']:
        mudancas.append(f"Tipo mudado de {old_data['tipo'] or 'vazio'} para {new_data['tipo'] or 'vazio'}")

    # Verifica mudança no escopo
    if old_data['escopo'] != new_data['escopo']:
        mudancas.append(f"Escopo mudado de {old_data['escopo'] or 'vazio'} para {new_data['escopo'] or 'vazio'}")

    return ' | '.join(mudancas)

def formatar_dinheiro(valor):
    return f"R$ {float(valor):.2f}"

@login_required
def get_clientes_unicos(request):
    search = request.GET.get('q', '')
    clientes = Proposta.objects.values_list('cliente', flat=True).distinct()
    
    if search:
        clientes = clientes.filter(cliente__icontains=search)
    
    clientes = clientes.order_by('cliente')[:10]  # Limita a 10 resultados
    return JsonResponse({
        'results': [
            {'id': cliente, 'text': cliente} 
            for cliente in clientes 
            if cliente
        ]
    })

@login_required
def get_contatos_por_cliente(request):
    cliente = request.GET.get('cliente', '')
    search = request.GET.get('q', '')
    
    contatos = Proposta.objects.filter(cliente=cliente).values_list('contato', flat=True).distinct()
    
    if search:
        contatos = contatos.filter(contato__icontains=search)
    
    contatos = contatos.order_by('contato')[:10]
    
    return JsonResponse({
        'results': [
            {'id': contato, 'text': contato} 
            for contato in contatos 
            if contato
        ]
    })

@login_required
def get_proposta_unicos(request):
    search = request.GET.get('q', '')
    
    if len(search) >= 5 and search.isdigit():
        proposta = Proposta.objects.filter(proposta__startswith=search)
    
        if not proposta.exists():
            return JsonResponse({
                'results': [],
                'message': 'Nenhum resultado encontrado ou a pesquisa tem menos de 5 digitos'
            })
        proposta = proposta.order_by('proposta')[:10]

        return JsonResponse({
            'results': [
                {'id': prop, 'text': prop} 
                for prop in proposta.values_list('proposta', flat=True)
                if prop
            ]
        })
    else:
        return JsonResponse({
            'results': [],
            'message': 'Nenhum resultado encontrado ou a pesquisa tem menos de 5 digitos'
        })

def get_propostas_totais(request):
    """
    View para obter o valor quantitativo de propostas e valor monetário de acordo com os filtros.
    """
    try:
        data = json.loads(request.body)
        filters = data.get('filters', {})
        mostrar_fechados = data.get('mostrar_fechados') == 'true'
        mostrar_atrasados = data.get('mostrar_atrasados') == 'true'
        mostrar_meus_follows = data.get('mostrar_meus_follows') == 'true'
        search_value = data.get('search', '')

        # Inicia com uma query otimizada
        queryset = Proposta.objects.only('id_proposta', 'valor', 'estagio', 'next', 'last', 'controle_interno_id')

        # Aplica filtros básicos usando Q objects para melhor performance
        filters_q = Q()
        if not mostrar_fechados:
            filters_q &= Q(estagio__in=ESTAGIOS_ABERTOS)
        
        if mostrar_atrasados:
            today = now().date()
            filters_q &= (Q(next__lt=today) | Q(next__isnull=True, last__lt=today))
        
        if mostrar_meus_follows:
            filters_q &= Q(controle_interno=request.user)

        if search_value:
            search_q = (Q(proposta__icontains=search_value) |
                       Q(cliente__icontains=search_value) |
                       Q(obra__icontains=search_value) |
                       Q(contato__icontains=search_value) |
                       Q(escopo__icontains=search_value) |
                       Q(tipo__icontains=search_value) |
                       Q(estagio__icontains=search_value))
            filters_q &= search_q

        queryset = queryset.filter(filters_q)

        # Aplica filtros customizados em lote
        if filters:
            custom_filters_q = Q()
            for index, filter_data in filters.items():
                field = get_field_name(int(index))
                if not field:
                    continue

                if filter_data['type'] == 'date':
                    if filter_data.get('start'):
                        custom_filters_q &= Q(**{f"{field}__gte": filter_data['start']})
                    if filter_data.get('end'):
                        custom_filters_q &= Q(**{f"{field}__lte": filter_data['end']})
                
                elif filter_data['type'] == 'number':
                    if filter_data.get('min') is not None:
                        custom_filters_q &= Q(**{f"{field}__gte": float(filter_data['min'])})
                    if filter_data.get('max') is not None:
                        custom_filters_q &= Q(**{f"{field}__lte": float(filter_data['max'])})
                
                elif filter_data['type'] == 'select' and filter_data.get('values'):
                    if field in ['controle_interno', 'orcamentista']:
                        # Tratamento especial para campos de usuário
                        names = [name.split() for name in filter_data['values']]
                        q_objects = Q()
                        for name_parts in names:
                            if len(name_parts) >= 2:
                                q_objects |= Q(
                                    **{f"{field}__first_name__icontains": name_parts[0],
                                       f"{field}__last_name__icontains": name_parts[-1]}
                                )
                        if q_objects:
                            custom_filters_q &= q_objects
                    else:
                        custom_filters_q &= Q(**{f"{field}__in": filter_data['values']})

            if custom_filters_q:
                queryset = queryset.filter(custom_filters_q)

        # Realiza agregação em uma única query
        totais = queryset.aggregate(
            total_propostas=Count('id_proposta'),
            valor_total=Sum('valor')
        )

        return JsonResponse({
            'success': True,
            'total_propostas': totais['total_propostas'],
            'valor_total': float(totais['valor_total'] or 0)
        })

    except Exception as e:
        print(f"Erro ao calcular totais: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def get_proposta_detalhes(request):
    proposta_numero = request.GET.get('proposta', '')
    
    try:
        proposta = Proposta.objects.get(proposta=proposta_numero)
        
        return JsonResponse({
            'cliente': proposta.cliente if proposta.cliente else '',
            'obra': proposta.obra or '',
            'uf': proposta.uf or '',
            'contato': proposta.contato if proposta.contato else '',
            'agente': proposta.get_agente_display() or '',
            'canal': proposta.get_canal_display() or '',
        })
    except Proposta.DoesNotExist:
        return JsonResponse({
            'error': 'Proposta não encontrada'
        }, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def atualizar_revisao(request):
    """
    Atualiza uma revisão existente com novos valores.
    
    Parâmetros esperados no request.data:
    - id_revisao: UUID da revisão
    - conteudo: JSON com o conteúdo da revisão
    - valor: Valor decimal da revisão
    - comentario: Texto do comentário
    - escopo: Texto do escopo
    """
    try:
        id_revisao = request.data.get('id_revisao')
        if not id_revisao:
            return Response({'error': 'ID da revisão é obrigatório'}, status=400)
            
        # Busca a revisão
        try:
            revisao = Revisao.objects.get(id_revisao=id_revisao)
        except Revisao.DoesNotExist:
            return Response({'error': 'Revisão não encontrada'}, status=404)
            
        # Atualiza os campos
        if 'conteudo' in request.data:
            revisao.conteudo = request.data['conteudo']
        if 'valor' in request.data:
            revisao.valor = request.data['valor']
        if 'comentario' in request.data:
            revisao.comentario = request.data['comentario']
        if 'escopo' in request.data:
            revisao.escopo = request.data['escopo']
            
        # Salva as alterações
        revisao.save()
        
        return Response({
            'success': True,
            'message': 'Revisão atualizada com sucesso',
            'data': {
                'id_revisao': str(revisao.id_revisao),
                'valor': float(revisao.valor),
                'comentario': revisao.comentario,
                'escopo': revisao.escopo
            }
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)

import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def inserir_revisao(request):
    """
    Insere uma nova revisão ou atualiza uma existente.
    """
    # Autenticação JWT
    authentication_classes = [JWTAuthentication]
    
    # Log do método da requisição
    logger.info(f"Método da requisição: {request.method}")
    logger.info(f"Content-Type: {request.headers.get('Content-Type', 'Não especificado')}")
    logger.info(f"Authorization: {request.headers.get('Authorization', 'Não especificado')}")
    
    # Log dos dados recebidos
    logger.info("Dados recebidos:")
    logger.info(f"request.data: {request.data}")
    logger.info(f"request.FILES: {request.FILES}")
    
    try:
        id_proposta = request.data.get('id_proposta')
        valor = request.data.get('valor')
        numero_revisao = request.data.get('revisao')
        escopo = request.data.get('escopo')
        tipo = request.data.get('tipo', '')
        dados = json.loads(request.data.get('conteudo', '{}'))
        arquivo = request.FILES.get('arquivo')

        logger.info(f"""
        Dados processados:
        - id_proposta: {id_proposta}
        - valor: {valor}
        - numero_revisao: {numero_revisao}
        - escopo: {escopo}
        - tipo: {tipo}
        - arquivo presente: {arquivo is not None}
        """)


        # Validações básicas
        if not all([id_proposta, valor is not None, numero_revisao is not None]):
            return Response({
                'error': 'id_proposta, valor e revisao são obrigatórios'
            }, status=400)

        # Busca a proposta
        try:
            proposta = Proposta.objects.get(id_proposta=id_proposta)
        except Proposta.DoesNotExist:
            return Response({'error': 'Proposta não encontrada'}, status=404)

        # Verifica se já existe uma revisão com este número
        revisao_existente = Revisao.objects.filter(
            id_proposta=proposta,
            revisao=numero_revisao
        ).order_by('-dt_revisao').first()

        if revisao_existente:
            # Atualiza a revisão existente
            revisao_existente.conteudo = dados
            revisao_existente.valor = valor
            revisao_existente.dt_revisao = now()
            revisao_existente.comentario = dados.get('dados_iniciais', {}).get('comentario', 'Revisão Atualizada')
            if arquivo:
                revisao_existente.arquivo = arquivo
            revisao_existente.escopo = escopo
            revisao_existente.save()

            revisao_id = revisao_existente.id_revisao

        else:
            # Verifica se é a próxima revisão válida
            ultima_revisao = Revisao.objects.filter(id_proposta=proposta).order_by('-revisao').first()
            proxima_revisao = 0 if not ultima_revisao else ultima_revisao.revisao + 1

            if int(numero_revisao) != proxima_revisao:
                return Response({
                    'error': f'Número de revisão inválido. A próxima revisão deve ser {proxima_revisao}'
                }, status=400)

            # Cria uma nova revisão
            comentario = 'Revisão Inicial' if numero_revisao == 0 else dados.get('dados_iniciais', {}).get('comentario', '')
            
            nova_revisao = Revisao.objects.create(
                id_proposta=proposta,
                conteudo=dados,
                valor=valor,
                revisao=numero_revisao,
                comentario=comentario,
                arquivo=arquivo if arquivo else None,
                escopo=escopo
            )

            revisao_id = nova_revisao.id_revisao

            # Se for a última revisão, atualiza a proposta
            if int(numero_revisao) > proposta.ultima_revisao:
                proposta.valor = valor
                proposta.ultima_revisao = numero_revisao
                proposta.tipo = tipo if tipo else proposta.tipo
                proposta.escopo = escopo
                proposta.save()

        return Response({
            'success': True,
            'message': 'Revisão processada com sucesso',
            'revisao': {
                'id': str(revisao_id)
            }
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

import jwt
from datetime import datetime, timedelta

@login_required
def generate_streamlit_token(request):
    """Gera um token JWT para autenticação com o Streamlit"""
    try:
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(request.user)
        
        # Log do token gerado
        logger.info(f"Token gerado para usuário: {request.user.username}")
        
        return JsonResponse({
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'token_type': 'Bearer'
        })
    except Exception as e:
        logger.error(f"Erro ao gerar token: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)