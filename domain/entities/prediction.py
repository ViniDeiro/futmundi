"""
Entidade Prediction - Representa palpites de usuários para partidas.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Prediction:
    """
    Entidade que representa um palpite de usuário para uma partida.
    """
    id: int
    user_id: int
    match_id: int
    home_score: int
    away_score: int
    points: int = 0
    created_at: datetime = None
    updated_at: Optional[datetime] = None
    
    @property
    def is_correct_winner(self, match_home_score: int, match_away_score: int) -> bool:
        """Verifica se o palpite acertou o vencedor da partida."""
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
    
    @property
    def is_exact_score(self, match_home_score: int, match_away_score: int) -> bool:
        """Verifica se o palpite acertou o placar exato da partida."""
        return self.home_score == match_home_score and self.away_score == match_away_score 