import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'futmundi.settings')
django.setup()

from django.db import connection

# Listar todas as tabelas
print("Tabelas no banco de dados:")
tables = connection.introspection.table_names()
for table in tables:
    print(f"- {table}")

# Verificar se a tabela scope_levels existe
if 'scope_levels' in tables:
    print("\nA tabela scope_levels EXISTE no banco de dados.")
else:
    print("\nA tabela scope_levels NÃO EXISTE no banco de dados.")

# Obter colunas da tabela scope (apenas se existir)
if 'scopes' in tables:
    print("\nColunas da tabela scopes:")
    columns = connection.introspection.get_table_description(connection.cursor(), 'scopes')
    for column in columns:
        print(f"- {column.name}") 