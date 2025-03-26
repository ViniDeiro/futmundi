"""
Implementações de repositórios usando Django ORM.
"""

from typing import List, Optional
from django.contrib.auth import get_user_model
from django.db.models import F

from domain.repositories.user_repository import IUserRepository

# Usando o model User do Django por enquanto para manter compatibilidade
User = get_user_model()


class DjangoUserRepository(IUserRepository):
    """
    Implementação do repositório de usuários usando Django ORM.
    """
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Recupera um usuário pelo ID.
        """
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
    
    def get_by_username(self, username: str) -> Optional[User]:
        """
        Recupera um usuário pelo nome de usuário.
        """
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None
    
    def get_all(self) -> List[User]:
        """
        Recupera todos os usuários.
        """
        return list(User.objects.all())
    
    def save(self, user: User) -> User:
        """
        Salva (cria ou atualiza) um usuário.
        """
        user.save()
        return user
    
    def delete(self, user: User) -> None:
        """
        Remove um usuário.
        """
        user.delete()
    
    def update_futcoins(self, user_id: int, amount: int) -> User:
        """
        Atualiza o saldo de futcoins de um usuário.
        """
        User.objects.filter(id=user_id).update(futcoins=F('futcoins') + amount)
        return self.get_by_id(user_id) 