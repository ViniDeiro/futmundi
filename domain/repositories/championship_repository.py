"""
Repositório para entidades relacionadas a campeonatos.
"""
from abc import abstractmethod
from typing import List, Optional, Dict, Tuple
from datetime import datetime

from domain.repositories.base_repository import BaseRepository
from domain.entities.championship import Championship, ChampionshipStage, ChampionshipRound, ChampionshipMatch, Team


class ChampionshipRepository(BaseRepository[Championship]):
    """
    Repositório para operações com campeonatos.
    """
    
    @abstractmethod
    def get_active_championships(self) -> List[Championship]:
        """
        Obtém todos os campeonatos ativos.
        
        Returns:
            Lista de campeonatos ativos.
        """
        pass
    
    @abstractmethod
    def get_stages_by_championship(self, championship_id: int) -> List[ChampionshipStage]:
        """
        Obtém todas as fases de um campeonato.
        
        Args:
            championship_id: ID do campeonato.
            
        Returns:
            Lista de fases do campeonato.
        """
        pass
    
    @abstractmethod
    def get_current_stage(self, championship_id: int) -> Optional[ChampionshipStage]:
        """
        Obtém a fase atual de um campeonato.
        
        Args:
            championship_id: ID do campeonato.
            
        Returns:
            A fase atual do campeonato, se existir.
        """
        pass
    
    @abstractmethod
    def get_rounds_by_stage(self, stage_id: int) -> List[ChampionshipRound]:
        """
        Obtém todas as rodadas de uma fase.
        
        Args:
            stage_id: ID da fase.
            
        Returns:
            Lista de rodadas da fase.
        """
        pass
    
    @abstractmethod
    def get_matches_by_round(self, round_id: int) -> List[ChampionshipMatch]:
        """
        Obtém todas as partidas de uma rodada.
        
        Args:
            round_id: ID da rodada.
            
        Returns:
            Lista de partidas da rodada.
        """
        pass
    
    @abstractmethod
    def get_team_by_id(self, team_id: int) -> Optional[Team]:
        """
        Obtém um time pelo ID.
        
        Args:
            team_id: ID do time.
            
        Returns:
            O time, se encontrado.
        """
        pass
    
    @abstractmethod
    def get_teams_by_championship(self, championship_id: int) -> List[Team]:
        """
        Obtém todos os times de um campeonato.
        
        Args:
            championship_id: ID do campeonato.
            
        Returns:
            Lista de times do campeonato.
        """
        pass
    
    @abstractmethod
    def update_match_score(self, match_id: int, home_score: int, away_score: int) -> ChampionshipMatch:
        """
        Atualiza o placar de uma partida.
        
        Args:
            match_id: ID da partida.
            home_score: Placar do time da casa.
            away_score: Placar do time visitante.
            
        Returns:
            A partida atualizada.
        """
        pass
    
    @abstractmethod
    def get_matches_by_date_range(self, start_date: datetime, end_date: datetime) -> List[ChampionshipMatch]:
        """
        Obtém todas as partidas em um intervalo de datas.
        
        Args:
            start_date: Data inicial.
            end_date: Data final.
            
        Returns:
            Lista de partidas no intervalo de datas.
        """
        pass 