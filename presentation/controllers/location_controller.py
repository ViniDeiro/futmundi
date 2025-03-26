"""
Controlador para operações de localização.
"""

from django.http import JsonResponse, HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
import json
from typing import Dict, Any, List

from application.services.user_app_service import UserAppService
from domain.config import DependencyContainer


def get_user_app_service() -> UserAppService:
    """
    Obtém uma instância do serviço de aplicação de usuários.
    """
    return DependencyContainer.get('user_app_service')


@login_required
@require_GET
def get_countries(request: HttpRequest) -> JsonResponse:
    """
    Retorna a lista de países disponíveis.
    """
    user_app_service = get_user_app_service()
    
    try:
        countries = user_app_service.get_all_countries()
        
        countries_data = [{
            'code': country.code,
            'name': country.name,
            'flag_url': country.flag_url if hasattr(country, 'flag_url') else None
        } for country in countries]
        
        return JsonResponse({
            'success': True,
            'countries': countries_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_GET
def get_states_by_country(request: HttpRequest, country_code: str) -> JsonResponse:
    """
    Retorna a lista de estados/províncias para um país específico.
    """
    user_app_service = get_user_app_service()
    
    try:
        states = user_app_service.get_states_by_country(country_code)
        
        states_data = [{
            'code': state.code,
            'name': state.name,
            'country_code': state.country_code
        } for state in states]
        
        return JsonResponse({
            'success': True,
            'states': states_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_GET
def get_cities_by_state(request: HttpRequest, country_code: str, state_code: str) -> JsonResponse:
    """
    Retorna a lista de cidades para um estado/província específico.
    """
    user_app_service = get_user_app_service()
    
    try:
        cities = user_app_service.get_cities_by_state(country_code, state_code)
        
        cities_data = [{
            'id': city.id,
            'name': city.name,
            'state_code': city.state_code,
            'country_code': city.country_code
        } for city in cities]
        
        return JsonResponse({
            'success': True,
            'cities': cities_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def update_user_location(request: HttpRequest) -> JsonResponse:
    """
    Atualiza as informações de localização do usuário.
    """
    user_app_service = get_user_app_service()
    user = request.user
    
    try:
        data = json.loads(request.body)
        
        required_fields = ['country_code', 'state_code', 'city_id']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'message': f'Campo obrigatório ausente: {field}'
                }, status=400)
        
        success = user_app_service.update_user_location(
            user_id=user.id,
            country_code=data['country_code'],
            state_code=data['state_code'],
            city_id=data['city_id']
        )
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Localização atualizada com sucesso!'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Não foi possível atualizar a localização.'
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


@login_required
@require_GET
def search_cities(request: HttpRequest) -> JsonResponse:
    """
    Pesquisa cidades por nome.
    """
    user_app_service = get_user_app_service()
    
    try:
        query = request.GET.get('q', '')
        
        if not query or len(query) < 3:
            return JsonResponse({
                'success': False,
                'message': 'A consulta de pesquisa deve ter pelo menos 3 caracteres.'
            }, status=400)
        
        cities = user_app_service.search_cities(query)
        
        cities_data = [{
            'id': city.id,
            'name': city.name,
            'state_code': city.state_code,
            'state_name': city.state_name if hasattr(city, 'state_name') else None,
            'country_code': city.country_code,
            'country_name': city.country_name if hasattr(city, 'country_name') else None
        } for city in cities]
        
        return JsonResponse({
            'success': True,
            'cities': cities_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500) 