"""
Serviço de Aplicação para gerenciamento de Palpites e seus Casos de Uso.
"""
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta

from domain.repositories.prediction_repository import PredictionRepository
from domain.repositories.championship_repository import ChampionshipRepository
from domain.repositories.user_repository import UserRepository
from domain.services.prediction_service import PredictionService
from domain.entities.prediction import Prediction, PredictionResult
from domain.entities.championship import ChampionshipMatch
from domain.events.prediction_events import PredictionCreatedEvent, PredictionUpdatedEvent, PredictionScoredEvent
from domain.events.event_dispatcher import EventDispatcher


class PredictionAppService:
    """
    Serviço de Aplicação para orquestrar operações relacionadas a palpites.
    """
    
    def __init__(
        self,
        prediction_repository: PredictionRepository,
        championship_repository: ChampionshipRepository,
        user_repository: UserRepository,
        prediction_service: PredictionService,
        event_dispatcher: EventDispatcher
    ):
        """
        Inicializa o serviço com os repositórios e serviços necessários.
        
        Args:
            prediction_repository: Repositório de palpites
            championship_repository: Repositório de campeonatos
            user_repository: Repositório de usuários
            prediction_service: Serviço de domínio para palpites
            event_dispatcher: Despachante de eventos
        """
        self.prediction_repository = prediction_repository
        self.championship_repository = championship_repository
        self.user_repository = user_repository
        self.prediction_service = prediction_service
        self.event_dispatcher = event_dispatcher
    
    def get_prediction(self, prediction_id: int) -> Optional[Prediction]:
        """
        Obtém um palpite pelo ID.
        
        Args:
            prediction_id: ID do palpite
            
        Returns:
            O palpite, se encontrado, ou None
        """
        return self.prediction_repository.get_by_id(prediction_id)
    
    def create_prediction(
        self,
        user_id: int,
        match_id: int,
        home_score: int,
        away_score: int
    ) -> Prediction:
        """
        Cria um novo palpite.
        
        Args:
            user_id: ID do usuário
            match_id: ID da partida
            home_score: Placar da equipe da casa
            away_score: Placar da equipe visitante
            
        Returns:
            O palpite criado
            
        Raises:
            ValueError: Se os dados fornecidos forem inválidos
            LookupError: Se o usuário ou partida não forem encontrados
        """
        # Verifica se o usuário existe
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise LookupError(f"Usuário com ID {user_id} não encontrado")
        
        # Verifica se a partida existe
        match = self.championship_repository.get_match_by_id(match_id)
        if not match:
            raise LookupError(f"Partida com ID {match_id} não encontrada")
        
        # Verifica se a partida ainda não começou
        if match.match_date <= datetime.now():
            raise ValueError("Não é possível criar palpites para partidas que já começaram")
        
        # Verifica se já existe um palpite para esta partida e usuário
        existing = self.prediction_repository.get_by_user_and_match(user_id, match_id)
        if existing:
            raise ValueError("Já existe um palpite para esta partida")
        
        # Validação básica
        if home_score < 0 or away_score < 0:
            raise ValueError("Os placares não podem ser negativos")
        
        # Cria o palpite
        prediction = Prediction(
            id=None,
            user_id=user_id,
            match_id=match_id,
            home_score=home_score,
            away_score=away_score,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            points=None,
            result=None
        )
        
        # Salva o palpite
        prediction = self.prediction_repository.create(prediction)
        
        # Publica evento de criação
        self.event_dispatcher.dispatch(PredictionCreatedEvent(prediction_id=prediction.id))
        
        return prediction
    
    def update_prediction(
        self,
        prediction_id: int,
        home_score: int,
        away_score: int
    ) -> Prediction:
        """
        Atualiza um palpite existente.
        
        Args:
            prediction_id: ID do palpite
            home_score: Novo placar da equipe da casa
            away_score: Novo placar da equipe visitante
            
        Returns:
            O palpite atualizado
            
        Raises:
            ValueError: Se os dados fornecidos forem inválidos
            LookupError: Se o palpite não for encontrado
        """
        # Obtém o palpite
        prediction = self.prediction_repository.get_by_id(prediction_id)
        if not prediction:
            raise LookupError(f"Palpite com ID {prediction_id} não encontrado")
        
        # Verifica se a partida existe
        match = self.championship_repository.get_match_by_id(prediction.match_id)
        if not match:
            raise LookupError(f"Partida com ID {prediction.match_id} não encontrada")
        
        # Verifica se a partida ainda não começou
        if match.match_date <= datetime.now():
            raise ValueError("Não é possível atualizar palpites para partidas que já começaram")
        
        # Validação básica
        if home_score < 0 or away_score < 0:
            raise ValueError("Os placares não podem ser negativos")
        
        # Atualiza o palpite
        prediction.home_score = home_score
        prediction.away_score = away_score
        prediction.updated_at = datetime.now()
        
        # Salva as alterações
        prediction = self.prediction_repository.update(prediction)
        
        # Publica evento de atualização
        self.event_dispatcher.dispatch(PredictionUpdatedEvent(prediction_id=prediction.id))
        
        return prediction
    
    def delete_prediction(self, prediction_id: int) -> bool:
        """
        Remove um palpite.
        
        Args:
            prediction_id: ID do palpite
            
        Returns:
            True se removido com sucesso, False caso contrário
        """
        # Obtém o palpite
        prediction = self.prediction_repository.get_by_id(prediction_id)
        if not prediction:
            return False
        
        # Verifica se a partida existe
        match = self.championship_repository.get_match_by_id(prediction.match_id)
        if not match:
            return False
        
        # Verifica se a partida ainda não começou
        if match.match_date <= datetime.now():
            raise ValueError("Não é possível remover palpites para partidas que já começaram")
        
        # Remove o palpite
        return self.prediction_repository.delete(prediction_id)
    
    def score_prediction(self, prediction_id: int) -> Prediction:
        """
        Calcula a pontuação de um palpite.
        
        Args:
            prediction_id: ID do palpite
            
        Returns:
            O palpite com pontuação atualizada
            
        Raises:
            ValueError: Se a partida ainda não terminou
            LookupError: Se o palpite não for encontrado
        """
        # Obtém o palpite
        prediction = self.prediction_repository.get_by_id(prediction_id)
        if not prediction:
            raise LookupError(f"Palpite com ID {prediction_id} não encontrado")
        
        # Verifica se a partida existe
        match = self.championship_repository.get_match_by_id(prediction.match_id)
        if not match:
            raise LookupError(f"Partida com ID {prediction.match_id} não encontrada")
        
        # Verifica se a partida terminou
        if match.status != "finished":
            raise ValueError("Não é possível calcular pontuação para partidas que ainda não terminaram")
        
        # Calcula a pontuação
        points, result = self.prediction_service.calculate_points(
            prediction.home_score,
            prediction.away_score,
            match.home_score,
            match.away_score
        )
        
        # Atualiza o palpite
        prediction.points = points
        prediction.result = result
        
        # Salva as alterações
        prediction = self.prediction_repository.update(prediction)
        
        # Publica evento de pontuação
        self.event_dispatcher.dispatch(PredictionScoredEvent(
            prediction_id=prediction.id,
            points=points,
            result=result
        ))
        
        return prediction
    
    def score_all_predictions_for_match(self, match_id: int) -> List[Prediction]:
        """
        Calcula a pontuação de todos os palpites para uma partida.
        
        Args:
            match_id: ID da partida
            
        Returns:
            Lista de palpites com pontuação atualizada
            
        Raises:
            ValueError: Se a partida ainda não terminou
            LookupError: Se a partida não for encontrada
        """
        # Verifica se a partida existe
        match = self.championship_repository.get_match_by_id(match_id)
        if not match:
            raise LookupError(f"Partida com ID {match_id} não encontrada")
        
        # Verifica se a partida terminou
        if match.status != "finished":
            raise ValueError("Não é possível calcular pontuação para partidas que ainda não terminaram")
        
        # Obtém todos os palpites para a partida
        predictions = self.prediction_repository.get_by_match(match_id)
        
        # Calcula a pontuação para cada palpite
        scored_predictions = []
        for prediction in predictions:
            points, result = self.prediction_service.calculate_points(
                prediction.home_score,
                prediction.away_score,
                match.home_score,
                match.away_score
            )
            
            # Atualiza o palpite
            prediction.points = points
            prediction.result = result
            
            # Salva as alterações
            prediction = self.prediction_repository.update(prediction)
            
            # Publica evento de pontuação
            self.event_dispatcher.dispatch(PredictionScoredEvent(
                prediction_id=prediction.id,
                points=points,
                result=result
            ))
            
            scored_predictions.append(prediction)
        
        return scored_predictions
    
    def get_user_predictions(self, user_id: int, limit: Optional[int] = None) -> List[Prediction]:
        """
        Obtém os palpites de um usuário.
        
        Args:
            user_id: ID do usuário
            limit: Limite de resultados
            
        Returns:
            Lista de palpites
        """
        return self.prediction_repository.get_by_user(user_id, limit=limit)
    
    def get_user_predictions_for_round(self, user_id: int, round_id: int) -> List[Prediction]:
        """
        Obtém os palpites de um usuário para uma rodada específica.
        
        Args:
            user_id: ID do usuário
            round_id: ID da rodada
            
        Returns:
            Lista de palpites
        """
        # Obtém todas as partidas da rodada
        matches = self.championship_repository.get_matches_by_round(round_id)
        match_ids = [match.id for match in matches]
        
        # Obtém os palpites para estas partidas
        if match_ids:
            return self.prediction_repository.get_by_user_and_matches(user_id, match_ids)
        
        return []
    
    def get_user_points(self, user_id: int, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> int:
        """
        Obtém a pontuação total de um usuário em um intervalo de datas.
        
        Args:
            user_id: ID do usuário
            start_date: Data inicial (opcional)
            end_date: Data final (opcional)
            
        Returns:
            Pontuação total
        """
        # Define datas padrão se não fornecidas
        if not start_date:
            start_date = datetime(2000, 1, 1)
        
        if not end_date:
            end_date = datetime.now() + timedelta(days=1)
        
        # Obtém os palpites no intervalo
        predictions = self.prediction_repository.get_by_user_in_date_range(user_id, start_date, end_date)
        
        # Calcula a pontuação total
        return sum(p.points or 0 for p in predictions)
    
    def get_ranking(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Obtém o ranking de usuários em um intervalo de datas.
        
        Args:
            start_date: Data inicial (opcional)
            end_date: Data final (opcional)
            limit: Limite de resultados (opcional)
            
        Returns:
            Lista de dicionários com ID do usuário e pontuação
        """
        return self.prediction_repository.get_ranking(start_date, end_date, limit)
    
    def get_prediction_stats(self, user_id: int) -> Dict[str, int]:
        """
        Obtém estatísticas de palpites de um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dicionário com estatísticas (total, acertos, parciais, erros)
        """
        # Obtém todos os palpites pontuados do usuário
        predictions = self.prediction_repository.get_scored_by_user(user_id)
        
        # Inicializa estatísticas
        stats = {
            "total": len(predictions),
            "exact": 0,
            "partial": 0,
            "miss": 0
        }
        
        # Calcula estatísticas
        for prediction in predictions:
            if prediction.result == PredictionResult.EXACT:
                stats["exact"] += 1
            elif prediction.result == PredictionResult.PARTIAL:
                stats["partial"] += 1
            elif prediction.result == PredictionResult.MISS:
                stats["miss"] += 1
        
        return stats
    
    def get_available_matches_for_prediction(self, user_id: int) -> List[ChampionshipMatch]:
        """
        Obtém as partidas disponíveis para palpite de um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Lista de partidas disponíveis
        """
        # Obtém as partidas futuras
        now = datetime.now()
        matches = self.championship_repository.get_matches_by_date_range(
            now,
            now + timedelta(days=7)
        )
        
        # Filtra partidas não terminadas
        available_matches = [m for m in matches if m.status != "finished"]
        
        # Obtém os palpites existentes do usuário
        user_predictions = self.prediction_repository.get_by_user(user_id)
        predicted_match_ids = [p.match_id for p in user_predictions]
        
        # Remove partidas já palpitadas
        return [m for m in available_matches if m.id not in predicted_match_ids] 