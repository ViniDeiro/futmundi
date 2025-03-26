"""
Controlador para operações de times.
"""

from django.http import JsonResponse, HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
import json
from typing import Dict, Any, List

from application.services.championship_app_service import ChampionshipAppService
from domain.config import DependencyContainer


def get_championship_app_service() -> ChampionshipAppService:
    """
    Obtém uma instância do serviço de aplicação de campeonatos (que gerencia times).
    """
    return DependencyContainer.get('championship_app_service')


@login_required
@require_GET
def get_teams_by_championship(request: HttpRequest, championship_id: int) -> JsonResponse:
    """
    Retorna todos os times de um campeonato.
    """
    app_service = get_championship_app_service()
    
    try:
        teams = app_service.get_teams_by_championship(championship_id)
        
        team_data = [{
            'id': team.id,
            'name': team.name,
            'short_name': team.short_name,
            'country': team.country,
            'image_url': team.image.url if team.image else None,
            'created_at': team.created_at.isoformat() if team.created_at else None
        } for team in teams]
        
        return JsonResponse({
            'success': True,
            'teams': team_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_GET
def get_team_detail(request: HttpRequest, team_id: int) -> JsonResponse:
    """
    Retorna os detalhes de um time específico.
    """
    app_service = get_championship_app_service()
    
    try:
        team = app_service.get_team_by_id(team_id)
        
        if not team:
            return JsonResponse({
                'success': False,
                'message': 'Time não encontrado.'
            }, status=404)
        
        team_data = {
            'id': team.id,
            'name': team.name,
            'short_name': team.short_name,
            'country': team.country,
            'image_url': team.image.url if team.image else None,
            'championships': [c.name for c in team.championships.all()],
            'created_at': team.created_at.isoformat() if team.created_at else None,
            'updated_at': team.updated_at.isoformat() if team.updated_at else None
        }
        
        return JsonResponse({
            'success': True,
            'team': team_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def create_team(request: HttpRequest) -> JsonResponse:
    """
    Cria um novo time. Apenas administradores podem executar esta operação.
    """
    app_service = get_championship_app_service()
    user = request.user
    
    if not user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'Acesso negado. Apenas administradores podem executar esta operação.'
        }, status=403)
    
    try:
        # Para imagens, usamos FormData em vez de JSON
        name = request.POST.get('name')
        short_name = request.POST.get('short_name')
        country = request.POST.get('country')
        image = request.FILES.get('image')
        championship_id = request.POST.get('championship_id')
        
        if not name or not country:
            return JsonResponse({
                'success': False,
                'message': 'Campos obrigatórios ausentes: name, country'
            }, status=400)
        
        team = app_service.create_team(
            name=name,
            short_name=short_name,
            country=country,
            image=image,
            championship_id=championship_id
        )
        
        return JsonResponse({
            'success': True,
            'team_id': team.id,
            'message': 'Time criado com sucesso!'
        }, status=201)
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@require_POST
def update_team(request: HttpRequest, team_id: int) -> JsonResponse:
    """
    Atualiza um time existente. Apenas administradores podem executar esta operação.
    """
    app_service = get_championship_app_service()
    user = request.user
    
    if not user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'Acesso negado. Apenas administradores podem executar esta operação.'
        }, status=403)
    
    try:
        # Para imagens, usamos FormData em vez de JSON
        name = request.POST.get('name')
        short_name = request.POST.get('short_name')
        country = request.POST.get('country')
        image = request.FILES.get('image')
        
        team = app_service.update_team(
            team_id=team_id,
            name=name,
            short_name=short_name,
            country=country,
            image=image
        )
        
        if not team:
            return JsonResponse({
                'success': False,
                'message': 'Time não encontrado.'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'message': 'Time atualizado com sucesso!'
        })
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@require_POST
def add_team_to_championship(request: HttpRequest) -> JsonResponse:
    """
    Adiciona um time a um campeonato. Apenas administradores podem executar esta operação.
    """
    app_service = get_championship_app_service()
    user = request.user
    
    if not user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'Acesso negado. Apenas administradores podem executar esta operação.'
        }, status=403)
    
    try:
        data = json.loads(request.body)
        
        if 'team_id' not in data or 'championship_id' not in data:
            return JsonResponse({
                'success': False,
                'message': 'Campos obrigatórios ausentes: team_id, championship_id'
            }, status=400)
        
        success = app_service.add_team_to_championship(
            team_id=data['team_id'],
            championship_id=data['championship_id']
        )
        
        if not success:
            return JsonResponse({
                'success': False,
                'message': 'Time ou campeonato não encontrado.'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'message': 'Time adicionado ao campeonato com sucesso!'
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