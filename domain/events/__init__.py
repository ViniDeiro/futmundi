"""
Eventos de Domínio - Representam fatos importantes que ocorreram no domínio.
Eventos são utilizados para comunicar mudanças entre diferentes partes do sistema.
"""

from domain.events.event import DomainEvent
from domain.events.championship_events import (
    ChampionshipCreatedEvent,
    MatchResultUpdatedEvent
)
from domain.events.futliga_events import (
    LeagueCreatedEvent,
    MemberJoinedLeagueEvent,
    AwardDistributedEvent
)
from domain.events.user_events import (
    UserRegisteredEvent,
    UserPremiumStatusChangedEvent
)
from domain.events.prediction_events import (
    PredictionCreatedEvent,
    PredictionPointsCalculatedEvent
) 