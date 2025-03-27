"""
Entidades de Pagamento - Representam elementos relacionados a pagamentos e produtos.
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class FutcoinPackage:
    """
    Entidade que representa um pacote de Futcoins disponível para compra.
    """
    id: int
    name: str
    quantity: int
    price: float
    is_active: bool = True
    discount_percentage: float = 0
    image: Optional[str] = None
    
    @property
    def final_price(self) -> float:
        """Calcula o preço final com desconto."""
        if self.discount_percentage > 0:
            return self.price * (1 - (self.discount_percentage / 100))
        return self.price


@dataclass
class SubscriptionPlan:
    """
    Entidade que representa um plano de assinatura disponível para compra.
    """
    id: int
    name: str
    description: str
    price: float
    duration_days: int
    is_active: bool = True
    futcoins: int = 0
    discount_percentage: float = 0
    image: Optional[str] = None
    features: List[str] = None
    
    def __post_init__(self):
        if self.features is None:
            self.features = []
    
    @property
    def final_price(self) -> float:
        """Calcula o preço final com desconto."""
        if self.discount_percentage > 0:
            return self.price * (1 - (self.discount_percentage / 100))
        return self.price


@dataclass
class PaymentMethod:
    """
    Entidade que representa um método de pagamento cadastrado por um usuário.
    """
    id: int
    user_id: int
    type: str  # credit_card, debit_card, pix, etc.
    is_default: bool = False
    created_at: datetime = None
    last_used_at: Optional[datetime] = None
    
    # Campos para cartão de crédito/débito
    card_brand: Optional[str] = None
    card_last_digits: Optional[str] = None
    card_expiry: Optional[str] = None
    
    # Campo para outros detalhes específicos do método de pagamento
    details: Optional[dict] = None


@dataclass
class Payment:
    """
    Entidade que representa um pagamento realizado no sistema.
    """
    id: int
    user_id: int
    amount: float
    payment_method_id: Optional[int] = None
    status: str = "pending"  # pending, completed, failed, refunded
    transaction_id: Optional[str] = None
    created_at: datetime = None
    updated_at: Optional[datetime] = None
    details: Optional[dict] = None
    
    # Referências para outros objetos
    payment_method: Optional[PaymentMethod] = None


@dataclass
class Subscription:
    """
    Entidade que representa uma assinatura de um usuário.
    """
    id: int
    user_id: int
    plan_id: int
    start_date: datetime
    end_date: datetime
    status: str = "active"  # active, cancelled, expired
    auto_renew: bool = True
    payment_method_id: Optional[int] = None
    created_at: datetime = None
    cancelled_at: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None
    
    # Referências para outros objetos
    plan: Optional[SubscriptionPlan] = None
    payment_method: Optional[PaymentMethod] = None


@dataclass
class Transaction:
    """
    Entidade que representa uma transação financeira no sistema.
    """
    id: int
    user_id: int
    amount: float
    type: str  # purchase, subscription, bonus, etc.
    status: str  # pending, completed, failed, refunded
    payment_method: Optional[str] = None
    transaction_date: datetime = None
    details: Optional[str] = None
    reference_id: Optional[str] = None  # ID da transação externa (gateway de pagamento)
    futcoins_amount: int = 0 