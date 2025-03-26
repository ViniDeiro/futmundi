"""
Controlador para operações de previsões.
"""

from django.http import JsonResponse, HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
import json
from typing import Dict, Any, List

from application.services.prediction_app_service import PredictionAppService
from domain.config import DependencyContainer


def get_prediction_app_service() -> PredictionAppService:
    """
    Obtém uma instância do serviço de aplicação de previsões.
    """
    return DependencyContainer.get('prediction_app_service')


@login_required
@require_GET
def get_user_predictions(request: HttpRequest, round_id: int) -> JsonResponse:
    """
    Retorna todas as previsões do usuário para uma rodada específica.
    """
    prediction_app_service = get_prediction_app_service()
    user = request.user
    
    try:
        predictions = prediction_app_service.get_user_predictions_by_round(
            user_id=user.id,
            round_id=round_id
        )
        
        predictions_data = [{
            'id': prediction.id,
            'match_id': prediction.match_id,
            'home_team': prediction.match.home_team.name if prediction.match and prediction.match.home_team else None,
            'away_team': prediction.match.away_team.name if prediction.match and prediction.match.away_team else None,
            'home_score': prediction.home_score,
            'away_score': prediction.away_score,
            'points_earned': prediction.points_earned,
            'created_at': prediction.created_at.isoformat() if prediction.created_at else None
        } for prediction in predictions]
        
        return JsonResponse({
            'success': True,
            'predictions': predictions_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def create_prediction(request: HttpRequest) -> JsonResponse:
    """
    Cria ou atualiza uma previsão para uma partida.
    """
    prediction_app_service = get_prediction_app_service()
    user = request.user
    
    try:
        data = json.loads(request.body)
        
        required_fields = ['match_id', 'home_score', 'away_score']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'message': f'Campo obrigatório ausente: {field}'
                }, status=400)
        
        prediction = prediction_app_service.create_or_update_prediction(
            user_id=user.id,
            match_id=data['match_id'],
            home_score=data['home_score'],
            away_score=data['away_score']
        )
        
        return JsonResponse({
            'success': True,
            'prediction_id': prediction.id,
            'message': 'Previsão salva com sucesso!'
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
def get_round_predictions_summary(request: HttpRequest, round_id: int) -> JsonResponse:
    """
    Retorna um resumo das previsões de uma rodada específica.
    """
    prediction_app_service = get_prediction_app_service()
    user = request.user
    
    try:
        summary = prediction_app_service.get_round_predictions_summary(
            user_id=user.id,
            round_id=round_id
        )
        
        return JsonResponse({
            'success': True,
            'total_matches': summary.get('total_matches', 0),
            'predicted_matches': summary.get('predicted_matches', 0),
            'total_points': summary.get('total_points', 0),
            'matches_with_exact_score': summary.get('matches_with_exact_score', 0),
            'matches_with_correct_result': summary.get('matches_with_correct_result', 0)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_GET
def get_championship_predictions_summary(request: HttpRequest, championship_id: int) -> JsonResponse:
    """
    Retorna um resumo das previsões de um campeonato específico.
    """
    prediction_app_service = get_prediction_app_service()
    user = request.user
    
    try:
        summary = prediction_app_service.get_championship_predictions_summary(
            user_id=user.id,
            championship_id=championship_id
        )
        
        return JsonResponse({
            'success': True,
            'total_matches': summary.get('total_matches', 0),
            'predicted_matches': summary.get('predicted_matches', 0),
            'total_points': summary.get('total_points', 0),
            'accuracy_percentage': summary.get('accuracy_percentage', 0),
            'average_points_per_match': summary.get('average_points_per_match', 0)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_GET
def get_prediction_statistics(request: HttpRequest, match_id: int) -> JsonResponse:
    """
    Retorna estatísticas de previsões para uma partida específica.
    """
    prediction_app_service = get_prediction_app_service()
    
    try:
        statistics = prediction_app_service.get_match_prediction_statistics(match_id)
        
        return JsonResponse({
            'success': True,
            'total_predictions': statistics.get('total_predictions', 0),
            'home_win_percentage': statistics.get('home_win_percentage', 0),
            'draw_percentage': statistics.get('draw_percentage', 0),
            'away_win_percentage': statistics.get('away_win_percentage', 0),
            'most_predicted_score': statistics.get('most_predicted_score', '0-0'),
            'average_home_score': statistics.get('average_home_score', 0),
            'average_away_score': statistics.get('average_away_score', 0)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def calculate_prediction_points(request: HttpRequest, match_id: int) -> JsonResponse:
    """
    Calcula os pontos das previsões para uma partida específica.
    Só pode ser usado por administradores.
    """
    prediction_app_service = get_prediction_app_service()
    user = request.user
    
    if not user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'Acesso negado. Apenas administradores podem executar esta operação.'
        }, status=403)
    
    try:
        data = json.loads(request.body)
        
        if 'home_score' not in data or 'away_score' not in data:
            return JsonResponse({
                'success': False,
                'message': 'Campos obrigatórios ausentes: home_score, away_score'
            }, status=400)
        
        result = prediction_app_service.calculate_prediction_points(
            match_id=match_id,
            home_score=data['home_score'],
            away_score=data['away_score']
        )
        
        return JsonResponse({
            'success': True,
            'predictions_calculated': result.get('predictions_calculated', 0),
            'total_points_distributed': result.get('total_points_distributed', 0),
            'message': 'Pontos das previsões calculados com sucesso!'
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