"""
Serviços - Contém a lógica de negócio que não se encaixa naturalmente em uma entidade.
Os serviços implementam operações que envolvem múltiplas entidades ou lógica de domínio complexa.
"""

from domain.services.championship_service import ChampionshipService
from domain.services.user_service import UserService
from domain.services.prediction_service import PredictionService
from domain.services.futliga_service import FutLigaService
from domain.services.payment_service import PaymentService 