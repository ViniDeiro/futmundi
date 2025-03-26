"""
Objeto de valor Score - Representa uma pontuação com categoria.
"""
from dataclasses import dataclass
from typing import Optional, Union, Dict


@dataclass(frozen=True)
class Score:
    """
    Objeto de valor imutável que representa uma pontuação.
    Pode incluir pontuações por categoria.
    """
    total: int
    categories: Dict[str, int] = None
    
    def __init__(self, total: int, categories: Optional[Dict[str, int]] = None):
        """
        Inicializa um novo objeto Score.
        
        Args:
            total: A pontuação total.
            categories: Um dicionário com pontuações por categoria.
        """
        object.__setattr__(self, "total", total)
        
        if categories is None:
            categories = {}
        object.__setattr__(self, "categories", categories)
    
    def __str__(self) -> str:
        """
        Retorna a representação em string.
        
        Returns:
            A pontuação formatada.
        """
        if not self.categories:
            return f"{self.total} pts"
        
        category_str = ", ".join(f"{cat}: {pts} pts" for cat, pts in self.categories.items())
        return f"{self.total} pts ({category_str})"
    
    def __add__(self, other: Union["Score", int]) -> "Score":
        """
        Soma duas pontuações.
        
        Args:
            other: Outra pontuação ou um valor inteiro.
            
        Returns:
            Uma nova pontuação com a soma.
        """
        if isinstance(other, int):
            return Score(self.total + other, self.categories.copy() if self.categories else None)
        
        if not isinstance(other, Score):
            raise TypeError("Só é possível somar Score com Score ou int")
        
        # Soma as categorias
        new_categories = self.categories.copy() if self.categories else {}
        for cat, pts in (other.categories or {}).items():
            if cat in new_categories:
                new_categories[cat] += pts
            else:
                new_categories[cat] = pts
                
        return Score(self.total + other.total, new_categories)
    
    def __sub__(self, other: Union["Score", int]) -> "Score":
        """
        Subtrai duas pontuações.
        
        Args:
            other: Outra pontuação ou um valor inteiro.
            
        Returns:
            Uma nova pontuação com a diferença.
        """
        if isinstance(other, int):
            return Score(self.total - other, self.categories.copy() if self.categories else None)
        
        if not isinstance(other, Score):
            raise TypeError("Só é possível subtrair Score de Score ou int")
        
        # Subtrai as categorias
        new_categories = self.categories.copy() if self.categories else {}
        for cat, pts in (other.categories or {}).items():
            if cat in new_categories:
                new_categories[cat] = max(0, new_categories[cat] - pts)
            
        return Score(max(0, self.total - other.total), new_categories)
    
    def __lt__(self, other: Union["Score", int]) -> bool:
        """
        Compara se esta pontuação é menor que outra.
        
        Args:
            other: Outra pontuação ou um valor inteiro.
            
        Returns:
            True se esta pontuação for menor, False caso contrário.
        """
        if isinstance(other, int):
            return self.total < other
        
        if not isinstance(other, Score):
            raise TypeError("Só é possível comparar Score com Score ou int")
            
        return self.total < other.total
    
    def __gt__(self, other: Union["Score", int]) -> bool:
        """
        Compara se esta pontuação é maior que outra.
        
        Args:
            other: Outra pontuação ou um valor inteiro.
            
        Returns:
            True se esta pontuação for maior, False caso contrário.
        """
        if isinstance(other, int):
            return self.total > other
        
        if not isinstance(other, Score):
            raise TypeError("Só é possível comparar Score com Score ou int")
            
        return self.total > other.total
        
    def get_category_score(self, category: str) -> int:
        """
        Retorna a pontuação de uma categoria específica.
        
        Args:
            category: O nome da categoria.
            
        Returns:
            A pontuação da categoria ou 0 se não existir.
        """
        if not self.categories:
            return 0
        return self.categories.get(category, 0) 