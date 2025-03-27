"""
Serviço de domínio para operações com pagamentos.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from domain.repositories.payment_repository import PaymentRepository
from domain.entities.payment import Payment, PaymentMethod, Subscription, SubscriptionPlan


class PaymentService:
    """
    Serviço de domínio para lógica de negócio relacionada a pagamentos.
    """
    
    def __init__(self, payment_repository: PaymentRepository):
        self.payment_repository = payment_repository
    
    def get_payment_methods(self, user_id: int) -> List[PaymentMethod]:
        """
        Obtém os métodos de pagamento de um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Lista de métodos de pagamento
        """
        return self.payment_repository.get_payment_methods_by_user(user_id)
    
    def add_payment_method(self, user_id: int, payment_method: PaymentMethod) -> PaymentMethod:
        """
        Adiciona um método de pagamento para um usuário.
        
        Args:
            user_id: ID do usuário
            payment_method: Método de pagamento a ser adicionado
            
        Returns:
            O método de pagamento adicionado
        """
        # Validações
        if not payment_method.type:
            raise ValueError("O tipo de método de pagamento é obrigatório")
        
        # Adiciona o método de pagamento
        return self.payment_repository.add_payment_method(user_id, payment_method)
    
    def remove_payment_method(self, method_id: int, user_id: int) -> bool:
        """
        Remove um método de pagamento de um usuário.
        
        Args:
            method_id: ID do método de pagamento
            user_id: ID do usuário
            
        Returns:
            True se removido com sucesso, False caso contrário
        """
        # Verifica se o método de pagamento pertence ao usuário
        method = self.payment_repository.get_payment_method_by_id(method_id)
        if not method or method.user_id != user_id:
            raise ValueError("Método de pagamento não encontrado ou não pertence ao usuário")
        
        return self.payment_repository.remove_payment_method(method_id, user_id)
    
    def get_subscription_plans(self) -> List[SubscriptionPlan]:
        """
        Obtém todos os planos de assinatura disponíveis.
        
        Returns:
            Lista de planos de assinatura
        """
        return self.payment_repository.get_all_subscription_plans()
    
    def get_user_subscription(self, user_id: int) -> Optional[Subscription]:
        """
        Obtém a assinatura ativa de um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            A assinatura ativa ou None
        """
        return self.payment_repository.get_user_subscription(user_id)
    
    def create_subscription(self, user_id: int, plan_id: int, payment_method_id: int) -> Subscription:
        """
        Cria uma assinatura para um usuário.
        
        Args:
            user_id: ID do usuário
            plan_id: ID do plano
            payment_method_id: ID do método de pagamento
            
        Returns:
            A assinatura criada
            
        Raises:
            ValueError: Se os dados forem inválidos ou se o usuário já tiver uma assinatura ativa
        """
        # Verifica se o usuário já tem uma assinatura ativa
        current_subscription = self.payment_repository.get_user_subscription(user_id)
        if current_subscription and current_subscription.status == "active":
            raise ValueError("O usuário já possui uma assinatura ativa")
        
        # Verifica se o plano existe
        plan = self.payment_repository.get_subscription_plan_by_id(plan_id)
        if not plan:
            raise ValueError(f"Plano com ID {plan_id} não encontrado")
        
        # Verifica se o método de pagamento existe e pertence ao usuário
        payment_method = self.payment_repository.get_payment_method_by_id(payment_method_id)
        if not payment_method or payment_method.user_id != user_id:
            raise ValueError(f"Método de pagamento não encontrado ou não pertence ao usuário")
        
        # Cria a assinatura
        subscription = self.payment_repository.create_subscription(user_id, plan_id, payment_method_id)
        if not subscription:
            raise RuntimeError("Falha ao criar assinatura")
        
        return subscription
    
    def cancel_subscription(self, subscription_id: int, user_id: int) -> bool:
        """
        Cancela uma assinatura.
        
        Args:
            subscription_id: ID da assinatura
            user_id: ID do usuário
            
        Returns:
            True se cancelada com sucesso, False caso contrário
            
        Raises:
            ValueError: Se a assinatura não existir ou não pertencer ao usuário
        """
        # Verifica se a assinatura existe e pertence ao usuário
        subscription = self.payment_repository.get_user_subscription(user_id)
        if not subscription or subscription.id != subscription_id:
            raise ValueError("Assinatura não encontrada ou não pertence ao usuário")
        
        if subscription.status != "active":
            raise ValueError("Assinatura já está cancelada ou expirada")
        
        return self.payment_repository.cancel_subscription(subscription_id, user_id)
    
    def process_payment(self, payment: Payment) -> Dict[str, Any]:
        """
        Processa um pagamento.
        
        Args:
            payment: Dados do pagamento
            
        Returns:
            Resultado do processamento
            
        Raises:
            ValueError: Se os dados do pagamento forem inválidos
        """
        # Validações
        if payment.amount <= 0:
            raise ValueError("O valor do pagamento deve ser maior que zero")
        
        if not payment.payment_method_id:
            raise ValueError("Método de pagamento não especificado")
        
        # Processa o pagamento
        return self.payment_repository.process_payment(payment) 