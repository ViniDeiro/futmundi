"""
Serviço de Aplicação para gerenciamento de Campeonatos e seus Casos de Uso.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from domain.repositories.championship_repository import ChampionshipRepository
from domain.repositories.template_repository import TemplateRepository
from domain.services.championship_service import ChampionshipService
from domain.entities.championship import Championship, ChampionshipStage, ChampionshipRound, ChampionshipMatch
from domain.factories.championship_factory import ChampionshipFactory
from domain.events.championship_events import ChampionshipCreatedEvent, ChampionshipUpdatedEvent, StageUpdatedEvent
from domain.events.event_dispatcher import EventDispatcher


class ChampionshipAppService:
    """
    Serviço de Aplicação para orquestrar operações relacionadas a campeonatos.
    """
    
    def __init__(
        self,
        championship_repository: ChampionshipRepository,
        template_repository: TemplateRepository,
        championship_service: ChampionshipService,
        championship_factory: ChampionshipFactory,
        event_dispatcher: EventDispatcher
    ):
        """
        Inicializa o serviço com os repositórios e serviços necessários.
        
        Args:
            championship_repository: Repositório de campeonatos
            template_repository: Repositório de templates
            championship_service: Serviço de domínio para campeonatos
            championship_factory: Fábrica para criação de campeonatos
            event_dispatcher: Despachante de eventos
        """
        self.championship_repository = championship_repository
        self.template_repository = template_repository
        self.championship_service = championship_service
        self.championship_factory = championship_factory
        self.event_dispatcher = event_dispatcher
    
    def get_championship(self, championship_id: int) -> Optional[Championship]:
        """
        Obtém um campeonato pelo ID.
        
        Args:
            championship_id: ID do campeonato
            
        Returns:
            O campeonato, se encontrado, ou None
        """
        return self.championship_repository.get_by_id(championship_id)
    
    def create_championship(self, name: str, season: str, scope_id: int, start_date: datetime, end_date: datetime, image: Optional[str] = None) -> Championship:
        """
        Cria um novo campeonato.
        
        Args:
            name: Nome do campeonato
            season: Temporada do campeonato
            scope_id: ID do escopo (país, continente, mundial)
            start_date: Data de início
            end_date: Data de término
            image: URL da imagem (opcional)
            
        Returns:
            O campeonato criado
            
        Raises:
            ValueError: Se os dados fornecidos forem inválidos
        """
        # Validação básica
        if not name:
            raise ValueError("O nome do campeonato é obrigatório")
        
        if not season:
            raise ValueError("A temporada do campeonato é obrigatória")
        
        if not scope_id:
            raise ValueError("O escopo do campeonato é obrigatório")
        
        if not start_date or not end_date:
            raise ValueError("As datas de início e término são obrigatórias")
        
        if start_date >= end_date:
            raise ValueError("A data de início deve ser anterior à data de término")
        
        # Cria o campeonato usando a fábrica
        championship = self.championship_factory.create_empty_championship(
            name=name,
            season=season,
            scope_id=scope_id,
            start_date=start_date,
            end_date=end_date,
            image=image
        )
        
        # Salva o campeonato
        championship = self.championship_repository.create(championship)
        
        # Publica evento de criação
        self.event_dispatcher.dispatch(ChampionshipCreatedEvent(championship_id=championship.id))
        
        return championship
    
    def create_championship_from_template(self, template_id: int, name: str, season: str, start_date: datetime, end_date: datetime, image: Optional[str] = None) -> Championship:
        """
        Cria um campeonato a partir de um template.
        
        Args:
            template_id: ID do template
            name: Nome do campeonato
            season: Temporada do campeonato
            start_date: Data de início
            end_date: Data de término
            image: URL da imagem (opcional)
            
        Returns:
            O campeonato criado
            
        Raises:
            ValueError: Se os dados fornecidos forem inválidos
            LookupError: Se o template não for encontrado
        """
        # Obtém o template
        template = self.template_repository.get_by_id(template_id)
        if not template:
            raise LookupError(f"Template com ID {template_id} não encontrado")
        
        # Obtém as equipes do template
        teams = self.template_repository.get_teams(template_id)
        
        # Cria o campeonato a partir do template
        championship = self.championship_factory.create_from_template(
            template=template,
            teams=teams,
            name=name,
            season=season,
            start_date=start_date,
            end_date=end_date,
            image=image
        )
        
        # Publica evento de criação
        self.event_dispatcher.dispatch(ChampionshipCreatedEvent(championship_id=championship.id))
        
        return championship
    
    def update_championship(self, championship_id: int, **kwargs) -> Championship:
        """
        Atualiza um campeonato existente.
        
        Args:
            championship_id: ID do campeonato
            **kwargs: Campos a serem atualizados
            
        Returns:
            O campeonato atualizado
            
        Raises:
            ValueError: Se os dados fornecidos forem inválidos
            LookupError: Se o campeonato não for encontrado
        """
        # Obtém o campeonato
        championship = self.championship_repository.get_by_id(championship_id)
        if not championship:
            raise LookupError(f"Campeonato com ID {championship_id} não encontrado")
        
        # Atualiza os campos
        for key, value in kwargs.items():
            if hasattr(championship, key):
                setattr(championship, key, value)
        
        # Salva as alterações
        championship = self.championship_repository.update(championship)
        
        # Publica evento de atualização
        self.event_dispatcher.dispatch(ChampionshipUpdatedEvent(championship_id=championship.id))
        
        return championship
    
    def delete_championship(self, championship_id: int) -> bool:
        """
        Remove um campeonato.
        
        Args:
            championship_id: ID do campeonato
            
        Returns:
            True se removido com sucesso, False caso contrário
        """
        return self.championship_repository.delete(championship_id)
    
    def add_stage(
        self,
        championship_id: int,
        name: str,
        order: int,
        elimination: bool = False,
        is_current: bool = False
    ) -> ChampionshipStage:
        """
        Adiciona um estágio a um campeonato.
        
        Args:
            championship_id: ID do campeonato
            name: Nome do estágio
            order: Ordem do estágio
            elimination: Se é um estágio eliminatório
            is_current: Se é o estágio atual
            
        Returns:
            O estágio criado
            
        Raises:
            LookupError: Se o campeonato não for encontrado
        """
        # Verifica se o campeonato existe
        championship = self.championship_repository.get_by_id(championship_id)
        if not championship:
            raise LookupError(f"Campeonato com ID {championship_id} não encontrado")
        
        # Cria o estágio
        stage = self.championship_factory.create_stage(
            championship_id=championship_id,
            name=name,
            order=order,
            elimination=elimination,
            is_current=is_current
        )
        
        # Publica evento de atualização do estágio
        self.event_dispatcher.dispatch(StageUpdatedEvent(stage_id=stage.id, championship_id=championship_id))
        
        return stage
    
    def add_round(
        self,
        stage_id: int,
        number: int,
        deadline: Optional[datetime] = None,
        is_current: bool = False
    ) -> ChampionshipRound:
        """
        Adiciona uma rodada a um estágio.
        
        Args:
            stage_id: ID do estágio
            number: Número da rodada
            deadline: Prazo para palpites (opcional)
            is_current: Se é a rodada atual
            
        Returns:
            A rodada criada
        """
        # Cria a rodada
        round = self.championship_factory.create_round(
            stage_id=stage_id,
            number=number,
            deadline=deadline,
            is_current=is_current
        )
        
        return round
    
    def add_match(
        self,
        round_id: int,
        home_team_id: int,
        away_team_id: int,
        match_date: datetime,
        home_score: Optional[int] = None,
        away_score: Optional[int] = None,
        status: str = "scheduled"
    ) -> ChampionshipMatch:
        """
        Adiciona uma partida a uma rodada.
        
        Args:
            round_id: ID da rodada
            home_team_id: ID da equipe da casa
            away_team_id: ID da equipe visitante
            match_date: Data da partida
            home_score: Placar da equipe da casa (opcional)
            away_score: Placar da equipe visitante (opcional)
            status: Status da partida (scheduled, live, finished, postponed, cancelled)
            
        Returns:
            A partida criada
        """
        # Cria a partida
        match = self.championship_factory.create_match(
            round_id=round_id,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            match_date=match_date,
            home_score=home_score,
            away_score=away_score,
            status=status
        )
        
        return match
    
    def generate_matches_for_round(
        self,
        round_id: int,
        team_ids: List[int],
        start_date: datetime,
        interval_hours: int = 3
    ) -> List[ChampionshipMatch]:
        """
        Gera partidas para uma rodada com base em uma lista de equipes.
        
        Args:
            round_id: ID da rodada
            team_ids: Lista de IDs das equipes
            start_date: Data de início da rodada
            interval_hours: Intervalo entre partidas em horas
            
        Returns:
            Lista de partidas geradas
        """
        # Gera as partidas
        matches = self.championship_factory.generate_matches_for_round(
            round_id=round_id,
            team_ids=team_ids,
            start_date=start_date,
            interval_hours=interval_hours
        )
        
        return matches
    
    def update_match_score(self, match_id: int, home_score: int, away_score: int, status: str = "finished") -> ChampionshipMatch:
        """
        Atualiza o placar de uma partida.
        
        Args:
            match_id: ID da partida
            home_score: Placar da equipe da casa
            away_score: Placar da equipe visitante
            status: Status da partida
            
        Returns:
            A partida atualizada
            
        Raises:
            LookupError: Se a partida não for encontrada
        """
        # Obtém a partida
        match = self.championship_repository.get_match_by_id(match_id)
        if not match:
            raise LookupError(f"Partida com ID {match_id} não encontrada")
        
        # Atualiza o placar
        match.home_score = home_score
        match.away_score = away_score
        match.status = status
        
        # Salva as alterações
        match = self.championship_repository.update_match(match)
        
        return match
    
    def set_current_stage(self, championship_id: int, stage_id: int) -> ChampionshipStage:
        """
        Define o estágio atual de um campeonato.
        
        Args:
            championship_id: ID do campeonato
            stage_id: ID do estágio
            
        Returns:
            O estágio definido como atual
            
        Raises:
            LookupError: Se o campeonato ou estágio não forem encontrados
        """
        # Obtém o estágio
        stages = self.championship_repository.get_stages_by_championship(championship_id)
        stage = next((s for s in stages if s.id == stage_id), None)
        
        if not stage:
            raise LookupError(f"Estágio com ID {stage_id} não encontrado para o campeonato {championship_id}")
        
        # Define como atual
        stage.is_current = True
        stage = self.championship_repository.update_stage(stage)
        
        # Publica evento de atualização do estágio
        self.event_dispatcher.dispatch(StageUpdatedEvent(stage_id=stage.id, championship_id=championship_id))
        
        return stage
    
    def set_current_round(self, stage_id: int, round_id: int) -> ChampionshipRound:
        """
        Define a rodada atual de um estágio.
        
        Args:
            stage_id: ID do estágio
            round_id: ID da rodada
            
        Returns:
            A rodada definida como atual
            
        Raises:
            LookupError: Se o estágio ou rodada não forem encontrados
        """
        # Obtém a rodada
        rounds = self.championship_repository.get_rounds_by_stage(stage_id)
        round = next((r for r in rounds if r.id == round_id), None)
        
        if not round:
            raise LookupError(f"Rodada com ID {round_id} não encontrada para o estágio {stage_id}")
        
        # Define como atual
        round.is_current = True
        round = self.championship_repository.update_round(round)
        
        return round
    
    def get_upcoming_matches(self, days: int = 7) -> List[ChampionshipMatch]:
        """
        Obtém as partidas que ocorrerão nos próximos dias.
        
        Args:
            days: Número de dias a considerar
            
        Returns:
            Lista de partidas
        """
        now = datetime.now()
        end_date = now + timedelta(days=days)
        
        return self.championship_repository.get_matches_by_date_range(now, end_date)
    
    def list_championships(self, filters: Optional[Dict] = None, order_by: Optional[str] = None, limit: Optional[int] = None) -> List[Championship]:
        """
        Lista campeonatos com filtros opcionais.
        
        Args:
            filters: Filtros a serem aplicados
            order_by: Campo para ordenação
            limit: Limite de resultados
            
        Returns:
            Lista de campeonatos
        """
        return self.championship_repository.list(filters, order_by, limit) 