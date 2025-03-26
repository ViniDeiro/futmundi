"""
Serviço de domínio para operações relacionadas a campeonatos.
"""
from typing import List, Optional, Dict, Tuple
from datetime import datetime

from domain.entities.championship import Championship, ChampionshipStage, ChampionshipRound, ChampionshipMatch
from domain.entities.prediction import Prediction
from domain.repositories.championship_repository import ChampionshipRepository
from domain.repositories.prediction_repository import PredictionRepository


class ChampionshipService:
    """
    Serviço para operações de negócio relacionadas a campeonatos.
    """
    
    def __init__(self, championship_repository: ChampionshipRepository, prediction_repository: PredictionRepository):
        self.championship_repository = championship_repository
        self.prediction_repository = prediction_repository
    
    def get_championship_stages(self, championship_id: int) -> List[ChampionshipStage]:
        """
        Obtém todas as fases de um campeonato.
        
        Args:
            championship_id: ID do campeonato.
            
        Returns:
            Lista de fases do campeonato.
        """
        return self.championship_repository.get_stages_by_championship(championship_id)
    
    def get_stage_rounds(self, stage_id: int) -> List[ChampionshipRound]:
        """
        Obtém todas as rodadas de uma fase.
        
        Args:
            stage_id: ID da fase.
            
        Returns:
            Lista de rodadas da fase.
        """
        return self.championship_repository.get_rounds_by_stage(stage_id)
    
    def calculate_points_for_predictions(self, match_id: int, home_score: int, away_score: int) -> List[Tuple[Prediction, int]]:
        """
        Calcula pontos para todos os palpites de uma partida.
        
        Args:
            match_id: ID da partida.
            home_score: Placar do time da casa.
            away_score: Placar do time visitante.
            
        Returns:
            Lista de tuplas com palpite e pontos calculados.
        """
        # Obter todos os palpites para esta partida
        predictions = self.prediction_repository.get_predictions_by_match(match_id)
        
        result = []
        for prediction in predictions:
            points = 0
            
            # Placar exato
            if prediction.home_score == home_score and prediction.away_score == away_score:
                points = 20
            # Acertou o vencedor e a diferença de gols
            elif (prediction.home_score - prediction.away_score) == (home_score - away_score):
                points = 15
            # Acertou apenas o vencedor
            elif (prediction.home_score > prediction.away_score and home_score > away_score) or \
                 (prediction.home_score < prediction.away_score and home_score < away_score) or \
                 (prediction.home_score == prediction.away_score and home_score == away_score):
                points = 10
                
            result.append((prediction, points))
            
        return result
    
    def update_match_result(self, match_id: int, home_score: int, away_score: int) -> ChampionshipMatch:
        """
        Atualiza o resultado de uma partida e processa os palpites.
        
        Args:
            match_id: ID da partida.
            home_score: Placar do time da casa.
            away_score: Placar do time visitante.
            
        Returns:
            A partida atualizada.
        """
        # Atualiza o placar no banco de dados
        match = self.championship_repository.update_match_score(match_id, home_score, away_score)
        
        # Calcula pontos dos palpites
        prediction_points = self.calculate_points_for_predictions(match_id, home_score, away_score)
        
        # Atualiza os pontos no banco de dados
        for prediction, points in prediction_points:
            prediction.points = points
            self.prediction_repository.update(prediction)
            
        return match
    
    def get_matches_for_date_range(self, start_date: datetime, end_date: datetime) -> List[ChampionshipMatch]:
        """
        Obtém todas as partidas em um intervalo de datas.
        
        Args:
            start_date: Data inicial.
            end_date: Data final.
            
        Returns:
            Lista de partidas no intervalo.
        """
        return self.championship_repository.get_matches_by_date_range(start_date, end_date)
    
    def get_current_rounds(self) -> List[ChampionshipRound]:
        """
        Obtém todas as rodadas atuais de todos os campeonatos.
        
        Returns:
            Lista de rodadas atuais.
        """
        # Obter todos os campeonatos ativos
        championships = self.championship_repository.get_active_championships()
        
        current_rounds = []
        for championship in championships:
            # Obter fase atual de cada campeonato
            current_stage = self.championship_repository.get_current_stage(championship.id)
            if current_stage:
                # Obter rodadas da fase atual
                rounds = self.championship_repository.get_rounds_by_stage(current_stage.id)
                # Filtrar apenas as rodadas atuais
                current_rounds.extend([r for r in rounds if r.is_current])
                
        return current_rounds 