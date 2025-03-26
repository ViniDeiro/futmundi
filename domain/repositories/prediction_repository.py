"""
Repositório para operações em previsões.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from domain.entities.prediction import Prediction
from domain.repositories.base_repository import BaseRepository


class PredictionRepository(BaseRepository[Prediction], ABC):
    """
    Repositório para gerenciar previsões.
    """

    @abstractmethod
    def get_by_user_and_match(self, user_id: int, match_id: int) -> Optional[Prediction]:
        """
        Obtém uma previsão específica de um usuário para uma partida.

        Args:
            user_id: ID do usuário.
            match_id: ID da partida.

        Returns:
            A previsão encontrada ou None.
        """
        pass

    @abstractmethod
    def get_by_user_and_round(self, user_id: int, round_id: int) -> List[Prediction]:
        """
        Obtém todas as previsões de um usuário para uma rodada.

        Args:
            user_id: ID do usuário.
            round_id: ID da rodada.

        Returns:
            Lista de previsões.
        """
        pass

    @abstractmethod
    def get_by_match(self, match_id: int) -> List[Prediction]:
        """
        Obtém todas as previsões para uma partida.

        Args:
            match_id: ID da partida.

        Returns:
            Lista de previsões.
        """
        pass

    @abstractmethod
    def get_user_predictions_by_championship(self, user_id: int, championship_id: int) -> List[Prediction]:
        """
        Obtém todas as previsões de um usuário para um campeonato.

        Args:
            user_id: ID do usuário.
            championship_id: ID do campeonato.

        Returns:
            Lista de previsões.
        """
        pass

    @abstractmethod
    def get_prediction_statistics(self, match_id: int) -> Dict[str, Any]:
        """
        Obtém estatísticas de previsões para uma partida específica.

        Args:
            match_id: ID da partida.

        Returns:
            Dicionário com estatísticas das previsões.
        """
        pass

    @abstractmethod
    def calculate_points_for_match(self, match_id: int, home_score: int, away_score: int) -> int:
        """
        Calcula os pontos das previsões para uma partida com base no resultado.

        Args:
            match_id: ID da partida.
            home_score: Gols do time da casa.
            away_score: Gols do time visitante.

        Returns:
            Número de previsões atualizadas.
        """
        pass

    @abstractmethod
    def get_user_prediction_summary(self, user_id: int, championship_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtém um resumo das previsões de um usuário.

        Args:
            user_id: ID do usuário.
            championship_id: ID do campeonato (opcional).

        Returns:
            Dicionário com resumo das previsões.
        """
        pass 