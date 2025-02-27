import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'futmundi.settings')
django.setup()

from django.db import connection
from django.contrib.auth.hashers import make_password
from administrativo.models import User

# Verificar se existem administradores
with connection.cursor() as cursor:
    cursor.execute("SELECT * FROM administrators")
    columns = [col[0] for col in cursor.description]
    admins = [dict(zip(columns, row)) for row in cursor.fetchall()]

# Ver a estrutura da tabela users para garantir que incluímos todos os campos
with connection.cursor() as cursor:
    cursor.execute("DESCRIBE users")
    user_fields = cursor.fetchall()
    print("Campos na tabela users:")
    for field in user_fields:
        print(f"  - {field[0]} ({field[1]})")

# Adicionar o administrador diretamente na tabela
if admins:
    print(f"\nEncontrados {len(admins)} administradores no banco de dados")
    
    for admin in admins:
        # Usar SQL direto para evitar problemas com o ORM
        admin_email = admin['email']
        admin_name = admin['name']
        admin_password = admin['password']
        with connection.cursor() as cursor:
            # Verificar se já existe usuário com esse email
            cursor.execute("SELECT id FROM users WHERE email = %s", [admin_email])
            if cursor.fetchone():
                print(f"Usuário com email {admin_email} já existe, pulando...")
                continue
            
            # Inserir usuário diretamente via SQL
            username = admin_email.split('@')[0]
            cursor.execute("""
                INSERT INTO users 
                (username, email, password, name, first_name, last_name, is_superuser, is_staff, is_active, date_joined, 
                futcoins, current_plan, registration_date, current_period, period_renewals, facebook_linked, google_linked, 
                total_spent, plan_spent, packages_spent, is_star) 
                VALUES (%s, %s, %s, %s, %s, '', 1, 1, 1, NOW(), 0, 'common', NOW(), 'monthly', 0, 0, 0, 0, 0, 0, 0)
            """, [username, admin_email, admin_password, admin_name, admin_name])
            
            print(f"Usuário {username} criado com sucesso!")
    
    print("\nUsuários copiados com sucesso!")
    print("Tente fazer login com o email e senha existentes no banco de dados.")
else:
    print("Nenhum administrador encontrado no banco de dados.") 