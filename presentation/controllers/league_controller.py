"""
Controlador para operações de ligas.
"""

from django.http import JsonResponse, HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
import json
from typing import Dict, Any, List

from application.services.league_app_service import LeagueAppService
from domain.config import DependencyContainer


def get_league_app_service() -> LeagueAppService:
    """
    Obtém uma instância do serviço de aplicação de ligas.
    """
    return DependencyContainer.get('league_app_service')


@login_required
@require_GET
def get_league_list(request: HttpRequest) -> JsonResponse:
    """
    Retorna a lista de ligas disponíveis.
    """
    league_app_service = get_league_app_service()
    
    try:
        leagues = league_app_service.get_all_leagues()
        
        league_data = [{
            'id': league.id,
            'name': league.name,
            'entry_fee': league.entry_fee,
            'championship_id': league.championship_id,
            'championship_name': league.championship.name if league.championship else None,
            'is_public': league.is_public,
            'max_participants': league.max_participants,
            'creation_date': league.creation_date.isoformat() if league.creation_date else None,
            'is_active': league.is_active,
            'members_count': league.members_count
        } for league in leagues]
        
        return JsonResponse({
            'success': True,
            'leagues': league_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_GET
def get_league_detail(request: HttpRequest, league_id: int) -> JsonResponse:
    """
    Retorna os detalhes de uma liga específica.
    """
    league_app_service = get_league_app_service()
    
    try:
        league = league_app_service.get_league_by_id(league_id)
        
        if not league:
            return JsonResponse({
                'success': False,
                'message': 'Liga não encontrada.'
            }, status=404)
        
        league_data = {
            'id': league.id,
            'name': league.name,
            'description': league.description,
            'entry_fee': league.entry_fee,
            'prize_pool': league.prize_pool,
            'championship_id': league.championship_id,
            'championship_name': league.championship.name if league.championship else None,
            'is_public': league.is_public,
            'code': league.code,
            'max_participants': league.max_participants,
            'creation_date': league.creation_date.isoformat() if league.creation_date else None,
            'is_active': league.is_active,
            'members_count': league.members_count,
            'created_by_id': league.created_by_id,
            'created_by_name': league.created_by.username if league.created_by else None
        }
        
        return JsonResponse({
            'success': True,
            'league': league_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def create_league(request: HttpRequest) -> JsonResponse:
    """
    Cria uma nova liga.
    """
    league_app_service = get_league_app_service()
    user = request.user
    
    try:
        data = json.loads(request.body)
        
        required_fields = ['name', 'championship_id']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'message': f'Campo obrigatório ausente: {field}'
                }, status=400)
        
        league = league_app_service.create_league(
            name=data['name'],
            championship_id=data['championship_id'],
            created_by_id=user.id,
            description=data.get('description', ''),
            entry_fee=data.get('entry_fee', 0),
            is_public=data.get('is_public', True),
            max_participants=data.get('max_participants', 100)
        )
        
        return JsonResponse({
            'success': True,
            'league_id': league.id,
            'league_code': league.code,
            'message': 'Liga criada com sucesso!'
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
@require_POST
def join_league(request: HttpRequest) -> JsonResponse:
    """
    Adiciona o usuário atual a uma liga através do código de convite.
    """
    league_app_service = get_league_app_service()
    user = request.user
    
    try:
        data = json.loads(request.body)
        
        if 'code' not in data:
            return JsonResponse({
                'success': False,
                'message': 'Código da liga é obrigatório.'
            }, status=400)
        
        league = league_app_service.join_league_by_code(
            user_id=user.id,
            league_code=data['code']
        )
        
        if not league:
            return JsonResponse({
                'success': False,
                'message': 'Liga não encontrada ou código inválido.'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'league_id': league.id,
            'league_name': league.name,
            'message': 'Você entrou na liga com sucesso!'
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
def get_user_leagues(request: HttpRequest) -> JsonResponse:
    """
    Retorna todas as ligas que o usuário atual participa.
    """
    league_app_service = get_league_app_service()
    user = request.user
    
    try:
        leagues = league_app_service.get_leagues_by_user(user.id)
        
        league_data = [{
            'id': league.id,
            'name': league.name,
            'championship_id': league.championship_id,
            'championship_name': league.championship.name if league.championship else None,
            'entry_fee': league.entry_fee,
            'is_public': league.is_public,
            'user_position': league.get_user_position(user.id),
            'is_creator': league.created_by_id == user.id,
            'creation_date': league.creation_date.isoformat() if league.creation_date else None,
            'members_count': league.members_count
        } for league in leagues]
        
        return JsonResponse({
            'success': True,
            'leagues': league_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_GET
def get_league_leaderboard(request: HttpRequest, league_id: int) -> JsonResponse:
    """
    Retorna o ranking de uma liga específica.
    """
    league_app_service = get_league_app_service()
    
    try:
        leaderboard = league_app_service.get_league_leaderboard(league_id)
        
        leaderboard_data = [{
            'position': entry['position'],
            'user_id': entry['user_id'],
            'username': entry['username'],
            'total_points': entry['total_points'],
            'round_points': entry.get('round_points', 0)
        } for entry in leaderboard]
        
        return JsonResponse({
            'success': True,
            'leaderboard': leaderboard_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def leave_league(request: HttpRequest, league_id: int) -> JsonResponse:
    """
    Remove o usuário atual de uma liga.
    """
    league_app_service = get_league_app_service()
    user = request.user
    
    try:
        success = league_app_service.leave_league(
            user_id=user.id,
            league_id=league_id
        )
        
        if not success:
            return JsonResponse({
                'success': False,
                'message': 'Liga não encontrada ou você não é membro.'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'message': 'Você saiu da liga com sucesso!'
        })
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400) 