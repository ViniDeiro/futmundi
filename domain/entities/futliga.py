"""
Entidade FutLiga - Representa ligas customizadas no sistema.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime


@dataclass
class CustomLeagueLevel:
    """
    Entidade que representa um nível de liga customizada.
    Define requisitos e configurações para cada nível.
    """
    id: int
    name: str
    players: int
    premium_players: int
    owner_premium: bool = False
    image: Optional[str] = None


@dataclass
class CustomLeaguePrize:
    """
    Entidade que representa um prêmio em uma liga customizada.
    """
    id: int
    position: int
    league_id: int
    image: Optional[str] = None
    values: Dict[int, int] = field(default_factory=dict)  # level_id -> value
    

@dataclass
class AwardConfig:
    """
    Configuração de premiação para uma liga customizada.
    """
    weekly: Dict[str, str] = field(default_factory=dict)  # day, time
    season: Dict[str, str] = field(default_factory=dict)  # month, day, time


@dataclass
class LeagueMember:
    """
    Entidade que representa um membro de uma liga.
    """
    id: int
    league_id: int
    user_id: int
    joined_date: datetime
    is_owner: bool = False
    is_admin: bool = False
    is_active: bool = True
    score: int = 0
    ranking: int = 0


@dataclass
class CustomLeague:
    """
    Entidade que representa uma liga customizada completa.
    """
    id: int
    name: str
    owner_id: int
    level_id: int
    is_active: bool = True
    image: Optional[str] = None
    description: Optional[str] = None
    creation_date: datetime = None
    members_count: int = 0
    members: List[LeagueMember] = field(default_factory=list)
    level: Optional[CustomLeagueLevel] = None
    prizes: List[CustomLeaguePrize] = field(default_factory=list)
    award_config: Optional[AwardConfig] = None 