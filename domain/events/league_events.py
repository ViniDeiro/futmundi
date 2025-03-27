"""
Eventos relacionados a ligas (FutLigas).
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime

from domain.events.event import DomainEvent


@dataclass
class LeagueCreatedEvent(DomainEvent):
    """
    Evento emitido quando uma nova liga é criada.
    """
    league_id: int
    name: str
    description: str
    creator_id: int  # ID do usuário que criou
    entry_fee: Optional[int] = None
    max_members: Optional[int] = None
    created_at: datetime = None
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "League")
        self.add_metadata("entity_id", self.league_id)
        self.add_metadata("creator_id", self.creator_id)
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class LeagueUpdatedEvent(DomainEvent):
    """
    Evento emitido quando uma liga é atualizada.
    """
    league_id: int
    updated_fields: Dict[str, Any]
    updater_id: int  # ID do usuário que atualizou
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "League")
        self.add_metadata("entity_id", self.league_id)
        self.add_metadata("updater_id", self.updater_id)


@dataclass
class MemberAddedEvent(DomainEvent):
    """
    Evento emitido quando um membro é adicionado a uma liga.
    """
    league_id: int
    user_id: int
    added_at: datetime = None
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "LeagueMember")
        self.add_metadata("entity_id", f"{self.league_id}_{self.user_id}")
        self.add_metadata("league_id", self.league_id)
        self.add_metadata("user_id", self.user_id)
        if self.added_at is None:
            self.added_at = datetime.now()


@dataclass
class MemberRemovedEvent(DomainEvent):
    """
    Evento emitido quando um membro é removido de uma liga.
    """
    league_id: int
    user_id: int
    removed_by_id: int  # ID do usuário que removeu (pode ser o próprio membro ou o dono da liga)
    reason: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "LeagueMember")
        self.add_metadata("entity_id", f"{self.league_id}_{self.user_id}")
        self.add_metadata("league_id", self.league_id)
        self.add_metadata("user_id", self.user_id)
        self.add_metadata("is_self_removal", self.user_id == self.removed_by_id)


@dataclass
class AwardDistributedEvent(DomainEvent):
    """
    Evento emitido quando uma premiação é distribuída em uma liga.
    """
    league_id: int
    award_id: int
    winner_id: int
    award_amount: int
    award_type: str  # 'futcoins', 'badge', etc.
    round_id: Optional[int] = None
    championship_id: Optional[int] = None
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "Award")
        self.add_metadata("entity_id", self.award_id)
        self.add_metadata("league_id", self.league_id)
        self.add_metadata("winner_id", self.winner_id)
        self.add_metadata("award_type", self.award_type)
        if self.round_id:
            self.add_metadata("round_id", self.round_id)
        if self.championship_id:
            self.add_metadata("championship_id", self.championship_id)


@dataclass
class LeagueRankingUpdatedEvent(DomainEvent):
    """
    Evento emitido quando o ranking de uma liga é atualizado.
    """
    league_id: int
    round_id: Optional[int] = None
    championship_id: Optional[int] = None
    ranking_data: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "League")
        self.add_metadata("entity_id", self.league_id)
        if self.round_id:
            self.add_metadata("round_id", self.round_id)
        if self.championship_id:
            self.add_metadata("championship_id", self.championship_id) 