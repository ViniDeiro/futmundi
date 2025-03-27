"""
Fábrica para criação de entidades de Usuários.
"""

from typing import Optional, Dict, Any
from datetime import datetime

from django.contrib.auth import get_user_model
from domain.entities.user import User, UserProfile, UserPreference
from domain.aggregates.user_aggregate import UserAggregate

# Usando o model User do Django por enquanto para manter compatibilidade
DjangoUser = get_user_model()


class UserFactory:
    """
    Fábrica para criar instâncias de usuários com seus dados relacionados.
    """
    
    @staticmethod
    def create_user(
        username: str,
        email: str,
        password: str,
        first_name: str = "",
        last_name: str = "",
        is_active: bool = True,
        futcoins: int = 0,
        profile_data: Optional[Dict[str, Any]] = None,
        preferences_data: Optional[Dict[str, Any]] = None
    ) -> User:
        """
        Cria uma nova entidade de usuário.
        
        Args:
            username: Nome de usuário
            email: Email do usuário
            password: Senha
            first_name: Primeiro nome
            last_name: Sobrenome
            is_active: Se o usuário está ativo
            futcoins: Quantidade inicial de futcoins
            profile_data: Dados do perfil do usuário
            preferences_data: Preferências do usuário
            
        Returns:
            Nova entidade de usuário
        """
        # Cria o perfil, se fornecido
        profile = None
        if profile_data:
            profile = UserProfile(
                id=None,
                user_id=None,  # Será definido posteriormente
                bio=profile_data.get('bio', ''),
                avatar=profile_data.get('avatar'),
                phone=profile_data.get('phone'),
                birth_date=profile_data.get('birth_date'),
                address=profile_data.get('address'),
                city=profile_data.get('city'),
                state=profile_data.get('state'),
                country=profile_data.get('country'),
                postal_code=profile_data.get('postal_code'),
                social_media=profile_data.get('social_media', {})
            )
        
        # Cria as preferências, se fornecidas
        preferences = None
        if preferences_data:
            preferences = UserPreference(
                id=None,
                user_id=None,  # Será definido posteriormente
                email_notifications=preferences_data.get('email_notifications', True),
                push_notifications=preferences_data.get('push_notifications', True),
                language=preferences_data.get('language', 'pt-br'),
                timezone=preferences_data.get('timezone', 'America/Sao_Paulo'),
                theme=preferences_data.get('theme', 'light'),
                favorite_teams=preferences_data.get('favorite_teams', [])
            )
        
        # Cria a entidade de usuário
        user = User(
            id=None,
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=is_active,
            futcoins=futcoins,
            date_joined=datetime.now(),
            last_login=None,
            profile=profile,
            preferences=preferences
        )
        
        return user
    
    @staticmethod
    def create_user_aggregate(user: User) -> UserAggregate:
        """
        Cria um agregado de usuário a partir de uma entidade de usuário.
        
        Args:
            user: Entidade de usuário
            
        Returns:
            Agregado de usuário
        """
        return UserAggregate(
            user=user,
            subscription=None,
            payment_methods=[],
            prediction_stats=None,
            leagues=[]
        )
    
    @staticmethod
    def create_from_django_user(django_user: DjangoUser) -> User:
        """
        Cria uma entidade de usuário a partir de um usuário do Django.
        
        Args:
            django_user: Usuário do Django
            
        Returns:
            Entidade de usuário
        """
        # Obtém ou cria o perfil do usuário
        profile = None
        try:
            if hasattr(django_user, 'profile'):
                django_profile = django_user.profile
                profile = UserProfile(
                    id=django_profile.id,
                    user_id=django_user.id,
                    bio=getattr(django_profile, 'bio', ''),
                    avatar=getattr(django_profile, 'avatar', None),
                    phone=getattr(django_profile, 'phone', None),
                    birth_date=getattr(django_profile, 'birth_date', None),
                    address=getattr(django_profile, 'address', None),
                    city=getattr(django_profile, 'city', None),
                    state=getattr(django_profile, 'state', None),
                    country=getattr(django_profile, 'country', None),
                    postal_code=getattr(django_profile, 'postal_code', None),
                    social_media=getattr(django_profile, 'social_media', {})
                )
        except (AttributeError, Exception):
            pass
        
        # Obtém ou cria as preferências do usuário
        preferences = None
        try:
            if hasattr(django_user, 'preferences'):
                django_pref = django_user.preferences
                preferences = UserPreference(
                    id=django_pref.id,
                    user_id=django_user.id,
                    email_notifications=getattr(django_pref, 'email_notifications', True),
                    push_notifications=getattr(django_pref, 'push_notifications', True),
                    language=getattr(django_pref, 'language', 'pt-br'),
                    timezone=getattr(django_pref, 'timezone', 'America/Sao_Paulo'),
                    theme=getattr(django_pref, 'theme', 'light'),
                    favorite_teams=getattr(django_pref, 'favorite_teams', [])
                )
        except (AttributeError, Exception):
            pass
        
        # Cria a entidade de usuário
        user = User(
            id=django_user.id,
            username=django_user.username,
            email=django_user.email,
            password='',  # Não armazenamos a senha em texto puro
            first_name=django_user.first_name,
            last_name=django_user.last_name,
            is_active=django_user.is_active,
            futcoins=getattr(django_user, 'futcoins', 0),
            date_joined=django_user.date_joined,
            last_login=django_user.last_login,
            profile=profile,
            preferences=preferences
        )
        
        return user 