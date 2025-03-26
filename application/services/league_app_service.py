"""
Serviço de Aplicação para gerenciamento de Ligas Personalizadas e seus Casos de Uso.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from domain.repositories.futliga_repository import FutLigaRepository
from domain.repositories.user_repository import UserRepository
from domain.repositories.payment_repository import PaymentRepository
from domain.services.futliga_service import FutLigaService
from domain.entities.futliga import (
    CustomLeague, 
    CustomLeagueLevel, 
    CustomLeaguePrize,
    LeagueMember,
    AwardConfig
)
from domain.factories.league_factory import LeagueFactory
from domain.events.league_events import LeagueCreatedEvent, LeagueUpdatedEvent, MemberAddedEvent
from domain.events.event_dispatcher import EventDispatcher


class LeagueAppService:
    """
    Serviço de Aplicação para orquestrar operações relacionadas a ligas personalizadas.
    """
    
    def __init__(
        self,
        futliga_repository: FutLigaRepository,
        user_repository: UserRepository,
        payment_repository: PaymentRepository,
        futliga_service: FutLigaService,
        league_factory: LeagueFactory,
        event_dispatcher: EventDispatcher
    ):
        """
        Inicializa o serviço com os repositórios e serviços necessários.
        
        Args:
            futliga_repository: Repositório de ligas personalizadas
            user_repository: Repositório de usuários
            payment_repository: Repositório de pagamentos
            futliga_service: Serviço de domínio para ligas personalizadas
            league_factory: Fábrica para criação de ligas
            event_dispatcher: Despachante de eventos
        """
        self.futliga_repository = futliga_repository
        self.user_repository = user_repository
        self.payment_repository = payment_repository
        self.futliga_service = futliga_service
        self.league_factory = league_factory
        self.event_dispatcher = event_dispatcher
    
    def get_league(self, league_id: int) -> Optional[CustomLeague]:
        """
        Obtém uma liga personalizada pelo ID.
        
        Args:
            league_id: ID da liga
            
        Returns:
            A liga, se encontrada, ou None
        """
        return self.futliga_repository.get_by_id(league_id)
    
    def create_league(
        self,
        name: str,
        owner_id: int,
        level_id: int,
        description: Optional[str] = None,
        image: Optional[str] = None
    ) -> CustomLeague:
        """
        Cria uma nova liga personalizada.
        
        Args:
            name: Nome da liga
            owner_id: ID do proprietário
            level_id: ID do nível
            description: Descrição da liga (opcional)
            image: URL da imagem (opcional)
            
        Returns:
            A liga criada
            
        Raises:
            ValueError: Se os dados fornecidos forem inválidos
            LookupError: Se o usuário ou nível não forem encontrados
        """
        # Validação básica
        if not name:
            raise ValueError("O nome da liga é obrigatório")
        
        # Verifica se o usuário existe
        owner = self.user_repository.get_by_id(owner_id)
        if not owner:
            raise LookupError(f"Usuário com ID {owner_id} não encontrado")
        
        # Verifica se o nível existe
        level = self.futliga_repository.get_level_by_id(level_id)
        if not level:
            raise LookupError(f"Nível com ID {level_id} não encontrado")
        
        # Verifica se o usuário é premium, se necessário
        if level.owner_premium:
            # Verifica se o usuário tem assinatura premium ativa
            if not self.payment_repository.has_active_subscription(owner_id):
                raise ValueError("O nível selecionado requer que o proprietário tenha uma assinatura premium ativa")
        
        # Cria a liga usando a fábrica
        league = self.league_factory.create_league_with_owner(
            name=name,
            owner_id=owner_id,
            level_id=level_id,
            description=description,
            image=image
        )
        
        # Publica evento de criação
        self.event_dispatcher.dispatch(LeagueCreatedEvent(league_id=league.id))
        
        return league
    
    def update_league(self, league_id: int, **kwargs) -> CustomLeague:
        """
        Atualiza uma liga existente.
        
        Args:
            league_id: ID da liga
            **kwargs: Campos a serem atualizados
            
        Returns:
            A liga atualizada
            
        Raises:
            ValueError: Se os dados fornecidos forem inválidos
            LookupError: Se a liga não for encontrada
        """
        # Obtém a liga
        league = self.futliga_repository.get_by_id(league_id)
        if not league:
            raise LookupError(f"Liga com ID {league_id} não encontrada")
        
        # Atualiza os campos
        for key, value in kwargs.items():
            if hasattr(league, key):
                setattr(league, key, value)
        
        # Salva as alterações
        league = self.futliga_repository.update(league)
        
        # Publica evento de atualização
        self.event_dispatcher.dispatch(LeagueUpdatedEvent(league_id=league.id))
        
        return league
    
    def delete_league(self, league_id: int) -> bool:
        """
        Remove uma liga.
        
        Args:
            league_id: ID da liga
            
        Returns:
            True se removida com sucesso, False caso contrário
        """
        return self.futliga_repository.delete(league_id)
    
    def add_member(self, league_id: int, user_id: int, is_admin: bool = False) -> LeagueMember:
        """
        Adiciona um membro a uma liga.
        
        Args:
            league_id: ID da liga
            user_id: ID do usuário
            is_admin: Se o membro é administrador
            
        Returns:
            O membro adicionado
            
        Raises:
            ValueError: Se a liga já estiver cheia ou o usuário já for membro
            LookupError: Se a liga ou usuário não forem encontrados
        """
        # Obtém a liga
        league = self.futliga_repository.get_by_id(league_id)
        if not league:
            raise LookupError(f"Liga com ID {league_id} não encontrada")
        
        # Verifica se o usuário existe
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise LookupError(f"Usuário com ID {user_id} não encontrado")
        
        # Obtém o nível da liga
        level = self.futliga_repository.get_level_by_id(league.level_id)
        if not level:
            raise LookupError(f"Nível com ID {league.level_id} não encontrado")
        
        # Obtém os membros atuais
        members = self.futliga_repository.get_members_by_league(league_id)
        
        # Verifica se o usuário já é membro
        if any(m.user_id == user_id and m.is_active for m in members):
            raise ValueError(f"O usuário com ID {user_id} já é membro desta liga")
        
        # Verifica se a liga está cheia
        active_members = sum(1 for m in members if m.is_active)
        
        # Verifica se o usuário é premium
        is_premium = self.payment_repository.has_active_subscription(user_id)
        max_players = level.premium_players if is_premium else level.players
        
        if active_members >= max_players:
            raise ValueError(f"A liga está cheia. Limite: {max_players} jogadores")
        
        # Cria o membro usando a fábrica
        member = self.league_factory.create_member(
            league_id=league_id,
            user_id=user_id,
            is_owner=False,
            is_admin=is_admin
        )
        
        # Publica evento de adição de membro
        self.event_dispatcher.dispatch(MemberAddedEvent(league_id=league_id, user_id=user_id))
        
        return member
    
    def remove_member(self, league_id: int, user_id: int) -> bool:
        """
        Remove um membro de uma liga.
        
        Args:
            league_id: ID da liga
            user_id: ID do usuário
            
        Returns:
            True se removido com sucesso, False caso contrário
            
        Raises:
            ValueError: Se o usuário for o proprietário da liga
            LookupError: Se a liga ou membro não forem encontrados
        """
        # Obtém a liga
        league = self.futliga_repository.get_by_id(league_id)
        if not league:
            raise LookupError(f"Liga com ID {league_id} não encontrada")
        
        # Verifica se o usuário é o proprietário
        if league.owner_id == user_id:
            raise ValueError("O proprietário da liga não pode ser removido")
        
        # Obtém os membros
        members = self.futliga_repository.get_members_by_league(league_id)
        
        # Busca o membro
        member = next((m for m in members if m.user_id == user_id and m.is_active), None)
        
        if not member:
            raise LookupError(f"Usuário com ID {user_id} não é membro desta liga")
        
        # Desativa o membro
        member.is_active = False
        
        # Atualiza o membro
        self.futliga_repository.add_member(member)
        
        return True
    
    def set_admin_status(self, league_id: int, user_id: int, is_admin: bool) -> LeagueMember:
        """
        Define o status de administrador de um membro.
        
        Args:
            league_id: ID da liga
            user_id: ID do usuário
            is_admin: Se o membro é administrador
            
        Returns:
            O membro atualizado
            
        Raises:
            LookupError: Se a liga ou membro não forem encontrados
        """
        # Obtém os membros
        members = self.futliga_repository.get_members_by_league(league_id)
        
        # Busca o membro
        member = next((m for m in members if m.user_id == user_id and m.is_active), None)
        
        if not member:
            raise LookupError(f"Usuário com ID {user_id} não é membro desta liga")
        
        # Atualiza o status de administrador
        member.is_admin = is_admin
        
        # Atualiza o membro
        self.futliga_repository.add_member(member)
        
        return member
    
    def add_prize(self, league_id: int, position: int, image: Optional[str] = None) -> CustomLeaguePrize:
        """
        Adiciona um prêmio a uma liga.
        
        Args:
            league_id: ID da liga
            position: Posição do prêmio
            image: URL da imagem (opcional)
            
        Returns:
            O prêmio criado
            
        Raises:
            LookupError: Se a liga não for encontrada
            ValueError: Se a posição for inválida
        """
        # Obtém a liga
        league = self.futliga_repository.get_by_id(league_id)
        if not league:
            raise LookupError(f"Liga com ID {league_id} não encontrada")
        
        # Verifica se a posição é válida
        if position < 1:
            raise ValueError("A posição deve ser um número positivo")
        
        # Obtém os prêmios existentes
        prizes = self.futliga_repository.get_prizes_by_league(league_id)
        
        # Verifica se já existe um prêmio para esta posição
        if any(p.position == position for p in prizes):
            raise ValueError(f"Já existe um prêmio para a posição {position}")
        
        # Obtém os níveis para configurar os valores padrão
        levels = self.futliga_repository.get_league_levels()
        
        # Cria o prêmio usando a fábrica
        prize = self.league_factory.create_prize(
            league_id=league_id,
            position=position,
            image=image
        )
        
        # Define os valores padrão para cada nível
        prize = self.league_factory.create_default_prizes([prize], levels)[0]
        
        # Salva o prêmio
        prize = self.futliga_repository.save_prize(prize)
        
        return prize
    
    def update_prize(self, prize_id: int, position: Optional[int] = None, image: Optional[str] = None, values: Optional[Dict[int, float]] = None) -> CustomLeaguePrize:
        """
        Atualiza um prêmio existente.
        
        Args:
            prize_id: ID do prêmio
            position: Nova posição do prêmio (opcional)
            image: Nova URL da imagem (opcional)
            values: Novos valores por nível (opcional)
            
        Returns:
            O prêmio atualizado
            
        Raises:
            LookupError: Se o prêmio não for encontrado
        """
        # Obtém os prêmios
        prizes = []
        found = False
        
        # Busca em todas as ligas (não é eficiente, mas funciona)
        leagues = self.futliga_repository.list()
        for league in leagues:
            league_prizes = self.futliga_repository.get_prizes_by_league(league.id)
            prizes.extend(league_prizes)
            if any(p.id == prize_id for p in league_prizes):
                found = True
        
        if not found:
            raise LookupError(f"Prêmio com ID {prize_id} não encontrado")
        
        # Busca o prêmio
        prize = next((p for p in prizes if p.id == prize_id), None)
        
        # Atualiza os campos
        if position is not None:
            prize.position = position
        
        if image is not None:
            prize.image = image
        
        if values is not None:
            prize.values = values
        
        # Salva o prêmio
        prize = self.futliga_repository.save_prize(prize)
        
        return prize
    
    def delete_prize(self, prize_id: int) -> bool:
        """
        Remove um prêmio.
        
        Args:
            prize_id: ID do prêmio
            
        Returns:
            True se removido com sucesso, False caso contrário
        """
        return self.futliga_repository.delete_prize(prize_id)
    
    def set_award_config(self, league_id: int, weekly: Optional[Dict[str, Any]] = None, season: Optional[Dict[str, Any]] = None) -> AwardConfig:
        """
        Define a configuração de premiação de uma liga.
        
        Args:
            league_id: ID da liga
            weekly: Configuração semanal (opcional)
            season: Configuração da temporada (opcional)
            
        Returns:
            A configuração de premiação
            
        Raises:
            LookupError: Se a liga não for encontrada
        """
        # Obtém a liga
        league = self.futliga_repository.get_by_id(league_id)
        if not league:
            raise LookupError(f"Liga com ID {league_id} não encontrada")
        
        # Cria o objeto de configuração
        config = AwardConfig(weekly=weekly or {}, season=season or {})
        
        # Salva a configuração
        config = self.futliga_repository.save_award_config(league_id, config)
        
        return config
    
    def get_user_leagues(self, user_id: int) -> List[CustomLeague]:
        """
        Obtém todas as ligas das quais um usuário é membro.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Lista de ligas
        """
        return self.futliga_repository.get_leagues_by_user(user_id)
    
    def get_created_leagues(self, user_id: int) -> List[CustomLeague]:
        """
        Obtém todas as ligas criadas por um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Lista de ligas
        """
        return self.futliga_repository.get_leagues_created_by_user(user_id)
    
    def get_league_members(self, league_id: int) -> List[LeagueMember]:
        """
        Obtém todos os membros de uma liga.
        
        Args:
            league_id: ID da liga
            
        Returns:
            Lista de membros
        """
        return self.futliga_repository.get_members_by_league(league_id)
    
    def get_league_prizes(self, league_id: int) -> List[CustomLeaguePrize]:
        """
        Obtém todos os prêmios de uma liga.
        
        Args:
            league_id: ID da liga
            
        Returns:
            Lista de prêmios
        """
        return self.futliga_repository.get_prizes_by_league(league_id)
    
    def list_leagues(self, filters: Optional[Dict] = None, order_by: Optional[str] = None, limit: Optional[int] = None) -> List[CustomLeague]:
        """
        Lista ligas com filtros opcionais.
        
        Args:
            filters: Filtros a serem aplicados
            order_by: Campo para ordenação
            limit: Limite de resultados
            
        Returns:
            Lista de ligas
        """
        return self.futliga_repository.list(filters, order_by, limit)
    
    def get_league_levels(self) -> List[CustomLeagueLevel]:
        """
        Obtém todos os níveis de ligas disponíveis.
        
        Returns:
            Lista de níveis
        """
        return self.futliga_repository.get_league_levels() 