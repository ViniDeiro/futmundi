import os
import re

def fix_links(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Corrige o link de logout
    content = re.sub(
        r'href="{% url \'administrativo:login\' %}"([^>]*>)[^<]*<i class="fa fa-sign-out"></i>\s*Sair',
        r'href="{% url \'administrativo:logout\' %}\1<i class="fa fa-sign-out"></i> Sair',
        content
    )

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def main():
    templates_dir = 'administrativo/templates/administrativo'
    for filename in os.listdir(templates_dir):
        if filename.endswith('.html'):
            file_path = os.path.join(templates_dir, filename)
            print(f'Corrigindo links em {filename}...')
            fix_links(file_path)
            print(f'✓ {filename} corrigido!')

if __name__ == '__main__':
    main() 