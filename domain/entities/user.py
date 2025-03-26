"""
Entidade User - Representa um usuário no sistema.
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class User:
    """
    Entidade que representa um usuário do sistema.
    Armazena informações de identidade, autenticação e perfil.
    """
    id: int
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_joined: datetime = None
    is_active: bool = True
    is_premium: bool = False
    futcoins: int = 0
    avatar: Optional[str] = None
    
    @property
    def full_name(self) -> str:
        """Retorna o nome completo do usuário."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        return self.username 