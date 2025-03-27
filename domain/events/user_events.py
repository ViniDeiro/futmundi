"""
Eventos relacionados a usuários.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

from domain.events.event import DomainEvent


@dataclass
class UserCreatedEvent(DomainEvent):
    """
    Evento emitido quando um novo usuário é criado no sistema.
    """
    user_id: int
    username: str
    email: str
    created_at: datetime
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "User")
        self.add_metadata("entity_id", self.user_id)


@dataclass
class UserRegisteredEvent(DomainEvent):
    """
    Evento emitido quando um novo usuário se registra no sistema.
    """
    user_id: int
    username: str
    email: str
    registration_date: datetime
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "User")
        self.add_metadata("entity_id", self.user_id)


@dataclass
class UserUpdatedEvent(DomainEvent):
    """
    Evento emitido quando os dados principais de um usuário são atualizados.
    """
    user_id: int
    updated_fields: Dict[str, Any]
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "User")
        self.add_metadata("entity_id", self.user_id)


@dataclass
class UserProfileUpdatedEvent(DomainEvent):
    """
    Evento emitido quando o perfil de um usuário é atualizado.
    """
    user_id: int
    updated_fields: Dict[str, Any]
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "UserProfile")
        self.add_metadata("entity_id", self.user_id)


@dataclass
class UserPreferencesUpdatedEvent(DomainEvent):
    """
    Evento emitido quando as preferências de um usuário são atualizadas.
    """
    user_id: int
    updated_fields: Dict[str, Any]
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "UserPreference")
        self.add_metadata("entity_id", self.user_id)


@dataclass
class UserPremiumStatusChangedEvent(DomainEvent):
    """
    Evento emitido quando o status premium de um usuário muda.
    """
    user_id: int
    is_premium: bool
    previous_status: bool
    change_date: datetime
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "User")
        self.add_metadata("entity_id", self.user_id)
        self.add_metadata("status_change", f"{'premium' if self.is_premium else 'regular'}")


@dataclass
class UserDailyRewardClaimedEvent(DomainEvent):
    """
    Evento emitido quando um usuário reivindica sua recompensa diária.
    """
    user_id: int
    reward_amount: int
    streak_count: int
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "User")
        self.add_metadata("entity_id", self.user_id)
        self.add_metadata("reward_type", "daily")


@dataclass
class UserFutcoinsUpdatedEvent(DomainEvent):
    """
    Evento emitido quando o saldo de futcoins de um usuário é atualizado.
    """
    user_id: int
    amount: int
    previous_balance: int
    new_balance: int
    reason: str
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "User")
        self.add_metadata("entity_id", self.user_id)
        self.add_metadata("transaction_type", "futcoins_update")
        self.add_metadata("change_amount", self.amount)
        self.add_metadata("change_reason", self.reason) 