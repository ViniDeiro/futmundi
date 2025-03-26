"""
Controlador para operações de usuários.
"""

from django.http import JsonResponse, HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json
import datetime

from application.services.user_app_service import UserAppService
from domain.config import DependencyContainer


def get_user_app_service() -> UserAppService:
    """
    Obtém uma instância do serviço de aplicação de usuários.
    """
    return DependencyContainer.get('user_app_service')


@login_required
def get_user_profile(request: HttpRequest) -> JsonResponse:
    """
    Obtém o perfil do usuário autenticado.
    """
    user = request.user
    
    # Dados básicos do usuário para o perfil
    profile_data = {
        'id': user.id,
        'username': user.username,
        'full_name': user.get_full_name(),
        'futcoins': user.futcoins,
        'is_star': user.is_star,
        'current_plan': user.current_plan,
        'registration_date': user.registration_date.isoformat() if user.registration_date else None,
    }
    
    return JsonResponse(profile_data)


@login_required
@require_POST
def add_daily_reward(request: HttpRequest) -> JsonResponse:
    """
    Adiciona a recompensa diária ao usuário.
    """
    user = request.user
    user_app_service = get_user_app_service()
    
    # Verifica se o usuário já recebeu a recompensa hoje
    if user.last_daily_reward and user.last_daily_reward.date() == datetime.date.today():
        return JsonResponse({
            'success': False,
            'message': 'Você já recebeu sua recompensa diária hoje.'
        }, status=400)
    
    try:
        # Adiciona recompensa com base no dia da semana atual
        day_of_week = datetime.date.today().weekday()
        updated_user = user_app_service.add_daily_reward(user.id, day_of_week)
        
        # Atualiza a data da última recompensa
        updated_user.last_daily_reward = datetime.datetime.now()
        updated_user.save()
        
        return JsonResponse({
            'success': True,
            'futcoins': updated_user.futcoins,
            'message': 'Recompensa diária adicionada com sucesso!'
        })
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@require_POST
def process_purchase(request: HttpRequest) -> JsonResponse:
    """
    Processa uma compra para o usuário.
    """
    user = request.user
    user_app_service = get_user_app_service()
    
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        price = int(data.get('price', 0))
        
        if not item_id:
            return JsonResponse({
                'success': False,
                'message': 'ID do item não fornecido.'
            }, status=400)
        
        success = user_app_service.process_purchase(user.id, item_id, price)
        
        if success:
            # Atualiza o usuário após a compra
            user.refresh_from_db()
            
            return JsonResponse({
                'success': True,
                'futcoins': user.futcoins,
                'message': 'Compra realizada com sucesso!'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Futcoins insuficientes para esta compra.'
            }, status=400)
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