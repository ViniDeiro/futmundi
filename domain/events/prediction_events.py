"""
Eventos relacionados a previsões de resultados.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

from domain.events.event import DomainEvent


@dataclass
class PredictionCreatedEvent(DomainEvent):
    """
    Evento emitido quando uma nova previsão é criada.
    """
    prediction_id: int
    user_id: int
    match_id: int
    home_score: int
    away_score: int
    created_at: datetime
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "Prediction")
        self.add_metadata("entity_id", self.prediction_id)
        self.add_metadata("user_id", self.user_id)
        self.add_metadata("match_id", self.match_id)


@dataclass
class PredictionUpdatedEvent(DomainEvent):
    """
    Evento emitido quando uma previsão é atualizada.
    """
    prediction_id: int
    user_id: int
    match_id: int
    previous_home_score: int
    previous_away_score: int
    new_home_score: int
    new_away_score: int
    updated_at: datetime
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "Prediction")
        self.add_metadata("entity_id", self.prediction_id)
        self.add_metadata("user_id", self.user_id)
        self.add_metadata("match_id", self.match_id)


@dataclass
class PredictionScoredEvent(DomainEvent):
    """
    Evento emitido quando uma previsão é pontuada.
    """
    prediction_id: int
    user_id: int
    match_id: int
    points: int
    is_exact_score: bool
    is_correct_winner: bool
    scored_at: datetime = None
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "Prediction")
        self.add_metadata("entity_id", self.prediction_id)
        self.add_metadata("user_id", self.user_id)
        self.add_metadata("match_id", self.match_id)
        self.add_metadata("points", self.points)
        self.add_metadata("is_exact_score", self.is_exact_score)
        self.add_metadata("is_correct_winner", self.is_correct_winner)
        
        if self.scored_at is None:
            self.scored_at = datetime.now()


@dataclass
class PredictionPointsCalculatedEvent(DomainEvent):
    """
    Evento emitido quando os pontos de uma previsão são calculados após o resultado de uma partida.
    """
    prediction_id: int
    user_id: int
    match_id: int
    home_score_predicted: int
    away_score_predicted: int
    home_score_actual: int
    away_score_actual: int
    points_earned: int
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "Prediction")
        self.add_metadata("entity_id", self.prediction_id)
        self.add_metadata("user_id", self.user_id)
        self.add_metadata("match_id", self.match_id)
        self.add_metadata("points", self.points_earned)
        
        # Determina o nível de precisão da previsão
        if (self.home_score_predicted == self.home_score_actual and 
            self.away_score_predicted == self.away_score_actual):
            accuracy = "exact"
        elif ((self.home_score_predicted > self.away_score_predicted and 
              self.home_score_actual > self.away_score_actual) or
              (self.home_score_predicted < self.away_score_predicted and 
              self.home_score_actual < self.away_score_actual) or
              (self.home_score_predicted == self.away_score_predicted and 
              self.home_score_actual == self.away_score_actual)):
            accuracy = "winner"
        else:
            accuracy = "wrong"
            
        self.add_metadata("accuracy", accuracy)


@dataclass
class UserRoundPredictionsCompletedEvent(DomainEvent):
    """
    Evento emitido quando um usuário completa todas as previsões para uma rodada.
    """
    user_id: int
    round_id: int
    championship_id: int
    prediction_count: int
    completed_at: datetime
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "User")
        self.add_metadata("entity_id", self.user_id)
        self.add_metadata("round_id", self.round_id)
        self.add_metadata("championship_id", self.championship_id)
        self.add_metadata("prediction_count", self.prediction_count)


@dataclass
class RoundPointsCalculatedEvent(DomainEvent):
    """
    Evento emitido quando os pontos de todas as previsões de uma rodada são calculados.
    """
    round_id: int
    championship_id: int
    match_count: int
    prediction_count: int
    user_count: int
    completed_at: datetime
    
    def __post_init__(self):
        super().__post_init__()
        self.add_metadata("entity_type", "ChampionshipRound")
        self.add_metadata("entity_id", self.round_id)
        self.add_metadata("championship_id", self.championship_id)
        self.add_metadata("matches", self.match_count)
        self.add_metadata("predictions", self.prediction_count)
        self.add_metadata("users", self.user_count) 