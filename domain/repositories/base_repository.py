"""
Interface base para todos os repositórios.
Define os métodos comuns que todos os repositórios devem implementar.
"""
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Any

T = TypeVar('T')  # Tipo genérico para representar uma entidade


class BaseRepository(Generic[T], ABC):
    """
    Repositório base com métodos CRUD genéricos.
    
    Esta é uma classe abstrata que define o contrato para os repositórios.
    Todas as implementações concretas devem estender esta classe.
    """
    
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        """
        Recupera uma entidade pelo seu ID.
        
        Args:
            id: O ID da entidade a ser recuperada.
            
        Returns:
            A entidade, se encontrada, ou None.
        """
        pass
    
    @abstractmethod
    def list(self, filters: Optional[dict] = None, order_by: Optional[str] = None, limit: Optional[int] = None) -> List[T]:
        """
        Lista entidades com filtros opcionais.
        
        Args:
            filters: Dicionário com filtros a serem aplicados.
            order_by: Campo para ordenação.
            limit: Limite de itens a retornar.
            
        Returns:
            Lista de entidades.
        """
        pass
    
    @abstractmethod
    def create(self, entity: T) -> T:
        """
        Cria uma nova entidade.
        
        Args:
            entity: A entidade a ser criada.
            
        Returns:
            A entidade criada com ID atribuído.
        """
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        """
        Atualiza uma entidade existente.
        
        Args:
            entity: A entidade a ser atualizada.
            
        Returns:
            A entidade atualizada.
        """
        pass
    
    @abstractmethod
    def delete(self, id: int) -> bool:
        """
        Remove uma entidade pelo ID.
        
        Args:
            id: O ID da entidade a ser removida.
            
        Returns:
            True se a entidade foi removida, False caso contrário.
        """
        pass
    
    @abstractmethod
    def count(self, filters: Optional[dict] = None) -> int:
        """
        Conta o número de entidades que correspondem aos filtros.
        
        Args:
            filters: Dicionário com filtros a serem aplicados.
            
        Returns:
            Número de entidades.
        """
        pass 