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
                    <button type="button" class="btn btn-danger btn-xs" id="remove_image_btn" style="position: absolute; bottom: -7px; right: -30px;">
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
    $(document).on('click', '.remove-image, #remove_image_btn', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $("#image").val('');
        $("#image-preview").html('<i class="fa fa-file-image-o" style="font-size: 32px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>');
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

        // Criar um FormData para enviar incluindo a imagem
        const formData = new FormData(this);
        
        // Alterar o botão para indicar processamento
        const $btn = $("#submit-btn");
        const originalText = $btn.html();
        $btn.html('<i class="fa fa-spinner fa-spin"></i> Processando...').prop('disabled', true);
        
        // URL para salvar o nível (novo ou edição)
        let url = ADMIN_URL_PREFIX + '/futligas/jogadores/nivel/novo/';
        if (isEditing) {
            url = ADMIN_URL_PREFIX + '/futligas/jogadores/nivel/editar/' + editingId + '/';
        }
        
        // Enviar via AJAX
        $.ajax({
            url: url,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                $btn.html(originalText).prop('disabled', false);
                
                if (response.success) {
                    // Recuperar a URL da imagem da resposta
                    const imageData = response.image_url;
                    
                    if (isEditing) {
                        updateLevel(editingId, name, players, premium_players, owner_premium, imageData);
                        toastr.success('Nível atualizado com sucesso!');
                    } else {
                        // Usar o ID retornado pelo backend para o novo nível
                        addLevel(name, players, premium_players, owner_premium, imageData, response.id);
                        toastr.success('Nível adicionado com sucesso!');
                    }
                    
                    resetForm();
                } else {
                    toastr.error(response.message || 'Erro ao salvar nível!');
                    console.error("Erro ao salvar nível:", response);
                }
            },
            error: function(xhr, status, error) {
                $btn.html(originalText).prop('disabled', false);
                
                console.error("Erro na requisição AJAX:", {status: status, error: error, response: xhr.responseText});
                
                let errorMsg = 'Erro ao salvar nível';
                try {
                    const errorResponse = JSON.parse(xhr.responseText);
                    if (errorResponse && errorResponse.message) {
                        errorMsg += ': ' + errorResponse.message;
                    }
                } catch (e) {
                    errorMsg += ': ' + error;
                }
                
                toastr.error(errorMsg);
            }
        });
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
                <button type="button" class="btn btn-danger btn-xs" id="remove_image_btn" style="position: absolute; bottom: -7px; right: -30px;">
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

    // Excluir nível
    $(document).on('click', '.btn-danger', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const row = $(this).closest('tr');
        const nivelId = row.data('id');
        const nivelNome = row.find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim();
        
        // Abre o modal de confirmação
        $('#levelNameToDelete').text(nivelNome);
        $('#modalConfirmDelete').data('row', row).modal('show');
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
            url: ADMIN_URL_PREFIX + '/futligas/jogadores/excluir/',
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
                    
                    // Fecha o modal
                    $('#modalConfirmDelete').modal('hide');
                    $('.modal-backdrop').remove();
                    $('body').removeClass('modal-open');
                    
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

    // Adicionar prêmio
    $(".btn-adicionar-premio").click(function() {
        const posicao = $('#premios table tbody tr').length + 1;
        
        // Obtém a lista de níveis
        const niveis = [];
        $("#table tbody tr").each(function() {
            niveis.push($(this).find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim());
        });
        
        // Cria a nova linha
        let newRow = `
            <tr>
                <td>${posicao}°</td>
                <td class="center-middle">
                    <div class="dropzone-imagem" style="height: 32px; width: 32px; border: 1px dashed #ccc; border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center;">
                        <i class="fa fa-plus"></i>
                    </div>
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
        
        // Adiciona células para cada nível
        niveis.forEach(nivel => {
            row.find('td:last').before(`
                <td>
                    <input type="number" class="form-control premio-valor" data-nivel="${nivel}" value="1000" min="0">
                </td>
            `);
        });
        
        // Adiciona evento de clique para a dropzone da nova linha
        row.find('.dropzone-imagem').on('click', handleDropzoneClick);
        
        // Adiciona evento de clique para o botão de excluir
        row.find('.btn-danger').on('click', function() {
            if (confirm('Tem certeza que deseja excluir este prêmio?')) {
                row.remove();
                
                // Atualiza as posições
                $('#premios table tbody tr').each(function(index) {
                    $(this).find('td:first').text((index + 1) + '°');
                });
            }
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
        $('.premio-table tbody tr').each(function(index) {
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
            
            // Procura imagem do prêmio - verificando dentro do container de imagem também
            let image = null;
            // Primeiro, tenta encontrar a imagem diretamente
            let $img = $row.find('td:eq(1) > img');
            
            // Se não encontrar, tenta encontrar a imagem dentro do container
            if (!$img.length) {
                $img = $row.find('td:eq(1) .image-container img');
            }
            
            if ($img.length) {
                image = $img.attr('src');
                console.log(`Prêmio posição ${position}: Imagem encontrada com src: ${image.substring(0, 30)}...`);
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
        
        $btn.html('<i class="fa fa-spinner fa-spin"></i> Salvando...').prop('disabled', true);

        $.ajax({
            url: ADMIN_URL_PREFIX + '/futligas/jogadores/salvar/',
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
                if (response.success) {
                    toastr.success('Alterações salvas com sucesso!');
                    
                    // Recarregar os dados após salvar com sucesso
                    setTimeout(function() {
                        // Recarregar a página para garantir que os dados estejam atualizados
                        window.location.reload();
                    }, 1500);
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
    function addLevel(name, players, premium_players, owner_premium, imageData = null, id = null) {
        const levelId = id || Date.now(); // Usar o ID retornado pelo backend ou gerar um temporário
        const newRow = `
            <tr data-id="${levelId}">
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
        
        // Só limpa o preview se não estiver editando
        if (!isEditing) {
            $("#image-preview").html(`
                <label class="label-card label-card-small">
                    <i class="fa fa-file-image-o label-content" style="font-size: 48px; color: #ccc; cursor: pointer;" onclick="document.getElementById('image').click()"></i>
                    <input accept="image/*" type="file" name="image" id="image" class="input-image">
                </label>
            `);
        }
        
        $('.i-checks').iCheck('update');
        
        if (isEditing) {
            $("#submit-btn").html('<i class="fa fa-plus mr5"></i> Adicionar');
            isEditing = false;
            editingId = null;
        }
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
        
        // Verifica quantas posições existem
        let premioRows = $('#premios table tbody tr').length;
        if (premioRows === 0) {
            // Adiciona pelo menos 3 posições se não houver nenhuma
            for (let i = 1; i <= 3; i++) {
                $('#premios table tbody').append(`
                    <tr>
                        <td>${i}°</td>
                        <td class="center-middle">
                            <div class="dropzone-imagem" style="height: 32px; width: 32px; border: 1px dashed #ccc; border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center;">
                                <i class="fa fa-plus"></i>
                            </div>
                        </td>
                        <td>
                            <div>
                                <button type="button" class="btn btn-danger btn-xs mr5" title="Excluir"><i class="glyphicon glyphicon-trash"></i></button>
                            </div>
                        </td>
                    </tr>
                `);
            }
            premioRows = 3;
        }

        // Atualiza os cabeçalhos da tabela para incluir os níveis
        const premiosHeader = $('#premios table thead tr');
        premiosHeader.find('th:gt(1):not(:last)').remove();
        niveis.forEach(nivel => {
            premiosHeader.find('th:last').before(`<th class="per15" data-nivel="${nivel}">${nivel}</th>`);
        });

        // Atualiza cada linha existente para incluir células para cada nível
        $('#premios table tbody tr').each(function() {
            const row = $(this);
            row.find('td:gt(1):not(:last)').remove();
            niveis.forEach((nivel, index) => {
                row.find('td:last').before(`
                    <td>
                        <input type="number" class="form-control premio-valor" data-nivel="${nivel}" value="1000" min="0">
                    </td>
                `);
            });
        });

        // Reaplica o evento de clique nas dropzones após carregar os dados
        $('#premios table .dropzone-imagem').each(function() {
            $(this).on('click', handleDropzoneClick);
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
            const file = this.files[0];
            
            // Verifica se é uma imagem
            if (file && !file.type.match('image.*')) {
                toastr.error('Por favor, selecione apenas arquivos de imagem.');
                $(this).remove();
                return;
            }
            
            // Verifica o tamanho do arquivo (máximo 2MB)
            if (file.size > 2 * 1024 * 1024) {
                toastr.error('A imagem deve ter no máximo 2MB.');
                $(this).remove();
                return;
            }
            
            // Mostra indicador de carregamento
            currentCell.html('<div style="text-align: center;"><i class="fa fa-spinner fa-spin"></i></div>');
            
            // Lê o arquivo como DataURL
            const reader = new FileReader();
            
            reader.onload = function(e) {
                // Quando a leitura for concluída, substitui o dropzone pela imagem
                currentCell.html(`
                    <div class="image-container" style="position: relative; width: 32px; height: 32px; display: inline-block;">
                        <img src="${e.target.result}" height="32" width="32" alt="Imagem" style="object-fit: contain;">
                        <div class="image-remove-btn" style="position: absolute; bottom: 0; right: 0; background-color: #f8f8f8; border-radius: 50%; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 1px 3px rgba(0,0,0,0.2);">
                            <i class="fa fa-trash" style="font-size: 10px; color: #FF5252;"></i>
                        </div>
                    </div>
                `);
                
                toastr.success('Imagem adicionada com sucesso!');
            };
            
            reader.onerror = function() {
                // Em caso de erro, reverte para o dropzone
                currentCell.html(`
                    <div class="dropzone-imagem" style="height: 32px; width: 32px; border: 1px dashed #ccc; border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center;">
                        <i class="fa fa-plus"></i>
                    </div>
                `);
                
                toastr.error('Erro ao processar a imagem. Tente novamente.');
            };
            
            // Inicia a leitura do arquivo
            reader.readAsDataURL(file);
            
            // Remove o input temporário
            $(this).remove();
        });
        
        // Abre o seletor de arquivos
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
        url: ADMIN_URL_PREFIX + '/futligas/jogadores/dados/',
        method: 'GET',
        success: function(data) {
            if (data.success === false) {
                toastr.error(data.message || "Erro ao carregar dados");
                return;
            }
            
            // Primeiro carregamos os níveis
            data.levels.forEach(nivel => {
                addLevel(
                    nivel.name,
                    nivel.players,
                    nivel.premium_players,
                    nivel.owner_premium,
                    nivel.image
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
                            
                            // Reaplica o evento de clique na nova dropzone
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
        // Remove o redirecionamento de URL que estava invertido
        // O correto é manter as URLs em /futligas/jogadores/... e não converter para administrativo
        if (options.url.indexOf('/administrativo/futligas/jogadores/dados/') !== -1) {
            options.url = "/futligas/jogadores/dados/";
        } else if (options.url.indexOf('/administrativo/futligas/jogadores/salvar/') !== -1) {
            options.url = "/futligas/jogadores/salvar/";
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
});