"""
Serviço de Aplicação para gerenciamento de Usuários e seus Casos de Uso.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from domain.repositories.user_repository import UserRepository
from domain.entities.user import User, UserProfile, UserPreference
from domain.events.user_events import UserCreatedEvent, UserUpdatedEvent, UserProfileUpdatedEvent
from domain.events.event_dispatcher import EventDispatcher


class UserAppService:
    """
    Serviço de Aplicação para orquestrar operações relacionadas a usuários.
    """
    
    def __init__(
        self,
        user_repository: UserRepository,
        event_dispatcher: EventDispatcher
    ):
        """
        Inicializa o serviço com os repositórios e serviços necessários.
        
        Args:
            user_repository: Repositório de usuários
            event_dispatcher: Despachante de eventos
        """
        self.user_repository = user_repository
        self.event_dispatcher = event_dispatcher
    
    def get_user(self, user_id: int) -> Optional[User]:
        """
        Obtém um usuário pelo ID.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            O usuário, se encontrado, ou None
        """
        return self.user_repository.get_by_id(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Obtém um usuário pelo nome de usuário.
        
        Args:
            username: Nome de usuário
            
        Returns:
            O usuário, se encontrado, ou None
        """
        return self.user_repository.get_by_username(username)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Obtém um usuário pelo e-mail.
        
        Args:
            email: E-mail do usuário
            
        Returns:
            O usuário, se encontrado, ou None
        """
        return self.user_repository.get_by_email(email)
    
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        profile: Optional[UserProfile] = None,
        preferences: Optional[UserPreference] = None
    ) -> User:
        """
        Cria um novo usuário.
        
        Args:
            username: Nome de usuário
            email: E-mail
            password: Senha
            first_name: Primeiro nome
            last_name: Sobrenome
            profile: Perfil do usuário (opcional)
            preferences: Preferências do usuário (opcional)
            
        Returns:
            O usuário criado
            
        Raises:
            ValueError: Se os dados fornecidos forem inválidos
        """
        # Validação básica
        if not username:
            raise ValueError("O nome de usuário é obrigatório")
        
        if not email:
            raise ValueError("O e-mail é obrigatório")
        
        if not password:
            raise ValueError("A senha é obrigatória")
        
        # Verifica disponibilidade do nome de usuário e e-mail
        if not self.user_repository.is_username_available(username):
            raise ValueError(f"O nome de usuário '{username}' já está em uso")
        
        if not self.user_repository.is_email_available(email):
            raise ValueError(f"O e-mail '{email}' já está em uso")
        
        # Cria o usuário
        user = User(
            id=None,
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            is_staff=False,
            is_superuser=False,
            date_joined=datetime.now(),
            last_login=None,
            profile=profile,
            preferences=preferences
        )
        
        # Salva o usuário
        user = self.user_repository.create(user)
        
        # Publica evento de criação
        self.event_dispatcher.dispatch(UserCreatedEvent(user_id=user.id))
        
        return user
    
    def update_user(self, user_id: int, **kwargs) -> User:
        """
        Atualiza um usuário existente.
        
        Args:
            user_id: ID do usuário
            **kwargs: Campos a serem atualizados
            
        Returns:
            O usuário atualizado
            
        Raises:
            ValueError: Se os dados fornecidos forem inválidos
            LookupError: Se o usuário não for encontrado
        """
        # Obtém o usuário
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise LookupError(f"Usuário com ID {user_id} não encontrado")
        
        # Verifica disponibilidade do nome de usuário e e-mail, se fornecidos
        if 'username' in kwargs and kwargs['username'] != user.username:
            if not self.user_repository.is_username_available(kwargs['username'], user_id):
                raise ValueError(f"O nome de usuário '{kwargs['username']}' já está em uso")
        
        if 'email' in kwargs and kwargs['email'] != user.email:
            if not self.user_repository.is_email_available(kwargs['email'], user_id):
                raise ValueError(f"O e-mail '{kwargs['email']}' já está em uso")
        
        # Extrai profile e preferences, se fornecidos
        profile = kwargs.pop('profile', None)
        preferences = kwargs.pop('preferences', None)
        
        # Atualiza os campos
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        # Atualiza o perfil, se fornecido
        if profile:
            user.profile = profile
        
        # Atualiza as preferências, se fornecidas
        if preferences:
            user.preferences = preferences
        
        # Salva as alterações
        user = self.user_repository.update(user)
        
        # Publica evento de atualização
        self.event_dispatcher.dispatch(UserUpdatedEvent(user_id=user.id))
        
        return user
    
    def update_profile(self, user_id: int, **kwargs) -> User:
        """
        Atualiza o perfil de um usuário.
        
        Args:
            user_id: ID do usuário
            **kwargs: Campos do perfil a serem atualizados
            
        Returns:
            O usuário com perfil atualizado
            
        Raises:
            LookupError: Se o usuário não for encontrado
        """
        # Obtém o usuário
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise LookupError(f"Usuário com ID {user_id} não encontrado")
        
        # Inicializa o perfil, se não existir
        if not user.profile:
            user.profile = UserProfile()
        
        # Atualiza os campos do perfil
        for key, value in kwargs.items():
            if hasattr(user.profile, key):
                setattr(user.profile, key, value)
        
        # Salva as alterações
        user = self.user_repository.update(user)
        
        # Publica evento de atualização de perfil
        self.event_dispatcher.dispatch(UserProfileUpdatedEvent(user_id=user.id))
        
        return user
    
    def update_preferences(self, user_id: int, **kwargs) -> User:
        """
        Atualiza as preferências de um usuário.
        
        Args:
            user_id: ID do usuário
            **kwargs: Campos de preferências a serem atualizados
            
        Returns:
            O usuário com preferências atualizadas
            
        Raises:
            LookupError: Se o usuário não for encontrado
        """
        # Obtém o usuário
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise LookupError(f"Usuário com ID {user_id} não encontrado")
        
        # Inicializa as preferências, se não existirem
        if not user.preferences:
            user.preferences = UserPreference()
        
        # Atualiza os campos das preferências
        for key, value in kwargs.items():
            if hasattr(user.preferences, key):
                setattr(user.preferences, key, value)
        
        # Salva as alterações
        user = self.user_repository.update(user)
        
        return user
    
    def delete_user(self, user_id: int) -> bool:
        """
        Remove um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            True se removido com sucesso, False caso contrário
        """
        return self.user_repository.delete(user_id)
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        Autentica um usuário.
        
        Args:
            username: Nome de usuário ou e-mail
            password: Senha
            
        Returns:
            O usuário autenticado, se as credenciais forem válidas, ou None
        """
        user = self.user_repository.authenticate(username, password)
        
        if user:
            # Atualiza a data de último login
            self.user_repository.update_last_login(user.id)
        
        return user
    
    def list_users(self, filters: Optional[Dict] = None, order_by: Optional[str] = None, limit: Optional[int] = None) -> List[User]:
        """
        Lista usuários com filtros opcionais.
        
        Args:
            filters: Filtros a serem aplicados
            order_by: Campo para ordenação
            limit: Limite de resultados
            
        Returns:
            Lista de usuários
        """
        return self.user_repository.list(filters, order_by, limit)
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """
        Altera a senha de um usuário.
        
        Args:
            user_id: ID do usuário
            current_password: Senha atual
            new_password: Nova senha
            
        Returns:
            True se a senha foi alterada com sucesso, False caso contrário
            
        Raises:
            ValueError: Se as senhas fornecidas forem inválidas
            LookupError: Se o usuário não for encontrado
        """
        # Obtém o usuário
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise LookupError(f"Usuário com ID {user_id} não encontrado")
        
        # Verifica a senha atual
        auth_user = self.user_repository.authenticate(user.username, current_password)
        if not auth_user:
            raise ValueError("Senha atual incorreta")
        
        # Atualiza a senha
        user.password = new_password
        self.user_repository.update(user)
        
        return True
    
    def is_username_available(self, username: str, current_user_id: Optional[int] = None) -> bool:
        """
        Verifica se um nome de usuário está disponível.
        
        Args:
            username: Nome de usuário a ser verificado
            current_user_id: ID do usuário atual (para excluir da verificação)
            
        Returns:
            True se disponível, False caso contrário
        """
        return self.user_repository.is_username_available(username, current_user_id)
    
    def is_email_available(self, email: str, current_user_id: Optional[int] = None) -> bool:
        """
        Verifica se um e-mail está disponível.
        
        Args:
            email: E-mail a ser verificado
            current_user_id: ID do usuário atual (para excluir da verificação)
            
        Returns:
            True se disponível, False caso contrário
        """
        return self.user_repository.is_email_available(email, current_user_id)

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
        return self.user_repository.add_futcoins(user_id, rewards[day_of_week])
    
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
        if not self.user_repository.can_purchase(user_id, price):
            return False
        
        try:
            # Remove futcoins do usuário
            self.user_repository.remove_futcoins(user_id, price)
            
            # Aqui seria registrada a compra no sistema
            # (código omitido para manter o exemplo simples)
            
            return True
        except ValueError:
            return False 