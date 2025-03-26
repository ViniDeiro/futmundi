"""
Serviços de Aplicação - Implementam casos de uso específicos coordenando entidades e repositórios.

Cada serviço de aplicação é responsável por um conjunto de funcionalidades relacionadas,
encapsulando a lógica de negócio em casos de uso específicos.
"""

from application.services.championship_app_service import ChampionshipAppService
from application.services.league_app_service import LeagueAppService
from application.services.user_app_service import UserAppService
from application.services.prediction_app_service import PredictionAppService 