import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'futmundi.settings')
django.setup()

from django.db import connection
from django.utils import timezone
from administrativo.models import Scope, ScopeLevel

def create_default_scope_levels():
    """
    Cria os níveis padrão para cada âmbito existente.
    """
    # Obtém todos os âmbitos
    scopes = Scope.objects.all()
    
    # Contador de níveis criados
    created_count = 0
    
    for scope in scopes:
        # Verifica se o âmbito já tem níveis
        existing_levels = ScopeLevel.objects.filter(scope=scope).count()
        
        if existing_levels == 0:
            print(f"Criando níveis para o âmbito: {scope.name}")
            
            # Cria níveis de alavancagem (1, 2 e 3)
            for level in range(1, 4):
                ScopeLevel.objects.create(
                    scope=scope,
                    type='leverage',
                    level=level,
                    points=level * 10,  # Valores padrão: 10, 20, 30
                    futcoins=level * 5,  # Valores padrão: 5, 10, 15
                    is_active=True,
                    created_at=timezone.now()
                )
                created_count += 1
            
            # Cria níveis de seguro (1, 2 e 3)
            for level in range(1, 4):
                ScopeLevel.objects.create(
                    scope=scope,
                    type='insurance',
                    level=level,
                    points=level * 5,  # Valores padrão: 5, 10, 15
                    futcoins=level * 3,  # Valores padrão: 3, 6, 9
                    is_active=True,
                    created_at=timezone.now()
                )
                created_count += 1
        else:
            print(f"O âmbito '{scope.name}' já possui níveis ({existing_levels})")
    
    return created_count

if __name__ == "__main__":
    print("Iniciando criação de níveis padrão para âmbitos...")
    count = create_default_scope_levels()
    print(f"Concluído! {count} níveis foram criados.") 