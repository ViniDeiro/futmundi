"""
Repositórios para acesso e persistência de entidades do domínio.

Os repositórios encapsulam o acesso a dados e fornecem métodos para operações CRUD
nas entidades do domínio, isolando a camada de domínio das implementações de armazenamento.
"""

from domain.repositories.base_repository import BaseRepository
from domain.repositories.user_repository import UserRepository
from domain.repositories.championship_repository import ChampionshipRepository
from domain.repositories.futliga_repository import FutLigaRepository
from domain.repositories.prediction_repository import PredictionRepository
from domain.repositories.location_repository import LocationRepository
from domain.repositories.payment_repository import PaymentRepository
from domain.repositories.template_repository import TemplateRepository

__all__ = [
    'BaseRepository',
    'UserRepository',
    'ChampionshipRepository',
    'FutLigaRepository',
    'PredictionRepository',
    'LocationRepository',
    'PaymentRepository',
    'TemplateRepository',
] 