"""
Serviço de domínio para operações relacionadas a FutLigas (ligas customizadas).
"""
from typing import List, Optional, Dict
from datetime import datetime

from domain.entities.futliga import (
    CustomLeague,
    CustomLeagueLevel,
    CustomLeaguePrize,
    LeagueMember,
    AwardConfig
)
from domain.repositories.futliga_repository import FutLigaRepository
from domain.repositories.user_repository import UserRepository
from domain.entities.user import User


class FutLigaService:
    """
    Serviço para operações de negócio relacionadas a FutLigas.
    """
    
    def __init__(self, futliga_repository: FutLigaRepository, user_repository: UserRepository):
        self.futliga_repository = futliga_repository
        self.user_repository = user_repository
    
    def create_league(self, name: str, owner_id: int, level_id: int, description: Optional[str] = None,
                     image: Optional[str] = None) -> CustomLeague:
        """
        Cria uma nova liga customizada.
        
        Args:
            name: Nome da liga.
            owner_id: ID do usuário dono da liga.
            level_id: ID do nível da liga.
            description: Descrição da liga (opcional).
            image: URL da imagem da liga (opcional).
            
        Returns:
            A liga criada.
        """
        # Verificar se o usuário existe
        owner = self.user_repository.get_by_id(owner_id)
        if not owner:
            raise ValueError(f"Usuário com ID {owner_id} não encontrado.")
        
        # Verificar se o nível existe
        level = self.futliga_repository.get_level_by_id(level_id)
        if not level:
            raise ValueError(f"Nível com ID {level_id} não encontrado.")
        
        # Verificar requisitos premium do nível
        if level.owner_premium and not owner.is_premium:
            raise ValueError("Este nível requer que o dono da liga seja um usuário premium.")
        
        # Criar a liga
        league = CustomLeague(
            id=0,  # ID será atribuído pelo repositório
            name=name,
            owner_id=owner_id,
            level_id=level_id,
            description=description,
            image=image,
            creation_date=datetime.now(),
            is_active=True,
            level=level
        )
        
        # Salvar no repositório
        created_league = self.futliga_repository.create(league)
        
        # Adicionar o dono como membro da liga
        member = LeagueMember(
            id=0,
            league_id=created_league.id,
            user_id=owner_id,
            joined_date=datetime.now(),
            is_owner=True,
            is_admin=True,
            is_active=True
        )
        self.add_member_to_league(member)
        
        return created_league
    
    def add_member_to_league(self, member: LeagueMember) -> LeagueMember:
        """
        Adiciona um novo membro a uma liga.
        
        Args:
            member: Membro a ser adicionado.
            
        Returns:
            O membro adicionado.
        """
        # Verificar se a liga existe
        league = self.futliga_repository.get_by_id(member.league_id)
        if not league:
            raise ValueError(f"Liga com ID {member.league_id} não encontrada.")
        
        # Verificar se o usuário existe
        user = self.user_repository.get_by_id(member.user_id)
        if not user:
            raise ValueError(f"Usuário com ID {member.user_id} não encontrado.")
        
        # Verificar limite de membros do nível
        current_members = self.futliga_repository.get_members_by_league(league.id)
        level = self.futliga_repository.get_level_by_id(league.level_id)
        
        if len(current_members) >= level.players:
            # Verificar se pode adicionar como premium
            premium_count = sum(1 for m in current_members if self.user_repository.get_by_id(m.user_id).is_premium)
            
            if not user.is_premium or premium_count >= level.premium_players:
                raise ValueError(f"Liga já atingiu o limite máximo de {level.players} participantes.")
        
        # Adicionar membro
        return self.futliga_repository.add_member(member)
    
    def save_prize_configuration(self, league_id: int, prizes: List[CustomLeaguePrize]) -> List[CustomLeaguePrize]:
        """
        Salva a configuração de prêmios de uma liga.
        
        Args:
            league_id: ID da liga.
            prizes: Lista de prêmios a serem configurados.
            
        Returns:
            Lista de prêmios salvos.
        """
        # Verificar se a liga existe
        league = self.futliga_repository.get_by_id(league_id)
        if not league:
            raise ValueError(f"Liga com ID {league_id} não encontrada.")
        
        # Excluir prêmios existentes que não estão na lista
        existing_prizes = self.futliga_repository.get_prizes_by_league(league_id)
        existing_ids = set(p.id for p in existing_prizes if p.id > 0)
        new_ids = set(p.id for p in prizes if p.id > 0)
        
        # IDs a serem excluídos (existem no banco mas não na nova lista)
        ids_to_delete = existing_ids - new_ids
        for prize_id in ids_to_delete:
            self.futliga_repository.delete_prize(prize_id)
        
        # Salvar novos prêmios ou atualizar existentes
        saved_prizes = []
        for prize in prizes:
            # Garantir que o league_id está correto
            prize.league_id = league_id
            saved_prize = self.futliga_repository.save_prize(prize)
            saved_prizes.append(saved_prize)
        
        return saved_prizes
    
    def save_award_configuration(self, league_id: int, award_config: AwardConfig) -> AwardConfig:
        """
        Salva a configuração de premiação de uma liga.
        
        Args:
            league_id: ID da liga.
            award_config: Configuração de premiação.
            
        Returns:
            A configuração salva.
        """
        # Verificar se a liga existe
        league = self.futliga_repository.get_by_id(league_id)
        if not league:
            raise ValueError(f"Liga com ID {league_id} não encontrada.")
        
        # Salvar configuração
        return self.futliga_repository.save_award_config(league_id, award_config)
    
    def get_league_with_details(self, league_id: int) -> Optional[CustomLeague]:
        """
        Obtém uma liga com todos os detalhes (membros, prêmios, etc).
        
        Args:
            league_id: ID da liga.
            
        Returns:
            A liga com detalhes, se encontrada.
        """
        # Buscar a liga
        league = self.futliga_repository.get_by_id(league_id)
        if not league:
            return None
        
        # Buscar nível
        league.level = self.futliga_repository.get_level_by_id(league.level_id)
        
        # Buscar membros
        league.members = self.futliga_repository.get_members_by_league(league_id)
        
        # Buscar prêmios
        league.prizes = self.futliga_repository.get_prizes_by_league(league_id)
        
        # Buscar configuração de premiação
        league.award_config = self.futliga_repository.get_award_config(league_id)
        
        # Contar membros ativos
        league.members_count = sum(1 for m in league.members if m.is_active)
        
        return league 