import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'futmundi.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from administrativo.models import User

# Verificar se existe usuário
users = User.objects.all()
print(f"Total de usuários encontrados: {users.count()}")

if users.exists():
    # Atualizar o primeiro usuário para ser superusuário com senha conhecida
    admin_user = users.first()
    admin_user.username = admin_user.email if admin_user.email else 'admin'
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.password = make_password('admin123')  # Senha temporária: admin123
    admin_user.save()
    print(f"Usuário atualizado: {admin_user.username}")
    print(f"Senha definida para: admin123")
else:
    # Criar um novo superusuário
    User.objects.create(
        username='admin',
        email='admin@futmundi.com',
        is_staff=True,
        is_superuser=True,
        password=make_password('admin123'),
        first_name='Administrador',
        name='Administrador Sistema',
        is_active=True
    )
    print("Novo superusuário criado:")
    print("Username: admin")
    print("Email: admin@futmundi.com")
    print("Senha: admin123")

print("\nAcesse o sistema com estas credenciais e depois altere a senha por segurança!") 