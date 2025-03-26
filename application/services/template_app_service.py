"""
Serviço de aplicação para operações de templates.
"""

from typing import List, Optional, Dict, Any

from domain.entities.template import Template
from domain.repositories.template_repository import TemplateRepository


class TemplateAppService:
    """
    Serviço de aplicação para gerenciar operações de templates.
    """

    def __init__(self, template_repository: TemplateRepository):
        """
        Inicializa o serviço de aplicação de templates.

        Args:
            template_repository: Repositório de templates.
        """
        self._template_repository = template_repository

    def get_all_templates(self) -> List[Template]:
        """
        Obtém todos os templates.

        Returns:
            Lista de templates.
        """
        return self._template_repository.get_all()

    def get_template_by_id(self, template_id: int) -> Optional[Template]:
        """
        Obtém um template pelo ID.

        Args:
            template_id: ID do template.

        Returns:
            O template encontrado ou None.
        """
        return self._template_repository.get_by_id(template_id)

    def get_templates_by_type(self, template_type: str) -> List[Template]:
        """
        Obtém todos os templates de um tipo específico.

        Args:
            template_type: Tipo do template.

        Returns:
            Lista de templates.
        """
        return self._template_repository.get_by_type(template_type)

    def get_template_by_name(self, name: str) -> Optional[Template]:
        """
        Obtém um template pelo nome.

        Args:
            name: Nome do template.

        Returns:
            O template encontrado ou None.
        """
        return self._template_repository.get_by_name(name)

    def get_active_templates(self) -> List[Template]:
        """
        Obtém todos os templates ativos.

        Returns:
            Lista de templates ativos.
        """
        return self._template_repository.get_active_templates()

    def get_default_template(self, template_type: str) -> Optional[Template]:
        """
        Obtém o template padrão para um tipo específico.

        Args:
            template_type: Tipo do template.

        Returns:
            O template padrão ou None.
        """
        return self._template_repository.get_default_template(template_type)

    def create_template(self, name: str, content: str, template_type: str, 
                        is_active: bool = True, is_default: bool = False) -> Template:
        """
        Cria um novo template.

        Args:
            name: Nome do template.
            content: Conteúdo do template.
            template_type: Tipo do template.
            is_active: Se o template está ativo (opcional).
            is_default: Se o template é o padrão para seu tipo (opcional).

        Returns:
            O template criado.
        """
        # Verificar se o nome já existe
        existing_template = self.get_template_by_name(name)
        if existing_template:
            raise ValueError(f"Já existe um template com o nome '{name}'")
        
        # Se for definido como padrão, atualizar os outros templates do mesmo tipo
        if is_default:
            templates_of_same_type = self.get_templates_by_type(template_type)
            for template in templates_of_same_type:
                if template.is_default:
                    template.is_default = False
                    self._template_repository.update(template)
        
        # Criar o novo template
        template = Template(
            id=None,  # Será atribuído pelo repositório
            name=name,
            content=content,
            template_type=template_type,
            is_active=is_active,
            is_default=is_default
        )
        
        return self._template_repository.add(template)

    def update_template(self, template_id: int, name: Optional[str] = None, 
                        content: Optional[str] = None, is_active: Optional[bool] = None,
                        is_default: Optional[bool] = None) -> Optional[Template]:
        """
        Atualiza um template existente.

        Args:
            template_id: ID do template.
            name: Novo nome (opcional).
            content: Novo conteúdo (opcional).
            is_active: Novo status ativo (opcional).
            is_default: Novo status padrão (opcional).

        Returns:
            O template atualizado ou None se não encontrado.
        """
        template = self.get_template_by_id(template_id)
        if not template:
            return None
        
        # Verificar se o novo nome já existe (se for fornecido)
        if name and name != template.name:
            existing_template = self.get_template_by_name(name)
            if existing_template and existing_template.id != template_id:
                raise ValueError(f"Já existe um template com o nome '{name}'")
            template.name = name
        
        # Atualizar os outros campos se fornecidos
        if content is not None:
            template.content = content
        
        if is_active is not None:
            template.is_active = is_active
        
        # Se for definido como padrão, atualizar os outros templates do mesmo tipo
        if is_default is not None and is_default != template.is_default:
            template.is_default = is_default
            if is_default:
                templates_of_same_type = self.get_templates_by_type(template.template_type)
                for t in templates_of_same_type:
                    if t.id != template.id and t.is_default:
                        t.is_default = False
                        self._template_repository.update(t)
        
        return self._template_repository.update(template)

    def delete_template(self, template_id: int) -> bool:
        """
        Exclui um template.

        Args:
            template_id: ID do template.

        Returns:
            True se excluído com sucesso, False caso contrário.
        """
        template = self.get_template_by_id(template_id)
        if not template:
            return False
        
        # Não permitir a exclusão de um template padrão
        if template.is_default:
            raise ValueError("Não é possível excluir um template padrão. Defina outro template como padrão antes de excluir este.")
        
        return self._template_repository.delete(template_id)

    def render_template(self, template_id: int, context: Dict[str, Any]) -> str:
        """
        Renderiza um template com o contexto fornecido.

        Args:
            template_id: ID do template.
            context: Contexto para renderização.

        Returns:
            O template renderizado.
        """
        return self._template_repository.render_template(template_id, context)

    def render_template_by_type(self, template_type: str, context: Dict[str, Any]) -> str:
        """
        Renderiza o template padrão de um tipo específico com o contexto fornecido.

        Args:
            template_type: Tipo do template.
            context: Contexto para renderização.

        Returns:
            O template renderizado.
        """
        template = self.get_default_template(template_type)
        if not template:
            raise ValueError(f"Nenhum template padrão encontrado para o tipo '{template_type}'")
        
        return self.render_template(template.id, context) 