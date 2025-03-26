"""
Repositório para entidades relacionadas a FutLigas (ligas customizadas).
"""
from abc import abstractmethod
from typing import List, Optional, Dict
from datetime import datetime

from domain.repositories.base_repository import BaseRepository
from domain.entities.futliga import (
    CustomLeague, 
    CustomLeagueLevel, 
    CustomLeaguePrize,
    LeagueMember,
    AwardConfig
)


class FutLigaRepository(BaseRepository[CustomLeague]):
    """
    Repositório para operações com ligas customizadas.
    """
    
    @abstractmethod
    def get_leagues_by_user(self, user_id: int) -> List[CustomLeague]:
        """
        Obtém todas as ligas das quais um usuário é membro.
        
        Args:
            user_id: ID do usuário.
            
        Returns:
            Lista de ligas do usuário.
        """
        pass
    
    @abstractmethod
    def get_leagues_created_by_user(self, user_id: int) -> List[CustomLeague]:
        """
        Obtém todas as ligas criadas por um usuário.
        
        Args:
            user_id: ID do usuário.
            
        Returns:
            Lista de ligas criadas pelo usuário.
        """
        pass
    
    @abstractmethod
    def get_members_by_league(self, league_id: int) -> List[LeagueMember]:
        """
        Obtém todos os membros de uma liga.
        
        Args:
            league_id: ID da liga.
            
        Returns:
            Lista de membros da liga.
        """
        pass
    
    @abstractmethod
    def get_league_levels(self) -> List[CustomLeagueLevel]:
        """
        Obtém todos os níveis de ligas disponíveis.
        
        Returns:
            Lista de níveis de ligas.
        """
        pass
    
    @abstractmethod
    def get_level_by_id(self, level_id: int) -> Optional[CustomLeagueLevel]:
        """
        Obtém um nível de liga pelo ID.
        
        Args:
            level_id: ID do nível.
            
        Returns:
            O nível de liga, se encontrado.
        """
        pass
    
    @abstractmethod
    def get_prizes_by_league(self, league_id: int) -> List[CustomLeaguePrize]:
        """
        Obtém todos os prêmios de uma liga.
        
        Args:
            league_id: ID da liga.
            
        Returns:
            Lista de prêmios da liga.
        """
        pass
    
    @abstractmethod
    def save_prize(self, prize: CustomLeaguePrize) -> CustomLeaguePrize:
        """
        Salva um prêmio (cria novo ou atualiza existente).
        
        Args:
            prize: O prêmio a ser salvo.
            
        Returns:
            O prêmio salvo com ID atribuído.
        """
        pass
    
    @abstractmethod
    def delete_prize(self, prize_id: int) -> bool:
        """
        Remove um prêmio pelo ID.
        
        Args:
            prize_id: ID do prêmio.
            
        Returns:
            True se o prêmio foi removido, False caso contrário.
        """
        pass
    
    @abstractmethod
    def save_award_config(self, league_id: int, config: AwardConfig) -> AwardConfig:
        """
        Salva a configuração de premiação de uma liga.
        
        Args:
            league_id: ID da liga.
            config: Configuração de premiação.
            
        Returns:
            A configuração salva.
        """
        pass
    
    @abstractmethod
    def get_award_config(self, league_id: int) -> Optional[AwardConfig]:
        """
        Obtém a configuração de premiação de uma liga.
        
        Args:
            league_id: ID da liga.
            
        Returns:
            A configuração de premiação, se existir.
        """
        pass 