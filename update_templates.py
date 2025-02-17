import os
import re

def update_template(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Adiciona {% load static %} no início do arquivo se não existir
    if '{% load static %}' not in content:
        content = '{% load static %}\n' + content

    # Atualiza os caminhos dos arquivos CSS
    content = re.sub(
        r'href="(css|font-awesome|fonts)/(.*?)"',
        r'href="{% static \'administrativo/\1/\2\' %}"',
        content
    )

    # Atualiza os caminhos das imagens
    content = re.sub(
        r'src="img/(.*?)"',
        r'src="{% static \'administrativo/img/\1\' %}"',
        content
    )

    # Atualiza os caminhos dos arquivos JavaScript
    content = re.sub(
        r'src="js/(.*?)"',
        r'src="{% static \'administrativo/js/\1\' %}"',
        content
    )

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def main():
    templates_dir = 'administrativo/templates/administrativo'
    for filename in os.listdir(templates_dir):
        if filename.endswith('.html'):
            file_path = os.path.join(templates_dir, filename)
            print(f'Atualizando {filename}...')
            update_template(file_path)
            print(f'✓ {filename} atualizado!')

if __name__ == '__main__':
    main() 