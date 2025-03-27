"""
Interface do repositório de usuários.
Define o contrato para operações com usuários no domínio.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from django.contrib.auth import get_user_model

# Usando o model User do Django por enquanto para manter compatibilidade
User = get_user_model()


class UserRepository(ABC):
    """
    Interface para operações de persistência com usuários.
    """
    
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Recupera um usuário pelo ID.
        """
        pass
    
    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        """
        Recupera um usuário pelo nome de usuário.
        """
        pass
    
    @abstractmethod
    def get_all(self) -> List[User]:
        """
        Recupera todos os usuários.
        """
        pass
    
    @abstractmethod
    def save(self, user: User) -> User:
        """
        Salva (cria ou atualiza) um usuário.
        """
        pass
    
    @abstractmethod
    def delete(self, user: User) -> None:
        """
        Remove um usuário.
        """
        pass
    
    @abstractmethod
    def update_futcoins(self, user_id: int, amount: int) -> User:
        """
        Atualiza o saldo de futcoins de um usuário.
        """
        pass 