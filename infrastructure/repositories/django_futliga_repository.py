"""
Implementação Django do repositório de FutLiga.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from django.db import transaction

from domain.entities.futliga import (
    CustomLeague, 
    CustomLeagueLevel, 
    CustomLeaguePrize,
    LeagueMember,
    AwardConfig
)
from domain.repositories.futliga_repository import FutLigaRepository
from administrativo.models import (
    CustomLeague as DjangoCustomLeague,
    CustomLeagueLevel as DjangoCustomLeagueLevel,
    CustomLeaguePrize as DjangoCustomLeaguePrize,
    CustomLeaguePrizeValue as DjangoCustomLeaguePrizeValue,
    LeagueMember as DjangoLeagueMember
)


class DjangoFutLigaRepository(FutLigaRepository):
    """
    Implementação do repositório de FutLiga usando o Django ORM.
    """
    
    def get_by_id(self, id: int) -> Optional[CustomLeague]:
        """
        Recupera uma liga pelo seu ID.
        
        Args:
            id: O ID da liga a ser recuperada.
            
        Returns:
            A liga, se encontrada, ou None.
        """
        try:
            league_db = DjangoCustomLeague.objects.get(id=id)
            return self._map_to_domain_league(league_db)
        except DjangoCustomLeague.DoesNotExist:
            return None
    
    def list(self, filters: Optional[dict] = None, order_by: Optional[str] = None, limit: Optional[int] = None) -> List[CustomLeague]:
        """
        Lista ligas com filtros opcionais.
        
        Args:
            filters: Dicionário com filtros a serem aplicados.
            order_by: Campo para ordenação.
            limit: Limite de itens a retornar.
            
        Returns:
            Lista de ligas.
        """
        # Inicializa a query
        query = DjangoCustomLeague.objects.all()
        
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
        return [self._map_to_domain_league(league_db) for league_db in query]
    
    def create(self, entity: CustomLeague) -> CustomLeague:
        """
        Cria uma nova liga.
        
        Args:
            entity: A liga a ser criada.
            
        Returns:
            A liga criada com ID atribuído.
        """
        with transaction.atomic():
            # Cria a liga no banco de dados
            league_db = DjangoCustomLeague(
                name=entity.name,
                owner_id=entity.owner_id,
                level_id=entity.level_id,
                description=entity.description,
                image=entity.image,
                creation_date=entity.creation_date or datetime.now(),
                is_active=entity.is_active
            )
            league_db.save()
            
            # Atualiza o ID da entidade
            entity.id = league_db.id
            
            return entity
    
    def update(self, entity: CustomLeague) -> CustomLeague:
        """
        Atualiza uma liga existente.
        
        Args:
            entity: A liga a ser atualizada.
            
        Returns:
            A liga atualizada.
        """
        with transaction.atomic():
            try:
                # Busca a liga no banco de dados
                league_db = DjangoCustomLeague.objects.get(id=entity.id)
                
                # Atualiza os campos
                league_db.name = entity.name
                league_db.owner_id = entity.owner_id
                league_db.level_id = entity.level_id
                league_db.description = entity.description
                league_db.image = entity.image
                league_db.is_active = entity.is_active
                
                # Salva as alterações
                league_db.save()
                
                return entity
            except DjangoCustomLeague.DoesNotExist:
                raise ValueError(f"Liga com ID {entity.id} não encontrada")
    
    def delete(self, id: int) -> bool:
        """
        Remove uma liga pelo ID.
        
        Args:
            id: O ID da liga a ser removida.
            
        Returns:
            True se a liga foi removida, False caso contrário.
        """
        try:
            league_db = DjangoCustomLeague.objects.get(id=id)
            league_db.delete()
            return True
        except DjangoCustomLeague.DoesNotExist:
            return False
    
    def count(self, filters: Optional[dict] = None) -> int:
        """
        Conta o número de ligas que correspondem aos filtros.
        
        Args:
            filters: Dicionário com filtros a serem aplicados.
            
        Returns:
            Número de ligas.
        """
        # Inicializa a query
        query = DjangoCustomLeague.objects.all()
        
        # Aplica filtros, se fornecidos
        if filters:
            query = query.filter(**filters)
            
        return query.count()
    
    def get_leagues_by_user(self, user_id: int) -> List[CustomLeague]:
        """
        Obtém todas as ligas das quais um usuário é membro.
        
        Args:
            user_id: ID do usuário.
            
        Returns:
            Lista de ligas do usuário.
        """
        # Busca os membros do usuário
        members_db = DjangoLeagueMember.objects.filter(user_id=user_id, is_active=True)
        
        # Busca as ligas correspondentes
        leagues = []
        for member_db in members_db:
            try:
                league_db = DjangoCustomLeague.objects.get(id=member_db.league_id)
                leagues.append(self._map_to_domain_league(league_db))
            except DjangoCustomLeague.DoesNotExist:
                continue
                
        return leagues
    
    def get_leagues_created_by_user(self, user_id: int) -> List[CustomLeague]:
        """
        Obtém todas as ligas criadas por um usuário.
        
        Args:
            user_id: ID do usuário.
            
        Returns:
            Lista de ligas criadas pelo usuário.
        """
        # Busca as ligas do usuário
        leagues_db = DjangoCustomLeague.objects.filter(owner_id=user_id)
        
        # Mapeia para entidades de domínio
        return [self._map_to_domain_league(league_db) for league_db in leagues_db]
    
    def get_members_by_league(self, league_id: int) -> List[LeagueMember]:
        """
        Obtém todos os membros de uma liga.
        
        Args:
            league_id: ID da liga.
            
        Returns:
            Lista de membros da liga.
        """
        # Busca os membros da liga
        members_db = DjangoLeagueMember.objects.filter(league_id=league_id)
        
        # Mapeia para entidades de domínio
        return [self._map_to_domain_member(member_db) for member_db in members_db]
    
    def get_league_levels(self) -> List[CustomLeagueLevel]:
        """
        Obtém todos os níveis de ligas disponíveis.
        
        Returns:
            Lista de níveis de ligas.
        """
        # Busca os níveis de liga
        levels_db = DjangoCustomLeagueLevel.objects.all().order_by('id')
        
        # Mapeia para entidades de domínio
        return [self._map_to_domain_level(level_db) for level_db in levels_db]
    
    def get_level_by_id(self, level_id: int) -> Optional[CustomLeagueLevel]:
        """
        Obtém um nível de liga pelo ID.
        
        Args:
            level_id: ID do nível.
            
        Returns:
            O nível de liga, se encontrado.
        """
        try:
            level_db = DjangoCustomLeagueLevel.objects.get(id=level_id)
            return self._map_to_domain_level(level_db)
        except DjangoCustomLeagueLevel.DoesNotExist:
            return None
    
    def get_prizes_by_league(self, league_id: int) -> List[CustomLeaguePrize]:
        """
        Obtém todos os prêmios de uma liga.
        
        Args:
            league_id: ID da liga.
            
        Returns:
            Lista de prêmios da liga.
        """
        # Busca os prêmios da liga
        prizes_db = DjangoCustomLeaguePrize.objects.filter(league_id=league_id).order_by('position')
        
        # Mapeia para entidades de domínio
        return [self._map_to_domain_prize(prize_db) for prize_db in prizes_db]
    
    def save_prize(self, prize: CustomLeaguePrize) -> CustomLeaguePrize:
        """
        Salva um prêmio (cria novo ou atualiza existente).
        
        Args:
            prize: O prêmio a ser salvo.
            
        Returns:
            O prêmio salvo com ID atribuído.
        """
        with transaction.atomic():
            if prize.id:
                # Atualiza um prêmio existente
                try:
                    prize_db = DjangoCustomLeaguePrize.objects.get(id=prize.id)
                    prize_db.position = prize.position
                    prize_db.image = prize.image
                    prize_db.save()
                except DjangoCustomLeaguePrize.DoesNotExist:
                    # Se não existir, cria um novo
                    prize_db = DjangoCustomLeaguePrize(
                        position=prize.position,
                        league_id=prize.league_id,
                        image=prize.image
                    )
                    prize_db.save()
                    prize.id = prize_db.id
            else:
                # Cria um novo prêmio
                prize_db = DjangoCustomLeaguePrize(
                    position=prize.position,
                    league_id=prize.league_id,
                    image=prize.image
                )
                prize_db.save()
                prize.id = prize_db.id
            
            # Atualiza os valores do prêmio
            if prize.values:
                # Remove valores existentes
                DjangoCustomLeaguePrizeValue.objects.filter(prize_id=prize_db.id).delete()
                
                # Cria novos valores
                for level_id, value in prize.values.items():
                    DjangoCustomLeaguePrizeValue.objects.create(
                        prize_id=prize_db.id,
                        level_id=level_id,
                        value=value
                    )
            
            return prize
    
    def delete_prize(self, prize_id: int) -> bool:
        """
        Remove um prêmio pelo ID.
        
        Args:
            prize_id: ID do prêmio.
            
        Returns:
            True se o prêmio foi removido, False caso contrário.
        """
        try:
            prize_db = DjangoCustomLeaguePrize.objects.get(id=prize_id)
            prize_db.delete()
            return True
        except DjangoCustomLeaguePrize.DoesNotExist:
            return False
    
    def save_award_config(self, league_id: int, config: AwardConfig) -> AwardConfig:
        """
        Salva a configuração de premiação de uma liga.
        
        Args:
            league_id: ID da liga.
            config: Configuração de premiação.
            
        Returns:
            A configuração salva.
        """
        with transaction.atomic():
            try:
                # Busca a liga no banco de dados
                league_db = DjangoCustomLeague.objects.get(id=league_id)
                
                # Atualiza a configuração de premiação
                if config.weekly:
                    league_db.weekly_award_day = config.weekly.get("day")
                    league_db.weekly_award_time = config.weekly.get("time")
                
                if config.season:
                    league_db.season_award_month = config.season.get("month")
                    league_db.season_award_day = config.season.get("day")
                    league_db.season_award_time = config.season.get("time")
                
                # Salva as alterações
                league_db.save()
                
                return config
            except DjangoCustomLeague.DoesNotExist:
                raise ValueError(f"Liga com ID {league_id} não encontrada")
    
    def get_award_config(self, league_id: int) -> Optional[AwardConfig]:
        """
        Obtém a configuração de premiação de uma liga.
        
        Args:
            league_id: ID da liga.
            
        Returns:
            A configuração de premiação, se existir.
        """
        try:
            # Busca a liga no banco de dados
            league_db = DjangoCustomLeague.objects.get(id=league_id)
            
            # Cria a configuração de premiação
            weekly = {}
            season = {}
            
            if league_db.weekly_award_day:
                weekly["day"] = league_db.weekly_award_day
            
            if league_db.weekly_award_time:
                weekly["time"] = league_db.weekly_award_time
            
            if league_db.season_award_month:
                season["month"] = league_db.season_award_month
            
            if league_db.season_award_day:
                season["day"] = league_db.season_award_day
            
            if league_db.season_award_time:
                season["time"] = league_db.season_award_time
            
            return AwardConfig(weekly=weekly, season=season)
        except DjangoCustomLeague.DoesNotExist:
            return None
    
    def add_member(self, member: LeagueMember) -> LeagueMember:
        """
        Adiciona um novo membro a uma liga.
        
        Args:
            member: O membro a ser adicionado.
            
        Returns:
            O membro adicionado com ID atribuído.
        """
        with transaction.atomic():
            # Cria o membro no banco de dados
            member_db = DjangoLeagueMember(
                league_id=member.league_id,
                user_id=member.user_id,
                joined_date=member.joined_date or datetime.now(),
                is_owner=member.is_owner,
                is_admin=member.is_admin,
                is_active=member.is_active,
                score=member.score,
                ranking=member.ranking
            )
            member_db.save()
            
            # Atualiza o ID do membro
            member.id = member_db.id
            
            # Atualiza a contagem de membros da liga
            self._update_league_members_count(member.league_id)
            
            return member
    
    # Métodos auxiliares de mapeamento
    
    def _map_to_domain_league(self, league_db: DjangoCustomLeague) -> CustomLeague:
        """
        Mapeia uma liga do banco de dados para uma entidade de domínio.
        
        Args:
            league_db: Liga do banco de dados.
            
        Returns:
            Entidade de domínio.
        """
        return CustomLeague(
            id=league_db.id,
            name=league_db.name,
            owner_id=league_db.owner_id,
            level_id=league_db.level_id,
            description=league_db.description,
            image=league_db.image.url if league_db.image else None,
            creation_date=league_db.creation_date,
            is_active=league_db.is_active,
            members_count=league_db.members_count
        )
    
    def _map_to_domain_level(self, level_db: DjangoCustomLeagueLevel) -> CustomLeagueLevel:
        """
        Mapeia um nível de liga do banco de dados para uma entidade de domínio.
        
        Args:
            level_db: Nível de liga do banco de dados.
            
        Returns:
            Entidade de domínio.
        """
        return CustomLeagueLevel(
            id=level_db.id,
            name=level_db.name,
            players=level_db.players,
            premium_players=level_db.premium_players,
            owner_premium=level_db.owner_premium,
            image=level_db.image.url if level_db.image else None
        )
    
    def _map_to_domain_prize(self, prize_db: DjangoCustomLeaguePrize) -> CustomLeaguePrize:
        """
        Mapeia um prêmio do banco de dados para uma entidade de domínio.
        
        Args:
            prize_db: Prêmio do banco de dados.
            
        Returns:
            Entidade de domínio.
        """
        # Busca os valores do prêmio
        values_db = DjangoCustomLeaguePrizeValue.objects.filter(prize_id=prize_db.id)
        
        # Cria um dicionário com os valores
        values = {value_db.level_id: value_db.value for value_db in values_db}
        
        return CustomLeaguePrize(
            id=prize_db.id,
            position=prize_db.position,
            league_id=prize_db.league_id,
            image=prize_db.image.url if prize_db.image else None,
            values=values
        )
    
    def _map_to_domain_member(self, member_db: DjangoLeagueMember) -> LeagueMember:
        """
        Mapeia um membro do banco de dados para uma entidade de domínio.
        
        Args:
            member_db: Membro do banco de dados.
            
        Returns:
            Entidade de domínio.
        """
        return LeagueMember(
            id=member_db.id,
            league_id=member_db.league_id,
            user_id=member_db.user_id,
            joined_date=member_db.joined_date,
            is_owner=member_db.is_owner,
            is_admin=member_db.is_admin,
            is_active=member_db.is_active,
            score=member_db.score,
            ranking=member_db.ranking
        )
    
    def _update_league_members_count(self, league_id: int) -> None:
        """
        Atualiza a contagem de membros de uma liga.
        
        Args:
            league_id: ID da liga.
        """
        try:
            # Busca a liga no banco de dados
            league_db = DjangoCustomLeague.objects.get(id=league_id)
            
            # Conta os membros ativos
            members_count = DjangoLeagueMember.objects.filter(
                league_id=league_id,
                is_active=True
            ).count()
            
            # Atualiza a contagem
            league_db.members_count = members_count
            league_db.save(update_fields=['members_count'])
        except DjangoCustomLeague.DoesNotExist:
            pass 