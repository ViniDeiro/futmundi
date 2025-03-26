"""
Configuração central para injeção de dependências entre as camadas do DDD.
Este arquivo permite uma integração mais suave entre o Django e a arquitetura DDD.
"""

from typing import Dict, Type, Any


class DependencyContainer:
    """
    Contêiner simples para gerenciar dependências e serviços.
    """
    _instances: Dict[str, Any] = {}
    
    @classmethod
    def register(cls, key: str, instance: Any) -> None:
        """
        Registra uma instância no contêiner.
        """
        cls._instances[key] = instance
    
    @classmethod
    def get(cls, key: str) -> Any:
        """
        Recupera uma instância do contêiner.
        """
        return cls._instances.get(key)


# Função para inicializar o contêiner de dependências
def initialize_dependencies():
    """
    Inicializa as dependências para a aplicação.
    Esta função deve ser chamada durante a inicialização do Django.
    """
    # Importa as implementações dos repositórios e serviços
    from domain.repositories.user_repository import IUserRepository
    from infrastructure.persistence.django_repositories import DjangoUserRepository
    from domain.services.user_service import UserService
    from application.services.user_app_service import UserAppService
    
    # Registra o repositório de usuários
    user_repository = DjangoUserRepository()
    DependencyContainer.register('user_repository', user_repository)
    
    # Registra o serviço de domínio de usuários
    user_service = UserService(user_repository)
    DependencyContainer.register('user_service', user_service)
    
    # Registra o serviço de aplicação de usuários
    user_app_service = UserAppService(user_service)
    DependencyContainer.register('user_app_service', user_app_service)
    
    print("Dependências DDD inicializadas com sucesso!") 