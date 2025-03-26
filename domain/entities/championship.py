"""
Entidade Championship - Representa um campeonato no sistema.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime


@dataclass
class ChampionshipStage:
    """
    Entidade que representa uma fase de um campeonato.
    Exemplo: Fase de grupos, oitavas de final, semifinal, etc.
    """
    id: int
    name: str
    order: int
    championship_id: int
    elimination: bool = False
    is_current: bool = False


@dataclass
class ChampionshipRound:
    """
    Entidade que representa uma rodada dentro de uma fase de campeonato.
    """
    id: int
    number: int
    stage_id: int
    is_current: bool = False
    deadline: Optional[datetime] = None


@dataclass
class Team:
    """
    Entidade que representa um time de futebol.
    """
    id: int
    name: str
    short_name: Optional[str] = None
    image: Optional[str] = None
    country_id: Optional[int] = None
    is_active: bool = True


@dataclass
class ChampionshipMatch:
    """
    Entidade que representa uma partida dentro de um campeonato.
    """
    id: int
    round_id: int
    home_team_id: int
    away_team_id: int
    home_team: Optional[Team] = None
    away_team: Optional[Team] = None
    match_date: Optional[datetime] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    status: str = "pending"  # pending, in_progress, finished, canceled


@dataclass
class Championship:
    """
    Entidade que representa um campeonato completo.
    """
    id: int
    name: str
    season: str
    scope_id: int
    start_date: datetime
    end_date: datetime
    is_active: bool = True
    image: Optional[str] = None
    stages: List[ChampionshipStage] = field(default_factory=list)
    rounds: Dict[int, List[ChampionshipRound]] = field(default_factory=dict)  # stage_id -> rounds
    matches: Dict[int, List[ChampionshipMatch]] = field(default_factory=dict)  # round_id -> matches 