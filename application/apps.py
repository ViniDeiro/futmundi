"""
Configuração de aplicação para a camada de Aplicação do DDD.
"""

from django.apps import AppConfig


class ApplicationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'application'
    
    def ready(self):
        """
        Inicializa o contêiner de dependências quando o aplicativo é carregado.
        """
        from domain.config import initialize_dependencies
        
        # Inicializa todas as dependências do DDD
        initialize_dependencies() 