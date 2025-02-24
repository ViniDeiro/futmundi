#!/bin/bash

# Cria o diretório se não existir
mkdir -p administrativo/static/administrativo/js/plugins/dataTables/pdfmake

# Download dos arquivos do pdfmake
curl -o administrativo/static/administrativo/js/plugins/dataTables/pdfmake/pdfmake.min.js https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.70/pdfmake.min.js
curl -o administrativo/static/administrativo/js/plugins/dataTables/pdfmake/pdfmake.min.js.map https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.70/pdfmake.min.js.map
curl -o administrativo/static/administrativo/js/plugins/dataTables/pdfmake/vfs_fonts.js https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.70/vfs_fonts.js 