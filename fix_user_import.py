import re

with open('administrativo/views.py', 'r', encoding='utf-8') as file:
    content = file.read()

# Remover a importação User do django.contrib.auth.models
content = re.sub(r'from django\.contrib\.auth\.models import User', 'from django.contrib.auth import get_user_model\nUser = get_user_model()', content)

with open('administrativo/views.py', 'w', encoding='utf-8') as file:
    file.write(content)

print('Arquivo administrativo/views.py atualizado com sucesso.') 