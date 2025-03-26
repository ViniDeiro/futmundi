"""
Controlador para operações administrativas.
"""

from django.http import JsonResponse, HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST, require_GET
import json
from typing import Dict, Any, List
import datetime

from application.services.championship_app_service import ChampionshipAppService
from application.services.league_app_service import LeagueAppService
from application.services.user_app_service import UserAppService
from domain.config import DependencyContainer


def is_staff(user):
    """
    Verifica se o usuário é membro da equipe administrativa.
    """
    return user.is_staff


def get_championship_app_service() -> ChampionshipAppService:
    """
    Obtém uma instância do serviço de aplicação de campeonatos.
    """
    return DependencyContainer.get('championship_app_service')


def get_league_app_service() -> LeagueAppService:
    """
    Obtém uma instância do serviço de aplicação de ligas.
    """
    return DependencyContainer.get('league_app_service')


def get_user_app_service() -> UserAppService:
    """
    Obtém uma instância do serviço de aplicação de usuários.
    """
    return DependencyContainer.get('user_app_service')


@login_required
@user_passes_test(is_staff)
@require_GET
def get_admin_dashboard(request: HttpRequest) -> JsonResponse:
    """
    Retorna dados para o dashboard administrativo.
    """
    championship_app_service = get_championship_app_service()
    league_app_service = get_league_app_service()
    user_app_service = get_user_app_service()
    
    try:
        # Estatísticas gerais
        total_users = user_app_service.get_total_users()
        total_leagues = league_app_service.get_total_leagues()
        total_championships = championship_app_service.get_total_championships()
        total_predictions = user_app_service.get_total_predictions()
        
        # Usuários recentes
        recent_users = user_app_service.get_recent_users(limit=10)
        recent_users_data = [{
            'id': user.id,
            'username': user.username,
            'registration_date': user.registration_date.isoformat() if user.registration_date else None,
            'is_active': user.is_active,
            'is_star': user.is_star
        } for user in recent_users]
        
        # Ligas recentes
        recent_leagues = league_app_service.get_recent_leagues(limit=10)
        recent_leagues_data = [{
            'id': league.id,
            'name': league.name,
            'championship_name': league.championship.name if league.championship else None,
            'members_count': league.members_count,
            'creation_date': league.creation_date.isoformat() if league.creation_date else None
        } for league in recent_leagues]
        
        # Próximas partidas
        upcoming_matches = championship_app_service.get_upcoming_matches(limit=10)
        upcoming_matches_data = [{
            'id': match.id,
            'home_team': match.home_team.name if match.home_team else None,
            'away_team': match.away_team.name if match.away_team else None,
            'match_date': match.match_date.isoformat() if match.match_date else None,
            'championship_name': match.round.stage.championship.name if match.round and match.round.stage and match.round.stage.championship else None
        } for match in upcoming_matches]
        
        # Estatísticas de pagamentos
        payment_stats = user_app_service.get_payment_statistics()
        
        return JsonResponse({
            'success': True,
            'statistics': {
                'total_users': total_users,
                'total_leagues': total_leagues,
                'total_championships': total_championships,
                'total_predictions': total_predictions,
                'users_today': payment_stats.get('users_today', 0),
                'revenue_today': payment_stats.get('revenue_today', 0),
                'revenue_month': payment_stats.get('revenue_month', 0),
                'active_subscriptions': payment_stats.get('active_subscriptions', 0)
            },
            'recent_users': recent_users_data,
            'recent_leagues': recent_leagues_data,
            'upcoming_matches': upcoming_matches_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@user_passes_test(is_staff)
@require_GET
def get_user_stats(request: HttpRequest) -> JsonResponse:
    """
    Retorna estatísticas detalhadas sobre usuários.
    """
    user_app_service = get_user_app_service()
    
    try:
        # Parâmetros para filtragem
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        start_date = None
        end_date = None
        
        if start_date_str:
            start_date = datetime.datetime.fromisoformat(start_date_str)
        if end_date_str:
            end_date = datetime.datetime.fromisoformat(end_date_str)
        
        stats = user_app_service.get_user_statistics(start_date, end_date)
        
        return JsonResponse({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@user_passes_test(is_staff)
@require_POST
def update_system_settings(request: HttpRequest) -> JsonResponse:
    """
    Atualiza configurações do sistema.
    """
    user_app_service = get_user_app_service()
    
    try:
        data = json.loads(request.body)
        
        settings = user_app_service.update_system_settings(data)
        
        return JsonResponse({
            'success': True,
            'settings': settings,
            'message': 'Configurações atualizadas com sucesso!'
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
@require_GET
def get_system_settings(request: HttpRequest) -> JsonResponse:
    """
    Retorna as configurações do sistema.
    """
    user_app_service = get_user_app_service()
    
    try:
        settings = user_app_service.get_system_settings()
        
        return JsonResponse({
            'success': True,
            'settings': settings
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@user_passes_test(is_staff)
@require_POST
def send_system_notification(request: HttpRequest) -> JsonResponse:
    """
    Envia uma notificação para usuários.
    """
    user_app_service = get_user_app_service()
    
    try:
        data = json.loads(request.body)
        
        if 'title' not in data or 'message' not in data:
            return JsonResponse({
                'success': False,
                'message': 'Campos obrigatórios ausentes: title, message'
            }, status=400)
        
        # Alvos da notificação: all, premium, free
        target = data.get('target', 'all')
        
        # ID específico de usuário se aplicável
        user_id = data.get('user_id')
        
        result = user_app_service.send_notification(
            title=data['title'],
            message=data['message'],
            target=target,
            user_id=user_id
        )
        
        return JsonResponse({
            'success': True,
            'notifications_sent': result.get('count', 0),
            'message': 'Notificações enviadas com sucesso!'
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
@require_GET
def get_championship_activity(request: HttpRequest, championship_id: int) -> JsonResponse:
    """
    Retorna estatísticas de atividade para um campeonato específico.
    """
    championship_app_service = get_championship_app_service()
    
    try:
        activity = championship_app_service.get_championship_activity(championship_id)
        
        return JsonResponse({
            'success': True,
            'activity': activity
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@user_passes_test(is_staff)
@require_POST
def calculate_round_points(request: HttpRequest, round_id: int) -> JsonResponse:
    """
    Calcula e atualiza os pontos para todas as previsões de uma rodada.
    """
    championship_app_service = get_championship_app_service()
    
    try:
        result = championship_app_service.calculate_round_points(round_id)
        
        return JsonResponse({
            'success': True,
            'matches_processed': result.get('matches_processed', 0),
            'predictions_calculated': result.get('predictions_calculated', 0),
            'message': 'Pontos da rodada calculados com sucesso!'
        })
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400) 