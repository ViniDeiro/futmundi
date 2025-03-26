"""
Implementação Django do repositório de usuários.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from django.db import transaction
from django.contrib.auth import get_user_model

from domain.entities.user import User, UserProfile, UserPreference
from domain.repositories.user_repository import UserRepository

User_Model = get_user_model()


class DjangoUserRepository(UserRepository):
    """
    Implementação do repositório de usuários usando o Django ORM.
    """
    
    def get_by_id(self, id: int) -> Optional[User]:
        """
        Recupera um usuário pelo seu ID.
        
        Args:
            id: O ID do usuário a ser recuperado.
            
        Returns:
            O usuário, se encontrado, ou None.
        """
        try:
            user_db = User_Model.objects.get(id=id)
            return self._map_to_domain_user(user_db)
        except User_Model.DoesNotExist:
            return None
    
    def get_by_username(self, username: str) -> Optional[User]:
        """
        Recupera um usuário pelo seu nome de usuário.
        
        Args:
            username: O nome de usuário.
            
        Returns:
            O usuário, se encontrado, ou None.
        """
        try:
            user_db = User_Model.objects.get(username=username)
            return self._map_to_domain_user(user_db)
        except User_Model.DoesNotExist:
            return None
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Recupera um usuário pelo seu e-mail.
        
        Args:
            email: O e-mail do usuário.
            
        Returns:
            O usuário, se encontrado, ou None.
        """
        try:
            user_db = User_Model.objects.get(email=email)
            return self._map_to_domain_user(user_db)
        except User_Model.DoesNotExist:
            return None
    
    def list(self, filters: Optional[dict] = None, order_by: Optional[str] = None, limit: Optional[int] = None) -> List[User]:
        """
        Lista usuários com filtros opcionais.
        
        Args:
            filters: Dicionário com filtros a serem aplicados.
            order_by: Campo para ordenação.
            limit: Limite de itens a retornar.
            
        Returns:
            Lista de usuários.
        """
        # Inicializa a query
        query = User_Model.objects.all()
        
        # Aplica filtros, se fornecidos
        if filters:
            query = query.filter(**filters)
            
        # Aplica ordenação, se fornecida
        if order_by:
            query = query.order_by(order_by)
            
        # Aplica limite, se fornecido
        if limit is not None:
            query = query[:limit]
            
        # Mapeia para entidades de domínio
        return [self._map_to_domain_user(user_db) for user_db in query]
    
    def create(self, entity: User) -> User:
        """
        Cria um novo usuário.
        
        Args:
            entity: O usuário a ser criado.
            
        Returns:
            O usuário criado com ID atribuído.
        """
        with transaction.atomic():
            # Cria o usuário no banco de dados
            user_db = User_Model.objects.create_user(
                username=entity.username,
                email=entity.email,
                password=entity.password,
                first_name=entity.first_name,
                last_name=entity.last_name,
                is_active=entity.is_active,
                date_joined=entity.date_joined or datetime.now()
            )
            
            # Atualiza o ID da entidade
            entity.id = user_db.id
            
            # Configura o perfil do usuário, se fornecido
            if entity.profile:
                self._create_or_update_profile(user_db, entity.profile)
            
            # Configura as preferências do usuário, se fornecidas
            if entity.preferences:
                self._create_or_update_preferences(user_db, entity.preferences)
            
            return entity
    
    def update(self, entity: User) -> User:
        """
        Atualiza um usuário existente.
        
        Args:
            entity: O usuário a ser atualizado.
            
        Returns:
            O usuário atualizado.
        """
        with transaction.atomic():
            try:
                # Busca o usuário no banco de dados
                user_db = User_Model.objects.get(id=entity.id)
                
                # Atualiza os campos
                user_db.username = entity.username
                user_db.email = entity.email
                user_db.first_name = entity.first_name
                user_db.last_name = entity.last_name
                user_db.is_active = entity.is_active
                
                # Atualiza a senha se ela estiver presente
                if entity.password:
                    user_db.set_password(entity.password)
                
                # Salva as alterações
                user_db.save()
                
                # Atualiza o perfil do usuário, se fornecido
                if entity.profile:
                    self._create_or_update_profile(user_db, entity.profile)
                
                # Atualiza as preferências do usuário, se fornecidas
                if entity.preferences:
                    self._create_or_update_preferences(user_db, entity.preferences)
                
                return entity
            except User_Model.DoesNotExist:
                raise ValueError(f"Usuário com ID {entity.id} não encontrado")
    
    def delete(self, id: int) -> bool:
        """
        Remove um usuário pelo ID.
        
        Args:
            id: O ID do usuário a ser removido.
            
        Returns:
            True se o usuário foi removido, False caso contrário.
        """
        try:
            user_db = User_Model.objects.get(id=id)
            user_db.delete()
            return True
        except User_Model.DoesNotExist:
            return False
    
    def count(self, filters: Optional[dict] = None) -> int:
        """
        Conta o número de usuários que correspondem aos filtros.
        
        Args:
            filters: Dicionário com filtros a serem aplicados.
            
        Returns:
            Número de usuários.
        """
        # Inicializa a query
        query = User_Model.objects.all()
        
        # Aplica filtros, se fornecidos
        if filters:
            query = query.filter(**filters)
            
        return query.count()
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        Autentica um usuário com nome de usuário e senha.
        
        Args:
            username: Nome de usuário ou e-mail.
            password: Senha do usuário.
            
        Returns:
            O usuário autenticado, se as credenciais forem válidas, ou None.
        """
        from django.contrib.auth import authenticate
        
        # Tenta autenticar usando o nome de usuário
        user_db = authenticate(username=username, password=password)
        
        # Se não foi possível, tenta com o e-mail
        if not user_db:
            try:
                email_user = User_Model.objects.get(email=username)
                user_db = authenticate(username=email_user.username, password=password)
            except User_Model.DoesNotExist:
                pass
        
        if user_db:
            return self._map_to_domain_user(user_db)
        
        return None
    
    def update_last_login(self, user_id: int) -> bool:
        """
        Atualiza a data de último login do usuário.
        
        Args:
            user_id: ID do usuário.
            
        Returns:
            True se a atualização foi bem-sucedida, False caso contrário.
        """
        try:
            user_db = User_Model.objects.get(id=user_id)
            user_db.last_login = datetime.now()
            user_db.save(update_fields=['last_login'])
            return True
        except User_Model.DoesNotExist:
            return False
    
    def is_email_available(self, email: str, current_user_id: Optional[int] = None) -> bool:
        """
        Verifica se um e-mail está disponível para uso.
        
        Args:
            email: E-mail a ser verificado.
            current_user_id: ID do usuário atual (para excluir da verificação).
            
        Returns:
            True se o e-mail está disponível, False caso contrário.
        """
        query = User_Model.objects.filter(email=email)
        
        if current_user_id is not None:
            query = query.exclude(id=current_user_id)
            
        return not query.exists()
    
    def is_username_available(self, username: str, current_user_id: Optional[int] = None) -> bool:
        """
        Verifica se um nome de usuário está disponível para uso.
        
        Args:
            username: Nome de usuário a ser verificado.
            current_user_id: ID do usuário atual (para excluir da verificação).
            
        Returns:
            True se o nome de usuário está disponível, False caso contrário.
        """
        query = User_Model.objects.filter(username=username)
        
        if current_user_id is not None:
            query = query.exclude(id=current_user_id)
            
        return not query.exists()
    
    # Métodos auxiliares
    
    def _create_or_update_profile(self, user_db, profile: UserProfile) -> None:
        """
        Cria ou atualiza o perfil de um usuário.
        
        Args:
            user_db: Usuário do banco de dados.
            profile: Perfil a ser criado/atualizado.
        """
        from usuarios.models import UserProfile as DjangoUserProfile
        
        try:
            # Tenta obter o perfil existente
            profile_db = DjangoUserProfile.objects.get(user=user_db)
            
            # Atualiza os campos
            profile_db.avatar = profile.avatar
            profile_db.phone = profile.phone
            profile_db.bio = profile.bio
            profile_db.birth_date = profile.birth_date
            profile_db.location = profile.location
            
            # Salva as alterações
            profile_db.save()
        except DjangoUserProfile.DoesNotExist:
            # Cria um novo perfil
            DjangoUserProfile.objects.create(
                user=user_db,
                avatar=profile.avatar,
                phone=profile.phone,
                bio=profile.bio,
                birth_date=profile.birth_date,
                location=profile.location
            )
    
    def _create_or_update_preferences(self, user_db, preferences: UserPreference) -> None:
        """
        Cria ou atualiza as preferências de um usuário.
        
        Args:
            user_db: Usuário do banco de dados.
            preferences: Preferências a serem criadas/atualizadas.
        """
        from usuarios.models import UserPreference as DjangoUserPreference
        
        try:
            # Tenta obter as preferências existentes
            pref_db = DjangoUserPreference.objects.get(user=user_db)
            
            # Atualiza os campos
            pref_db.language = preferences.language
            pref_db.dark_mode = preferences.dark_mode
            pref_db.email_notifications = preferences.email_notifications
            pref_db.push_notifications = preferences.push_notifications
            pref_db.favorite_team_id = preferences.favorite_team_id
            
            # Salva as alterações
            pref_db.save()
        except DjangoUserPreference.DoesNotExist:
            # Cria novas preferências
            DjangoUserPreference.objects.create(
                user=user_db,
                language=preferences.language,
                dark_mode=preferences.dark_mode,
                email_notifications=preferences.email_notifications,
                push_notifications=preferences.push_notifications,
                favorite_team_id=preferences.favorite_team_id
            )
    
    def _map_to_domain_user(self, user_db) -> User:
        """
        Mapeia um usuário do banco de dados para uma entidade de domínio.
        
        Args:
            user_db: Usuário do banco de dados.
            
        Returns:
            Entidade de domínio.
        """
        from usuarios.models import UserProfile as DjangoUserProfile, UserPreference as DjangoUserPreference
        
        # Tenta obter o perfil
        profile = None
        try:
            profile_db = DjangoUserProfile.objects.get(user=user_db)
            profile = UserProfile(
                avatar=profile_db.avatar.url if profile_db.avatar else None,
                phone=profile_db.phone,
                bio=profile_db.bio,
                birth_date=profile_db.birth_date,
                location=profile_db.location
            )
        except DjangoUserProfile.DoesNotExist:
            pass
        
        # Tenta obter as preferências
        preferences = None
        try:
            pref_db = DjangoUserPreference.objects.get(user=user_db)
            preferences = UserPreference(
                language=pref_db.language,
                dark_mode=pref_db.dark_mode,
                email_notifications=pref_db.email_notifications,
                push_notifications=pref_db.push_notifications,
                favorite_team_id=pref_db.favorite_team_id
            )
        except DjangoUserPreference.DoesNotExist:
            pass
        
        # Mapeia para a entidade de domínio
        return User(
            id=user_db.id,
            username=user_db.username,
            email=user_db.email,
            password=None,  # Não incluímos a senha no mapeamento por segurança
            first_name=user_db.first_name,
            last_name=user_db.last_name,
            is_active=user_db.is_active,
            is_staff=user_db.is_staff,
            is_superuser=user_db.is_superuser,
            date_joined=user_db.date_joined,
            last_login=user_db.last_login,
            profile=profile,
            preferences=preferences
        ) 