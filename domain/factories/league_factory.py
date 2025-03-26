"""
Factory para criação de ligas customizadas e suas entidades relacionadas.
"""
from typing import List, Dict, Optional
from datetime import datetime

from domain.entities.futliga import (
    CustomLeague, 
    CustomLeagueLevel, 
    CustomLeaguePrize,
    LeagueMember,
    AwardConfig
)
from domain.aggregates.league_aggregate import LeagueAggregate


class LeagueFactory:
    """
    Factory responsável pela criação de ligas customizadas e suas entidades relacionadas.
    """
    
    @staticmethod
    def create_empty_league(
        name: str,
        owner_id: int,
        level_id: int,
        description: Optional[str] = None,
        image: Optional[str] = None
    ) -> LeagueAggregate:
        """
        Cria uma liga vazia.
        
        Args:
            name: Nome da liga.
            owner_id: ID do usuário dono da liga.
            level_id: ID do nível da liga.
            description: Descrição da liga (opcional).
            image: URL da imagem da liga (opcional).
            
        Returns:
            Um agregado de liga.
        """
        # Cria a entidade de liga
        league = CustomLeague(
            id=0,  # ID será atribuído pelo repositório
            name=name,
            owner_id=owner_id,
            level_id=level_id,
            description=description,
            image=image,
            creation_date=datetime.now(),
            is_active=True,
            members_count=0
        )
        
        # Retorna o agregado
        return LeagueAggregate(root=league)
    
    @staticmethod
    def create_league_with_owner(
        name: str,
        owner_id: int,
        level: CustomLeagueLevel,
        description: Optional[str] = None,
        image: Optional[str] = None
    ) -> LeagueAggregate:
        """
        Cria uma liga com o dono já adicionado como membro.
        
        Args:
            name: Nome da liga.
            owner_id: ID do usuário dono da liga.
            level: Nível da liga.
            description: Descrição da liga (opcional).
            image: URL da imagem da liga (opcional).
            
        Returns:
            Um agregado de liga.
        """
        # Cria a liga vazia
        league_aggregate = LeagueFactory.create_empty_league(
            name=name,
            owner_id=owner_id,
            level_id=level.id,
            description=description,
            image=image
        )
        
        # Define o nível da liga
        league_aggregate.set_level(level)
        
        # Cria o membro dono
        owner_member = LeagueFactory.create_member(
            league_id=league_aggregate.id,
            user_id=owner_id,
            is_owner=True,
            is_admin=True
        )
        
        # Adiciona o membro à liga
        league_aggregate.add_member(owner_member)
        
        # Cria a configuração de premiação padrão
        award_config = LeagueFactory.create_default_award_config()
        
        # Define a configuração de premiação
        league_aggregate.set_award_config(award_config)
        
        return league_aggregate
    
    @staticmethod
    def create_member(
        league_id: int,
        user_id: int,
        is_owner: bool = False,
        is_admin: bool = False,
        is_active: bool = True,
        score: int = 0,
        ranking: int = 0
    ) -> LeagueMember:
        """
        Cria um membro de liga.
        
        Args:
            league_id: ID da liga.
            user_id: ID do usuário.
            is_owner: Indica se o membro é o dono da liga.
            is_admin: Indica se o membro é administrador da liga.
            is_active: Indica se o membro está ativo.
            score: Pontuação do membro.
            ranking: Classificação do membro.
            
        Returns:
            Um membro de liga.
        """
        return LeagueMember(
            id=0,  # ID será atribuído pelo repositório
            league_id=league_id,
            user_id=user_id,
            joined_date=datetime.now(),
            is_owner=is_owner,
            is_admin=is_admin,
            is_active=is_active,
            score=score,
            ranking=ranking
        )
    
    @staticmethod
    def create_prize(
        league_id: int,
        position: int,
        image: Optional[str] = None,
        values: Optional[Dict[int, int]] = None
    ) -> CustomLeaguePrize:
        """
        Cria um prêmio de liga.
        
        Args:
            league_id: ID da liga.
            position: Posição do prêmio.
            image: URL da imagem do prêmio (opcional).
            values: Valores do prêmio por nível (opcional).
            
        Returns:
            Um prêmio de liga.
        """
        if values is None:
            values = {}
            
        return CustomLeaguePrize(
            id=0,  # ID será atribuído pelo repositório
            position=position,
            league_id=league_id,
            image=image,
            values=values
        )
    
    @staticmethod
    def create_default_prizes(league_id: int, levels: List[CustomLeagueLevel]) -> List[CustomLeaguePrize]:
        """
        Cria prêmios padrão para uma liga.
        
        Args:
            league_id: ID da liga.
            levels: Lista de níveis disponíveis.
            
        Returns:
            Lista de prêmios padrão.
        """
        prizes = []
        
        # Cria prêmios para as posições 1, 2 e 3
        for position in range(1, 4):
            # Define valores proporcionais à posição
            values = {}
            for level in levels:
                base_value = 1000 if level.premium_players == 0 else 2000
                multiplier = 3 if position == 1 else (2 if position == 2 else 1)
                values[level.id] = base_value * multiplier
            
            # Cria o prêmio
            prize = LeagueFactory.create_prize(
                league_id=league_id,
                position=position,
                values=values
            )
            
            prizes.append(prize)
        
        return prizes
    
    @staticmethod
    def create_default_award_config() -> AwardConfig:
        """
        Cria uma configuração de premiação padrão.
        
        Returns:
            Uma configuração de premiação padrão.
        """
        return AwardConfig(
            weekly={
                "day": "1",  # Segunda-feira
                "time": "12:00"
            },
            season={
                "month": "12",  # Dezembro
                "day": "31",  # Dia 31
                "time": "18:00"
            }
        ) 