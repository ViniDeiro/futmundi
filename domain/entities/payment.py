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
class Plan:
    """
    Entidade que representa um plano de assinatura.
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
    
    @property
    def final_price(self) -> float:
        """Calcula o preço final com desconto."""
        if self.discount_percentage > 0:
            return self.price * (1 - (self.discount_percentage / 100))
        return self.price


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