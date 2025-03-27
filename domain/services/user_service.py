"""
Serviço de domínio para operações com usuários.
"""

from typing import Optional
from django.contrib.auth import get_user_model
from domain.repositories.user_repository import UserRepository

# Usando o model User do Django por enquanto para manter compatibilidade
User = get_user_model()


class UserService:
    """
    Serviço de domínio para lógica de negócio relacionada a usuários.
    """
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    def add_futcoins(self, user_id: int, amount: int) -> User:
        """
        Adiciona futcoins à conta do usuário.
        
        Args:
            user_id: ID do usuário
            amount: Quantidade de futcoins a adicionar
        
        Returns:
            User: Usuário atualizado
        
        Raises:
            ValueError: Se a quantidade for negativa
        """
        if amount < 0:
            raise ValueError("A quantidade de futcoins não pode ser negativa")
        
        return self.user_repository.update_futcoins(user_id, amount)
    
    def remove_futcoins(self, user_id: int, amount: int) -> User:
        """
        Remove futcoins da conta do usuário.
        
        Args:
            user_id: ID do usuário
            amount: Quantidade de futcoins a remover
        
        Returns:
            User: Usuário atualizado
        
        Raises:
            ValueError: Se a quantidade for negativa ou se o usuário não tiver saldo suficiente
        """
        if amount < 0:
            raise ValueError("A quantidade de futcoins não pode ser negativa")
        
        user = self.user_repository.get_by_id(user_id)
        if user is None:
            raise ValueError(f"Usuário com ID {user_id} não encontrado")
        
        if user.futcoins < amount:
            raise ValueError("Saldo de futcoins insuficiente")
        
        return self.user_repository.update_futcoins(user_id, -amount)
    
    def can_purchase(self, user_id: int, price: int) -> bool:
        """
        Verifica se o usuário tem saldo suficiente para uma compra.
        
        Args:
            user_id: ID do usuário
            price: Preço do item
        
        Returns:
            bool: True se o usuário tem saldo suficiente, False caso contrário
        """
        user = self.user_repository.get_by_id(user_id)
        if user is None:
            return False
        
        return user.futcoins >= price 