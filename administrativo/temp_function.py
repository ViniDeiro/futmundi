@login_required
def pacotes_futcoins_ativos(request):
    '''
    API para retornar pacotes de futcoins ativos em formato JSON
    '''
    try:
        # Busca todos os pacotes de futcoins ativos
        pacotes = FutcoinPackage.objects.filter(enabled=True).order_by('name')
        
        # Formata os pacotes para o formato de resposta
        pacotes_json = []
        for pacote in pacotes:
            pacotes_json.append({
                'id': pacote.id,
                'name': pacote.name,
                'price': float(pacote.promotional_price) if hasattr(pacote, 'promotional_price') and pacote.promotional_price else float(pacote.full_price)
            })
        
        # Retorna os pacotes em formato JSON
        return JsonResponse({
            'success': True,
            'pacotes': pacotes_json
        })
    except Exception as e:
        # Em caso de erro, retorna uma resposta de erro
        import traceback
        print(f'Erro ao buscar pacotes de futcoins: {str(e)}')
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'Erro ao buscar pacotes de futcoins: {str(e)}',
            'pacotes': []
        })
