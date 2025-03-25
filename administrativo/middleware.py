import json
import time
from datetime import datetime
from django.http import HttpResponse

class ApiDebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Processa requisições para o endpoint de futligas jogadores (com ou sem prefixo administrativo)
        if '/futligas/jogadores/salvar/' in request.path:
            print(f"\n[API-DEBUG] Detectada requisição para futligas jogadores: {request.path}")
            
            # Redireciona automaticamente requisições sem o prefixo 'administrativo'
            if request.path == '/futligas/jogadores/salvar/':
                print(f"[API-DEBUG] Redirecionando de {request.path} para /administrativo/futligas/jogadores/salvar/")
                
                # Preservar o corpo da requisição e o método
                request.path = '/administrativo/futligas/jogadores/salvar/'
                request.path_info = '/administrativo/futligas/jogadores/salvar/'
                
            return self.process_futligas_request(request)
        else:
            # Para outras requisições, apenas passa adiante
            return self.get_response(request)
    
    def process_futligas_request(self, request):
        # Grava informações da requisição
        request_time = datetime.now()
        request_id = int(time.time() * 1000)
        
        # Loga a requisição
        self.log_request(request, request_id, request_time)
        
        # Obtém a resposta
        response = self.get_response(request)
        
        # Loga a resposta
        self.log_response(request, response, request_id, request_time)
        
        return response
    
    def log_request(self, request, request_id, request_time):
        print(f"\n[API-DEBUG] ====== NOVA REQUISIÇÃO {request_id} - {request_time} ======")
        print(f"[API-DEBUG] Método: {request.method}")
        print(f"[API-DEBUG] Path: {request.path}")
        print(f"[API-DEBUG] Usuário: {request.user.username if request.user.is_authenticated else 'Anônimo'}")
        
        # Tenta capturar o corpo da requisição
        if request.method == 'POST':
            try:
                # Para requisições JSON
                if 'application/json' in request.headers.get('Content-Type', ''):
                    body = json.loads(request.body.decode('utf-8'))
                    
                    # Cria uma cópia sem as imagens para ser mais legível
                    body_copy = body.copy() if isinstance(body, dict) else body
                    
                    if isinstance(body_copy, dict):
                        if 'prizes' in body_copy:
                            for prize in body_copy['prizes']:
                                if 'image' in prize and prize['image'] and isinstance(prize['image'], str) and prize['image'].startswith('data:'):
                                    prize['image'] = "[IMAGEM BASE64]"
                        
                        if 'levels' in body_copy:
                            for level in body_copy['levels']:
                                if 'image' in level and level['image'] and isinstance(level['image'], str) and level['image'].startswith('data:'):
                                    level['image'] = "[IMAGEM BASE64]"
                    
                    print(f"[API-DEBUG] Corpo: {json.dumps(body_copy, indent=2)}")
                else:
                    # Para requisições form-data
                    print(f"[API-DEBUG] Dados POST: {dict(request.POST)}")
                    if request.FILES:
                        file_names = {name: f.name for name, f in request.FILES.items()}
                        print(f"[API-DEBUG] Arquivos: {file_names}")
            except Exception as e:
                print(f"[API-DEBUG] Erro ao processar corpo da requisição: {str(e)}")
        
        print(f"[API-DEBUG] Cabeçalhos: {dict(request.headers)}")
    
    def log_response(self, request, response, request_id, request_time):
        duration = datetime.now() - request_time
        print(f"\n[API-DEBUG] ====== RESPOSTA {request_id} - Duração: {duration.total_seconds():.3f}s ======")
        print(f"[API-DEBUG] Status: {response.status_code}")
        
        # Tenta capturar o corpo da resposta
        if hasattr(response, 'content'):
            try:
                if 'application/json' in response.get('Content-Type', ''):
                    body = json.loads(response.content.decode('utf-8'))
                    print(f"[API-DEBUG] Corpo: {json.dumps(body, indent=2)}")
                else:
                    if len(response.content) < 1000:
                        print(f"[API-DEBUG] Conteúdo: {response.content.decode('utf-8')}")
                    else:
                        print(f"[API-DEBUG] Conteúdo: [muito grande, {len(response.content)} bytes]")
            except Exception as e:
                print(f"[API-DEBUG] Erro ao processar corpo da resposta: {str(e)}")
        
        print(f"[API-DEBUG] Cabeçalhos: {dict(response.headers)}")
        print(f"[API-DEBUG] ====== FIM RESPOSTA {request_id} ======\n")
