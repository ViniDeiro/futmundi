$(document).ready(function() {
    let isEditing = false;
    let editingId = null;
    let niveisData = [];
    let imageWasRemoved = false;
    
    // Atualiza o nome do arquivo selecionado
    $('input[type="file"]').change(function(e) {
        if (e.target.files && e.target.files[0]) {
            var fileName = e.target.files[0].name;
            $(this).closest('.input-group').find('input[type="text"]').val(fileName);
        }
    });
    
    // Função para reinicializar o drag and drop
    function initDragAndDrop() {
        $("#table tbody").tableDnD({
            onDrop: function(table, row) {
                saveOrder();
                updatePremiosTable();
            },
            dragHandle: ".drag-handle"
        });
    }
    
    // Inicializa o drag and drop
    initDragAndDrop();

    // Inicializa iCheck para checkbox
    $('.i-checks').iCheck({
        checkboxClass: 'icheckbox_square-green',
        radioClass: 'iradio_square-green',
    });

    // Inicializa clockpicker
    $('.clockpicker').clockpicker({
        placement: 'bottom',
        align: 'left',
        autoclose: true
    });

    // Inicializa o plugin Jasny Bootstrap para o upload de imagem
    $('.fileinput').fileinput();

    // Função para carregar dados iniciais
    function carregarDadosIniciais() {
        // Adiciona um indicador de carregamento na tabela
        $('#table tbody').html('<tr><td colspan="6" class="text-center"><i class="fa fa-spinner fa-spin"></i> Carregando dados...</td></tr>');
        
        // Cria uma cópia de backup dos níveis atuais (se existirem)
        const niveisDataBackup = [...niveisData];
        console.log("Backup de dados antes da carga:", JSON.stringify(niveisDataBackup));
        
        // Sistema para salvar as imagens no localStorage como backup
        let imagensLocais = {};
        try {
            const imagensLocaisStr = localStorage.getItem('niveisImagens');
            if (imagensLocaisStr) {
                imagensLocais = JSON.parse(imagensLocaisStr);
                console.log("Imagens recuperadas do localStorage:", Object.keys(imagensLocais).length);
            }
        } catch (e) {
            console.error("Erro ao recuperar imagens do localStorage:", e);
        }
        
        // Faz a requisição AJAX para carregar os dados
        $.ajax({
            url: '/futligas/jogadores/dados/',
            method: 'GET',
            success: function(response) {
                console.log("Dados carregados com sucesso:", response);
                if (response && response.levels) {
                    // Se já temos dados, vamos mesclar preservando as imagens
                    if (niveisDataBackup.length > 0) {
                        console.log("Mesclando dados existentes com dados do servidor");
                        
                        // Para cada nível carregado do servidor
                        response.levels.forEach(novoNivel => {
                            // Verifica se já existe um nível com o mesmo ID
                            const nivelExistente = niveisDataBackup.find(n => n.id === novoNivel.id);
                            if (nivelExistente) {
                                console.log(`Nível ID ${novoNivel.id} já existe, verificando imagem`);
                                
                                // Se o nível do servidor não tiver imagem mas o nível existente tiver,
                                // mantém a imagem do nível existente
                                if (!novoNivel.image && nivelExistente.image) {
                                    console.log(`Mantendo imagem existente para nível ID ${novoNivel.id}`);
                                    novoNivel.image = nivelExistente.image;
                                }
                            } else {
                                console.log(`Novo nível ID ${novoNivel.id} adicionado dos dados do servidor`);
                            }
                            
                            // Verifica se temos esta imagem no localStorage
                            if (!novoNivel.image && imagensLocais[novoNivel.id]) {
                                console.log(`Recuperando imagem do localStorage para nível ID ${novoNivel.id}`);
                                novoNivel.image = imagensLocais[novoNivel.id];
                            }
                        });
                    } else if (Object.keys(imagensLocais).length > 0) {
                        // Se não temos dados em memória mas temos no localStorage
                        response.levels.forEach(nivel => {
                            if (!nivel.image && imagensLocais[nivel.id]) {
                                console.log(`Recuperando imagem do localStorage para nível ID ${nivel.id}`);
                                nivel.image = imagensLocais[nivel.id];
                            }
                        });
                    }
                    
                    // Atualiza os dados armazenados
                    niveisData = response.levels;
                    
                    // Garante que não haja valores undefined nas imagens
                    niveisData.forEach(nivel => {
                        if (nivel.image === undefined) {
                            nivel.image = null;
                        }
                        console.log(`Nível carregado: ${nivel.name}, ID: ${nivel.id}, Imagem: ${nivel.image || 'Nenhuma'}`);
                    });
                    
                    // Preenche a tabela de níveis
                    renderNiveisTable();
                    
                    // Preenche a tabela de prêmios
                    updatePremiosTableWithoutReset();
                    
                    // Configura formulário de premiação
                    if (response.award_config) {
                        const weekly = response.award_config.weekly || {};
                        const season = response.award_config.season || {};
                        
                        // Semanal
                        if (weekly.day) {
                            $('#dia-premiacao').val(weekly.day);
                        }
                        if (weekly.time) {
                            $('.clockpicker:eq(0) input').val(weekly.time);
                        }
                        
                        // Temporada
                        if (season.month) {
                            $('#mes-ano-premiacao').val(season.month);
                        }
                        if (season.day) {
                            $('#dia-ano-premiacao').val(season.day);
                        }
                        if (season.time) {
                            $('.clockpicker:eq(1) input').val(season.time);
                        }
                    }
                    
                    // Inicializa drag and drop na tabela
                    initDragAndDrop();
                    
                    // Se não há prêmios no banco de dados, deixa a tabela vazia
                    if (!response.prizes || response.prizes.length === 0) {
                        $('#premios table tbody').empty();
                    }
                } else {
                    $('#table tbody').html('<tr><td colspan="6" class="text-center">Nenhum nível encontrado.</td></tr>');
                }
            },
            error: function(xhr, status, error) {
                console.error("Erro ao carregar dados:", error);
                console.error("Status HTTP:", xhr.status);
                console.error("Resposta:", xhr.responseText);
                
                $('#table tbody').html('<tr><td colspan="6" class="text-center text-danger">Erro ao carregar dados. <button class="btn btn-xs btn-primary" id="btn-retry">Tentar novamente</button></td></tr>');
                
                // Adiciona listener para o botão de tentar novamente
                $('#btn-retry').on('click', function() {
                    carregarDadosIniciais();
                });
                
                toastr.error('Ocorreu um erro ao carregar os dados. Por favor, verifique o console para mais detalhes ou tente novamente.');
            }
        });
    }
    
    // Renderiza a tabela de níveis de forma robusta
    function renderNiveisTable() {
        console.log("Renderizando tabela de níveis com", niveisData ? niveisData.length : 0, "níveis");
        
        // Guarda as imagens atuais na tabela para referência
        const imagensAtuais = {};
        $('#table tbody tr').each(function() {
            const id = $(this).data('id');
            const imgElement = $(this).find('td:eq(1) img');
            if (imgElement.length && imgElement.attr('src')) {
                imagensAtuais[id] = imgElement.attr('src');
                console.log(`Imagem encontrada na tabela para nível ID ${id}: ${imgElement.attr('src')}`);
            }
        });
        
        if (!niveisData || niveisData.length === 0) {
            $('#table tbody').html('<tr><td colspan="6" class="text-center">Nenhum nível encontrado.</td></tr>');
            return;
        }
        
        // Validar os dados das imagens antes de renderizar
        niveisData.forEach(nivel => {
            // Verificar se temos uma imagem na tabela atual que não está nos dados
            if (!nivel.image && imagensAtuais[nivel.id]) {
                console.log(`Recuperando imagem da tabela para nível ID ${nivel.id}`);
                nivel.image = imagensAtuais[nivel.id];
            }
            
            // Garantir que a propriedade image não se torne undefined
            if (nivel.image === undefined) {
                nivel.image = null;
            }
            
            console.log(`Renderizando nível: ${nivel.name}, ID: ${nivel.id}, tem imagem: ${nivel.image ? 'Sim' : 'Não'}`);
        });
        
        // Atualizar o localStorage com as imagens atuais
        try {
            const imagensParaArmazenar = {};
            niveisData.forEach(nivel => {
                if (nivel.image) {
                    imagensParaArmazenar[nivel.id] = nivel.image;
                }
            });
            localStorage.setItem('niveisImagens', JSON.stringify(imagensParaArmazenar));
            console.log(`${Object.keys(imagensParaArmazenar).length} imagens salvas no localStorage`);
        } catch (e) {
            console.error("Erro ao salvar imagens no localStorage:", e);
        }
        
        let html = '';
        niveisData.forEach(function(nivel) {
            // Garante que a imagem seja exibida se estiver disponível
            const imagemHTML = nivel.image 
                ? `<img src="${nivel.image}" height="32" width="32" alt="Imagem" onerror="this.onerror=null; this.src='data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMiIgaGVpZ2h0PSIzMiI+PHJlY3Qgd2lkdGg9IjMyIiBoZWlnaHQ9IjMyIiBmaWxsPSIjZWVlIi8+PHRleHQgdGV4dC1hbmNob3I9Im1pZGRsZSIgeD0iMTYiIHk9IjE2IiBzdHlsZT0iZmlsbDojYWFhO2ZvbnQtd2VpZ2h0OmJvbGQ7Zm9udC1zaXplOjEycHg7Zm9udC1mYW1pbHk6QXJpYWwsSGVsdmV0aWNhLHNhbnMtc2VyaWY7ZG9taW5hbnQtYmFzZWxpbmU6Y2VudHJhbCI+Pzw8L3RleHQ+PC9zdmc+'; console.log('Erro ao carregar imagem para nível ID ' + nivel.id);">`
                : '-';
            
            html += `
            <tr data-id="${nivel.id}" data-order="${nivel.order}">
                <td><span class="drag-handle" style="cursor: move; margin-right: 5px;">&#9776;</span> ${nivel.name || '-'}</td>
                <td class="center-middle" data-has-image="${!!nivel.image}">${imagemHTML}</td>
                <td>${nivel.players || 0}</td>
                <td>${nivel.premium_players || 0}</td>
                <td>${nivel.owner_premium ? 'Sim' : 'Não'}</td>
                <td>
                    <div>
                        <button type="button" class="btn btn-info btn-xs mr5" title="Editar"><i class="glyphicon glyphicon-pencil"></i></button>
                        <button type="button" class="btn btn-danger btn-xs mr5" title="Excluir"><i class="glyphicon glyphicon-trash"></i></button>
                    </div>
                </td>
            </tr>`;
        });
        
        $('#table tbody').html(html);
        
        // Verifica depois da renderização se as imagens estão sendo exibidas corretamente
        setTimeout(function() {
            $('#table tbody tr').each(function() {
                const id = $(this).data('id');
                const nivel = niveisData.find(n => n.id == id);
                
                if (nivel && nivel.image) {
                    const imgElement = $(this).find('td:eq(1) img');
                    if (imgElement.length === 0) {
                        console.error(`Imagem não renderizada para nível ID ${id}, apesar de ter dados de imagem`);
                    }
                }
            });
        }, 500);
    }
    
    // Carrega os dados iniciais quando a página carrega
    carregarDadosIniciais();

    // Preview da imagem com validações
    $("#image").change(function() {
        const file = this.files[0];
        if (file) {
            // Validações
            if (!file.type.match('image.*')) {
                toastr.error('Por favor, selecione uma imagem válida');
                this.value = '';
                return;
            }

            if (file.size > 2 * 1024 * 1024) {
                toastr.error('A imagem não pode ter mais que 2MB');
                this.value = '';
                return;
            }

            const reader = new FileReader();
            reader.onload = function(e) {
                $("#image-preview").html(`
                    <img src="${e.target.result}" style="max-width: 50px; max-height: 50px; object-fit: contain; cursor: pointer;" onclick="document.getElementById('image').click()">
                    <button type="button" class="btn btn-danger btn-xs img-remove-btn" id="remove_image_btn" style="position: absolute; bottom: -7px; right: -30px;">
                        <i class="fa fa-trash"></i>
                    </button>
                `);
                $('#image-preview').css('margin-top', '-7px');
                
                // Adiciona handler para o botão de remover
                $('#remove_image_btn').on('click', function() {
                    $('#image').val('');
                    $('#image-preview').html('<i class="fa fa-file-image-o" style="font-size: 32px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>');
                    return false;
                });
            };
            reader.readAsDataURL(file);
        }
    });

    // Remove imagem (delegate event para funcionar com elementos criados dinamicamente)
    $(document).on('click.imageRemoval', '.remove-image, #remove_image_btn, .img-remove-btn', function(e) {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation(); // Impede que outros manipuladores sejam chamados
        
        console.log("Botão de remover imagem clicado - removendo imagem intencionalmente");
        
        // Marca que a imagem foi intencionalmente removida
        imageWasRemoved = true;
        
        // Limpa o campo de arquivo
        $("#image").val('');
        
        // Reinicia o visualizador
        $("#image-preview").html('<i class="fa fa-file-image-o" style="font-size: 32px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>');
        
        // Garante que o evento não propague para outros elementos
        return false;
    });

    // Submit do formulário
    $("#form-futliga").submit(function(e) {
        e.preventDefault();
        
        const name = $("#name").val();
        const players = $("#players").val();
        const premium_players = $("#premium_players").val();
        const owner_premium = $("#owner_premium").prop('checked');
        
        // Validações básicas
        if (!name || !players || !premium_players) {
            toastr.error('Preencha todos os campos obrigatórios!');
            return;
        }
        
        // Validação de nome duplicado
        if (!isEditing && checkDuplicateName(name)) {
            toastr.error('Já existe um nível com este nome!');
            return;
        }

        // Processar a imagem se houver
        let imageData = null;
        const imagePreview = $("#image-preview img");
        if (imagePreview.length) {
            imageData = imagePreview.attr('src');
            console.log('Imagem encontrada no formulário e será usada');
        } else {
            console.log('Nenhuma imagem encontrada no formulário');
            
            // Se estiver editando e a imagem NÃO foi removida intencionalmente, 
            // verificar se o nível já tem uma imagem que deve ser mantida
            if (isEditing && !imageWasRemoved) {
                const existingLevel = niveisData.find(nivel => nivel.id == editingId);
                if (existingLevel && existingLevel.image) {
                    console.log('Mantendo imagem existente do nível em edição');
                    imageData = existingLevel.image;
                }
            } else if (imageWasRemoved) {
                console.log('Imagem foi intencionalmente removida pelo usuário');
            }
        }

        // Cria ou atualiza o nível
        try {
        if (isEditing) {
                console.log(`Atualizando nível ID: ${editingId}, Nome: ${name}, Imagem: ${imageData ? 'Com imagem' : 'Sem imagem'}`);
            updateLevel(editingId, name, players, premium_players, owner_premium, imageData);
            toastr.success('Nível atualizado com sucesso!');
        } else {
                console.log(`Adicionando novo nível, Nome: ${name}, Imagem: ${imageData ? 'Com imagem' : 'Sem imagem'}`);
            addLevel(name, players, premium_players, owner_premium, imageData);
            toastr.success('Nível adicionado com sucesso!');
            }
        } catch (error) {
            console.error('Erro ao salvar nível:', error);
            toastr.error('Ocorreu um erro ao salvar. Por favor, tente novamente.');
        }

        // Resetar o flag de remoção de imagem
        imageWasRemoved = false;

        resetForm();
    });

    // Editar nível
    $(document).on('click', '.btn-info', function() {
        const row = $(this).closest('tr');
        editingId = row.data('id');
        
        console.log(`Editando nível ID: ${editingId}`);
        
        // Obtém o nível dos dados em memória para garantir todos os detalhes
        const nivel = niveisData.find(n => n.id == editingId);
        if (!nivel) {
            console.error(`Nível com ID ${editingId} não encontrado nos dados em memória`);
            toastr.error('Erro ao editar: nível não encontrado');
            return;
        }
        
        // Preenche o formulário com dados do nível
        $("#name").val(nivel.name);
        $("#players").val(nivel.players);
        $("#premium_players").val(nivel.premium_players);
        $("#owner_premium").prop('checked', nivel.owner_premium).iCheck('update');
        
        // Recupera a imagem existente se houver
        if (nivel.image) {
            console.log(`Nível tem imagem: ${nivel.image}`);
            $("#image-preview").html(`
                <img src="${nivel.image}" style="max-width: 50px; max-height: 50px; object-fit: contain; cursor: pointer;" onclick="document.getElementById('image').click()">
                <button type="button" class="btn btn-danger btn-xs img-remove-btn" id="remove_image_btn" style="position: absolute; bottom: -7px; right: -30px;">
                    <i class="fa fa-trash"></i>
                </button>
            `);
            $('#image-preview').css('margin-top', '-7px');
        } else {
            console.log(`Nível não tem imagem`);
            $("#image-preview").html('<i class="fa fa-file-image-o" style="font-size: 32px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>');
        }
        
        $("#submit-btn").html('<i class="fa fa-save mr5"></i> Salvar Alterações');
        isEditing = true;
        
        // Manter foco no formulário
        $('html, body').animate({
            scrollTop: $("#form-futliga").offset().top - 100
        }, 300);
    });

    // Excluir nível - seletor específico para botões dentro da tabela de níveis
    $(document).on('click', '#table tbody tr .btn-danger:not(.img-remove-btn)', function(e) {
        console.log("Botão de exclusão de nível clicado");
        e.preventDefault();
        e.stopPropagation();
        
        const row = $(this).closest('tr');
        const nivelId = row.data('id');
        const nivelNome = row.find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim();
        
        // Abre o modal de confirmação
        $('#levelNameToDelete').text(nivelNome);
        $('#modalConfirmDelete').data('row', row).modal('show');
    });

    // Adicionar manipulador de eventos para os botões de exclusão na aba prêmios
    $(document).on('click', '#premios table tbody tr .btn-danger', function(e) {
        console.log("Botão de exclusão de prêmio clicado");
        e.preventDefault();
        e.stopPropagation();
        
        const row = $(this).closest('tr');
        
        if (confirm('Tem certeza que deseja excluir este prêmio?')) {
            row.remove();
            
            // Atualiza as posições
            $('#premios table tbody tr').each(function(index) {
                $(this).find('td:first').text((index + 1) + '°');
                $(this).attr('data-position', index + 1);
            });
            
            toastr.success('Prêmio excluído com sucesso!');
        }
    });
    
    // Confirmar exclusão de nível
    $('#confirmDeleteButton').click(function() {
        // Obter dados do modal
        const $row = $('#modalConfirmDelete').data('row');
        const nivelId = $row.data('id');
        
        // Encontra o índice no array de dados
        const levelIndex = niveisData.findIndex(nivel => nivel.id == nivelId);
        if (levelIndex >= 0) {
            // Remove do array de dados
            niveisData.splice(levelIndex, 1);
            
            // Atualiza os índices de ordem
            niveisData.forEach((nivel, index) => {
                nivel.order = index;
            });
            
            // Renderiza a tabela novamente
            renderNiveisTable();
            
            // Atualiza a tabela de prêmios sem resetar as linhas
            updatePremiosTableWithoutReset();
            
            // Reinicializa o drag and drop
            initDragAndDrop();
            
            // Fecha o modal
                    $('#modalConfirmDelete').modal('hide');
                    
            // Notificar o usuário
            toastr.success("Nível excluído com sucesso!");
            
            // Reseta o estado de edição, se o nível que estava sendo editado foi excluído
            if (isEditing && editingId == nivelId) {
                resetForm();
                $("#submit-btn").html('<i class="fa fa-plus mr5"></i> Adicionar');
                isEditing = false;
                editingId = null;
            }
                    } else {
            console.error("Nível não encontrado para exclusão:", nivelId);
            toastr.error("Erro ao excluir nível, recarregue a página e tente novamente.");
                $('#modalConfirmDelete').modal('hide');
            }
    });

    // Botão para abrir modal de importação
    $("#btn-importar").click(function() {
        // Limpa o input de arquivo
        $('#importFile').val('');
        
        // Abre o modal de importação
        $('#modalImport').modal('show');
    });
    
    // Botão para confirmar importação
    $('#confirmImportButton').click(function() {
        const fileInput = $('#importFile')[0];
        
        if (!fileInput.files || !fileInput.files[0]) {
            toastr.error('Selecione um arquivo para importar.');
            return;
        }
        
        const file = fileInput.files[0];
        
        if (!file.name.endsWith('.xls') && !file.name.endsWith('.xlsx')) {
            toastr.error('Formato de arquivo inválido. Use .xls ou .xlsx');
            return;
        }
        
        const reader = new FileReader();
        toastr.info('Processando arquivo, aguarde...');
        
        reader.onload = function(e) {
            try {
                const data = new Uint8Array(e.target.result);
                const workbook = XLSX.read(data, {type: 'array'});
                const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
                const jsonData = XLSX.utils.sheet_to_json(firstSheet);
                
                if (jsonData.length === 0) {
                    toastr.error('O arquivo não contém dados.');
                    return;
                }
                
                // Verifica se as colunas necessárias existem
                const firstRow = jsonData[0];
                const requiredColumns = ['Nível', 'Participantes', 'Craques', 'Dono Craque'];
                const missingColumns = requiredColumns.filter(column => !(column in firstRow));
                
                if (missingColumns.length > 0) {
                    toastr.error('Colunas obrigatórias ausentes: ' + missingColumns.join(', '));
                    return;
                }
                
                // Pergunta ao usuário se deseja limpar os níveis existentes
                if ($("#table tbody tr").length > 0) {
                    if (confirm('Deseja substituir os níveis existentes pelos importados?')) {
                        $("#table tbody").empty();
                    }
                }
                
                // Adiciona os níveis importados
                let importCount = 0;
                jsonData.forEach(function(row) {
                    if (row['Nível']) {
                        addLevel(
                            row['Nível'],
                            row['Participantes'] || 0,
                            row['Craques'] || 0,
                            row['Dono Craque'] === 'Sim' || false,
                            null // Não importamos imagens do Excel
                        );
                        importCount++;
                    }
                });
                
                updatePremiosTable();
                
                // Fecha o modal
                $('#modalImport').modal('hide');
                
                toastr.success(`${importCount} níveis importados com sucesso!`);
                
                // Reinicializa o drag and drop após importar
                initDragAndDrop();
            } catch (error) {
                console.error(error);
                toastr.error('Erro ao importar arquivo. Verifique o formato!');
            }
        };
        
        reader.readAsArrayBuffer(file);
    });

    // Exportar níveis
    $("a[title='Exportar']").click(function() {
        const data = [];
        $("#table tbody tr").each(function() {
            const row = $(this);
            data.push({
                'Nível': row.find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim(),
                'Participantes': row.find('td:eq(2)').text(),
                'Craques': row.find('td:eq(3)').text(),
                'Dono Craque': row.find('td:eq(4)').text()
            });
        });

        if (data.length === 0) {
            toastr.warning('Nenhum nível para exportar!');
            return;
        }

        const ws = XLSX.utils.json_to_sheet(data);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Níveis");
        XLSX.writeFile(wb, "futligas_niveis.xlsx");
        toastr.success('Níveis exportados com sucesso!');
    });

    // Adiciona evento para o botão de adicionar prêmio
    $('.btn-adicionar-premio, #addPremioRow').off('click').on('click', function() {
        const $premiTable = $('#premiosTable');
        const numRows = $premiTable.find('tbody tr').length;
        const position = numRows + 1;
        
        const niveis = [];
        $("#table tbody tr").each(function() {
            niveis.push($(this).find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim());
        });
        
        // Cria uma nova linha
        let newRow = `
            <tr>
                <td>${position}°</td>
                <td class="center-middle">
                    <div class="premio-image-container" style="position: relative; display: inline-block;">
                        <div class="premio-image-preview dropzone-imagem" style="height: 32px; width: 32px; border: 1px dashed #ccc; border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center;">
                            <i class="fa fa-plus"></i>
                        </div>
                        <input type="file" class="premio-image" style="display: none;" accept="image/*">
                    </div>
                </td>`;
                
        // Adiciona células para cada nível
        niveis.forEach(nivel => {
            newRow += `
                <td>
                    <input type="number" class="form-control premio-valor" data-nivel="${nivel}" value="1000" min="0">
                </td>`;
        });
        
        // Finaliza a linha com a célula de ações - botão simplificado e maior
        newRow += `
                <td>
                    <button type="button" class="btn btn-danger delete-premio" title="Excluir"><i class="glyphicon glyphicon-trash"></i></button>
                </td>
            </tr>`;
        
        // Adiciona a linha à tabela
        $premiTable.find('tbody').append(newRow);
        
        // Inicializa o preview de imagem para a nova linha
        initPremioImagePreview($premiTable.find('tbody tr:last'));
        
        // Reaplica os eventos aos botões de exclusão
        initDeletePremioButtons();
        
        toastr.success('Prêmio adicionado com sucesso!');
    });
    
    // Função para inicializar a visualização de imagem de prêmio
    function initPremioImagePreview(row) {
        const previewContainer = row.find('.premio-image-preview');
        const fileInput = row.find('.premio-image');
        
        // Marca o container como inicializado
        previewContainer.data('click-initialized', true);
        
        // Ao clicar no contêiner, ativa o input de arquivo
        previewContainer.off('click').on('click', function() {
            fileInput.click();
        });
        
        // Ao selecionar um arquivo, exibe a pré-visualização
        fileInput.off('change').on('change', function(e) {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewContainer.html(`
                        <div style="position: relative; width: 100%; height: 100%;">
                            <img src="${e.target.result}" style="max-width: 100%; max-height: 32px; position: relative;">
                            <div class="remove-premio-image" style="position: absolute; bottom: 0; right: 0; background-color: #f8f8f8; border-radius: 50%; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 1px 3px rgba(0,0,0,0.2);">
                                <i class="fa fa-trash" style="font-size: 10px; color: #FF5252;"></i>
                            </div>
                        </div>
                    `);
                    
                    // Adiciona evento para remover imagem
                    previewContainer.find('.remove-premio-image').on('click', function(e) {
                        e.stopPropagation();
                        previewContainer.html('<i class="fa fa-plus"></i>');
                        fileInput.val('');
                    });
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    }
    
    // Função para inicializar os botões de exclusão de prêmios
    function initDeletePremioButtons() {
        // Remover handlers de clique anteriores para evitar duplicação
        $('.delete-premio').off('click');
        
        // Adicionar novos handlers
        $('.delete-premio').on('click', function() {
            const $row = $(this).closest('tr');
            const position = $row.find('td:first').text();
            
            if (confirm(`Tem certeza que deseja excluir o prêmio da posição ${position}?`)) {
                $row.remove();
                
                // Atualiza as posições dos prêmios
                $('#premiosTable tbody tr').each(function(index) {
                    $(this).find('td:first').text((index + 1) + '°');
                });
                
                toastr.success(`Prêmio da posição ${position} excluído com sucesso!`);
            }
        });
    }
    
    // Delegação de evento para os botões de excluir prêmio (para botões adicionados dinamicamente)
    $(document).on('click', '.delete-premio', function() {
        const row = $(this).closest('tr');
        const position = row.find('td:first').text();
        
        if (confirm(`Tem certeza que deseja excluir o prêmio da posição ${position}?`)) {
            row.remove();
            
            // Atualiza as posições das linhas restantes
            $('#premiosTable tbody tr').each(function(index) {
                $(this).find('td:first').text((index + 1) + '°');
            });
            
            toastr.success(`Prêmio da posição ${position} excluído com sucesso!`);
        }
    });
    
    // Inicializa as visualizações de imagem para os prêmios existentes
    $(document).ready(function() {
        $('#premiosTable tbody tr').each(function() {
            initPremioImagePreview($(this));
        });
    });

    // Salvar todas as configurações
    $("#successToast").click(function() {
        console.log("Iniciando processo de salvar todas as configurações");
        
        // Mostra indicador de carregamento
        const $btn = $(this);
        const originalHtml = $btn.html();
        $btn.html('<i class="fa fa-spinner fa-spin mr5"></i> Salvando...').prop('disabled', true);
        
        // IMPORTANTE: Certifique-se que niveisData está atualizado com as imagens corretas
        console.log("Verificando dados antes do envio para o servidor");
        
        // Verifica se há alguma imagem na tabela que não está nos dados em memória
        $('#table tbody tr').each(function() {
            const id = $(this).data('id');
            const nivel = niveisData.find(n => n.id == id);
            const imgElement = $(this).find('td:eq(1) img');
            
            // Se temos um nível mas ele não tem imagem, e a tabela tem uma imagem
            if (nivel && !nivel.image && imgElement.length) {
                console.log(`Recuperando imagem da tabela para nível ID ${id} antes de salvar`);
                nivel.image = imgElement.attr('src');
            }
        });
        
        // Verifica se todos os níveis têm dados de imagem válidos
        niveisData.forEach(nivel => {
            if (nivel.image === undefined) {
                nivel.image = null;
                console.log(`Corrigido valor 'undefined' para imagem do nível ID ${nivel.id}`);
            }
        });
        
        // Salva as imagens no localStorage como backup
        try {
            const imagensParaArmazenar = {};
            niveisData.forEach(nivel => {
                if (nivel.image) {
                    imagensParaArmazenar[nivel.id] = nivel.image;
                }
            });
            localStorage.setItem('niveisImagens', JSON.stringify(imagensParaArmazenar));
            console.log(`${Object.keys(imagensParaArmazenar).length} imagens salvas no localStorage antes do salvamento no servidor`);
        } catch (e) {
            console.error("Erro ao salvar imagens no localStorage:", e);
        }
        
        // Obter os dados de todos os níveis da tabela
        const levels = [];
        niveisData.forEach(function(nivel, index) {
            // Verificar se a imagem do nível existe na interface antes de enviá-la
            const rowElement = $(`#table tbody tr[data-id="${nivel.id}"]`);
            if (rowElement.length) {
                const imgElement = rowElement.find('td:eq(1) img');
                if (imgElement.length && imgElement.attr('src') && !nivel.image) {
                    console.log(`CORREÇÃO CRÍTICA: Recuperando imagem da DOM para o nível ${nivel.name} antes de salvar`);
                    nivel.image = imgElement.attr('src');
                }
            }
            
            // IMPORTANTE: Força salvar todos os campos, até mesmo null, para garantir que o backend não descarte dados
            levels.push({
                id: nivel.id,
                name: nivel.name,
                players: nivel.players,
                premium_players: nivel.premium_players,
                owner_premium: nivel.owner_premium,
                image: nivel.image, // Garantir que imagem seja enviada, mesmo que seja null
                order: index
            });
            
            // Log detalhado para diagnóstico
            console.log(`VERIFICAÇÃO PRÉ-ENVIO: Nível ${nivel.name} (ID: ${nivel.id}), Ordem: ${index}, Imagem: ${nivel.image ? 'SIM' : 'NÃO'}`);
        });
        
        // Obter os dados dos prêmios
        const prizes = [];
        $("#premios table tbody tr").each(function() {
            const row = $(this);
            const position = parseInt(row.find('td:eq(0)').text());
            const imageElement = row.find('td:eq(1) img');
            const image = imageElement.length ? imageElement.attr('src') : null;
            
            // Obter valores por nível
            const values = {};
            row.find('.premio-valor').each(function() {
                const nivel = $(this).data('nivel');
                const valor = parseInt($(this).val());
                values[nivel] = isNaN(valor) ? 0 : valor;
            });
            
            prizes.push({
                position,
                image,
                values
            });
        });
        
        // Obter configurações de premiação
        const awardConfig = {
            weekly: {
                day: $("#dia-premiacao").val(),
                time: $(".clockpicker:eq(0) input").val()
            },
            season: {
                month: $("#mes-ano-premiacao").val(),
                day: $("#dia-ano-premiacao").val(),
                time: $(".clockpicker:eq(1) input").val()
            }
        };
        
        // Adicionar função de proteção para data.levels antes do envio
        function garantirCompletudeDeDados(dados) {
            console.log("PROTEÇÃO: Verificando completude de dados antes do envio");
            
            // Verificar se todos os níveis têm todas as propriedades necessárias
            if (dados.levels) {
                dados.levels.forEach((nivel, index) => {
                    // Garantir que todas as propriedades estão definidas (mesmo que sejam null)
                    const propriedadesNecessarias = ['id', 'name', 'players', 'premium_players', 'owner_premium', 'image', 'order'];
                    propriedadesNecessarias.forEach(prop => {
                        if (nivel[prop] === undefined) {
                            console.warn(`CORREÇÃO: Propriedade '${prop}' ausente no nível ${nivel.name || index}, definindo como null`);
                            nivel[prop] = null;
                        }
                    });
                    
                    // Double-check para imagens
                    if (nivel.image === undefined) nivel.image = null;
                });
            }
            
            return dados;
        }

        // Dados completos para envio
        const data = garantirCompletudeDeDados({
            levels,
            prizes,
            award_config: awardConfig
        });
        
        console.log("Dados a serem enviados:", data);
        console.log("Detalhe das imagens nos dados a serem enviados:");
        levels.forEach(level => {
            console.log(`Nível ID ${level.id}, Nome: ${level.name}, Tem imagem: ${level.image ? 'Sim' : 'Não'}`);
        });
        
        // Enviar dados ao servidor
            $.ajax({
            url: "/futligas/jogadores/salvar/",
            type: "POST",
            data: JSON.stringify(data),
            contentType: "application/json",
                headers: {
                    'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
                },
                success: function(response) {
                    console.log("Resposta do servidor:", response);
                if (response.success) {
                    toastr.success("Configurações salvas com sucesso!");
                    
                    // IMPORTANTE: Não recarregar os dados, pois pode perder as imagens
                    // Em vez disso, apenas atualiza os IDs se necessário
                    if (response.levels) {
                        console.log("Atualizando IDs dos níveis após salvar");
                        
                        // Criar um backup das imagens existentes indexado por nome e ordem
                        const imagensBackup = {};
                        niveisData.forEach(nivel => {
                                if (nivel.image) {
                                // Usar nome e ordem como chave para garantir correspondência após salvamento
                                const chave = `${nivel.name}_${nivel.order}`;
                                imagensBackup[chave] = nivel.image;
                            }
                        });
                        
                        response.levels.forEach(nivelServidor => {
                            const nivelLocal = niveisData.find(n => 
                                n.name === nivelServidor.name && 
                                n.order === nivelServidor.order);
                            
                            if (nivelLocal) {
                                // Atualiza o ID
                                if (nivelLocal.id !== nivelServidor.id) {
                                    console.log(`Atualizando ID do nível ${nivelLocal.name} de ${nivelLocal.id} para ${nivelServidor.id}`);
                                    
                                    // Preserva a imagem ao atualizar o ID
                                    const imagemOriginal = nivelLocal.image;
                                    nivelLocal.id = nivelServidor.id;
                                    
                                    // Se o servidor não retornou imagem mas tínhamos uma, mantemos
                                    if (!nivelServidor.image && imagemOriginal) {
                                        console.log(`Mantendo imagem original para ${nivelLocal.name} após atualização de ID`);
                                        nivelLocal.image = imagemOriginal;
                                    }
                                }
                                
                                // Verifica se a imagem foi perdida na resposta do servidor
                                if (!nivelServidor.image && nivelLocal.image) {
                                    console.log(`Mantendo imagem local para nível ${nivelLocal.name} (ID: ${nivelLocal.id})`);
                                } else if (!nivelLocal.image) {
                                    // Tenta recuperar do backup por nome e ordem
                                    const chave = `${nivelLocal.name}_${nivelLocal.order}`;
                                    if (imagensBackup[chave]) {
                                        console.log(`Recuperando imagem do backup para ${nivelLocal.name}`);
                                        nivelLocal.image = imagensBackup[chave];
                                    }
                                }
                    } else {
                                // Nível novo do servidor, adicionar aos dados locais
                                console.log(`Adicionando novo nível do servidor: ${nivelServidor.name} (ID: ${nivelServidor.id})`);
                                niveisData.push(nivelServidor);
                            }
                        });
                        
                        // Renderiza novamente com os IDs atualizados
                        renderNiveisTable();
                    }
                } else {
                    toastr.error("Erro ao salvar: " + (response.error || "Erro desconhecido"));
                }
                
                // Restaurar o botão
                $btn.html(originalHtml).prop('disabled', false);
                },
                error: function(xhr, status, error) {
                console.error("Erro ao salvar dados:", error);
                console.error("Status:", status);
                console.error("Resposta:", xhr.responseText);
                
                toastr.error("Ocorreu um erro ao salvar. Por favor, tente novamente.");
                
                // Restaurar o botão
                $btn.html(originalHtml).prop('disabled', false);
            }
        });
    });

    // Funções auxiliares
    function addLevel(name, players, premium_players, owner_premium, imageData = null) {
        console.log("Adicionando novo nível:", name);
        
        // Gerar um ID único temporário até que o nível seja salvo no servidor
        const id = 'temp_' + Date.now();
        
        // Backup das imagens existentes antes de qualquer modificação
        const imagensBackup = {};
        niveisData.forEach(nivel => {
            if (nivel.image) {
                imagensBackup[nivel.id] = nivel.image;
            }
        });
        
        // Garante que os dados da imagem sejam válidos
        if (imageData === undefined) {
            console.log("Corrigindo undefined para imageData");
            imageData = null;
        }
        
        // Cria o objeto de nível completo
        const newLevel = {
            id: id,
            name: name,
            players: parseInt(players) || 0,
            premium_players: parseInt(premium_players) || 0,
            owner_premium: !!owner_premium,
            image: imageData,
            order: niveisData.length
        };
        
        console.log("Objeto de nível criado:", newLevel);
        console.log("Tem imagem:", newLevel.image ? "Sim" : "Não");
        
        // Adiciona aos dados em memória
        niveisData.push(newLevel);
        
        // Restaura as imagens do backup para os níveis existentes
        niveisData.forEach(nivel => {
            if (nivel.id !== id && imagensBackup[nivel.id]) {
                nivel.image = imagensBackup[nivel.id];
            }
        });
        
        // Atualiza o localStorage com as imagens atuais
        try {
            const imagensParaArmazenar = {...imagensBackup};
            if (newLevel.image) {
                imagensParaArmazenar[newLevel.id] = newLevel.image;
            }
            localStorage.setItem('niveisImagens', JSON.stringify(imagensParaArmazenar));
            console.log(`${Object.keys(imagensParaArmazenar).length} imagens salvas no localStorage`);
        } catch (e) {
            console.error("Erro ao salvar imagens no localStorage:", e);
        }
        
        // Renderiza a tabela com o novo nível
        renderNiveisTable();
        
        // Atualiza a tabela de prêmios sem perder os dados existentes
        updatePremiosTableWithoutReset();
        
        // Reinicializa o drag and drop após adicionar nova linha
        initDragAndDrop();
    }
    
    // Nova função para atualizar a tabela de prêmios sem resetar/recriar todas as linhas
    function updatePremiosTableWithoutReset() {
        console.log("Iniciando updatePremiosTableWithoutReset");
        
        // Obtém a lista de níveis disponíveis
        const niveis = [];
        $("#table tbody tr").each(function() {
            niveis.push($(this).find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim());
        });
        console.log("Níveis disponíveis para atualização:", niveis);
        
        // Verifica se a tabela tem o seletor correto
        const $premiosTable = $('#premiosTable');
        
        // Verifica quantas posições existem
        let premioRows = $premiosTable.find('tbody tr').length;
        console.log(`Número de linhas de prêmios existentes: ${premioRows}`);
        
        if (premioRows === 0) {
            // Se não há linhas, chama a função original para criar as linhas iniciais
            console.log("Nenhuma linha de prêmio encontrada, criando tabela inicial");
            updatePremiosTable();
            return;
        }

        // Atualiza os cabeçalhos da tabela para incluir os níveis
        const premiosHeader = $premiosTable.find('thead tr');
        
        // Guarda os níveis que já estão na tabela
        const niveisExistentes = [];
        premiosHeader.find('th[data-nivel]').each(function() {
            niveisExistentes.push($(this).attr('data-nivel'));
        });
        console.log("Níveis existentes na tabela:", niveisExistentes);
        
        // Remove colunas de níveis que não existem mais
        premiosHeader.find('th[data-nivel]').each(function() {
            const nivel = $(this).attr('data-nivel');
            if (!niveis.includes(nivel)) {
                console.log(`Removendo coluna do nível '${nivel}' que não existe mais`);
                const index = $(this).index();
                $premiosTable.find(`tbody tr`).each(function() {
                    $(this).find(`td:eq(${index})`).remove();
                });
                $(this).remove();
            }
        });
        
        // Adiciona colunas para novos níveis
        for (let i = 0; i < niveis.length; i++) {
            const nivel = niveis[i];
            if (!niveisExistentes.includes(nivel)) {
                console.log(`Adicionando nova coluna para o nível '${nivel}'`);
                premiosHeader.find('th:last').before(`<th class="per15" data-nivel="${nivel}">${nivel}</th>`);
                
                // Adiciona células para este nível em todas as linhas
                $premiosTable.find('tbody tr').each(function() {
                    const $actionCell = $(this).find('td:last');
                    $actionCell.before(`
                        <td>
                            <input type="number" class="form-control premio-valor" data-nivel="${nivel}" value="1000" min="0">
                </td>
                    `);
                });
            }
        }

        // Verificar se as imagens estão sendo exibidas corretamente
        $premiosTable.find('tbody tr').each(function(index) {
            const $row = $(this);
            const $imageCell = $row.find('td:eq(1)');
            
            // Verifica se a célula de imagem tem conteúdo
            if ($imageCell.find('img').length === 0 && $imageCell.find('.premio-image-preview').length === 0) {
                console.log(`Corrigindo célula de imagem na linha ${index + 1}`);
                $imageCell.html(`
                    <div class="premio-image-container" style="position: relative; display: inline-block;">
                        <div class="premio-image-preview dropzone-imagem" style="height: 32px; width: 32px; border: 1px dashed #ccc; border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center;">
                            <i class="fa fa-plus"></i>
                        </div>
                        <input type="file" class="premio-image" style="display: none;" accept="image/*">
                    </div>
                `);
                
                // Inicializa o preview para esta linha
                initPremioImagePreview($row);
            }
            
            // Verifica se a célula de ação tem o botão de exclusão
            const $actionCell = $row.find('td:last');
            if ($actionCell.find('.delete-premio').length === 0) {
                console.log(`Adicionando botão de exclusão na linha ${index + 1}`);
                $actionCell.html(`
                    <button type="button" class="btn btn-danger delete-premio" title="Excluir"><i class="glyphicon glyphicon-trash"></i></button>
                `);
            }
        });
        
        // Inicializa os botões de exclusão para garantir que funcionem
        initDeletePremioButtons();
        
        console.log("updatePremiosTableWithoutReset concluído com sucesso");
    }

    function updateLevel(id, name, players, premium_players, owner_premium, imageData = null) {
        console.log(`Atualizando nível ID ${id} - Nome: ${name}`);
        
        // Backup das imagens existentes
        const imagensBackup = {};
        niveisData.forEach(nivel => {
            if (nivel.image) {
                imagensBackup[nivel.id] = nivel.image;
            }
        });
        
        // Encontra o nível nos dados em memória
        const levelIndex = niveisData.findIndex(nivel => nivel.id == id);
        if (levelIndex >= 0) {
            // Preserva os dados atuais para comparação
            const nivelAntigo = {...niveisData[levelIndex]};
            console.log("Dados anteriores:", nivelAntigo);
            console.log("Imagem anterior:", nivelAntigo.image ? "Sim" : "Não");
            console.log("Nova imagem:", imageData ? "Sim" : "Não");
            
            // Determina qual imagem usar
            let imagemFinal = imageData;
            
            // Se não foi fornecida uma nova imagem (null/undefined) E não houve remoção explícita,
            // mantém a imagem existente
            if ((imageData === null || imageData === undefined) && !imageWasRemoved && nivelAntigo.image) {
                console.log("Mantendo imagem existente");
                imagemFinal = nivelAntigo.image;
            } else if (imageWasRemoved) {
                console.log("Imagem foi removida explicitamente");
                imagemFinal = null;
            }
            
            // Atualiza os dados em memória preservando a ordem e outras propriedades
            niveisData[levelIndex] = {
                ...nivelAntigo,
                name: name,
                players: parseInt(players) || 0,
                premium_players: parseInt(premium_players) || 0,
                owner_premium: !!owner_premium,
                image: imagemFinal
            };
            
            // Restaura as imagens do backup para os outros níveis
            niveisData.forEach(nivel => {
                if (nivel.id !== id && imagensBackup[nivel.id]) {
                    nivel.image = imagensBackup[nivel.id];
                }
            });
            
            // Atualiza o localStorage com as imagens atuais
            try {
                const imagensParaArmazenar = {...imagensBackup};
                if (imagemFinal) {
                    imagensParaArmazenar[id] = imagemFinal;
                } else {
                    delete imagensParaArmazenar[id];
                }
                localStorage.setItem('niveisImagens', JSON.stringify(imagensParaArmazenar));
                console.log(`${Object.keys(imagensParaArmazenar).length} imagens salvas no localStorage`);
            } catch (e) {
                console.error("Erro ao salvar imagens no localStorage:", e);
            }
            
            // Renderiza toda a tabela novamente
            renderNiveisTable();
            
            // Atualiza a tabela de prêmios sem resetar as linhas
            updatePremiosTableWithoutReset();
            
            // Reinicializa o drag and drop
            initDragAndDrop();
            
            // Limpa o campo de imagem e o preview
            $("#image").val('');
            $("#image-preview").html('<i class="fa fa-file-image-o" style="font-size: 32px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>');
            
            // Reset imageWasRemoved flag
            imageWasRemoved = false;
        } else {
            console.error("Nível não encontrado para atualizar:", id);
            toastr.error("Erro ao atualizar nível. O nível não foi encontrado.");
        }
    }

    function resetForm() {
        $("#form-futliga")[0].reset();
        
        // Reinicializa completamente o previsualizador e input de imagem
        $("#image-preview").html('<i class="fa fa-file-image-o" style="font-size: 32px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>');
        
        // Limpa o valor do input de arquivo
        $("#image").val('');
        
        $('.i-checks').iCheck('update');
        
        if (isEditing) {
            $("#submit-btn").html('<i class="fa fa-plus mr5"></i> Adicionar');
            isEditing = false;
            editingId = null;
        }
        
        // Resetar o flag de remoção de imagem
        imageWasRemoved = false;
        
        // Revincula eventos no input de imagem
        $("#image").off().on('change', function() {
            const file = this.files[0];
            if (file) {
                // Validações
                if (!file.type.match('image.*')) {
                    toastr.error('Por favor, selecione uma imagem válida');
                    this.value = '';
                    return;
                }

                if (file.size > 2 * 1024 * 1024) {
                    toastr.error('A imagem não pode ter mais que 2MB');
                    this.value = '';
                    return;
                }

                const reader = new FileReader();
                reader.onload = function(e) {
                    $("#image-preview").html(`
                        <img src="${e.target.result}" style="max-width: 50px; max-height: 50px; object-fit: contain; cursor: pointer;" onclick="document.getElementById('image').click()">
                        <button type="button" class="btn btn-danger btn-xs img-remove-btn" id="remove_image_btn" style="position: absolute; bottom: -7px; right: -30px;">
                            <i class="fa fa-trash"></i>
                        </button>
                    `);
                    $('#image-preview').css('margin-top', '-7px');
                    
                    // Adiciona handler para o botão de remover
                    $('#remove_image_btn').on('click', function() {
                        $('#image').val('');
                        $('#image-preview').html('<i class="fa fa-file-image-o" style="font-size: 32px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>');
                        return false;
                    });
                };
                reader.readAsDataURL(file);
            }
        });
    }

    function checkDuplicateName(name) {
        let isDuplicate = false;
        $("#table tbody tr").each(function() {
            const rowName = $(this).find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim();
            if (rowName.toLowerCase() === name.toLowerCase()) {
                isDuplicate = true;
                return false;
            }
        });
        return isDuplicate;
    }

    function saveOrder() {
        // Atualiza a ordem dos níveis
        $("#table tbody tr").each(function(index) {
            $(this).attr('data-order', index + 1);
        });
        
        // Atualiza a tabela de prêmios quando a ordem dos níveis muda
        updatePremiosTable();
    }

    function updatePremiosTable() {
        // Obtém a lista de níveis disponíveis
        const niveis = [];
        $("#table tbody tr").each(function() {
            niveis.push($(this).find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim());
        });
        console.log("Níveis disponíveis:", niveis);
        
        // Verifica se a tabela tem o seletor correto
        const $premiosTable = $('#premiosTable');
        
        // Verifica quantas posições existem
        let premioRows = $premiosTable.find('tbody tr').length;
        if (premioRows === 0) {
            // Adiciona pelo menos 3 posições se não houver nenhuma
            for (let i = 1; i <= 3; i++) {
                $premiosTable.find('tbody').append(`
                    <tr>
                        <td>${i}°</td>
                        <td class="center-middle">
                            <div class="premio-image-container" style="position: relative; display: inline-block;">
                                <div class="premio-image-preview dropzone-imagem" style="height: 32px; width: 32px; border: 1px dashed #ccc; border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center;">
                                    <i class="fa fa-plus"></i>
                                </div>
                                <input type="file" class="premio-image" style="display: none;" accept="image/*">
                            </div>
                        </td>`);
            
                // Adiciona colunas para cada nível
                niveis.forEach(nivel => {
                    $premiosTable.find('tbody tr:last').append(`
                        <td>
                            <input type="number" class="form-control premio-valor" data-nivel="${nivel}" value="1000" min="0">
                        </td>
                    `);
                });
                
                // Adiciona coluna de ações com ícone de lixeira bem visível
                $premiosTable.find('tbody tr:last').append(`
                        <td>
                        <button type="button" class="btn btn-danger btn-xs delete-premio" title="Excluir"><i class="glyphicon glyphicon-trash"></i></button>
                        </td>
                `);
            }
            premioRows = 3;
            
            // Inicializa os eventos de upload de imagem e botões de exclusão
            $premiosTable.find('tbody tr').each(function() {
                initPremioImagePreview($(this));
            });
            initDeletePremioButtons();
        }

        // Atualiza os cabeçalhos da tabela para incluir os níveis
        const premiosHeader = $premiosTable.find('thead tr');
        premiosHeader.find('th:gt(1):not(:last)').remove(); // Remove colunas de níveis existentes
        
        // Adiciona cabeçalhos para cada nível
        niveis.forEach(nivel => {
            premiosHeader.find('th:last').before(`<th class="per15" data-nivel="${nivel}">${nivel}</th>`);
        });

        // Atualiza cada linha existente para incluir células para cada nível
        $premiosTable.find('tbody tr').each(function() {
            const $row = $(this);
            const existingNiveis = [];
            
            // Identifica os níveis já existentes na linha
            $row.find('.premio-valor').each(function() {
                existingNiveis.push($(this).data('nivel'));
            });
            
            // Remove células de níveis que não existem mais
            $row.find('.premio-valor').each(function() {
                const nivel = $(this).data('nivel');
                if (!niveis.includes(nivel)) {
                    $(this).closest('td').remove();
                }
            });
            
            // Adiciona células para novos níveis
            const $actionCell = $row.find('td:last');
            niveis.forEach(nivel => {
                if (!existingNiveis.includes(nivel)) {
                    $actionCell.before(`
                        <td>
                            <input type="number" class="form-control premio-valor" data-nivel="${nivel}" value="1000" min="0">
                        </td>
                    `);
                }
            });
            
            // Verifica se existe o botão de exclusão, caso contrário adiciona
            if ($actionCell.find('.delete-premio').length === 0) {
                $actionCell.html(`
                    <button type="button" class="btn btn-danger btn-xs delete-premio" title="Excluir"><i class="glyphicon glyphicon-trash"></i></button>
                `);
            }
        });
        
        // Verifica se há alguma célula de imagem sem o evento de click configurado
        $premiosTable.find('.premio-image-preview').each(function() {
            if (!$(this).data('click-initialized')) {
                const $row = $(this).closest('tr');
                initPremioImagePreview($row);
            }
        });
        
        // Inicializa os botões de exclusão
        initDeletePremioButtons();
    }

    // Função para lidar com o clique na dropzone
    window.handleDropzoneClick = function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        // Armazena a célula atual para uso posterior
        const currentCell = $(this).closest('td');
        
        // Cria um ID único para o input temporário
        const tempInputId = 'temp-file-input-' + Date.now();
        
        // Remove qualquer input temporário existente
        $('.temp-file-input').remove();
        
        // Cria um input de arquivo oculto
        const fileInput = $('<input type="file" class="temp-file-input" id="' + tempInputId + '" accept="image/*" style="display:none;">');
        $('body').append(fileInput);
        
        // Define um timeout para remover o input se não for usado
        setTimeout(function() {
            $('#' + tempInputId).remove();
        }, 30000);
        
        // Quando um arquivo for selecionado
        fileInput.on('change', function(e) {
            if (this.files && this.files[0]) {
                const file = this.files[0];
                const reader = new FileReader();
                
                // Mostra um indicador de carregamento
                currentCell.html('<div class="loading"><i class="fa fa-spinner fa-spin"></i></div>');
                
                reader.onload = function(e) {
                    // Cria a visualização da imagem com o botão de remover
                    const imageContainer = $(`
                        <div style="position: relative; width: 32px; height: 32px; display: inline-block;">
                            <img src="${e.target.result}" height="32" width="32" alt="Imagem" style="object-fit: contain;">
                            <div class="image-remove-btn" style="position: absolute; bottom: 0; right: 0; background-color: #f8f8f8; border-radius: 50%; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 1px 3px rgba(0,0,0,0.2);">
                                <i class="fa fa-trash" style="font-size: 10px; color: #FF5252;"></i>
                            </div>
                        </div>
                    `);
                    
                    // Substitui o dropzone pela imagem
                    currentCell.html(imageContainer);
                    
                    // Adiciona evento ao botão de remover
                    imageContainer.find('.image-remove-btn').on('click', function(e) {
                        e.stopPropagation();
                        
                        // Recria o dropzone
                        const dropzone = $(`
                            <div class="dropzone-imagem" style="height: 32px; width: 32px; border: 1px dashed #ccc; border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center;">
                                <i class="fa fa-plus"></i>
                            </div>
                        `);
                        
                        imageContainer.replaceWith(dropzone);
                        
                        // Reaplica o evento de clique ao novo dropzone
                        dropzone.on('click', handleDropzoneClick);
                    });
                    
                    // Armazena dados da imagem para envio
                    currentCell.data('imageBase64', e.target.result);
                };
                
                reader.readAsDataURL(file);
            }
        });
        
        // Abre o seletor de arquivo
        fileInput.click();
    };
    
    // Delegação de evento para o botão de remover imagem
    $(document).on('click', '.image-remove-btn', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const cell = $(this).closest('td');
        cell.html(`
            <div class="dropzone-imagem" style="height: 32px; width: 32px; border: 1px dashed #ccc; border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center;">
                <i class="fa fa-plus"></i>
            </div>
        `);
        
        toastr.success('Imagem removida com sucesso!');
    });

    // Ajuste para o plugin de importação de Excel
    $('#importFile').on('change', function() {
        const file = this.files[0];
        if (file) {
            const filename = file.name;
            $(this).closest('.input-group').find('input[type="text"]').val(filename);
        }
    });

    // Função para reinicializar o estado do modal
    function resetModalState() {
        // Limpa os dados armazenados no modal
        $('#modalConfirmDelete').removeData('row');
        
        // Garante que o botão de confirmação esteja habilitado e com texto correto
        $('#confirmDeleteButton').prop('disabled', false).html('Excluir');
    }
    
    // Quando o modal é fechado, reinicia seu estado
    $('#modalConfirmDelete').on('hidden.bs.modal', function() {
        resetModalState();
        
        // Verifica se há backdrop residual e remove
        if ($('.modal-backdrop').length) {
            $('.modal-backdrop').remove();
        }
        
        // Garante que o body não tenha a classe modal-open se não houver modais abertos
        if ($('.modal.in').length === 0) {
            $('body').removeClass('modal-open');
        }
    });

    // Função para criar o html do botão de remoção de imagem
    function createImagePreviewWithRemoveButton(imageUrl) {
        return `
            <img src="${imageUrl}" style="max-width: 50px; max-height: 50px; object-fit: contain; cursor: pointer;" onclick="document.getElementById('image').click()">
            <button type="button" class="btn btn-danger btn-xs img-remove-btn" id="remove_image_btn" style="position: absolute; bottom: 0; right: 0; background-color: #f8f8f8; border-radius: 50%; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 1px 3px rgba(0,0,0,0.2);">
                                            <i class="fa fa-trash" style="font-size: 10px; color: #FF5252;"></i>
            </button>
        `;
    }

    // Função para criar o html do preview padrão sem imagem
    function createDefaultImagePreview() {
        return '<i class="fa fa-file-image-o" style="font-size: 32px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>';
    }

    // Ajuste do problema de AJAX - garante que as URLs são corretas
    $(document).ajaxSend(function(event, jqxhr, options) {
        // Logs para debug
        console.log("URL da requisição antes:", options.url);
        
        // Remover possíveis prefixos em URLs absolutas
        if (options.url && options.url.startsWith('/administrativo')) {
            options.url = options.url.replace('/administrativo', '');
            console.log("URL corrigida:", options.url);
        }
        
        console.log("URL da requisição após ajuste:", options.url);
    });
    
    // Adiciona CSS para o cursor de arrastar e imagens
    $("<style>")
        .prop("type", "text/css")
        .html(`
            .drag-handle {
                cursor: move;
                margin-right: 8px;
                color: #999;
            }
            .tDnD_whileDrag {
                background-color: #f5f5f5 !important;
            }
            .position-relative {
                position: relative;
                display: inline-block;
            }
            .center-middle {
                text-align: center;
                vertical-align: middle !important;
            }
            .label-card {
                display: inline-block;
                padding: 10px;
                border: 2px dashed #ccc;
                border-radius: 5px;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .label-card:hover {
                border-color: #1ab394;
            }
            .label-card-small {
                padding: 5px;
            }
            .label-content {
                font-size: 48px;
                color: #ccc;
            }
            .input-image {
                display: none;
            }
            .remove-image {
                position: absolute;
                bottom: -7px;
                right: -30px;
                padding: 2px 5px;
                font-size: 10px;
            }
            #image-preview {
                min-height: 50px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .dropzone-imagem:hover {
                background-color: #f9f9f9;
                border-color: #1ab394;
            }
        `)
        .appendTo("head");

    // Função para verificar se URLs requerem ajuste (usando jQuery)
    function isURLValid(url) {
        var result = false;
        $.ajax({
            url: url,
            type: 'HEAD',
            async: false,
            success: function() {
                result = true;
            }
        });
        return result;
    }

    // Inicializa os botões de exclusão de prêmios
    initDeletePremioButtons();
});