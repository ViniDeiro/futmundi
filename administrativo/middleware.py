from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.conf import settings

class AuthRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # URLs que não requerem autenticação
        self.exempt_urls = [
            reverse('administrativo:login'),  # URL de login
        ]

    def __call__(self, request):
        # O middleware é aplicado antes da view
        if not request.user.is_authenticated:
            # Verifica se a URL atual não está na lista de exceções
            current_url = request.path_info
            if current_url not in self.exempt_urls:
                # Redireciona para o login se não estiver autenticado
                return redirect(settings.LOGIN_URL)

        # Continua para a próxima etapa do middleware ou para a view
        response = self.get_response(request)
        return response 