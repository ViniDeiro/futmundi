import os
import re

def fix_static_tags(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Remove as aspas escapadas dentro das tags static
    content = re.sub(
        r'{%\s*static\s*\\\'(.*?)\\\'\s*%}',
        r"{% static '\1' %}",
        content
    )

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def main():
    templates_dir = 'administrativo/templates/administrativo'
    for filename in os.listdir(templates_dir):
        if filename.endswith('.html'):
            file_path = os.path.join(templates_dir, filename)
            print(f'Corrigindo tags static em {filename}...')
            fix_static_tags(file_path)
            print(f'✓ {filename} corrigido!')

if __name__ == '__main__':
    main() 