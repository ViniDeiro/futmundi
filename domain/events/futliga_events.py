"""
Eventos de domínio relacionados a FutLigas.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List

from domain.events.event import DomainEvent


@dataclass
class LeagueCreatedEvent(DomainEvent):
    """
    Evento emitido quando uma nova liga é criada.
    """
    league_id: int
    name: str
    owner_id: int
    level_id: int
    
    def __str__(self) -> str:
        """
        Retorna uma representação em string do evento.
        
        Returns:
            Descrição do evento.
        """
        return f"Liga '{self.name}' (ID: {self.league_id}) foi criada pelo usuário {self.owner_id}"


@dataclass
class MemberJoinedLeagueEvent(DomainEvent):
    """
    Evento emitido quando um novo membro se junta a uma liga.
    """
    league_id: int
    league_name: str
    user_id: int
    is_owner: bool = False
    is_admin: bool = False
    
    def __str__(self) -> str:
        """
        Retorna uma representação em string do evento.
        
        Returns:
            Descrição do evento.
        """
        role = "dono" if self.is_owner else "administrador" if self.is_admin else "membro"
        return f"Usuário {self.user_id} entrou na liga '{self.league_name}' (ID: {self.league_id}) como {role}"


@dataclass
class AwardDistributedEvent(DomainEvent):
    """
    Evento emitido quando prêmios são distribuídos em uma liga.
    """
    league_id: int
    league_name: str
    award_type: str  # "weekly" ou "season"
    prizes: List[Dict[str, Any]]  # Lista de prêmios distribuídos
    
    def __str__(self) -> str:
        """
        Retorna uma representação em string do evento.
        
        Returns:
            Descrição do evento.
        """
        award_type_desc = "semanal" if self.award_type == "weekly" else "da temporada"
        return f"Premiação {award_type_desc} distribuída na liga '{self.league_name}' (ID: {self.league_id})"


@dataclass
class LeagueConfigUpdatedEvent(DomainEvent):
    """
    Evento emitido quando a configuração de uma liga é atualizada.
    """
    league_id: int
    league_name: str
    updated_by_user_id: int
    updated_fields: List[str]
    
    def __str__(self) -> str:
        """
        Retorna uma representação em string do evento.
        
        Returns:
            Descrição do evento.
        """
        fields_str = ", ".join(self.updated_fields)
        return f"Configuração da liga '{self.league_name}' (ID: {self.league_id}) foi atualizada. Campos alterados: {fields_str}"


@dataclass
class LeagueMemberRemovedEvent(DomainEvent):
    """
    Evento emitido quando um membro é removido de uma liga.
    """
    league_id: int
    league_name: str
    user_id: int
    removed_by_user_id: int
    reason: Optional[str] = None
    
    def __str__(self) -> str:
        """
        Retorna uma representação em string do evento.
        
        Returns:
            Descrição do evento.
        """
        reason_str = f" Motivo: {self.reason}" if self.reason else ""
        return f"Usuário {self.user_id} foi removido da liga '{self.league_name}' (ID: {self.league_id}) por {self.removed_by_user_id}.{reason_str}" 