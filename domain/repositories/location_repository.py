"""
Repositório para operações em localizações.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from domain.entities.location import Country, State, City
from domain.repositories.base_repository import BaseRepository


class LocationRepository(ABC):
    """
    Repositório para gerenciar localizações geográficas.
    """

    @abstractmethod
    def get_all_countries(self) -> List[Country]:
        """
        Obtém todos os países disponíveis.

        Returns:
            Lista de países.
        """
        pass

    @abstractmethod
    def get_country_by_code(self, country_code: str) -> Optional[Country]:
        """
        Obtém um país pelo seu código.

        Args:
            country_code: Código do país.

        Returns:
            O país encontrado ou None.
        """
        pass

    @abstractmethod
    def get_states_by_country(self, country_code: str) -> List[State]:
        """
        Obtém todos os estados/províncias de um país.

        Args:
            country_code: Código do país.

        Returns:
            Lista de estados/províncias.
        """
        pass

    @abstractmethod
    def get_state_by_code(self, country_code: str, state_code: str) -> Optional[State]:
        """
        Obtém um estado/província pelo seu código.

        Args:
            country_code: Código do país.
            state_code: Código do estado/província.

        Returns:
            O estado/província encontrado ou None.
        """
        pass

    @abstractmethod
    def get_cities_by_state(self, country_code: str, state_code: str) -> List[City]:
        """
        Obtém todas as cidades de um estado/província.

        Args:
            country_code: Código do país.
            state_code: Código do estado/província.

        Returns:
            Lista de cidades.
        """
        pass

    @abstractmethod
    def get_city_by_id(self, city_id: int) -> Optional[City]:
        """
        Obtém uma cidade pelo seu ID.

        Args:
            city_id: ID da cidade.

        Returns:
            A cidade encontrada ou None.
        """
        pass

    @abstractmethod
    def search_cities(self, query: str, limit: int = 20) -> List[City]:
        """
        Pesquisa cidades por nome.

        Args:
            query: Termo de pesquisa.
            limit: Limite de resultados (padrão: 20).

        Returns:
            Lista de cidades encontradas.
        """
        pass 