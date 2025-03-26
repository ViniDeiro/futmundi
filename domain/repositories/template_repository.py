"""
Repositório para operações em templates.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from domain.entities.template import Template
from domain.repositories.base_repository import BaseRepository


class TemplateRepository(BaseRepository[Template], ABC):
    """
    Repositório para gerenciar templates.
    """

    @abstractmethod
    def get_by_type(self, template_type: str) -> List[Template]:
        """
        Obtém todos os templates de um tipo específico.

        Args:
            template_type: Tipo do template.

        Returns:
            Lista de templates.
        """
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Template]:
        """
        Obtém um template pelo nome.

        Args:
            name: Nome do template.

        Returns:
            O template encontrado ou None.
        """
        pass

    @abstractmethod
    def get_active_templates(self) -> List[Template]:
        """
        Obtém todos os templates ativos.

        Returns:
            Lista de templates ativos.
        """
        pass

    @abstractmethod
    def get_default_template(self, template_type: str) -> Optional[Template]:
        """
        Obtém o template padrão para um tipo específico.

        Args:
            template_type: Tipo do template.

        Returns:
            O template padrão ou None.
        """
        pass

    @abstractmethod
    def render_template(self, template_id: int, context: Dict[str, Any]) -> str:
        """
        Renderiza um template com o contexto fornecido.

        Args:
            template_id: ID do template.
            context: Contexto para renderização.

        Returns:
            O template renderizado.
        """
        pass 