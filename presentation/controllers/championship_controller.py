"""
Controlador para operações de campeonatos.
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
    Obtém uma instância do serviço de aplicação de campeonatos.
    """
    return DependencyContainer.get('championship_app_service')


@login_required
@require_GET
def get_championship_list(request: HttpRequest) -> JsonResponse:
    """
    Retorna a lista de campeonatos disponíveis.
    """
    championship_app_service = get_championship_app_service()
    
    try:
        championships = championship_app_service.get_all_championships()
        
        championship_data = [{
            'id': championship.id,
            'name': championship.name,
            'season': championship.season,
            'start_date': championship.start_date.isoformat() if championship.start_date else None,
            'end_date': championship.end_date.isoformat() if championship.end_date else None,
            'is_active': championship.is_active,
            'country': championship.country
        } for championship in championships]
        
        return JsonResponse({
            'success': True,
            'championships': championship_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_GET
def get_championship_detail(request: HttpRequest, championship_id: int) -> JsonResponse:
    """
    Retorna os detalhes de um campeonato específico.
    """
    championship_app_service = get_championship_app_service()
    
    try:
        championship = championship_app_service.get_championship_by_id(championship_id)
        
        if not championship:
            return JsonResponse({
                'success': False,
                'message': 'Campeonato não encontrado.'
            }, status=404)
        
        championship_data = {
            'id': championship.id,
            'name': championship.name,
            'season': championship.season,
            'start_date': championship.start_date.isoformat() if championship.start_date else None,
            'end_date': championship.end_date.isoformat() if championship.end_date else None,
            'is_active': championship.is_active,
            'country': championship.country,
            'created_at': championship.created_at.isoformat() if championship.created_at else None,
            'updated_at': championship.updated_at.isoformat() if championship.updated_at else None
        }
        
        return JsonResponse({
            'success': True,
            'championship': championship_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def create_championship(request: HttpRequest) -> JsonResponse:
    """
    Cria um novo campeonato.
    """
    championship_app_service = get_championship_app_service()
    
    try:
        data = json.loads(request.body)
        
        required_fields = ['name', 'season', 'country']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'message': f'Campo obrigatório ausente: {field}'
                }, status=400)
        
        championship = championship_app_service.create_championship(
            name=data['name'],
            season=data['season'],
            country=data['country'],
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            is_active=data.get('is_active', True)
        )
        
        return JsonResponse({
            'success': True,
            'championship_id': championship.id,
            'message': 'Campeonato criado com sucesso!'
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
def update_championship(request: HttpRequest, championship_id: int) -> JsonResponse:
    """
    Atualiza um campeonato existente.
    """
    championship_app_service = get_championship_app_service()
    
    try:
        data = json.loads(request.body)
        
        championship = championship_app_service.update_championship(
            championship_id=championship_id,
            **data
        )
        
        if not championship:
            return JsonResponse({
                'success': False,
                'message': 'Campeonato não encontrado.'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'message': 'Campeonato atualizado com sucesso!'
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
def get_stages_by_championship(request: HttpRequest, championship_id: int) -> JsonResponse:
    """
    Retorna todos os estágios de um campeonato.
    """
    championship_app_service = get_championship_app_service()
    
    try:
        stages = championship_app_service.get_stages_by_championship(championship_id)
        
        stages_data = [{
            'id': stage.id,
            'name': stage.name,
            'order': stage.order,
            'is_active': stage.is_active
        } for stage in stages]
        
        return JsonResponse({
            'success': True,
            'stages': stages_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_GET
def get_rounds_by_stage(request: HttpRequest, stage_id: int) -> JsonResponse:
    """
    Retorna todas as rodadas de um estágio.
    """
    championship_app_service = get_championship_app_service()
    
    try:
        rounds = championship_app_service.get_rounds_by_stage(stage_id)
        
        rounds_data = [{
            'id': round_obj.id,
            'number': round_obj.number,
            'name': round_obj.name,
            'is_current': round_obj.is_current,
            'start_date': round_obj.start_date.isoformat() if round_obj.start_date else None,
            'end_date': round_obj.end_date.isoformat() if round_obj.end_date else None
        } for round_obj in rounds]
        
        return JsonResponse({
            'success': True,
            'rounds': rounds_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_GET
def get_matches_by_round(request: HttpRequest, round_id: int) -> JsonResponse:
    """
    Retorna todas as partidas de uma rodada.
    """
    championship_app_service = get_championship_app_service()
    
    try:
        matches = championship_app_service.get_matches_by_round(round_id)
        
        matches_data = [{
            'id': match.id,
            'home_team_id': match.home_team_id,
            'home_team_name': match.home_team.name if match.home_team else None,
            'away_team_id': match.away_team_id,
            'away_team_name': match.away_team.name if match.away_team else None,
            'home_score': match.home_score,
            'away_score': match.away_score,
            'match_date': match.match_date.isoformat() if match.match_date else None,
            'status': match.status
        } for match in matches]
        
        return JsonResponse({
            'success': True,
            'matches': matches_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def update_match_result(request: HttpRequest, match_id: int) -> JsonResponse:
    """
    Atualiza o resultado de uma partida.
    """
    championship_app_service = get_championship_app_service()
    
    try:
        data = json.loads(request.body)
        
        if 'home_score' not in data or 'away_score' not in data:
            return JsonResponse({
                'success': False,
                'message': 'Campos obrigatórios ausentes: home_score, away_score'
            }, status=400)
        
        match = championship_app_service.update_match_result(
            match_id=match_id,
            home_score=data['home_score'],
            away_score=data['away_score']
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Resultado da partida atualizado com sucesso!'
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