#!/usr/bin/env bash
# exit on error
set -o errexit

# Instala as dependências
pip install -r requirements.txt

# Baixa as dependências do DataTables
mkdir -p administrativo/static/administrativo/js/plugins/dataTables/pdfmake
curl -o administrativo/static/administrativo/js/plugins/dataTables/pdfmake/pdfmake.min.js https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.70/pdfmake.min.js
curl -o administrativo/static/administrativo/js/plugins/dataTables/pdfmake/pdfmake.min.js.map https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.70/pdfmake.min.js.map
curl -o administrativo/static/administrativo/js/plugins/dataTables/pdfmake/vfs_fonts.js https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.70/vfs_fonts.js

# Coleta arquivos estáticos
python manage.py collectstatic --no-input

# Executa as migrações
python manage.py migrate 