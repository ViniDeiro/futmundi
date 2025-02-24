#!/usr/bin/env bash
# exit on error
set -o errexit

# Instala as dependências
pip install -r requirements.txt

# Cria diretórios necessários
mkdir -p administrativo/static/administrativo/js/plugins/dataTables/pdfmake

# Baixa as dependências do DataTables
wget -O administrativo/static/administrativo/js/plugins/dataTables/pdfmake/pdfmake.min.js https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.70/pdfmake.min.js
wget -O administrativo/static/administrativo/js/plugins/dataTables/pdfmake/vfs_fonts.js https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.70/vfs_fonts.js

# Coleta arquivos estáticos
python manage.py collectstatic --noinput --clear

# Executa as migrações
python manage.py migrate 