"""
Agregado de Liga - Gerencia as entidades relacionadas a uma FutLiga como uma unidade coesa.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

from domain.entities.futliga import (
    CustomLeague, 
    CustomLeagueLevel, 
    CustomLeaguePrize,
    LeagueMember,
    AwardConfig
)


@dataclass
class LeagueAggregate:
    """
    Agregado que gerencia uma liga customizada e todas as suas entidades relacionadas.
    
    A entidade raiz é CustomLeague. Todas as operações no agregado ocorrem através da raiz.
    """
    root: CustomLeague
    
    def __post_init__(self):
        """
        Inicializa o agregado garantindo que as coleções estejam criadas.
        """
        if not self.root.members:
            self.root.members = []
            
        if not self.root.prizes:
            self.root.prizes = []
    
    @property
    def id(self) -> int:
        """
        Retorna o ID da liga (entidade raiz).
        
        Returns:
            ID da liga.
        """
        return self.root.id
    
    def set_level(self, level: CustomLeagueLevel) -> None:
        """
        Define o nível da liga.
        
        Args:
            level: O nível a ser definido.
        """
        self.root.level = level
        self.root.level_id = level.id
    
    def add_member(self, member: LeagueMember) -> None:
        """
        Adiciona um membro à liga.
        
        Args:
            member: O membro a ser adicionado.
        """
        # Garante que o league_id está correto
        member.league_id = self.root.id
        
        # Adiciona o membro à lista
        self.root.members.append(member)
        
        # Atualiza a contagem de membros
        self.update_members_count()
    
    def remove_member(self, user_id: int) -> Optional[LeagueMember]:
        """
        Remove um membro da liga.
        
        Args:
            user_id: ID do usuário a ser removido.
            
        Returns:
            O membro removido ou None se não encontrado.
        """
        # Busca o membro na lista
        for i, member in enumerate(self.root.members):
            if member.user_id == user_id:
                # Remove o membro da lista
                removed = self.root.members.pop(i)
                
                # Atualiza a contagem de membros
                self.update_members_count()
                
                return removed
                
        return None
    
    def update_members_count(self) -> None:
        """
        Atualiza a contagem de membros ativos na liga.
        """
        self.root.members_count = sum(1 for member in self.root.members if member.is_active)
    
    def add_prize(self, prize: CustomLeaguePrize) -> None:
        """
        Adiciona um prêmio à liga.
        
        Args:
            prize: O prêmio a ser adicionado.
        """
        # Garante que o league_id está correto
        prize.league_id = self.root.id
        
        # Adiciona o prêmio à lista
        self.root.prizes.append(prize)
        
        # Ordena os prêmios por posição
        self.root.prizes.sort(key=lambda x: x.position)
    
    def remove_prize(self, prize_id: int) -> Optional[CustomLeaguePrize]:
        """
        Remove um prêmio da liga.
        
        Args:
            prize_id: ID do prêmio a ser removido.
            
        Returns:
            O prêmio removido ou None se não encontrado.
        """
        # Busca o prêmio na lista
        for i, prize in enumerate(self.root.prizes):
            if prize.id == prize_id:
                # Remove o prêmio da lista
                return self.root.prizes.pop(i)
                
        return None
    
    def set_award_config(self, config: AwardConfig) -> None:
        """
        Define a configuração de premiação da liga.
        
        Args:
            config: A configuração a ser definida.
        """
        self.root.award_config = config
    
    def get_member_by_user_id(self, user_id: int) -> Optional[LeagueMember]:
        """
        Retorna um membro pelo ID do usuário.
        
        Args:
            user_id: ID do usuário.
            
        Returns:
            O membro encontrado ou None.
        """
        for member in self.root.members:
            if member.user_id == user_id:
                return member
        return None
    
    def get_prize_by_id(self, prize_id: int) -> Optional[CustomLeaguePrize]:
        """
        Retorna um prêmio pelo ID.
        
        Args:
            prize_id: ID do prêmio.
            
        Returns:
            O prêmio encontrado ou None.
        """
        for prize in self.root.prizes:
            if prize.id == prize_id:
                return prize
        return None
    
    def get_prize_by_position(self, position: int) -> Optional[CustomLeaguePrize]:
        """
        Retorna um prêmio pela posição.
        
        Args:
            position: Posição do prêmio.
            
        Returns:
            O prêmio encontrado ou None.
        """
        for prize in self.root.prizes:
            if prize.position == position:
                return prize
        return None
    
    def update_prize_values(self, prize_id: int, values: Dict[int, int]) -> Optional[CustomLeaguePrize]:
        """
        Atualiza os valores de um prêmio.
        
        Args:
            prize_id: ID do prêmio.
            values: Dicionário com os valores (level_id -> value).
            
        Returns:
            O prêmio atualizado ou None se não encontrado.
        """
        prize = self.get_prize_by_id(prize_id)
        if prize:
            prize.values = values
            return prize
        return None 