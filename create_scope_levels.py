import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'futmundi.settings')
django.setup()

from django.db import connection
from django.conf import settings
from django.core import management

# Verificar se a tabela scope_levels existe
connection_introspection = connection.introspection
tables = connection_introspection.table_names()

if 'scope_levels' not in tables:
    print("A tabela scope_levels não existe. Criando migração para adicioná-la...")
    
    # Gera uma migração vazia
    management.call_command('makemigrations', 'administrativo', empty=True, name='add_missing_scope_levels_table')
    
    # Nome da migração gerada
    latest_migration = max([f for f in os.listdir('administrativo/migrations') if f.startswith('0') and f.endswith('.py')])
    migration_path = f'administrativo/migrations/{latest_migration}'
    
    print(f"Migração gerada: {migration_path}")
    print("Edite a migração manualmente para adicionar o código SQL para criar a tabela scope_levels.")
    print("Depois, execute: python manage.py migrate")
else:
    print("A tabela scope_levels já existe no banco de dados.") 