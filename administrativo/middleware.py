import json
import time
from datetime import datetime
from django.http import HttpResponse, JsonResponse
from django.urls import resolve
from django.urls.exceptions import Resolver404
from django.contrib.auth.models import AnonymousUser

# Classe de usuário personalizada para o middleware
class AdminUser(AnonymousUser):
    def __init__(self, admin_id=None, username=None):
        super().__init__()
        self._admin_id = admin_id
        self._username = username
        self._is_authenticated = admin_id is not None
    
    @property
    def is_authenticated(self):
        return self._is_authenticated
    
    @property
    def username(self):
        return self._username
    
    @property
    def id(self):
        return self._admin_id

class ApiDebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Processa requisições para o endpoint de futligas jogadores (com ou sem prefixo administrativo)
        if '/futligas/jogadores/salvar/' in request.path:
            print(f"\n[API-DEBUG] Detectada requisição para futligas jogadores: {request.path}")
            
            # Redireciona automaticamente requisições sem o prefixo 'administrativo'
            if request.path == '/futligas/jogadores/salvar/':
                print(f"[API-DEBUG] Processando requisição de {request.path} para view correta")
                
                # Em vez de modificar a requisição, vamos encontrar a view correta e invocá-la
                try:
                    # Tentamos resolver a URL com o prefixo 'administrativo'
                    admin_path = '/administrativo/futligas/jogadores/salvar/'
                    resolved = resolve(admin_path)
                    
                    # Adicionar o atributo user ao objeto request
                    # Verificar se há uma sessão de admin
                    admin_id = None
                    username = None
                    
                    if 'admin_id' in request.session:
                        from administrativo.models import Administrator
                        try:
                            admin = Administrator.objects.get(id=request.session['admin_id'])
                            admin_id = admin.id
                            username = admin.name
                            print(f"[API-DEBUG] Admin encontrado: {username} (ID: {admin_id})")
                        except Exception as e:
                            print(f"[API-DEBUG] Erro ao obter admin: {str(e)}")
                    
                    # Criar um objeto de usuário personalizado
                    request.user = AdminUser(admin_id=admin_id, username=username)
                        
                    # Aqui chamamos a view diretamente com a requisição atual
                    print(f"[API-DEBUG] Chamando view {resolved.func.__name__} diretamente")
                    return resolved.func(request)
                    
                except Resolver404:
                    print(f"[API-DEBUG] Não foi possível resolver a URL {admin_path}")
                    return JsonResponse({
                        'success': False,
                        'message': 'Erro de roteamento interno'
                    }, status=500)
            
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
