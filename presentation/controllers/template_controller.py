"""
Controlador para operações de templates.
"""

from django.http import JsonResponse, HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST, require_GET
import json
from typing import Dict, Any, List

from application.services.template_app_service import TemplateAppService
from domain.config import DependencyContainer


def is_staff(user):
    """
    Verifica se o usuário é membro da equipe administrativa.
    """
    return user.is_staff


def get_template_app_service() -> TemplateAppService:
    """
    Obtém uma instância do serviço de aplicação de templates.
    """
    return DependencyContainer.get('template_app_service')


@login_required
@user_passes_test(is_staff)
@require_GET
def get_all_templates(request: HttpRequest) -> JsonResponse:
    """
    Retorna todos os templates.
    Apenas para administradores.
    """
    template_app_service = get_template_app_service()
    
    try:
        templates = template_app_service.get_all_templates()
        
        templates_data = [{
            'id': template.id,
            'name': template.name,
            'template_type': template.template_type,
            'is_active': template.is_active,
            'is_default': template.is_default,
            'created_at': template.created_at.isoformat() if hasattr(template, 'created_at') and template.created_at else None,
            'updated_at': template.updated_at.isoformat() if hasattr(template, 'updated_at') and template.updated_at else None
        } for template in templates]
        
        return JsonResponse({
            'success': True,
            'templates': templates_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@user_passes_test(is_staff)
@require_GET
def get_template_detail(request: HttpRequest, template_id: int) -> JsonResponse:
    """
    Retorna os detalhes de um template específico.
    Apenas para administradores.
    """
    template_app_service = get_template_app_service()
    
    try:
        template = template_app_service.get_template_by_id(template_id)
        
        if not template:
            return JsonResponse({
                'success': False,
                'message': 'Template não encontrado.'
            }, status=404)
        
        template_data = {
            'id': template.id,
            'name': template.name,
            'content': template.content,
            'template_type': template.template_type,
            'is_active': template.is_active,
            'is_default': template.is_default,
            'created_at': template.created_at.isoformat() if hasattr(template, 'created_at') and template.created_at else None,
            'updated_at': template.updated_at.isoformat() if hasattr(template, 'updated_at') and template.updated_at else None
        }
        
        return JsonResponse({
            'success': True,
            'template': template_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@user_passes_test(is_staff)
@require_GET
def get_templates_by_type(request: HttpRequest, template_type: str) -> JsonResponse:
    """
    Retorna todos os templates de um tipo específico.
    Apenas para administradores.
    """
    template_app_service = get_template_app_service()
    
    try:
        templates = template_app_service.get_templates_by_type(template_type)
        
        templates_data = [{
            'id': template.id,
            'name': template.name,
            'is_active': template.is_active,
            'is_default': template.is_default
        } for template in templates]
        
        return JsonResponse({
            'success': True,
            'templates': templates_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@user_passes_test(is_staff)
@require_POST
def create_template(request: HttpRequest) -> JsonResponse:
    """
    Cria um novo template.
    Apenas para administradores.
    """
    template_app_service = get_template_app_service()
    
    try:
        data = json.loads(request.body)
        
        required_fields = ['name', 'content', 'template_type']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'message': f'Campo obrigatório ausente: {field}'
                }, status=400)
        
        template = template_app_service.create_template(
            name=data['name'],
            content=data['content'],
            template_type=data['template_type'],
            is_active=data.get('is_active', True),
            is_default=data.get('is_default', False)
        )
        
        return JsonResponse({
            'success': True,
            'template_id': template.id,
            'message': 'Template criado com sucesso!'
        }, status=201)
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Formato de dados inválido.'
        }, status=400)


@login_required
@user_passes_test(is_staff)
@require_POST
def update_template(request: HttpRequest, template_id: int) -> JsonResponse:
    """
    Atualiza um template existente.
    Apenas para administradores.
    """
    template_app_service = get_template_app_service()
    
    try:
        data = json.loads(request.body)
        
        template = template_app_service.update_template(
            template_id=template_id,
            name=data.get('name'),
            content=data.get('content'),
            is_active=data.get('is_active'),
            is_default=data.get('is_default')
        )
        
        if not template:
            return JsonResponse({
                'success': False,
                'message': 'Template não encontrado.'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'message': 'Template atualizado com sucesso!'
        })
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Formato de dados inválido.'
        }, status=400)


@login_required
@user_passes_test(is_staff)
@require_POST
def delete_template(request: HttpRequest, template_id: int) -> JsonResponse:
    """
    Exclui um template.
    Apenas para administradores.
    """
    template_app_service = get_template_app_service()
    
    try:
        success = template_app_service.delete_template(template_id)
        
        if not success:
            return JsonResponse({
                'success': False,
                'message': 'Template não encontrado.'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'message': 'Template excluído com sucesso!'
        })
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@require_POST
def render_template(request: HttpRequest, template_id: int) -> JsonResponse:
    """
    Renderiza um template com o contexto fornecido.
    """
    template_app_service = get_template_app_service()
    
    try:
        data = json.loads(request.body)
        
        if 'context' not in data:
            return JsonResponse({
                'success': False,
                'message': 'Campo obrigatório ausente: context'
            }, status=400)
        
        rendered_content = template_app_service.render_template(
            template_id=template_id,
            context=data['context']
        )
        
        return JsonResponse({
            'success': True,
            'rendered_content': rendered_content
        })
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Formato de dados inválido.'
        }, status=400)


@login_required
@require_POST
def render_template_by_type(request: HttpRequest) -> JsonResponse:
    """
    Renderiza o template padrão de um tipo específico com o contexto fornecido.
    """
    template_app_service = get_template_app_service()
    
    try:
        data = json.loads(request.body)
        
        if 'template_type' not in data or 'context' not in data:
            return JsonResponse({
                'success': False,
                'message': 'Campos obrigatórios ausentes: template_type, context'
            }, status=400)
        
        rendered_content = template_app_service.render_template_by_type(
            template_type=data['template_type'],
            context=data['context']
        )
        
        return JsonResponse({
            'success': True,
            'rendered_content': rendered_content
        })
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Formato de dados inválido.'
        }, status=400) 