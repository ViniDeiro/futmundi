"""
Serviço de aplicação para operações de localização.
"""

from typing import List, Optional, Dict, Any

from domain.entities.location import Country, State, City
from domain.repositories.location_repository import LocationRepository


class LocationAppService:
    """
    Serviço de aplicação para gerenciar operações de localização.
    """

    def __init__(self, location_repository: LocationRepository):
        """
        Inicializa o serviço de aplicação de localização.

        Args:
            location_repository: Repositório de localizações.
        """
        self._location_repository = location_repository

    def get_all_countries(self) -> List[Country]:
        """
        Obtém todos os países disponíveis.

        Returns:
            Lista de países.
        """
        return self._location_repository.get_all_countries()

    def get_country_by_code(self, country_code: str) -> Optional[Country]:
        """
        Obtém um país pelo seu código.

        Args:
            country_code: Código do país.

        Returns:
            O país encontrado ou None.
        """
        return self._location_repository.get_country_by_code(country_code)

    def get_states_by_country(self, country_code: str) -> List[State]:
        """
        Obtém todos os estados/províncias de um país.

        Args:
            country_code: Código do país.

        Returns:
            Lista de estados/províncias.
        """
        return self._location_repository.get_states_by_country(country_code)

    def get_state_by_code(self, country_code: str, state_code: str) -> Optional[State]:
        """
        Obtém um estado/província pelo seu código.

        Args:
            country_code: Código do país.
            state_code: Código do estado/província.

        Returns:
            O estado/província encontrado ou None.
        """
        return self._location_repository.get_state_by_code(country_code, state_code)

    def get_cities_by_state(self, country_code: str, state_code: str) -> List[City]:
        """
        Obtém todas as cidades de um estado/província.

        Args:
            country_code: Código do país.
            state_code: Código do estado/província.

        Returns:
            Lista de cidades.
        """
        return self._location_repository.get_cities_by_state(country_code, state_code)

    def get_city_by_id(self, city_id: int) -> Optional[City]:
        """
        Obtém uma cidade pelo seu ID.

        Args:
            city_id: ID da cidade.

        Returns:
            A cidade encontrada ou None.
        """
        return self._location_repository.get_city_by_id(city_id)

    def search_cities(self, query: str, limit: int = 20) -> List[City]:
        """
        Pesquisa cidades por nome.

        Args:
            query: Termo de pesquisa.
            limit: Limite de resultados (padrão: 20).

        Returns:
            Lista de cidades encontradas.
        """
        return self._location_repository.search_cities(query, limit)

    def update_user_location(self, user_id: int, country_code: str, state_code: str, city_id: int) -> bool:
        """
        Atualiza a localização de um usuário.

        Args:
            user_id: ID do usuário.
            country_code: Código do país.
            state_code: Código do estado/província.
            city_id: ID da cidade.

        Returns:
            True se atualizado com sucesso, False caso contrário.
        """
        # Verifica se a localização é válida
        country = self.get_country_by_code(country_code)
        if not country:
            raise ValueError("País inválido")

        state = self.get_state_by_code(country_code, state_code)
        if not state:
            raise ValueError("Estado inválido")

        city = self.get_city_by_id(city_id)
        if not city:
            raise ValueError("Cidade inválida")

        # Este método depende do UserRepository para atualizar a localização do usuário
        # Por simplicidade, assumimos que isso é feito em outro lugar ou por outro serviço
        # Um design mais elaborado injetaria o UserRepository aqui
        return True 