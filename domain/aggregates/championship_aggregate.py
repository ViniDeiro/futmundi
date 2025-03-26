"""
Agregado de Campeonato - Gerencia as entidades relacionadas a um campeonato como uma unidade coesa.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

from domain.entities.championship import Championship, ChampionshipStage, ChampionshipRound, ChampionshipMatch


@dataclass
class ChampionshipAggregate:
    """
    Agregado que gerencia um campeonato e todas as suas entidades relacionadas (fases, rodadas, partidas).
    
    A entidade raiz é Championship. Todas as operações no agregado ocorrem através da raiz.
    """
    root: Championship
    
    def __post_init__(self):
        """
        Inicializa o agregado garantindo que as coleções estejam criadas.
        """
        if not self.root.stages:
            self.root.stages = []
            
        if not self.root.rounds:
            self.root.rounds = {}
            
        if not self.root.matches:
            self.root.matches = {}
    
    @property
    def id(self) -> int:
        """
        Retorna o ID do campeonato (entidade raiz).
        
        Returns:
            ID do campeonato.
        """
        return self.root.id
    
    def add_stage(self, stage: ChampionshipStage) -> None:
        """
        Adiciona uma fase ao campeonato.
        
        Args:
            stage: A fase a ser adicionada.
        """
        # Garante que o championship_id está correto
        stage.championship_id = self.root.id
        
        # Adiciona a fase à lista
        self.root.stages.append(stage)
        
        # Ordena as fases por ordem
        self.root.stages.sort(key=lambda x: x.order)
    
    def add_round(self, stage_id: int, round: ChampionshipRound) -> None:
        """
        Adiciona uma rodada a uma fase do campeonato.
        
        Args:
            stage_id: ID da fase à qual a rodada pertence.
            round: A rodada a ser adicionada.
        """
        # Garante que o stage_id está correto
        round.stage_id = stage_id
        
        # Adiciona a rodada ao dicionário
        if stage_id not in self.root.rounds:
            self.root.rounds[stage_id] = []
            
        self.root.rounds[stage_id].append(round)
        
        # Ordena as rodadas por número
        self.root.rounds[stage_id].sort(key=lambda x: x.number)
    
    def add_match(self, round_id: int, match: ChampionshipMatch) -> None:
        """
        Adiciona uma partida a uma rodada do campeonato.
        
        Args:
            round_id: ID da rodada à qual a partida pertence.
            match: A partida a ser adicionada.
        """
        # Garante que o round_id está correto
        match.round_id = round_id
        
        # Adiciona a partida ao dicionário
        if round_id not in self.root.matches:
            self.root.matches[round_id] = []
            
        self.root.matches[round_id].append(match)
        
        # Ordena as partidas por data
        if all(m.match_date for m in self.root.matches[round_id]):
            self.root.matches[round_id].sort(key=lambda x: x.match_date)
    
    def set_stage_as_current(self, stage_id: int) -> None:
        """
        Define uma fase como atual e as demais como não atuais.
        
        Args:
            stage_id: ID da fase a ser definida como atual.
        """
        for stage in self.root.stages:
            stage.is_current = (stage.id == stage_id)
    
    def set_round_as_current(self, round_id: int) -> None:
        """
        Define uma rodada como atual e as demais como não atuais.
        
        Args:
            round_id: ID da rodada a ser definida como atual.
        """
        for rounds_list in self.root.rounds.values():
            for round in rounds_list:
                round.is_current = (round.id == round_id)
    
    def update_match_score(self, match_id: int, home_score: int, away_score: int) -> Optional[ChampionshipMatch]:
        """
        Atualiza o placar de uma partida.
        
        Args:
            match_id: ID da partida.
            home_score: Placar do time da casa.
            away_score: Placar do time visitante.
            
        Returns:
            A partida atualizada ou None se não encontrada.
        """
        # Busca a partida em todas as rodadas
        for matches_list in self.root.matches.values():
            for match in matches_list:
                if match.id == match_id:
                    match.home_score = home_score
                    match.away_score = away_score
                    match.status = "finished"
                    return match
                    
        return None
    
    def get_stage_by_id(self, stage_id: int) -> Optional[ChampionshipStage]:
        """
        Retorna uma fase pelo ID.
        
        Args:
            stage_id: ID da fase.
            
        Returns:
            A fase encontrada ou None.
        """
        for stage in self.root.stages:
            if stage.id == stage_id:
                return stage
        return None
    
    def get_round_by_id(self, round_id: int) -> Optional[ChampionshipRound]:
        """
        Retorna uma rodada pelo ID.
        
        Args:
            round_id: ID da rodada.
            
        Returns:
            A rodada encontrada ou None.
        """
        for rounds_list in self.root.rounds.values():
            for round in rounds_list:
                if round.id == round_id:
                    return round
        return None
    
    def get_match_by_id(self, match_id: int) -> Optional[ChampionshipMatch]:
        """
        Retorna uma partida pelo ID.
        
        Args:
            match_id: ID da partida.
            
        Returns:
            A partida encontrada ou None.
        """
        for matches_list in self.root.matches.values():
            for match in matches_list:
                if match.id == match_id:
                    return match
        return None
    
    def get_current_stage(self) -> Optional[ChampionshipStage]:
        """
        Retorna a fase atual do campeonato.
        
        Returns:
            A fase atual ou None se não houver.
        """
        for stage in self.root.stages:
            if stage.is_current:
                return stage
        return None
    
    def get_current_round(self) -> Optional[ChampionshipRound]:
        """
        Retorna a rodada atual do campeonato.
        
        Returns:
            A rodada atual ou None se não houver.
        """
        for rounds_list in self.root.rounds.values():
            for round in rounds_list:
                if round.is_current:
                    return round
        return None 