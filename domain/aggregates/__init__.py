"""
Agregados - Conjuntos de entidades que são tratadas como uma unidade para mudanças de dados.
Cada agregado tem uma raiz e uma fronteira. A raiz é uma entidade específica contida no agregado.
Todas as referências de fora do agregado só devem ir para a raiz.
"""

from domain.aggregates.championship_aggregate import ChampionshipAggregate
from domain.aggregates.league_aggregate import LeagueAggregate
from domain.aggregates.user_aggregate import UserAggregate 