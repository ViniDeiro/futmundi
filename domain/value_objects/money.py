"""
Objeto de valor Money - Representa um valor monetário com moeda.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Union, Optional


@dataclass(frozen=True)
class Money:
    """
    Objeto de valor imutável que representa um valor monetário.
    """
    amount: Decimal
    currency: str = "BRL"
    
    def __init__(self, amount: Union[Decimal, float, int, str], currency: str = "BRL"):
        """
        Inicializa um novo objeto Money.
        
        Args:
            amount: O valor monetário.
            currency: A moeda (padrão: BRL).
        """
        # Como é um dataclass frozen, precisamos fazer atribuição usando __setattr__
        object.__setattr__(self, "amount", Decimal(str(amount)).quantize(Decimal("0.01")))
        object.__setattr__(self, "currency", currency)
    
    def __str__(self) -> str:
        """
        Retorna a representação em string formatada como moeda.
        
        Returns:
            O valor formatado com símbolo da moeda.
        """
        currency_symbols = {
            "BRL": "R$",
            "USD": "$",
            "EUR": "€",
            "GBP": "£"
        }
        
        symbol = currency_symbols.get(self.currency, self.currency)
        return f"{symbol} {self.amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    def __add__(self, other: "Money") -> "Money":
        """
        Soma dois valores monetários.
        
        Args:
            other: Outro objeto Money.
            
        Returns:
            Um novo objeto Money com a soma.
            
        Raises:
            ValueError: Se as moedas forem diferentes.
        """
        if not isinstance(other, Money):
            raise TypeError("Só é possível somar Money com Money")
            
        if self.currency != other.currency:
            raise ValueError("Não é possível somar valores em moedas diferentes")
            
        return Money(self.amount + other.amount, self.currency)
    
    def __sub__(self, other: "Money") -> "Money":
        """
        Subtrai dois valores monetários.
        
        Args:
            other: Outro objeto Money.
            
        Returns:
            Um novo objeto Money com a diferença.
            
        Raises:
            ValueError: Se as moedas forem diferentes.
        """
        if not isinstance(other, Money):
            raise TypeError("Só é possível subtrair Money de Money")
            
        if self.currency != other.currency:
            raise ValueError("Não é possível subtrair valores em moedas diferentes")
            
        return Money(self.amount - other.amount, self.currency)
    
    def __mul__(self, factor: Union[Decimal, float, int]) -> "Money":
        """
        Multiplica o valor monetário por um fator.
        
        Args:
            factor: O fator de multiplicação.
            
        Returns:
            Um novo objeto Money com o valor multiplicado.
        """
        if isinstance(factor, (int, float, Decimal)):
            return Money(self.amount * Decimal(str(factor)), self.currency)
        else:
            raise TypeError("Fator de multiplicação deve ser um número")
    
    def __rmul__(self, factor: Union[Decimal, float, int]) -> "Money":
        """
        Multiplicação reversa.
        
        Args:
            factor: O fator de multiplicação.
            
        Returns:
            Um novo objeto Money com o valor multiplicado.
        """
        return self.__mul__(factor)
    
    def __lt__(self, other: "Money") -> bool:
        """
        Compara se este valor é menor que outro.
        
        Args:
            other: Outro objeto Money.
            
        Returns:
            True se este valor for menor, False caso contrário.
            
        Raises:
            ValueError: Se as moedas forem diferentes.
        """
        if not isinstance(other, Money):
            raise TypeError("Só é possível comparar Money com Money")
            
        if self.currency != other.currency:
            raise ValueError("Não é possível comparar valores em moedas diferentes")
            
        return self.amount < other.amount
    
    def __gt__(self, other: "Money") -> bool:
        """
        Compara se este valor é maior que outro.
        
        Args:
            other: Outro objeto Money.
            
        Returns:
            True se este valor for maior, False caso contrário.
            
        Raises:
            ValueError: Se as moedas forem diferentes.
        """
        if not isinstance(other, Money):
            raise TypeError("Só é possível comparar Money com Money")
            
        if self.currency != other.currency:
            raise ValueError("Não é possível comparar valores em moedas diferentes")
            
        return self.amount > other.amount 