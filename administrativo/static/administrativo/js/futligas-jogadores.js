$(document).ready(function() {
    let isEditing = false;
    let editingId = null;
    let niveisData = [];
    
    // Detecta o prefixo da URL dinamicamente
    const ADMIN_URL_PREFIX = (function() {
        const metaElement = document.querySelector('meta[name="url-prefix"]');
        if (metaElement && metaElement.getAttribute('content')) {
            return metaElement.getAttribute('content');
        }
        return '/administrativo'; // Valor padrão caso não encontre a meta tag
    })();
    
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
        }

        // Cria ou atualiza o nível
        if (isEditing) {
            updateLevel(editingId, name, players, premium_players, owner_premium, imageData);
            toastr.success('Nível atualizado com sucesso!');
        } else {
            addLevel(name, players, premium_players, owner_premium, imageData);
            toastr.success('Nível adicionado com sucesso!');
        }

        resetForm();
    });

    // Editar nível
    $(document).on('click', '.btn-info', function() {
        const row = $(this).closest('tr');
        editingId = row.data('id');
        
        // Remove o ícone de barras do nome
        const name = row.find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim();
        $("#name").val(name);
        $("#players").val(row.find('td:eq(2)').text());
        $("#premium_players").val(row.find('td:eq(3)').text());
        $("#owner_premium").prop('checked', row.find('td:eq(4)').text() === 'Sim').iCheck('update');
        
        // Recupera a imagem existente se houver
        const existingImage = row.find('td:eq(1) img');
        if (existingImage.length) {
            $("#image-preview").html(`
                <img src="${existingImage.attr('src')}" style="max-width: 50px; max-height: 50px; object-fit: contain; cursor: pointer;" onclick="document.getElementById('image').click()">
                <button type="button" class="btn btn-danger btn-xs img-remove-btn" id="remove_image_btn" style="position: absolute; bottom: -7px; right: -30px;">
                    <i class="fa fa-trash"></i>
                </button>
            `);
            $('#image-preview').css('margin-top', '-7px');
        } else {
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
    
    // Confirmar exclusão no modal
    $('#confirmDeleteButton').click(function() {
        const row = $('#modalConfirmDelete').data('row');
        const nivelId = row.data('id');
        const nivelNome = row.find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim();
        
        // Botão de confirmação - mostra spinner
        const $btn = $(this);
        const originalText = $btn.html();
        $btn.html('<i class="fa fa-spinner fa-spin"></i> Excluindo...').prop('disabled', true);
        
        // Envia solicitação AJAX para excluir o nível
        $.ajax({
            url: "/futligas/jogadores/excluir/",
            method: 'POST',
            headers: {
                'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
            },
            data: JSON.stringify({
                level_id: nivelId,
                level_name: nivelNome
            }),
            contentType: 'application/json',
            success: function(response) {
                if (response.success) {
                    // Remove a linha
                    row.remove();
                    
                    // Atualiza a tabela de prêmios
                    updatePremiosTable();
                    
                    // Restaura o botão antes de fechar o modal
                    $btn.html(originalText).prop('disabled', false);
                    
                    // Fecha o modal
                    $('#modalConfirmDelete').modal('hide');
                    
                    // Limpa o modal corretamente
                    setTimeout(function() {
                        $('.modal-backdrop').remove();
                        $('body').removeClass('modal-open');
                        resetModalState();
                    }, 300);
                    
                    // Notifica o usuário
                    toastr.success('Nível excluído com sucesso!');
                    
                    // Atualiza o drag and drop após excluir
                    initDragAndDrop();
                } else {
                    toastr.error(response.message || 'Erro ao excluir nível!');
                    console.error("Erro ao excluir (sucesso=false):", response);
                    
                    // Restaura o botão
                    $btn.html(originalText).prop('disabled', false);
                }
            },
            error: function(xhr, status, error) {
                console.error("Erro na requisição AJAX de exclusão:", {status: status, error: error, response: xhr.responseText});
                
                let errorMsg = 'Erro ao excluir nível';
                try {
                    const errorResponse = JSON.parse(xhr.responseText);
                    if (errorResponse && errorResponse.error) {
                        errorMsg += ': ' + errorResponse.error;
                    } else if (errorResponse && errorResponse.message) {
                        errorMsg += ': ' + errorResponse.message;
                    } else {
                        errorMsg += ': ' + error;
                    }
                } catch (e) {
                    errorMsg += ': ' + error;
                    if (xhr.status) {
                        errorMsg += ' (Status ' + xhr.status + ')';
                    }
                }
                
                toastr.error(errorMsg);
                
                // Restaura o botão
                $btn.html(originalText).prop('disabled', false);
                
                // Fecha o modal se houve erro
                $('#modalConfirmDelete').modal('hide');
                $('.modal-backdrop').remove();
                $('body').removeClass('modal-open');
            }
        });
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

    // Adiciona prêmio - Atualizar para usar o seletor correto do botão
    $("#addPremioRow, .btn-adicionar-premio").click(function() {
        const posicao = $('.premio-table tbody tr').length + 1;
        
        // Obtém a lista de níveis
        const niveis = [];
        $("#table tbody tr").each(function() {
            niveis.push($(this).find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim());
        });
        
        // Cria a nova linha
        let newRow = `
            <tr class="premio-row">
                <td>
                    <input type="number" class="form-control position-input" min="1" value="${posicao}">
                </td>
                <td class="center-middle">
                    <div class="image-preview-container">
                        <input type="file" class="premio-image" accept="image/*" style="display: none;">
                        <div class="premio-image-preview">
                            <i class="fa fa-file-image-o"></i>
                        </div>
                    </div>
                </td>`;
                
        // Adiciona uma coluna para cada nível
        niveis.forEach(nivel => {
            newRow += `
                <td>
                    <input type="number" class="form-control premio-valor" data-nivel="${nivel}" min="0" value="1000">
                </td>`;
        });
        
        // Adiciona a coluna de ações
        newRow += `
                <td>
                    <button type="button" class="btn btn-danger btn-xs delete-premio" title="Excluir"><i class="glyphicon glyphicon-trash"></i></button>
                </td>
            </tr>`;
        
        // Adiciona a nova linha à tabela
        $('.premio-table tbody').append(newRow);
        
        // Inicializa o preview de imagem para a nova linha
        initPremioImagePreview($('.premio-table tbody tr:last'));
        
        // Reaplica os eventos aos botões de exclusão
        initDeletePremioButtons();
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
        $('.delete-premio').off('click').on('click', function() {
            const $row = $(this).closest('tr');
            const position = $row.find('td:first').text();
            
            if (confirm(`Tem certeza que deseja excluir o prêmio da posição ${position}?`)) {
                $row.remove();
                
                // Atualiza as posições dos prêmios
                $('#premiosTable tbody tr').each(function(index) {
                    $(this).find('td:first').text((index + 1) + '°');
                });
            }
        });
    }
    
    // Delegação de evento para os botões de excluir prêmio
    $(document).on('click', '.remove-premio', function() {
        const row = $(this).closest('tr');
        const position = row.find('.position-input').val() || row.index() + 1;
        
        if (confirm(`Tem certeza que deseja excluir o prêmio da posição ${position}?`)) {
            row.remove();
            
            // Atualiza as posições das linhas restantes
            $('#premiosTable tbody tr').each(function(index) {
                $(this).find('.position-input').val(index + 1);
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

    // Salvar todas as alterações
    $("#successToast").click(function(e) {
        e.preventDefault();
        
        // Coleta todos os níveis da tabela
        const niveis = [];
        const $btn = $(this);
        const originalText = $btn.html();
        
        // Debug
        console.log("Iniciando coleta de dados");
        
        $('#table tbody tr').each(function(index) {
            const $row = $(this);
            const id = $row.data('id');
            
            // Remove o ícone de barras do nome
            const name = $row.find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim();
            
            // Obtém a imagem se houver
            const $img = $row.find('td:eq(1) img');
            let image = null;
            if ($img.length) {
                image = $img.attr('src');
                console.log(`Nível ${name}: Imagem encontrada com src ${image.substring(0, 30)}...`);
            } else {
                console.log(`Nível ${name}: Sem imagem`);
            }
            
            // Obtém os valores das colunas
            niveis.push({
                id: id,
                name: name,
                image: image,
                players: parseInt($row.find('td:eq(2)').text()),
                premium_players: parseInt($row.find('td:eq(3)').text()),
                owner_premium: $row.find('td:eq(4)').text() === 'Sim',
                order: index + 1
            });
        });
        
        // Obtém os prêmios da tabela
        const premios = [];
        $('#premiosTable tbody tr').each(function(index) {
            const $row = $(this);
            const position = index + 1;
            const values = {};
            
            // Para cada nível, obtém o valor correspondente
            $row.find('.premio-valor').each(function() {
                const nivelName = $(this).data('nivel');
                if (nivelName) {
                    console.log(`Coletando valor para posição ${position}, nível ${nivelName}: ${$(this).val()}`);
                    values[nivelName] = parseInt($(this).val()) || 0;
                }
            });
            
            // Procura imagem do prêmio
            let image = null;
            // Primeiro, tenta encontrar a imagem diretamente
            let $img = $row.find('td:eq(1) img');
            
            // Se não encontrar, tenta encontrar a imagem dentro de qualquer container
            if (!$img.length) {
                $img = $row.find('td:eq(1) img');
            }
            
            if ($img.length) {
                image = $img.attr('src');
                console.log(`Prêmio posição ${position}: Imagem encontrada com src: ${image ? image.substring(0, 30) + '...' : 'undefined'}`);
            } else {
                console.log(`Prêmio posição ${position}: Sem imagem`);
            }
            
            console.log(`Prêmio posição ${position}, valores:`, values);
            
            premios.push({
                position: position,
                values: values,
                image: image
            });
        });
        
        // Obtém as configurações de premiação
        const premiacao = {
            weekly: {
                day: $('#dia-premiacao').val(),
                time: $('.clockpicker:eq(0) input').val()
            },
            season: {
                month: $('#mes-ano-premiacao').val(),
                day: $('#dia-ano-premiacao').val(),
                time: $('.clockpicker:eq(1) input').val()
            }
        };
        
        // Debug dos dados
        console.log("Dados a serem enviados:", {
            levels: niveis,
            prizes: premios,
            award_config: premiacao
        });
        
        // Verificação detalhada de imagens nos níveis antes de enviar
        if (niveis && niveis.length > 0) {
            console.log("Verificação detalhada de imagens antes de enviar:");
            niveis.forEach((nivel, index) => {
                console.log(`Nível ${index + 1} - ${nivel.name}: Tem imagem? ${nivel.image ? 'Sim' : 'Não'}`);
                if (nivel.image) {
                    console.log(`Imagem URL: ${nivel.image.substring(0, 50)}...`);
                }
            });
        }
        
        $btn.html('<i class="fa fa-spinner fa-spin"></i> Salvando...').prop('disabled', true);

        $.ajax({
            url: "/futligas/jogadores/salvar/",
            method: 'POST',
            headers: {
                'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
            },
            data: JSON.stringify({
                levels: niveis,
                prizes: premios,
                award_config: premiacao
            }),
            contentType: 'application/json',
            success: function(response) {
                console.log("Resposta do servidor:", response);
                
                // Verificação detalhada da resposta do servidor
                if (response.success && response.data) {
                    console.log("Verificação da resposta do servidor após salvamento:");
                    
                    if (response.data.levels) {
                        console.log(`Níveis retornados pelo servidor: ${response.data.levels.length}`);
                        response.data.levels.forEach((nivel, index) => {
                            console.log(`Nível ${index + 1} - ${nivel.name}: Tem imagem? ${nivel.image ? 'Sim' : 'Não'}`);
                            if (nivel.image) {
                                console.log(`Imagem URL: ${nivel.image.substring(0, 50)}...`);
                            }
                        });
                    }
                }
                
                if (response.success) {
                    toastr.success('Alterações salvas com sucesso!');
                    // Não recarregamos a página para evitar perder as imagens
                    // Os dados já estão atualizados na interface
                    
                    // Aviso para não recarregar a página
                    setTimeout(function() {
                        toastr.info('Não recarregue a página (F5) para evitar perder as imagens. As alterações já foram salvas.');
                    }, 1000);
                } else {
                    toastr.error(response.message || response.error || 'Erro ao salvar alterações!');
                    console.error("Erro ao salvar (sucesso=false):", response);
                    
                    // Se há detalhes específicos do erro, mostrá-los no console
                    if (response.details) {
                        console.error("Detalhes do erro:", response.details);
                    }
                }
                $btn.html(originalText).prop('disabled', false);
            },
            error: function(xhr, status, error) {
                console.error("Erro na requisição AJAX:", {status: status, error: error, response: xhr.responseText});
                
                let errorMsg = 'Erro ao salvar dados';
                
                try {
                    const errorResponse = JSON.parse(xhr.responseText);
                    if (errorResponse && errorResponse.error) {
                        errorMsg += ': ' + errorResponse.error;
                        
                        // Se há detalhes específicos do erro, mostrá-los no console
                        if (errorResponse.details) {
                            console.error("Detalhes do erro:", errorResponse.details);
                        }
                    } else if (errorResponse && errorResponse.message) {
                        errorMsg += ': ' + errorResponse.message;
                    } else {
                        errorMsg += ': ' + error;
                    }
                } catch (e) {
                    errorMsg += ': ' + error;
                    if (xhr.status) {
                        errorMsg += ' (Status ' + xhr.status + ')';
                    }
                }
                
                toastr.error(errorMsg);
                $btn.html(originalText).prop('disabled', false);
            }
        });
    });

    // Funções auxiliares
    function addLevel(name, players, premium_players, owner_premium, imageData = null) {
        const newRow = `
            <tr data-id="${Date.now()}">
                <td><i class="fa fa-bars drag-handle"></i> ${name}</td>
                <td class="center-middle">
                    ${imageData ? `<img src="${imageData}" style="width: 32px; height: 32px; object-fit: contain;" alt="Imagem">` : ''}
                </td>
                <td>${players}</td>
                <td>${premium_players}</td>
                <td>${owner_premium ? 'Sim' : 'Não'}</td>
                <td>
                    <div>
                        <button type="button" class="btn btn-info btn-xs mr5" title="Editar"><i class="glyphicon glyphicon-pencil"></i></button>
                        <button type="button" class="btn btn-danger btn-xs mr5" title="Excluir"><i class="glyphicon glyphicon-trash"></i></button>
                    </div>
                </td>
            </tr>
        `;
        $("#table tbody").append(newRow);
        updatePremiosTable();
        
        // Reinicializa o drag and drop após adicionar nova linha
        initDragAndDrop();
    }

    function updateLevel(id, name, players, premium_players, owner_premium, imageData = null) {
        const row = $(`tr[data-id="${id}"]`);
        row.find('td:eq(0)').html(`<i class="fa fa-bars drag-handle"></i> ${name}`);
        row.find('td:eq(2)').text(players);
        row.find('td:eq(3)').text(premium_players);
        row.find('td:eq(4)').text(owner_premium ? 'Sim' : 'Não');
        
        // Atualiza a imagem se tiver uma nova
        if (imageData) {
            row.find('td:eq(1)').html(`<img src="${imageData}" style="width: 32px; height: 32px; object-fit: contain;" alt="Imagem">`);
        } else {
            row.find('td:eq(1)').html(''); // Remove a imagem se não tiver uma nova
        }
        
        // Limpa o campo de imagem e o preview
        $("#image").val('');
        $("#image-preview").html('<i class="fa fa-file-image-o" style="font-size: 32px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>');
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
        const niveis = [];
        $("#table tbody tr").each(function() {
            niveis.push($(this).find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim());
        });

        // Log para debug
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
                
                // Adiciona coluna de ações
                $premiosTable.find('tbody tr:last').append(`
                        <td>
                            <div>
                                <button type="button" class="btn btn-danger btn-xs mr5 delete-premio" title="Excluir"><i class="glyphicon glyphicon-trash"></i></button>
                            </div>
                        </td>
                    </tr>
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
        });
        
        // Verifica se há alguma célula de imagem sem o evento de click configurado
        $premiosTable.find('.premio-image-preview').each(function() {
            if (!$(this).data('click-initialized')) {
                const $row = $(this).closest('tr');
                initPremioImagePreview($row);
            }
        });
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

    // Carrega dados iniciais
    $.ajax({
        url: "/futligas/jogadores/dados/",
        method: 'GET',
        success: function(data) {
            if (data.success === false) {
                toastr.error(data.message || "Erro ao carregar dados");
                return;
            }
            
            // Debug dos dados recebidos
            console.log("Dados recebidos do servidor:", data);
            console.log("Níveis recebidos:", data.levels ? data.levels.length : 0);
            
            // Verificação de imagens nos níveis
            if (data.levels && data.levels.length > 0) {
                data.levels.forEach((nivel, index) => {
                    console.log(`Nível ${index + 1} - ${nivel.name}: Tem imagem? ${nivel.image ? 'Sim' : 'Não'}`);
                    if (nivel.image) {
                        console.log(`Imagem URL: ${nivel.image.substring(0, 50)}...`);
                    }
                });
            }
            
            // Salva as imagens existentes na tabela antes de limpar
            const imagensExistentes = {};
            $('#table tbody tr').each(function() {
                const nome = $(this).find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim();
                const img = $(this).find('td:eq(1) img').attr('src');
                if (img) {
                    imagensExistentes[nome] = img;
                    console.log(`Salvando imagem existente para ${nome}: ${img.substring(0, 30)}...`);
                }
            });
            
            // Limpa a tabela antes de adicionar os novos dados
            $('#table tbody').empty();
            
            // Primeiro carregamos os níveis
            data.levels.forEach(nivel => {
                // Se o nível não tem imagem mas temos uma imagem salva para ele, usamos a imagem salva
                let imagemFinal = nivel.image;
                if (!imagemFinal && imagensExistentes[nivel.name]) {
                    imagemFinal = imagensExistentes[nivel.name];
                    console.log(`Usando imagem existente para ${nivel.name}: ${imagemFinal.substring(0, 30)}...`);
                }
                
                addLevel(
                    nivel.name,
                    nivel.players,
                    nivel.premium_players,
                    nivel.owner_premium,
                    imagemFinal
                );
            });

            $("#dia-premiacao").val(data.award_config.weekly.day);
            $(".clockpicker:eq(0) input").val(data.award_config.weekly.time);
            $("#mes-ano-premiacao").val(data.award_config.season.month);
            $("#dia-ano-premiacao").val(data.award_config.season.day);
            $(".clockpicker:eq(1) input").val(data.award_config.season.time);
            
            // Atualizamos a tabela de prêmios
            updatePremiosTable();
            
            // Limpa a tabela de prêmios para recriar com base nos dados do banco
            $('#premios table tbody').empty();
            
            // Carregamos as posições de prêmios do banco de dados
            if (data.prizes && data.prizes.length > 0) {
                console.log("Carregando dados dos prêmios:", data.prizes);
                
                // Ordena os prêmios por posição para garantir que sejam exibidos na ordem correta
                data.prizes.sort((a, b) => a.position - b.position);
                
                // Para cada prêmio, criamos uma linha na tabela
                data.prizes.forEach(premio => {
                    // Cria a nova linha na tabela
                    let newRow = `
                        <tr data-position="${premio.position}">
                            <td>${premio.position}°</td>
                            <td class="center-middle">
                                ${premio.image ? 
                                    `<div class="image-container" style="position: relative; width: 32px; height: 32px; display: inline-block;">
                                        <img src="${premio.image}" height="32" width="32" alt="Imagem" style="object-fit: contain;">
                                        <div class="image-remove-btn" style="position: absolute; bottom: 0; right: 0; background-color: #f8f8f8; border-radius: 50%; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 1px 3px rgba(0,0,0,0.2);">
                                            <i class="fa fa-trash" style="font-size: 10px; color: #FF5252;"></i>
                                        </div>
                                    </div>` : 
                                    `<div class="dropzone-imagem" style="height: 32px; width: 32px; border: 1px dashed #ccc; border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center;">
                                        <i class="fa fa-plus"></i>
                                    </div>`
                                }
                            </td>
                            <td>
                                <div>
                                    <button type="button" class="btn btn-danger btn-xs mr5" title="Excluir"><i class="glyphicon glyphicon-trash"></i></button>
                                </div>
                            </td>
                        </tr>
                    `;
                    
                    $('#premios table tbody').append(newRow);
                    
                    // Obtém a linha recém-adicionada
                    const row = $('#premios table tbody tr').last();
                    
                    // Obtém a lista de níveis
                    const niveis = [];
                    $("#table tbody tr").each(function() {
                        niveis.push($(this).find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim());
                    });
                    
                    // Adiciona células para cada nível
                    niveis.forEach((nivel, index) => {
                        const valorPremio = premio.values && premio.values[nivel] !== undefined ? premio.values[nivel] : 1000;
                        row.find('td:last').before(`
                            <td>
                                <input type="number" class="form-control premio-valor" data-nivel="${nivel}" value="${valorPremio}" min="0">
                            </td>
                        `);
                    });
                    
                    console.log(`Criada linha para o prêmio posição ${premio.position}`);
                    
                    // Adiciona evento de clique para o botão de remover imagem
                    if (premio.image) {
                        row.find('.image-remove-btn').on('click', function(e) {
                            e.preventDefault();
                            e.stopPropagation();
                            
                            const cell = $(this).closest('td');
                            cell.html(`
                                <div class="dropzone-imagem" style="height: 32px; width: 32px; border: 1px dashed #ccc; border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center;">
                                    <i class="fa fa-plus"></i>
                                </div>
                            `);
                            
                            toastr.success('Imagem removida com sucesso!');
                            
                            // Reaplica o evento de clique à nova dropzone
                            cell.find('.dropzone-imagem').on('click', handleDropzoneClick);
                        });
                    }
                });
                
                // Reaplica o evento de clique nas dropzones após carregar os dados
                $('#premios table .dropzone-imagem').each(function() {
                    $(this).on('click', handleDropzoneClick);
                });
            } else {
                // Se não há prêmios, adicionamos pelo menos 3 posições padrão
                for (let i = 1; i <= 3; i++) {
                    $('.btn-adicionar-premio').click();
                }
            }
            
            // Inicializa o drag and drop após carregar os dados
            initDragAndDrop();
            
            // Mensagem de sucesso após carregamento
            toastr.success("Dados carregados com sucesso!");
        },
        error: function(xhr, status, error) {
            console.error("Erro ao carregar dados:", error);
            toastr.error("Ocorreu um erro ao carregar os dados. Por favor, atualize a página.");
        }
    });
    
    // Ajuste do problema de AJAX - garante que as URLs são redirecionadas corretamente
    $.ajaxPrefilter(function(options, originalOptions, jqXHR) {
        // Evitando loops de redirecionamento de URLs e garantindo formatos corretos
        if (options.url === '/futligas/jogadores/dados/') {
            options.url = "/futligas/jogadores/dados/";
        } else if (options.url === '/futligas/jogadores/salvar/') {
            options.url = "/futligas/jogadores/salvar/";
        }
        
        // Evitando duplicação de prefixos quando ADMIN_URL_PREFIX já foi adicionado
        if (options.url.includes("/administrativo/administrativo/")) {
            options.url = options.url.replace("/administrativo/administrativo/", "/futligas/");
        }
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

    // Adiciona evento para o botão de adicionar prêmio
    $('.btn-adicionar-premio').off('click').on('click', function() {
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
        
        // Finaliza a linha com a célula de ações
        newRow += `
                <td>
                    <div>
                        <button type="button" class="btn btn-danger btn-xs mr5 delete-premio" title="Excluir"><i class="glyphicon glyphicon-trash"></i></button>
                    </div>
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

    // Inicializa os botões de exclusão de prêmios
    initDeletePremioButtons();
});