import os
from pathlib import Path
from django.contrib import messages
from dotenv import load_dotenv
from datetime import timedelta

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

AZURE_APP_ID = os.getenv('AZURE_APP_ID')
AZURE_TENANT_ID = os.getenv('AZURE_TENANT_ID')
AZURE_APP_SECRET = os.getenv('AZURE_APP_SECRET')

STREAMLIT_SECO_URL = 'http://localhost:8502/'
STREAMLIT_BT_URL = 'http://localhost:8501/'
STREAMLIT_SOLAR_URL = 'http://localhost:8502'

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Configurações de segurança
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-o-ym^!2$dnu83gy$pe6b7%k^b!w2b1pxj1l*mdvmb6w-+*5nqj')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*'] 

# Sessões
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',
    'widget_tweaks',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'social_django',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.microsoft',
    'gerenciadorpropostas',
]

SITE_ID = 1

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware', 
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'gerenciadorpropostas.middleware.AzureADSyncMiddleware',
]

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'django_debug.log',
        },
        'console': {  # Este handler envia os logs para o terminal
            'level': 'DEBUG',  # Você pode ajustar o nível de log, se necessário
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Envia para o terminal
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],  # Adicionando o console ao logger principal
            'level': 'INFO',
            'propagate': True,
        },
        'gerenciadorpropostas.signals': {
            'handlers': ['file', 'console'],  # Adicionando o console ao logger específico
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

ROOT_URLCONF = 'app_propostas.urls'

# Templating
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'app_propostas.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'postgres'),  # Banco de dados
        'USER': os.getenv('DB_USER', 'postgres.ptrcozhpnxcvvvloerna'),  # Usuário
        'PASSWORD': os.getenv('DB_PASSWORD', 'KO9snICF4X9vQInn'),  # Senha
        'HOST': os.getenv('DB_HOST', 'aws-0-us-west-1.pooler.supabase.com'),  # Host do banco
        'PORT': os.getenv('DB_PORT', '6543'),  # Porta do banco
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Autenticação e usuário customizado
AUTH_USER_MODEL = 'gerenciadorpropostas.CustomUser'

URLSUPORTE = os.getenv('URLSUPORTE')

# Message tags para personalizar alertas no frontend
MESSAGE_TAGS = {
    messages.ERROR: 'danger',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.INFO: 'info',
}

# Login settings
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# Autenticação com Microsoft OAuth2
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

# OAuth2 Configuração
SOCIALACCOUNT_PROVIDERS = {
    'microsoft': {
        'TENANT': os.getenv('AZURE_TENANT_ID'),
        'APP': {
            'client_id': os.getenv('AZURE_CLIENT_ID'),
            'secret': os.getenv('AZURE_CLIENT_SECRET'),
            'key': ''
        },
        'SCOPE': ['User.Read', 'User.ReadBasic.All', 'offline_access'],
        'AUTH_PARAMS': {'prompt': 'select_account'},
    }
}

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'none'

# Configuração de internacionalização e fuso horário
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Configuração para testes
TEST_RUNNER = 'django.test.runner.DiscoverRunner'
TEST_DATABASE_CREATE = True
TEST_DATABASE_DESTROY = True

# Static and media files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Configurações de mídia
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Redis cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
    }
}

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

# JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True  # Apenas para desenvolvimento
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8501",  # Streamlit
    "http://localhost:8000",  # Django
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
