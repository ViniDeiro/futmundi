class DebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'POST' and ('plano_editar' in request.path or 'pacote-plano-novo' in request.path):
            print("\n\n==== DEBUG MIDDLEWARE - INÍCIO ====")
            print(f"PATH: {request.path}")
            print("POST DATA:")
            for key, value in request.POST.items():
                print(f"{key}: {value}")
            
            # Verificação específica dos campos problemáticos
            print("\nCAMPOS ESPECÍFICOS PARA NOVOS JOGADORES:")
            print(f"promotion_days: {request.POST.get('promotion_days', 'NÃO ENCONTRADO')}")
            print(f"futcoins_package_benefit: {request.POST.get('futcoins_package_benefit', 'NÃO ENCONTRADO')}")
            print(f"package_renewals: {request.POST.get('package_renewals', 'NÃO ENCONTRADO')}")
            
            print("\nCAMPOS DE CÓDIGO DE PRODUTO:")
            print(f"android_product_code: {request.POST.get('android_product_code', 'NÃO ENCONTRADO')}")
            print(f"apple_product_code: {request.POST.get('apple_product_code', 'NÃO ENCONTRADO')}")
            print(f"gateway_product_code: {request.POST.get('gateway_product_code', 'NÃO ENCONTRADO')}")
            
            print("==== DEBUG MIDDLEWARE - FIM ====\n\n")
        
        response = self.get_response(request)
        return response 