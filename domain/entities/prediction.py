"""
Entidade Prediction - Representa palpites de usuários para partidas.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class PredictionResult:
    """
    Entidade que representa o resultado de um palpite.
    Contém informações sobre a pontuação e acertos.
    """
    exact_score: bool = False  # Acertou o placar exato
    correct_winner: bool = False  # Acertou o vencedor
    correct_difference: bool = False  # Acertou a diferença de gols
    correct_home_score: bool = False  # Acertou o placar do time da casa
    correct_away_score: bool = False  # Acertou o placar do time visitante
    points_earned: int = 0  # Pontos ganhos
    
    def calculate_points(self) -> int:
        """
        Calcula os pontos com base nos acertos.
        
        Returns:
            Quantidade de pontos
        """
        if self.exact_score:
            return 25  # Placar exato
        elif self.correct_difference and self.correct_winner:
            return 18  # Vencedor correto e diferença de gols
        elif self.correct_winner:
            return 12  # Apenas o vencedor correto
        elif self.correct_home_score or self.correct_away_score:
            return 7  # Acertou o placar de um time
        else:
            return 0  # Errou completamente


@dataclass
class Prediction:
    """
    Entidade que representa um palpite de usuário para uma partida.
    """
    id: Optional[int]
    user_id: int
    match_id: int
    home_score: int
    away_score: int
    points: Optional[int] = None
    result: Optional[PredictionResult] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def is_correct_winner(self, match_home_score: int, match_away_score: int) -> bool:
        """
        Verifica se o palpite acertou o vencedor da partida.
        
        Args:
            match_home_score: Placar real do time da casa
            match_away_score: Placar real do time visitante
            
        Returns:
            True se acertou o vencedor, False caso contrário
        """
        # Empate
        if match_home_score == match_away_score and self.home_score == self.away_score:
            return True
        # Vitória do time da casa
        if match_home_score > match_away_score and self.home_score > self.away_score:
            return True
        # Vitória do time visitante
        if match_home_score < match_away_score and self.home_score < self.away_score:
            return True
        return False
    
    def is_exact_score(self, match_home_score: int, match_away_score: int) -> bool:
        """
        Verifica se o palpite acertou o placar exato da partida.
        
        Args:
            match_home_score: Placar real do time da casa
            match_away_score: Placar real do time visitante
            
        Returns:
            True se acertou o placar exato, False caso contrário
        """
        return self.home_score == match_home_score and self.away_score == match_away_score
    
    def is_correct_difference(self, match_home_score: int, match_away_score: int) -> bool:
        """
        Verifica se o palpite acertou a diferença de gols da partida.
        
        Args:
            match_home_score: Placar real do time da casa
            match_away_score: Placar real do time visitante
            
        Returns:
            True se acertou a diferença de gols, False caso contrário
        """
        pred_diff = self.home_score - self.away_score
        match_diff = match_home_score - match_away_score
        return pred_diff == match_diff
    
    def evaluate_result(self, match_home_score: int, match_away_score: int) -> PredictionResult:
        """
        Avalia o resultado do palpite comparando com o placar real.
        
        Args:
            match_home_score: Placar real do time da casa
            match_away_score: Placar real do time visitante
            
        Returns:
            Objeto PredictionResult com os acertos e pontuação
        """
        result = PredictionResult()
        
        # Verifica os acertos
        result.exact_score = self.is_exact_score(match_home_score, match_away_score)
        result.correct_winner = self.is_correct_winner(match_home_score, match_away_score)
        result.correct_difference = self.is_correct_difference(match_home_score, match_away_score)
        result.correct_home_score = self.home_score == match_home_score
        result.correct_away_score = self.away_score == match_away_score
        
        # Calcula os pontos
        result.points_earned = result.calculate_points()
        
        # Atualiza os pontos e o resultado
        self.points = result.points_earned
        self.result = result
        
        return result 