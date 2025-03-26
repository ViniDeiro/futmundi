"""
Serviço de aplicação para operações de pagamentos.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from domain.entities.payment import Payment, PaymentMethod, Subscription, SubscriptionPlan
from domain.repositories.payment_repository import PaymentRepository


class PaymentAppService:
    """
    Serviço de aplicação para gerenciar operações de pagamentos.
    """

    def __init__(self, payment_repository: PaymentRepository):
        """
        Inicializa o serviço de aplicação de pagamentos.

        Args:
            payment_repository: Repositório de pagamentos.
        """
        self._payment_repository = payment_repository

    def get_user_payment_history(self, user_id: int) -> List[Payment]:
        """
        Obtém o histórico de pagamentos de um usuário.

        Args:
            user_id: ID do usuário.

        Returns:
            Lista de pagamentos do usuário.
        """
        return self._payment_repository.get_by_user_id(user_id)

    def get_payment_by_transaction_id(self, transaction_id: str) -> Optional[Payment]:
        """
        Obtém um pagamento pelo ID da transação.

        Args:
            transaction_id: ID da transação.

        Returns:
            O pagamento encontrado ou None.
        """
        return self._payment_repository.get_by_transaction_id(transaction_id)

    def get_user_payment_methods(self, user_id: int) -> List[PaymentMethod]:
        """
        Obtém os métodos de pagamento de um usuário.

        Args:
            user_id: ID do usuário.

        Returns:
            Lista de métodos de pagamento.
        """
        return self._payment_repository.get_payment_methods_by_user(user_id)

    def add_payment_method(self, user_id: int, type: str, last_digits: str, holder_name: str,
                          expiry_date: Optional[datetime] = None, is_default: bool = False) -> PaymentMethod:
        """
        Adiciona um novo método de pagamento para um usuário.

        Args:
            user_id: ID do usuário.
            type: Tipo do método de pagamento (ex: "credit_card", "debit_card").
            last_digits: Últimos dígitos do cartão/conta.
            holder_name: Nome do titular.
            expiry_date: Data de expiração (opcional).
            is_default: Se é o método padrão (opcional).

        Returns:
            O método de pagamento adicionado.
        """
        # Criar o objeto PaymentMethod
        payment_method = PaymentMethod(
            id=None,  # Será atribuído pelo repositório
            user_id=user_id,
            type=type,
            last_digits=last_digits,
            holder_name=holder_name,
            expiry_date=expiry_date,
            is_default=is_default,
            created_at=datetime.now()
        )
        
        # Se for definido como padrão, atualizar os outros métodos
        if is_default:
            existing_methods = self.get_user_payment_methods(user_id)
            for method in existing_methods:
                if method.is_default:
                    method.is_default = False
                    self._payment_repository.update(method)
        
        return self._payment_repository.add_payment_method(user_id, payment_method)

    def remove_payment_method(self, user_id: int, payment_method_id: int) -> bool:
        """
        Remove um método de pagamento de um usuário.

        Args:
            user_id: ID do usuário.
            payment_method_id: ID do método de pagamento.

        Returns:
            True se removido com sucesso, False caso contrário.
        """
        return self._payment_repository.remove_payment_method(payment_method_id, user_id)

    def get_subscription_plans(self) -> List[SubscriptionPlan]:
        """
        Obtém todos os planos de assinatura disponíveis.

        Returns:
            Lista de planos de assinatura.
        """
        return self._payment_repository.get_all_subscription_plans()

    def get_subscription_plan_by_id(self, plan_id: int) -> Optional[SubscriptionPlan]:
        """
        Obtém um plano de assinatura pelo ID.

        Args:
            plan_id: ID do plano de assinatura.

        Returns:
            O plano de assinatura encontrado ou None.
        """
        return self._payment_repository.get_subscription_plan_by_id(plan_id)

    def get_user_subscription(self, user_id: int) -> Optional[Subscription]:
        """
        Obtém a assinatura ativa de um usuário.

        Args:
            user_id: ID do usuário.

        Returns:
            A assinatura ativa ou None.
        """
        return self._payment_repository.get_user_subscription(user_id)

    def process_subscription_payment(self, user_id: int, plan_id: int, payment_method_id: int) -> Dict[str, Any]:
        """
        Processa o pagamento de uma assinatura.

        Args:
            user_id: ID do usuário.
            plan_id: ID do plano de assinatura.
            payment_method_id: ID do método de pagamento.

        Returns:
            Dicionário com o resultado do processamento.
        """
        # Verificar se o plano existe
        plan = self.get_subscription_plan_by_id(plan_id)
        if not plan:
            return {
                'success': False,
                'error_code': 'invalid_plan',
                'message': 'Plano de assinatura inválido'
            }
        
        # Verificar se o método de pagamento existe e pertence ao usuário
        payment_method = self._payment_repository.get_payment_method_by_id(payment_method_id)
        if not payment_method or payment_method.user_id != user_id:
            return {
                'success': False,
                'error_code': 'invalid_payment_method',
                'message': 'Método de pagamento inválido ou não pertence ao usuário'
            }
        
        # Verificar se o usuário já tem uma assinatura ativa
        current_subscription = self.get_user_subscription(user_id)
        if current_subscription and current_subscription.is_active:
            # Cancelar assinatura atual se estiver ativa
            self.cancel_user_subscription(user_id)
        
        # Criar nova assinatura
        subscription = self._payment_repository.create_subscription(user_id, plan_id, payment_method_id)
        if not subscription:
            return {
                'success': False,
                'error_code': 'subscription_creation_failed',
                'message': 'Falha ao criar assinatura'
            }
        
        # Criar o pagamento
        payment = Payment(
            id=None,  # Será atribuído pelo repositório
            user_id=user_id,
            amount=plan.price,
            currency=plan.currency,
            payment_method_id=payment_method_id,
            payment_method_last_digits=payment_method.last_digits,
            description=f"Assinatura - {plan.name}",
            payment_date=datetime.now(),
            status='completed',
            transaction_id=f"SUB-{datetime.now().strftime('%Y%m%d%H%M%S')}-{user_id}",
            created_at=datetime.now()
        )
        
        # Processar o pagamento
        payment_result = self._payment_repository.process_payment(payment)
        
        if payment_result.get('success', False):
            return {
                'success': True,
                'transaction_id': payment.transaction_id,
                'subscription_id': subscription.id,
                'message': 'Assinatura processada com sucesso'
            }
        else:
            # Se o pagamento falhar, cancelar a assinatura
            self._payment_repository.cancel_subscription(subscription.id, user_id)
            return {
                'success': False,
                'error_code': 'payment_failed',
                'message': payment_result.get('message', 'Falha no processamento do pagamento')
            }

    def cancel_user_subscription(self, user_id: int) -> bool:
        """
        Cancela a assinatura de um usuário.

        Args:
            user_id: ID do usuário.

        Returns:
            True se cancelada com sucesso, False caso contrário.
        """
        subscription = self.get_user_subscription(user_id)
        if not subscription:
            return False
        
        return self._payment_repository.cancel_subscription(subscription.id, user_id)

    def get_payment_statistics(self) -> Dict[str, Any]:
        """
        Obtém estatísticas de pagamentos para o dashboard administrativo.

        Returns:
            Dicionário com estatísticas de pagamentos.
        """
        # Este método normalmente seria implementado com consultas específicas ao banco de dados
        # Por simplicidade, retornamos valores fictícios
        today = datetime.now().date()
        
        return {
            'users_today': 5,
            'revenue_today': 500.00,
            'revenue_month': 12500.00,
            'active_subscriptions': 150
        } 