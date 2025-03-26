"""
Factory para criação de campeonatos e suas entidades relacionadas.
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

from domain.entities.championship import Championship, ChampionshipStage, ChampionshipRound, ChampionshipMatch, Team
from domain.aggregates.championship_aggregate import ChampionshipAggregate
from domain.entities.template import Template, TemplateStage


class ChampionshipFactory:
    """
    Factory responsável pela criação de campeonatos e suas entidades relacionadas.
    """
    
    @staticmethod
    def create_empty_championship(
        name: str,
        season: str,
        scope_id: int,
        start_date: datetime,
        end_date: datetime,
        image: Optional[str] = None
    ) -> ChampionshipAggregate:
        """
        Cria um campeonato vazio.
        
        Args:
            name: Nome do campeonato.
            season: Temporada do campeonato.
            scope_id: ID do âmbito do campeonato.
            start_date: Data de início do campeonato.
            end_date: Data de fim do campeonato.
            image: URL da imagem do campeonato (opcional).
            
        Returns:
            Um agregado de campeonato.
        """
        # Cria a entidade de campeonato
        championship = Championship(
            id=0,  # ID será atribuído pelo repositório
            name=name,
            season=season,
            scope_id=scope_id,
            start_date=start_date,
            end_date=end_date,
            is_active=True,
            image=image
        )
        
        # Retorna o agregado
        return ChampionshipAggregate(root=championship)
    
    @staticmethod
    def create_from_template(
        name: str,
        season: str,
        scope_id: int,
        start_date: datetime,
        end_date: datetime,
        template: Template,
        teams: List[Team],
        image: Optional[str] = None
    ) -> ChampionshipAggregate:
        """
        Cria um campeonato a partir de um template.
        
        Args:
            name: Nome do campeonato.
            season: Temporada do campeonato.
            scope_id: ID do âmbito do campeonato.
            start_date: Data de início do campeonato.
            end_date: Data de fim do campeonato.
            template: Template a ser usado.
            teams: Lista de times do campeonato.
            image: URL da imagem do campeonato (opcional).
            
        Returns:
            Um agregado de campeonato.
        """
        # Cria o campeonato vazio
        championship_aggregate = ChampionshipFactory.create_empty_championship(
            name=name,
            season=season,
            scope_id=scope_id,
            start_date=start_date,
            end_date=end_date,
            image=image
        )
        
        # Adiciona as fases do template
        for template_stage in template.stages:
            # Cria a fase
            stage = ChampionshipStage(
                id=0,  # ID será atribuído pelo repositório
                name=template_stage.name,
                order=template_stage.order,
                championship_id=championship_aggregate.id,
                elimination=template_stage.elimination,
                is_current=(template_stage.order == 1)  # Primeira fase é a atual
            )
            
            # Adiciona a fase ao campeonato
            championship_aggregate.add_stage(stage)
            
            # Adiciona as rodadas à fase
            for i in range(1, template_stage.rounds_count + 1):
                # Calcula a data limite da rodada (1 semana por rodada)
                deadline = start_date + timedelta(days=7 * (i - 1))
                
                # Cria a rodada
                round = ChampionshipRound(
                    id=0,  # ID será atribuído pelo repositório
                    number=i,
                    stage_id=stage.id,
                    is_current=(i == 1 and template_stage.order == 1),  # Primeira rodada da primeira fase é a atual
                    deadline=deadline
                )
                
                # Adiciona a rodada ao campeonato
                championship_aggregate.add_round(stage.id, round)
        
        return championship_aggregate
    
    @staticmethod
    def create_stage(
        championship_id: int,
        name: str,
        order: int,
        elimination: bool = False,
        is_current: bool = False
    ) -> ChampionshipStage:
        """
        Cria uma fase de campeonato.
        
        Args:
            championship_id: ID do campeonato.
            name: Nome da fase.
            order: Ordem da fase.
            elimination: Indica se a fase é eliminatória.
            is_current: Indica se a fase é a atual.
            
        Returns:
            Uma fase de campeonato.
        """
        return ChampionshipStage(
            id=0,  # ID será atribuído pelo repositório
            name=name,
            order=order,
            championship_id=championship_id,
            elimination=elimination,
            is_current=is_current
        )
    
    @staticmethod
    def create_round(
        stage_id: int,
        number: int,
        is_current: bool = False,
        deadline: Optional[datetime] = None
    ) -> ChampionshipRound:
        """
        Cria uma rodada de campeonato.
        
        Args:
            stage_id: ID da fase.
            number: Número da rodada.
            is_current: Indica se a rodada é a atual.
            deadline: Data limite da rodada.
            
        Returns:
            Uma rodada de campeonato.
        """
        return ChampionshipRound(
            id=0,  # ID será atribuído pelo repositório
            number=number,
            stage_id=stage_id,
            is_current=is_current,
            deadline=deadline
        )
    
    @staticmethod
    def create_match(
        round_id: int,
        home_team_id: int,
        away_team_id: int,
        match_date: Optional[datetime] = None,
        home_score: Optional[int] = None,
        away_score: Optional[int] = None,
        status: str = "pending"
    ) -> ChampionshipMatch:
        """
        Cria uma partida de campeonato.
        
        Args:
            round_id: ID da rodada.
            home_team_id: ID do time da casa.
            away_team_id: ID do time visitante.
            match_date: Data da partida.
            home_score: Placar do time da casa.
            away_score: Placar do time visitante.
            status: Status da partida.
            
        Returns:
            Uma partida de campeonato.
        """
        return ChampionshipMatch(
            id=0,  # ID será atribuído pelo repositório
            round_id=round_id,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            match_date=match_date,
            home_score=home_score,
            away_score=away_score,
            status=status
        )
    
    @staticmethod
    def generate_matches_for_round(
        round_id: int,
        teams: List[Team],
        start_date: datetime,
        match_interval_hours: int = 2
    ) -> List[ChampionshipMatch]:
        """
        Gera partidas para uma rodada, fazendo a combinação dos times.
        
        Args:
            round_id: ID da rodada.
            teams: Lista de times.
            start_date: Data inicial para as partidas.
            match_interval_hours: Intervalo em horas entre as partidas.
            
        Returns:
            Lista de partidas geradas.
        """
        matches = []
        match_date = start_date
        
        # Para cada par de times, cria uma partida
        for i in range(0, len(teams), 2):
            if i + 1 < len(teams):
                home_team = teams[i]
                away_team = teams[i + 1]
                
                match = ChampionshipFactory.create_match(
                    round_id=round_id,
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    match_date=match_date
                )
                
                matches.append(match)
                
                # Incrementa a data para a próxima partida
                match_date = match_date + timedelta(hours=match_interval_hours)
        
        return matches 