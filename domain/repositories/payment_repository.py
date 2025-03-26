"""
Repositório para operações em pagamentos.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from domain.entities.payment import Payment, PaymentMethod, Subscription, SubscriptionPlan
from domain.repositories.base_repository import BaseRepository


class PaymentRepository(BaseRepository[Payment], ABC):
    """
    Repositório para gerenciar pagamentos.
    """

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> List[Payment]:
        """
        Obtém todos os pagamentos de um usuário.

        Args:
            user_id: ID do usuário.

        Returns:
            Lista de pagamentos.
        """
        pass

    @abstractmethod
    def get_by_transaction_id(self, transaction_id: str) -> Optional[Payment]:
        """
        Obtém um pagamento pelo ID da transação.

        Args:
            transaction_id: ID da transação.

        Returns:
            O pagamento encontrado ou None.
        """
        pass

    @abstractmethod
    def get_payment_methods_by_user(self, user_id: int) -> List[PaymentMethod]:
        """
        Obtém todos os métodos de pagamento de um usuário.

        Args:
            user_id: ID do usuário.

        Returns:
            Lista de métodos de pagamento.
        """
        pass

    @abstractmethod
    def get_payment_method_by_id(self, method_id: int) -> Optional[PaymentMethod]:
        """
        Obtém um método de pagamento pelo ID.

        Args:
            method_id: ID do método de pagamento.

        Returns:
            O método de pagamento encontrado ou None.
        """
        pass

    @abstractmethod
    def add_payment_method(self, user_id: int, payment_method: PaymentMethod) -> PaymentMethod:
        """
        Adiciona um novo método de pagamento para um usuário.

        Args:
            user_id: ID do usuário.
            payment_method: Método de pagamento a ser adicionado.

        Returns:
            O método de pagamento adicionado.
        """
        pass

    @abstractmethod
    def remove_payment_method(self, method_id: int, user_id: int) -> bool:
        """
        Remove um método de pagamento.

        Args:
            method_id: ID do método de pagamento.
            user_id: ID do usuário (para verificação de propriedade).

        Returns:
            True se removido com sucesso, False caso contrário.
        """
        pass

    @abstractmethod
    def get_all_subscription_plans(self) -> List[SubscriptionPlan]:
        """
        Obtém todos os planos de assinatura disponíveis.

        Returns:
            Lista de planos de assinatura.
        """
        pass

    @abstractmethod
    def get_subscription_plan_by_id(self, plan_id: int) -> Optional[SubscriptionPlan]:
        """
        Obtém um plano de assinatura pelo ID.

        Args:
            plan_id: ID do plano de assinatura.

        Returns:
            O plano de assinatura encontrado ou None.
        """
        pass

    @abstractmethod
    def get_user_subscription(self, user_id: int) -> Optional[Subscription]:
        """
        Obtém a assinatura ativa de um usuário.

        Args:
            user_id: ID do usuário.

        Returns:
            A assinatura ativa ou None.
        """
        pass

    @abstractmethod
    def create_subscription(self, user_id: int, plan_id: int, payment_method_id: int) -> Optional[Subscription]:
        """
        Cria uma nova assinatura para um usuário.

        Args:
            user_id: ID do usuário.
            plan_id: ID do plano de assinatura.
            payment_method_id: ID do método de pagamento.

        Returns:
            A assinatura criada ou None em caso de falha.
        """
        pass

    @abstractmethod
    def cancel_subscription(self, subscription_id: int, user_id: int) -> bool:
        """
        Cancela uma assinatura.

        Args:
            subscription_id: ID da assinatura.
            user_id: ID do usuário (para verificação de propriedade).

        Returns:
            True se cancelada com sucesso, False caso contrário.
        """
        pass

    @abstractmethod
    def process_payment(self, payment: Payment) -> Dict[str, Any]:
        """
        Processa um pagamento.

        Args:
            payment: Objeto Payment com os dados do pagamento.

        Returns:
            Dicionário com o resultado do processamento.
        """
        pass 