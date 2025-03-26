"""
Controlador para operações de pagamentos.
"""

from django.http import JsonResponse, HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
import json
from typing import Dict, Any, List
import datetime

from application.services.user_app_service import UserAppService
from domain.config import DependencyContainer


def get_user_app_service() -> UserAppService:
    """
    Obtém uma instância do serviço de aplicação de usuários (que gerencia pagamentos).
    """
    return DependencyContainer.get('user_app_service')


@login_required
@require_GET
def get_payment_methods(request: HttpRequest) -> JsonResponse:
    """
    Retorna os métodos de pagamento disponíveis.
    """
    user_app_service = get_user_app_service()
    user = request.user
    
    try:
        payment_methods = user_app_service.get_user_payment_methods(user.id)
        
        payment_methods_data = [{
            'id': method.id,
            'type': method.type,
            'last_digits': method.last_digits,
            'expiry_date': method.expiry_date.isoformat() if method.expiry_date else None,
            'holder_name': method.holder_name,
            'is_default': method.is_default,
            'created_at': method.created_at.isoformat() if method.created_at else None
        } for method in payment_methods]
        
        return JsonResponse({
            'success': True,
            'payment_methods': payment_methods_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def add_payment_method(request: HttpRequest) -> JsonResponse:
    """
    Adiciona um novo método de pagamento para o usuário.
    """
    user_app_service = get_user_app_service()
    user = request.user
    
    try:
        data = json.loads(request.body)
        
        required_fields = ['type', 'number', 'holder_name']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'message': f'Campo obrigatório ausente: {field}'
                }, status=400)
        
        # Não armazenamos o número completo por segurança, apenas os últimos dígitos
        card_number = data['number']
        last_digits = card_number[-4:] if len(card_number) >= 4 else card_number
        
        # Processamos a data de expiração se fornecida
        expiry_date = None
        if 'expiry_month' in data and 'expiry_year' in data:
            expiry_month = int(data['expiry_month'])
            expiry_year = int(data['expiry_year'])
            # Último dia do mês de expiração
            if expiry_month == 12:
                expiry_date = datetime.date(expiry_year + 1, 1, 1) - datetime.timedelta(days=1)
            else:
                expiry_date = datetime.date(expiry_year, expiry_month + 1, 1) - datetime.timedelta(days=1)
        
        payment_method = user_app_service.add_payment_method(
            user_id=user.id,
            type=data['type'],
            last_digits=last_digits,
            holder_name=data['holder_name'],
            expiry_date=expiry_date,
            is_default=data.get('is_default', False)
        )
        
        return JsonResponse({
            'success': True,
            'payment_method_id': payment_method.id,
            'message': 'Método de pagamento adicionado com sucesso!'
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
def remove_payment_method(request: HttpRequest, payment_method_id: int) -> JsonResponse:
    """
    Remove um método de pagamento do usuário.
    """
    user_app_service = get_user_app_service()
    user = request.user
    
    try:
        success = user_app_service.remove_payment_method(
            user_id=user.id,
            payment_method_id=payment_method_id
        )
        
        if not success:
            return JsonResponse({
                'success': False,
                'message': 'Método de pagamento não encontrado ou não pertence ao usuário.'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'message': 'Método de pagamento removido com sucesso!'
        })
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@require_POST
def process_subscription_payment(request: HttpRequest) -> JsonResponse:
    """
    Processa o pagamento de uma assinatura.
    """
    user_app_service = get_user_app_service()
    user = request.user
    
    try:
        data = json.loads(request.body)
        
        required_fields = ['plan_id', 'payment_method_id']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'message': f'Campo obrigatório ausente: {field}'
                }, status=400)
        
        payment_result = user_app_service.process_subscription_payment(
            user_id=user.id,
            plan_id=data['plan_id'],
            payment_method_id=data['payment_method_id']
        )
        
        if payment_result.get('success'):
            return JsonResponse({
                'success': True,
                'transaction_id': payment_result.get('transaction_id'),
                'message': 'Pagamento processado com sucesso!'
            })
        else:
            return JsonResponse({
                'success': False,
                'error_code': payment_result.get('error_code'),
                'message': payment_result.get('message', 'Erro ao processar pagamento.')
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
def get_payment_history(request: HttpRequest) -> JsonResponse:
    """
    Retorna o histórico de pagamentos do usuário.
    """
    user_app_service = get_user_app_service()
    user = request.user
    
    try:
        payments = user_app_service.get_user_payment_history(user.id)
        
        payments_data = [{
            'id': payment.id,
            'amount': payment.amount,
            'currency': payment.currency,
            'status': payment.status,
            'description': payment.description,
            'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
            'payment_method': payment.payment_method_last_digits,
            'transaction_id': payment.transaction_id
        } for payment in payments]
        
        return JsonResponse({
            'success': True,
            'payments': payments_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_GET
def get_subscription_plans(request: HttpRequest) -> JsonResponse:
    """
    Retorna os planos de assinatura disponíveis.
    """
    user_app_service = get_user_app_service()
    
    try:
        plans = user_app_service.get_subscription_plans()
        
        plans_data = [{
            'id': plan.id,
            'name': plan.name,
            'description': plan.description,
            'price': plan.price,
            'currency': plan.currency,
            'duration_days': plan.duration_days,
            'features': plan.features,
            'is_popular': plan.is_popular,
            'discount_percentage': plan.discount_percentage
        } for plan in plans]
        
        return JsonResponse({
            'success': True,
            'plans': plans_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_GET
def get_user_subscription(request: HttpRequest) -> JsonResponse:
    """
    Retorna informações sobre a assinatura atual do usuário.
    """
    user_app_service = get_user_app_service()
    user = request.user
    
    try:
        subscription = user_app_service.get_user_subscription(user.id)
        
        if not subscription:
            return JsonResponse({
                'success': True,
                'has_subscription': False
            })
        
        subscription_data = {
            'id': subscription.id,
            'plan_name': subscription.plan_name,
            'start_date': subscription.start_date.isoformat() if subscription.start_date else None,
            'end_date': subscription.end_date.isoformat() if subscription.end_date else None,
            'is_active': subscription.is_active,
            'auto_renew': subscription.auto_renew,
            'next_billing_date': subscription.next_billing_date.isoformat() if subscription.next_billing_date else None,
            'price_paid': subscription.price_paid,
            'currency': subscription.currency
        }
        
        return JsonResponse({
            'success': True,
            'has_subscription': True,
            'subscription': subscription_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def cancel_subscription(request: HttpRequest) -> JsonResponse:
    """
    Cancela a assinatura atual do usuário.
    """
    user_app_service = get_user_app_service()
    user = request.user
    
    try:
        success = user_app_service.cancel_user_subscription(user.id)
        
        if not success:
            return JsonResponse({
                'success': False,
                'message': 'Nenhuma assinatura ativa encontrada para cancelar.'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'message': 'Assinatura cancelada com sucesso!'
        })
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400) 