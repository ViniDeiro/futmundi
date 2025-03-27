"""
Serviço de domínio para operações com previsões.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from domain.repositories.prediction_repository import PredictionRepository
from domain.entities.prediction import Prediction


class PredictionService:
    """
    Serviço de domínio para lógica de negócio relacionada a previsões.
    """
    
    def __init__(self, prediction_repository: PredictionRepository):
        self.prediction_repository = prediction_repository
    
    def create_prediction(self, user_id: int, match_id: int, home_score: int, away_score: int) -> Prediction:
        """
        Cria uma nova previsão para uma partida.
        
        Args:
            user_id: ID do usuário
            match_id: ID da partida
            home_score: Placar do time da casa previsto
            away_score: Placar do time visitante previsto
        
        Returns:
            Prediction: A previsão criada
        
        Raises:
            ValueError: Se os dados forem inválidos
        """
        if home_score < 0 or away_score < 0:
            raise ValueError("Os placares não podem ser negativos")
        
        # Verifica se a partida está aberta para previsões
        match = self.prediction_repository.get_match(match_id)
        if match is None:
            raise ValueError(f"Partida com ID {match_id} não encontrada")
        
        if match.match_date <= datetime.now():
            raise ValueError("Não é possível fazer previsões para partidas que já começaram")
        
        # Verifica se o usuário já fez uma previsão para esta partida
        existing_prediction = self.prediction_repository.get_by_user_and_match(user_id, match_id)
        if existing_prediction:
            # Atualiza a previsão existente
            existing_prediction.home_score = home_score
            existing_prediction.away_score = away_score
            return self.prediction_repository.update(existing_prediction)
        
        # Cria uma nova previsão
        prediction = Prediction(
            id=None,
            user_id=user_id,
            match_id=match_id,
            home_score=home_score,
            away_score=away_score,
            points=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        return self.prediction_repository.create(prediction)
    
    def calculate_points(self, match_id: int) -> List[Dict[str, Any]]:
        """
        Calcula os pontos para todas as previsões de uma partida.
        
        Args:
            match_id: ID da partida
        
        Returns:
            List[Dict]: Lista de resultados de cálculo de pontos
        
        Raises:
            ValueError: Se a partida não existir ou não tiver resultado
        """
        match = self.prediction_repository.get_match(match_id)
        if match is None:
            raise ValueError(f"Partida com ID {match_id} não encontrada")
        
        if match.home_score is None or match.away_score is None:
            raise ValueError("A partida ainda não tem um resultado definido")
        
        # Obtém todas as previsões para a partida
        predictions = self.prediction_repository.get_by_match(match_id)
        
        results = []
        for prediction in predictions:
            # Calcula os pontos
            points = self._calculate_prediction_points(
                prediction.home_score, 
                prediction.away_score, 
                match.home_score, 
                match.away_score
            )
            
            # Atualiza os pontos da previsão
            prediction.points = points
            self.prediction_repository.update(prediction)
            
            results.append({
                "prediction_id": prediction.id,
                "user_id": prediction.user_id,
                "points": points
            })
        
        return results
    
    def _calculate_prediction_points(self, pred_home: int, pred_away: int, 
                                    real_home: int, real_away: int) -> int:
        """
        Calcula os pontos de uma previsão com base no resultado real.
        
        Args:
            pred_home: Placar previsto para o time da casa
            pred_away: Placar previsto para o time visitante
            real_home: Placar real do time da casa
            real_away: Placar real do time visitante
        
        Returns:
            int: Pontos ganhos pela previsão
        """
        # Acertou o resultado exato
        if pred_home == real_home and pred_away == real_away:
            return 25
        
        # Acertou o vencedor e a diferença de gols
        pred_diff = pred_home - pred_away
        real_diff = real_home - real_away
        
        if pred_diff == real_diff:
            return 18
        
        # Acertou apenas o vencedor (ou empate)
        if (pred_diff > 0 and real_diff > 0) or \
           (pred_diff < 0 and real_diff < 0) or \
           (pred_diff == 0 and real_diff == 0):
            return 12
        
        # Acertou o número de gols de um dos times
        if pred_home == real_home or pred_away == real_away:
            return 7
        
        # Errou completamente
        return 0 