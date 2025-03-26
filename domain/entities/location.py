"""
Entidades de Localização - Representam estruturas geográficas.
"""
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Continent:
    """
    Entidade que representa um continente.
    """
    id: int
    name: str
    code: str
    is_active: bool = True
    image: Optional[str] = None
    countries: List['Country'] = field(default_factory=list)


@dataclass
class Country:
    """
    Entidade que representa um país.
    """
    id: int
    name: str
    code: str
    continent_id: int
    is_active: bool = True
    image: Optional[str] = None
    continent: Optional[Continent] = None
    states: List['State'] = field(default_factory=list)


@dataclass
class State:
    """
    Entidade que representa um estado/província.
    """
    id: int
    name: str
    code: str
    country_id: int
    is_active: bool = True
    country: Optional[Country] = None 