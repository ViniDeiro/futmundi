"""
Serviço de aplicação para operações com usuários.
"""

from django.contrib.auth import get_user_model
from domain.services.user_service import UserService
from domain.repositories.user_repository import IUserRepository

# Usando o model User do Django por enquanto para manter compatibilidade
User = get_user_model()


class UserAppService:
    """
    Serviço de aplicação para coordenar operações relacionadas a usuários.
    """
    
    def __init__(self, user_service: UserService):
        self.user_service = user_service
    
    def add_daily_reward(self, user_id: int, day_of_week: int) -> User:
        """
        Adiciona recompensa diária ao usuário com base no dia da semana.
        
        Args:
            user_id: ID do usuário
            day_of_week: Dia da semana (0-6, onde 0 é segunda-feira)
        
        Returns:
            User: Usuário atualizado
        """
        # Mapeamento de dias da semana para recompensas (valores exemplo)
        rewards = {
            0: 5,   # Segunda-feira
            1: 10,  # Terça-feira
            2: 15,  # Quarta-feira
            3: 20,  # Quinta-feira
            4: 25,  # Sexta-feira
            5: 30,  # Sábado
            6: 50   # Domingo
        }
        
        # Verifica se o dia da semana é válido
        if day_of_week not in rewards:
            raise ValueError(f"Dia da semana inválido: {day_of_week}")
        
        # Adiciona recompensa com base no dia da semana
        return self.user_service.add_futcoins(user_id, rewards[day_of_week])
    
    def process_purchase(self, user_id: int, item_id: str, price: int) -> bool:
        """
        Processa uma compra para o usuário.
        
        Args:
            user_id: ID do usuário
            item_id: ID do item sendo comprado
            price: Preço do item
        
        Returns:
            bool: True se a compra foi bem-sucedida, False caso contrário
        """
        # Verifica se o usuário pode fazer a compra
        if not self.user_service.can_purchase(user_id, price):
            return False
        
        try:
            # Remove futcoins do usuário
            self.user_service.remove_futcoins(user_id, price)
            
            # Aqui seria registrada a compra no sistema
            # (código omitido para manter o exemplo simples)
            
            return True
        except ValueError:
            return False 