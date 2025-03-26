"""
Entidade Template - Representa templates para criação de campeonatos.
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class TemplateStage:
    """
    Entidade que representa uma fase de um template de campeonato.
    """
    id: int
    template_id: int
    name: str
    order: int
    elimination: bool = False
    rounds_count: int = 0
    

@dataclass
class Template:
    """
    Entidade que representa um template de campeonato.
    Templates são usados como base para criar novos campeonatos
    com estrutura pré-definida.
    """
    id: int
    name: str
    description: Optional[str] = None
    scope_id: Optional[int] = None
    is_active: bool = True
    created_at: datetime = None
    updated_at: Optional[datetime] = None
    creator_id: Optional[int] = None
    stages: List[TemplateStage] = field(default_factory=list) 