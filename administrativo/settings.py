import os
from datetime import timedelta
from pathlib import Path

# ... código existente ...

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'administrativo',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'drf_yasg',  # Swagger/OpenAPI
]

# ... código existente ...

# Configuração do drf-yasg (Swagger)
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'Formato: Bearer {token}'
        }
    },
    'USE_SESSION_AUTH': False,
    'DEFAULT_API_URL': 'https://api.futmundi.com.br',
    'DEFAULT_INFO': {
        'title': 'Futmundi API',
        'description': 'API de Bolão de Futebol para o aplicativo Futmundi',
        'version': '1.0.0',
        'contact': {
            'name': 'Suporte Futmundi',
            'email': 'suporte@futmundi.com.br',
        },
        'license': {
            'name': 'Proprietário',
        },
    },
    'JSON_EDITOR': True,
    'VALIDATOR_URL': None,
}

# ... resto do código ... 