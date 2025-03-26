"""
Implementação Django do repositório de campeonatos.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from django.db import transaction
from django.db.models import F, Q

from domain.entities.championship import (
    Championship,
    ChampionshipStage,
    ChampionshipRound,
    ChampionshipMatch
)
from domain.repositories.championship_repository import ChampionshipRepository
from campeonatos.models import (
    Championship as DjangoChampionship,
    ChampionshipStage as DjangoChampionshipStage,
    ChampionshipRound as DjangoChampionshipRound,
    ChampionshipMatch as DjangoChampionshipMatch,
    Team as DjangoTeam
)


class DjangoChampionshipRepository(ChampionshipRepository):
    """
    Implementação do repositório de campeonatos usando o Django ORM.
    """
    
    def get_by_id(self, id: int) -> Optional[Championship]:
        """
        Recupera um campeonato pelo seu ID.
        
        Args:
            id: O ID do campeonato a ser recuperado.
            
        Returns:
            O campeonato, se encontrado, ou None.
        """
        try:
            championship_db = DjangoChampionship.objects.get(id=id)
            return self._map_to_domain_championship(championship_db)
        except DjangoChampionship.DoesNotExist:
            return None
    
    def list(self, filters: Optional[dict] = None, order_by: Optional[str] = None, limit: Optional[int] = None) -> List[Championship]:
        """
        Lista campeonatos com filtros opcionais.
        
        Args:
            filters: Dicionário com filtros a serem aplicados.
            order_by: Campo para ordenação.
            limit: Limite de itens a retornar.
            
        Returns:
            Lista de campeonatos.
        """
        # Inicializa a query
        query = DjangoChampionship.objects.all()
        
        # Aplica filtros, se fornecidos
        if filters:
            query = query.filter(**filters)
            
        # Aplica ordenação, se fornecida
        if order_by:
            query = query.order_by(order_by)
            
        # Aplica limite, se fornecido
        if limit is not None:
            query = query[:limit]
            
        # Mapeia para entidades de domínio
        return [self._map_to_domain_championship(championship_db) for championship_db in query]
    
    def create(self, entity: Championship) -> Championship:
        """
        Cria um novo campeonato.
        
        Args:
            entity: O campeonato a ser criado.
            
        Returns:
            O campeonato criado com ID atribuído.
        """
        with transaction.atomic():
            # Cria o campeonato no banco de dados
            championship_db = DjangoChampionship(
                name=entity.name,
                season=entity.season,
                scope_id=entity.scope_id,
                start_date=entity.start_date,
                end_date=entity.end_date,
                image=entity.image
            )
            championship_db.save()
            
            # Atualiza o ID da entidade
            entity.id = championship_db.id
            
            return entity
    
    def update(self, entity: Championship) -> Championship:
        """
        Atualiza um campeonato existente.
        
        Args:
            entity: O campeonato a ser atualizado.
            
        Returns:
            O campeonato atualizado.
        """
        with transaction.atomic():
            try:
                # Busca o campeonato no banco de dados
                championship_db = DjangoChampionship.objects.get(id=entity.id)
                
                # Atualiza os campos
                championship_db.name = entity.name
                championship_db.season = entity.season
                championship_db.scope_id = entity.scope_id
                championship_db.start_date = entity.start_date
                championship_db.end_date = entity.end_date
                championship_db.image = entity.image
                
                # Salva as alterações
                championship_db.save()
                
                return entity
            except DjangoChampionship.DoesNotExist:
                raise ValueError(f"Campeonato com ID {entity.id} não encontrado")
    
    def delete(self, id: int) -> bool:
        """
        Remove um campeonato pelo ID.
        
        Args:
            id: O ID do campeonato a ser removido.
            
        Returns:
            True se o campeonato foi removido, False caso contrário.
        """
        try:
            championship_db = DjangoChampionship.objects.get(id=id)
            championship_db.delete()
            return True
        except DjangoChampionship.DoesNotExist:
            return False
    
    def count(self, filters: Optional[dict] = None) -> int:
        """
        Conta o número de campeonatos que correspondem aos filtros.
        
        Args:
            filters: Dicionário com filtros a serem aplicados.
            
        Returns:
            Número de campeonatos.
        """
        # Inicializa a query
        query = DjangoChampionship.objects.all()
        
        # Aplica filtros, se fornecidos
        if filters:
            query = query.filter(**filters)
            
        return query.count()
    
    # Métodos para estágios
    
    def create_stage(self, stage: ChampionshipStage) -> ChampionshipStage:
        """
        Cria um novo estágio de campeonato.
        
        Args:
            stage: O estágio a ser criado.
            
        Returns:
            O estágio criado com ID atribuído.
        """
        with transaction.atomic():
            # Cria o estágio no banco de dados
            stage_db = DjangoChampionshipStage(
                championship_id=stage.championship_id,
                name=stage.name,
                order=stage.order,
                elimination=stage.elimination,
                is_current=stage.is_current
            )
            stage_db.save()
            
            # Atualiza o ID da entidade
            stage.id = stage_db.id
            
            # Se for o estágio atual, atualiza os outros estágios
            if stage.is_current:
                self._update_current_stage(stage.championship_id, stage.id)
            
            return stage
    
    def update_stage(self, stage: ChampionshipStage) -> ChampionshipStage:
        """
        Atualiza um estágio existente.
        
        Args:
            stage: O estágio a ser atualizado.
            
        Returns:
            O estágio atualizado.
        """
        with transaction.atomic():
            try:
                # Busca o estágio no banco de dados
                stage_db = DjangoChampionshipStage.objects.get(id=stage.id)
                
                # Atualiza os campos
                stage_db.name = stage.name
                stage_db.order = stage.order
                stage_db.elimination = stage.elimination
                stage_db.is_current = stage.is_current
                
                # Salva as alterações
                stage_db.save()
                
                # Se for o estágio atual, atualiza os outros estágios
                if stage.is_current:
                    self._update_current_stage(stage.championship_id, stage.id)
                
                return stage
            except DjangoChampionshipStage.DoesNotExist:
                raise ValueError(f"Estágio com ID {stage.id} não encontrado")
    
    def get_stages_by_championship(self, championship_id: int) -> List[ChampionshipStage]:
        """
        Obtém todos os estágios de um campeonato.
        
        Args:
            championship_id: ID do campeonato.
            
        Returns:
            Lista de estágios do campeonato.
        """
        # Busca os estágios do campeonato
        stages_db = DjangoChampionshipStage.objects.filter(championship_id=championship_id).order_by('order')
        
        # Mapeia para entidades de domínio
        return [self._map_to_domain_stage(stage_db) for stage_db in stages_db]
    
    def get_current_stage(self, championship_id: int) -> Optional[ChampionshipStage]:
        """
        Obtém o estágio atual de um campeonato.
        
        Args:
            championship_id: ID do campeonato.
            
        Returns:
            O estágio atual, se encontrado.
        """
        try:
            stage_db = DjangoChampionshipStage.objects.get(championship_id=championship_id, is_current=True)
            return self._map_to_domain_stage(stage_db)
        except DjangoChampionshipStage.DoesNotExist:
            return None
    
    # Métodos para rodadas
    
    def create_round(self, round: ChampionshipRound) -> ChampionshipRound:
        """
        Cria uma nova rodada de campeonato.
        
        Args:
            round: A rodada a ser criada.
            
        Returns:
            A rodada criada com ID atribuído.
        """
        with transaction.atomic():
            # Cria a rodada no banco de dados
            round_db = DjangoChampionshipRound(
                stage_id=round.stage_id,
                number=round.number,
                is_current=round.is_current,
                deadline=round.deadline
            )
            round_db.save()
            
            # Atualiza o ID da entidade
            round.id = round_db.id
            
            # Se for a rodada atual, atualiza as outras rodadas
            if round.is_current:
                self._update_current_round(round.stage_id, round.id)
            
            return round
    
    def update_round(self, round: ChampionshipRound) -> ChampionshipRound:
        """
        Atualiza uma rodada existente.
        
        Args:
            round: A rodada a ser atualizada.
            
        Returns:
            A rodada atualizada.
        """
        with transaction.atomic():
            try:
                # Busca a rodada no banco de dados
                round_db = DjangoChampionshipRound.objects.get(id=round.id)
                
                # Atualiza os campos
                round_db.number = round.number
                round_db.is_current = round.is_current
                round_db.deadline = round.deadline
                
                # Salva as alterações
                round_db.save()
                
                # Se for a rodada atual, atualiza as outras rodadas
                if round.is_current:
                    self._update_current_round(round.stage_id, round.id)
                
                return round
            except DjangoChampionshipRound.DoesNotExist:
                raise ValueError(f"Rodada com ID {round.id} não encontrada")
    
    def get_rounds_by_stage(self, stage_id: int) -> List[ChampionshipRound]:
        """
        Obtém todas as rodadas de um estágio.
        
        Args:
            stage_id: ID do estágio.
            
        Returns:
            Lista de rodadas do estágio.
        """
        # Busca as rodadas do estágio
        rounds_db = DjangoChampionshipRound.objects.filter(stage_id=stage_id).order_by('number')
        
        # Mapeia para entidades de domínio
        return [self._map_to_domain_round(round_db) for round_db in rounds_db]
    
    def get_current_round(self, stage_id: int) -> Optional[ChampionshipRound]:
        """
        Obtém a rodada atual de um estágio.
        
        Args:
            stage_id: ID do estágio.
            
        Returns:
            A rodada atual, se encontrada.
        """
        try:
            round_db = DjangoChampionshipRound.objects.get(stage_id=stage_id, is_current=True)
            return self._map_to_domain_round(round_db)
        except DjangoChampionshipRound.DoesNotExist:
            return None
    
    # Métodos para partidas
    
    def create_match(self, match: ChampionshipMatch) -> ChampionshipMatch:
        """
        Cria uma nova partida de campeonato.
        
        Args:
            match: A partida a ser criada.
            
        Returns:
            A partida criada com ID atribuído.
        """
        with transaction.atomic():
            # Cria a partida no banco de dados
            match_db = DjangoChampionshipMatch(
                round_id=match.round_id,
                home_team_id=match.home_team_id,
                away_team_id=match.away_team_id,
                match_date=match.match_date,
                home_score=match.home_score,
                away_score=match.away_score,
                status=match.status
            )
            match_db.save()
            
            # Atualiza o ID da entidade
            match.id = match_db.id
            
            return match
    
    def update_match(self, match: ChampionshipMatch) -> ChampionshipMatch:
        """
        Atualiza uma partida existente.
        
        Args:
            match: A partida a ser atualizada.
            
        Returns:
            A partida atualizada.
        """
        with transaction.atomic():
            try:
                # Busca a partida no banco de dados
                match_db = DjangoChampionshipMatch.objects.get(id=match.id)
                
                # Atualiza os campos
                match_db.home_team_id = match.home_team_id
                match_db.away_team_id = match.away_team_id
                match_db.match_date = match.match_date
                match_db.home_score = match.home_score
                match_db.away_score = match.away_score
                match_db.status = match.status
                
                # Salva as alterações
                match_db.save()
                
                return match
            except DjangoChampionshipMatch.DoesNotExist:
                raise ValueError(f"Partida com ID {match.id} não encontrada")
    
    def get_matches_by_round(self, round_id: int) -> List[ChampionshipMatch]:
        """
        Obtém todas as partidas de uma rodada.
        
        Args:
            round_id: ID da rodada.
            
        Returns:
            Lista de partidas da rodada.
        """
        # Busca as partidas da rodada
        matches_db = DjangoChampionshipMatch.objects.filter(round_id=round_id).order_by('match_date')
        
        # Mapeia para entidades de domínio
        return [self._map_to_domain_match(match_db) for match_db in matches_db]
    
    def get_match_by_id(self, match_id: int) -> Optional[ChampionshipMatch]:
        """
        Obtém uma partida pelo ID.
        
        Args:
            match_id: ID da partida.
            
        Returns:
            A partida, se encontrada.
        """
        try:
            match_db = DjangoChampionshipMatch.objects.get(id=match_id)
            return self._map_to_domain_match(match_db)
        except DjangoChampionshipMatch.DoesNotExist:
            return None
    
    def get_matches_by_date_range(self, start_date: datetime, end_date: datetime) -> List[ChampionshipMatch]:
        """
        Obtém todas as partidas dentro de um intervalo de datas.
        
        Args:
            start_date: Data inicial.
            end_date: Data final.
            
        Returns:
            Lista de partidas dentro do intervalo.
        """
        # Busca as partidas no intervalo de datas
        matches_db = DjangoChampionshipMatch.objects.filter(
            match_date__gte=start_date,
            match_date__lte=end_date
        ).order_by('match_date')
        
        # Mapeia para entidades de domínio
        return [self._map_to_domain_match(match_db) for match_db in matches_db]
    
    # Métodos auxiliares
    
    def _update_current_stage(self, championship_id: int, current_stage_id: int) -> None:
        """
        Atualiza o estágio atual de um campeonato.
        
        Args:
            championship_id: ID do campeonato.
            current_stage_id: ID do estágio atual.
        """
        # Atualiza todos os outros estágios para não serem atuais
        DjangoChampionshipStage.objects.filter(
            championship_id=championship_id
        ).exclude(
            id=current_stage_id
        ).update(is_current=False)
    
    def _update_current_round(self, stage_id: int, current_round_id: int) -> None:
        """
        Atualiza a rodada atual de um estágio.
        
        Args:
            stage_id: ID do estágio.
            current_round_id: ID da rodada atual.
        """
        # Atualiza todas as outras rodadas para não serem atuais
        DjangoChampionshipRound.objects.filter(
            stage_id=stage_id
        ).exclude(
            id=current_round_id
        ).update(is_current=False)
    
    # Métodos de mapeamento
    
    def _map_to_domain_championship(self, championship_db: DjangoChampionship) -> Championship:
        """
        Mapeia um campeonato do banco de dados para uma entidade de domínio.
        
        Args:
            championship_db: Campeonato do banco de dados.
            
        Returns:
            Entidade de domínio.
        """
        return Championship(
            id=championship_db.id,
            name=championship_db.name,
            season=championship_db.season,
            scope_id=championship_db.scope_id,
            start_date=championship_db.start_date,
            end_date=championship_db.end_date,
            image=championship_db.image.url if championship_db.image else None
        )
    
    def _map_to_domain_stage(self, stage_db: DjangoChampionshipStage) -> ChampionshipStage:
        """
        Mapeia um estágio do banco de dados para uma entidade de domínio.
        
        Args:
            stage_db: Estágio do banco de dados.
            
        Returns:
            Entidade de domínio.
        """
        return ChampionshipStage(
            id=stage_db.id,
            championship_id=stage_db.championship_id,
            name=stage_db.name,
            order=stage_db.order,
            elimination=stage_db.elimination,
            is_current=stage_db.is_current
        )
    
    def _map_to_domain_round(self, round_db: DjangoChampionshipRound) -> ChampionshipRound:
        """
        Mapeia uma rodada do banco de dados para uma entidade de domínio.
        
        Args:
            round_db: Rodada do banco de dados.
            
        Returns:
            Entidade de domínio.
        """
        return ChampionshipRound(
            id=round_db.id,
            stage_id=round_db.stage_id,
            number=round_db.number,
            is_current=round_db.is_current,
            deadline=round_db.deadline
        )
    
    def _map_to_domain_match(self, match_db: DjangoChampionshipMatch) -> ChampionshipMatch:
        """
        Mapeia uma partida do banco de dados para uma entidade de domínio.
        
        Args:
            match_db: Partida do banco de dados.
            
        Returns:
            Entidade de domínio.
        """
        return ChampionshipMatch(
            id=match_db.id,
            round_id=match_db.round_id,
            home_team_id=match_db.home_team_id,
            away_team_id=match_db.away_team_id,
            match_date=match_db.match_date,
            home_score=match_db.home_score,
            away_score=match_db.away_score,
            status=match_db.status
        ) 