"""
Repositórios - Interfaces para acesso a dados.
Os repositórios abstraem a camada de persistência e proveem métodos para 
buscar e salvar entidades, independentemente da tecnologia de armazenamento.
"""

from domain.repositories.user_repository import UserRepository
from domain.repositories.championship_repository import ChampionshipRepository
from domain.repositories.template_repository import TemplateRepository
from domain.repositories.futliga_repository import FutLigaRepository
from domain.repositories.prediction_repository import PredictionRepository
from domain.repositories.location_repository import LocationRepository
from domain.repositories.payment_repository import PaymentRepository 