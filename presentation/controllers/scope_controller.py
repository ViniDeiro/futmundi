"""
Controlador para operações de escopo e permissões.
"""

from django.http import JsonResponse, HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST, require_GET
import json
from typing import Dict, Any, List

from application.services.user_app_service import UserAppService
from domain.config import DependencyContainer


def is_staff(user):
    """
    Verifica se o usuário é membro da equipe administrativa.
    """
    return user.is_staff


def get_user_app_service() -> UserAppService:
    """
    Obtém uma instância do serviço de aplicação de usuários.
    """
    return DependencyContainer.get('user_app_service')


@login_required
@user_passes_test(is_staff)
@require_GET
def get_all_scopes(request: HttpRequest) -> JsonResponse:
    """
    Retorna todos os escopos disponíveis no sistema.
    Apenas para administradores.
    """
    user_app_service = get_user_app_service()
    
    try:
        scopes = user_app_service.get_all_scopes()
        
        scopes_data = [{
            'id': scope.id,
            'name': scope.name,
            'description': scope.description,
            'is_system': scope.is_system
        } for scope in scopes]
        
        return JsonResponse({
            'success': True,
            'scopes': scopes_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@user_passes_test(is_staff)
@require_GET
def get_all_roles(request: HttpRequest) -> JsonResponse:
    """
    Retorna todos os papéis (roles) disponíveis no sistema.
    Apenas para administradores.
    """
    user_app_service = get_user_app_service()
    
    try:
        roles = user_app_service.get_all_roles()
        
        roles_data = [{
            'id': role.id,
            'name': role.name,
            'description': role.description,
            'is_system': role.is_system,
            'scopes': [scope.name for scope in role.scopes.all()] if hasattr(role, 'scopes') else []
        } for role in roles]
        
        return JsonResponse({
            'success': True,
            'roles': roles_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@user_passes_test(is_staff)
@require_POST
def create_role(request: HttpRequest) -> JsonResponse:
    """
    Cria um novo papel (role) no sistema.
    Apenas para administradores.
    """
    user_app_service = get_user_app_service()
    
    try:
        data = json.loads(request.body)
        
        required_fields = ['name', 'description']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'message': f'Campo obrigatório ausente: {field}'
                }, status=400)
        
        # Lista de IDs de escopo
        scope_ids = data.get('scope_ids', [])
        
        role = user_app_service.create_role(
            name=data['name'],
            description=data['description'],
            scope_ids=scope_ids
        )
        
        return JsonResponse({
            'success': True,
            'role_id': role.id,
            'message': 'Papel criado com sucesso!'
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
def update_role(request: HttpRequest, role_id: int) -> JsonResponse:
    """
    Atualiza um papel (role) existente.
    Apenas para administradores.
    """
    user_app_service = get_user_app_service()
    
    try:
        data = json.loads(request.body)
        
        # Lista de IDs de escopo
        scope_ids = data.get('scope_ids')
        
        role = user_app_service.update_role(
            role_id=role_id,
            name=data.get('name'),
            description=data.get('description'),
            scope_ids=scope_ids
        )
        
        if not role:
            return JsonResponse({
                'success': False,
                'message': 'Papel não encontrado.'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'message': 'Papel atualizado com sucesso!'
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
def assign_role_to_user(request: HttpRequest) -> JsonResponse:
    """
    Atribui um papel (role) a um usuário.
    Apenas para administradores.
    """
    user_app_service = get_user_app_service()
    
    try:
        data = json.loads(request.body)
        
        if 'user_id' not in data or 'role_id' not in data:
            return JsonResponse({
                'success': False,
                'message': 'Campos obrigatórios ausentes: user_id, role_id'
            }, status=400)
        
        success = user_app_service.assign_role_to_user(
            user_id=data['user_id'],
            role_id=data['role_id']
        )
        
        if not success:
            return JsonResponse({
                'success': False,
                'message': 'Usuário ou papel não encontrado.'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'message': 'Papel atribuído ao usuário com sucesso!'
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
def remove_role_from_user(request: HttpRequest) -> JsonResponse:
    """
    Remove um papel (role) de um usuário.
    Apenas para administradores.
    """
    user_app_service = get_user_app_service()
    
    try:
        data = json.loads(request.body)
        
        if 'user_id' not in data or 'role_id' not in data:
            return JsonResponse({
                'success': False,
                'message': 'Campos obrigatórios ausentes: user_id, role_id'
            }, status=400)
        
        success = user_app_service.remove_role_from_user(
            user_id=data['user_id'],
            role_id=data['role_id']
        )
        
        if not success:
            return JsonResponse({
                'success': False,
                'message': 'Usuário ou papel não encontrado, ou o usuário não possui este papel.'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'message': 'Papel removido do usuário com sucesso!'
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
@require_GET
def get_user_roles(request: HttpRequest, user_id: int) -> JsonResponse:
    """
    Retorna os papéis (roles) de um usuário específico.
    Administradores podem ver qualquer usuário, usuários comuns só podem ver os próprios.
    """
    user_app_service = get_user_app_service()
    user = request.user
    
    # Verifica permissão
    if not user.is_staff and user.id != user_id:
        return JsonResponse({
            'success': False,
            'message': 'Acesso negado. Você não tem permissão para ver os papéis deste usuário.'
        }, status=403)
    
    try:
        roles = user_app_service.get_user_roles(user_id)
        
        roles_data = [{
            'id': role.id,
            'name': role.name,
            'description': role.description
        } for role in roles]
        
        return JsonResponse({
            'success': True,
            'roles': roles_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_GET
def check_user_permission(request: HttpRequest) -> JsonResponse:
    """
    Verifica se o usuário atual tem uma determinada permissão.
    """
    user_app_service = get_user_app_service()
    user = request.user
    
    try:
        scope_name = request.GET.get('scope')
        
        if not scope_name:
            return JsonResponse({
                'success': False,
                'message': 'Parâmetro de escopo não fornecido.'
            }, status=400)
        
        has_permission = user_app_service.check_user_permission(
            user_id=user.id,
            scope_name=scope_name
        )
        
        return JsonResponse({
            'success': True,
            'has_permission': has_permission
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500) 