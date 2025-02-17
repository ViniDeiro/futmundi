import os
import re

def update_urls(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Mapeamento de URLs
    url_mapping = {
        'usuarios.html': '{% url "administrativo:usuarios" %}',
        'ambitos.html': '{% url "administrativo:ambitos" %}',
        'campeonatos.html': '{% url "administrativo:campeonatos" %}',
        'templates.html': '{% url "administrativo:templates" %}',
        'times.html': '{% url "administrativo:times" %}',
        'futcoins.html': '{% url "administrativo:futcoins" %}',
        'planos.html': '{% url "administrativo:planos" %}',
        'futligas-classicas.html': '{% url "administrativo:futligas_classicas" %}',
        'futligas-jogadores.html': '{% url "administrativo:futligas_jogadores" %}',
        'continentes.html': '{% url "administrativo:continentes" %}',
        'paises.html': '{% url "administrativo:paises" %}',
        'estados.html': '{% url "administrativo:estados" %}',
        'parametros.html': '{% url "administrativo:parametros" %}',
        'termo.html': '{% url "administrativo:termo" %}',
        'notificacoes.html': '{% url "administrativo:notificacoes" %}',
        'relatorios.html': '{% url "administrativo:relatorios" %}',
        'administradores.html': '{% url "administrativo:administradores" %}',
        'login.html': '{% url "administrativo:login" %}',
        'usuario-editar.html': '{% url "administrativo:usuario_editar" %}',
        'ambito-editar.html': '{% url "administrativo:ambito_editar" %}',
        'campeonato-novo.html': '{% url "administrativo:campeonato_novo" %}',
        'time-novo.html': '{% url "administrativo:time_novo" %}',
        'pacote-futcoin-novo.html': '{% url "administrativo:pacote_futcoin_novo" %}',
        'pacote-plano-novo.html': '{% url "administrativo:pacote_plano_novo" %}',
        'futliga-classica-novo.html': '{% url "administrativo:futliga_classica_novo" %}',
        'continente-novo.html': '{% url "administrativo:continente_novo" %}',
        'pais-novo.html': '{% url "administrativo:pais_novo" %}',
        'estado-novo.html': '{% url "administrativo:estado_novo" %}',
        'notificacao-novo.html': '{% url "administrativo:notificacao_novo" %}',
        'template-novo.html': '{% url "administrativo:template_novo" %}'
    }

    # Atualiza todos os links href que terminam em .html
    for old_url, new_url in url_mapping.items():
        content = re.sub(
            f'href="{old_url}"',
            f'href="{new_url}"',
            content
        )

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def main():
    templates_dir = 'administrativo/templates/administrativo'
    for filename in os.listdir(templates_dir):
        if filename.endswith('.html'):
            file_path = os.path.join(templates_dir, filename)
            print(f'Atualizando URLs em {filename}...')
            update_urls(file_path)
            print(f'✓ {filename} atualizado!')

if __name__ == '__main__':
    main() 