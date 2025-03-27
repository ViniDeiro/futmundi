"""
Agregado de Usuário - Representa um usuário e todos os seus dados relacionados como uma unidade consistente.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

from domain.entities.user import User
from domain.entities.payment import Subscription, PaymentMethod


@dataclass
class UserAggregate:
    """
    Agregado que encapsula um usuário e seus dados relacionados.
    Serve como raiz de agregação, mantendo a consistência entre o usuário e suas entidades relacionadas.
    """
    user: User
    subscription: Optional[Subscription] = None
    payment_methods: List[PaymentMethod] = field(default_factory=list)
    prediction_stats: Optional[Dict[str, Any]] = None
    leagues: List[Any] = field(default_factory=list)
    
    def add_payment_method(self, payment_method: PaymentMethod) -> None:
        """
        Adiciona um método de pagamento ao usuário.
        
        Args:
            payment_method: O método de pagamento a ser adicionado
        """
        # Verifica se é o primeiro método de pagamento
        is_first = len(self.payment_methods) == 0
        
        # Se for o primeiro, define como padrão
        if is_first:
            payment_method.is_default = True
        
        self.payment_methods.append(payment_method)
    
    def remove_payment_method(self, payment_method_id: int) -> bool:
        """
        Remove um método de pagamento do usuário.
        
        Args:
            payment_method_id: ID do método de pagamento a ser removido
            
        Returns:
            True se removido com sucesso, False caso contrário
        """
        for i, method in enumerate(self.payment_methods):
            if method.id == payment_method_id:
                # Se estiver removendo o método padrão e houver outros, define outro como padrão
                if method.is_default and len(self.payment_methods) > 1:
                    # Encontra o próximo método para definir como padrão
                    next_index = 0 if i == len(self.payment_methods) - 1 else i + 1
                    self.payment_methods[next_index].is_default = True
                
                # Remove o método
                self.payment_methods.pop(i)
                return True
        
        return False
    
    def set_subscription(self, subscription: Subscription) -> None:
        """
        Define a assinatura do usuário.
        
        Args:
            subscription: A assinatura a ser definida
        """
        self.subscription = subscription
    
    def cancel_subscription(self) -> None:
        """
        Cancela a assinatura atual do usuário.
        """
        if self.subscription:
            self.subscription.status = "cancelled"
            self.subscription.cancelled_at = datetime.now()
    
    def add_to_league(self, league: Any) -> None:
        """
        Adiciona o usuário a uma liga.
        
        Args:
            league: A liga a ser adicionada
        """
        self.leagues.append(league)
    
    def remove_from_league(self, league_id: int) -> bool:
        """
        Remove o usuário de uma liga.
        
        Args:
            league_id: ID da liga a ser removida
            
        Returns:
            True se removido com sucesso, False caso contrário
        """
        for i, league in enumerate(self.leagues):
            if league.id == league_id:
                self.leagues.pop(i)
                return True
        
        return False
    
    def update_prediction_stats(self, stats: Dict[str, Any]) -> None:
        """
        Atualiza as estatísticas de previsões do usuário.
        
        Args:
            stats: As estatísticas a serem atualizadas
        """
        if not self.prediction_stats:
            self.prediction_stats = {}
        
        self.prediction_stats.update(stats) 