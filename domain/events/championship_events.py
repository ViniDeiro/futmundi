"""
Eventos relacionados a campeonatos.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

from domain.events.event import DomainEvent


@dataclass
class ChampionshipCreatedEvent(DomainEvent):
    """
    Evento emitido quando um novo campeonato é criado.
    """
    championship_id: int
    name: str
    season: str
    start_date: datetime
    end_date: datetime
    created_by: int  # ID do usuário que criou
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "Championship")
        self.add_metadata("entity_id", self.championship_id)


@dataclass
class ChampionshipUpdatedEvent(DomainEvent):
    """
    Evento emitido quando um campeonato é atualizado.
    """
    championship_id: int
    updated_fields: Dict[str, Any]
    updated_by: int  # ID do usuário que atualizou
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "Championship")
        self.add_metadata("entity_id", self.championship_id)


@dataclass
class StageUpdatedEvent(DomainEvent):
    """
    Evento emitido quando um estágio de campeonato é atualizado.
    """
    stage_id: int
    championship_id: int
    name: str
    updated_fields: Dict[str, Any]
    updated_by: int  # ID do usuário que atualizou
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "ChampionshipStage")
        self.add_metadata("entity_id", self.stage_id)
        self.add_metadata("parent_entity_type", "Championship")
        self.add_metadata("parent_entity_id", self.championship_id)


@dataclass
class RoundCreatedEvent(DomainEvent):
    """
    Evento emitido quando uma rodada é criada.
    """
    round_id: int
    stage_id: int
    championship_id: int
    round_number: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "ChampionshipRound")
        self.add_metadata("entity_id", self.round_id)
        self.add_metadata("parent_entity_type", "ChampionshipStage")
        self.add_metadata("parent_entity_id", self.stage_id)


@dataclass
class MatchCreatedEvent(DomainEvent):
    """
    Evento emitido quando uma partida é criada.
    """
    match_id: int
    round_id: int
    championship_id: int
    home_team_id: int
    away_team_id: int
    match_date: datetime
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "ChampionshipMatch")
        self.add_metadata("entity_id", self.match_id)
        self.add_metadata("parent_entity_type", "ChampionshipRound")
        self.add_metadata("parent_entity_id", self.round_id)


@dataclass
class MatchResultUpdatedEvent(DomainEvent):
    """
    Evento emitido quando o resultado de uma partida é atualizado.
    """
    match_id: int
    round_id: int
    championship_id: int
    home_score: int
    away_score: int
    updated_by: int  # ID do usuário que atualizou
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "ChampionshipMatch")
        self.add_metadata("entity_id", self.match_id)
        self.add_metadata("parent_entity_type", "ChampionshipRound")
        self.add_metadata("parent_entity_id", self.round_id)
        self.add_metadata("requires_prediction_points_calculation", True)


@dataclass
class TeamAddedToChampionshipEvent(DomainEvent):
    """
    Evento emitido quando um time é adicionado a um campeonato.
    """
    team_id: int
    championship_id: int
    added_by: int  # ID do usuário que adicionou
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "Team")
        self.add_metadata("entity_id", self.team_id)
        self.add_metadata("parent_entity_type", "Championship")
        self.add_metadata("parent_entity_id", self.championship_id) 