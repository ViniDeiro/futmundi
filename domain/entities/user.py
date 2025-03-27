"""
Entidade User - Representa um usuário no sistema.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class UserProfile:
    """
    Entidade que representa o perfil de um usuário.
    Contém informações detalhadas do perfil de usuário.
    """
    id: Optional[int]
    user_id: Optional[int]
    bio: str = ""
    avatar: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[datetime] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    social_media: Dict[str, str] = field(default_factory=dict)


@dataclass
class UserPreference:
    """
    Entidade que representa as preferências de um usuário.
    Contém configurações e preferências personalizadas.
    """
    id: Optional[int]
    user_id: Optional[int]
    email_notifications: bool = True
    push_notifications: bool = True
    language: str = "pt-br"
    timezone: str = "America/Sao_Paulo"
    theme: str = "light"
    favorite_teams: List[int] = field(default_factory=list)


@dataclass
class User:
    """
    Entidade que representa um usuário do sistema.
    Armazena informações de identidade, autenticação e perfil.
    """
    id: Optional[int]
    username: str
    email: str
    password: str = ""
    first_name: str = ""
    last_name: str = ""
    date_joined: Optional[datetime] = None
    last_login: Optional[datetime] = None
    is_active: bool = True
    futcoins: int = 0
    profile: Optional[UserProfile] = None
    preferences: Optional[UserPreference] = None
    
    @property
    def full_name(self) -> str:
        """Retorna o nome completo do usuário."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        return self.username 