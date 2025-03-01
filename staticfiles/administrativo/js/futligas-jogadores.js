$(document).ready(function() {
    let isEditing = false;
    let editingId = null;
    
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
    });

    // Inicializa clockpicker
    $('.clockpicker').clockpicker();

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
                    <div class="position-relative">
                        <img src="${e.target.result}" style="width: 48px; height: 48px; object-fit: contain; cursor: pointer;" onclick="document.getElementById('image').click()">
                        <button type="button" class="btn btn-danger btn-xs remove-image" style="position: absolute; bottom: -7px; right: -30px;">
                            <i class="fa fa-trash"></i>
                        </button>
                    </div>
                `);
            };
            reader.readAsDataURL(file);
        }
    });

    // Remove imagem
    $(document).on('click', '.remove-image', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $("#image").val('');
        $("#image-preview").html(`
            <label class="label-card label-card-small">
                <i class="fa fa-file-image-o label-content" style="font-size: 48px; color: #ccc; cursor: pointer;" onclick="document.getElementById('image').click()"></i>
                <input accept="image/*" type="file" name="image" id="image" class="input-image">
            </label>
        `);
    });

    // Submit do formulário
    $("#form-futliga").submit(function(e) {
        e.preventDefault();
        
        const name = $("#name").val();
        const players = $("#players").val();
        const premium_players = $("#premium_players").val();
        const owner_premium = $("#owner_premium").prop('checked');
        
        // Validação de nome duplicado
        if (!isEditing && checkDuplicateName(name)) {
            toastr.error('Já existe um nível com este nome!');
            return;
        }

        // Cria ou atualiza o nível
        if (isEditing) {
            updateLevel(editingId, name, players, premium_players, owner_premium);
        } else {
            addLevel(name, players, premium_players, owner_premium);
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
                <div class="position-relative">
                    <img src="${existingImage.attr('src')}" style="width: 48px; height: 48px; object-fit: contain; cursor: pointer;" onclick="document.getElementById('image').click()">
                    <button type="button" class="btn btn-danger btn-xs remove-image" style="position: absolute; bottom: -7px; right: -30px;">
                        <i class="fa fa-trash"></i>
                    </button>
                </div>
            `);
        }
        
        $("#submit-btn").html('<i class="fa fa-save mr5"></i> Salvar Alterações');
        isEditing = true;
    });

    // Excluir nível
    $(document).on('click', '.btn-danger', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const row = $(this).closest('tr');
        const nivelId = row.data('id');
        
        // Confirma exclusão
        if (confirm('Tem certeza que deseja excluir este nível?')) {
            row.remove();
            updatePremiosTable();
            toastr.success('Nível excluído com sucesso!');
            
            // Atualiza o drag and drop após excluir
            initDragAndDrop();
        }
    });

    // Importar níveis
    $("button:contains('Importar')").click(function() {
        const input = $('<input type="file" accept=".xls,.xlsx" style="display:none">');
        input.click();

        input.change(function(e) {
            const file = e.target.files[0];
            const reader = new FileReader();

            reader.onload = function(e) {
                try {
                    const data = new Uint8Array(e.target.result);
                    const workbook = XLSX.read(data, {type: 'array'});
                    const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
                    const jsonData = XLSX.utils.sheet_to_json(firstSheet);

                    // Limpa a tabela atual
                    $("#table tbody").empty();

                    // Adiciona os níveis importados
                    jsonData.forEach(function(row) {
                        addLevel(
                            row['Nível'],
                            row['Participantes'],
                            row['Craques'],
                            row['Dono Craque'] === 'Sim',
                            row['Imagem']
                        );
                    });

                    updatePremiosTable();
                    toastr.success('Níveis importados com sucesso!');
                    
                    // Reinicializa o drag and drop após importar
                    initDragAndDrop();
                } catch (error) {
                    toastr.error('Erro ao importar arquivo. Verifique o formato!');
                }
            };

            reader.readAsArrayBuffer(file);
        });
    });

    // Exportar níveis
    $("a[title='Exportar']").click(function() {
        const data = [];
        $("#table tbody tr").each(function() {
            const row = $(this);
            data.push({
                'Nível': row.find('td:eq(0)').text(),
                'Participantes': row.find('td:eq(2)').text(),
                'Craques': row.find('td:eq(3)').text(),
                'Dono Craque': row.find('td:eq(4)').text()
            });
        });

        const ws = XLSX.utils.json_to_sheet(data);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Níveis");
        XLSX.writeFile(wb, "futligas_niveis.xlsx");
    });

    // Salvar todas as alterações
    $("#successToast").click(function() {
        const niveis = [];
        const premios = [];
        
        $("#table tbody tr").each(function(index) {
            const row = $(this);
            niveis.push({
                id: row.data('id'),
                name: row.find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim(),
                players: parseInt(row.find('td:eq(2)').text()),
                premium_players: parseInt(row.find('td:eq(3)').text()),
                owner_premium: row.find('td:eq(4)').text() === 'Sim',
                order: index,
                image: row.find('td:eq(1) img').attr('src') || null
            });
        });

        $('#premios table tbody tr').each(function() {
            const row = $(this);
            const premio = {
                position: parseInt(row.find('td:eq(0)').text()),
                values: {}
            };

            // Corrigido para pegar os valores dos inputs
            row.find('td:gt(1):not(:last)').each(function(index) {
                premio.values[niveis[index].name] = parseInt($(this).find('input').val()) || 0;
            });

            premios.push(premio);
        });

        const premiacao = {
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

        $.ajax({
            url: '/futligas/jogadores/salvar/',
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
                if (response.success) {
                    toastr.success('Alterações salvas com sucesso!');
                } else {
                    toastr.error(response.message || 'Erro ao salvar alterações!');
                }
            },
            error: function(xhr) {
                toastr.error(xhr.responseJSON?.message || 'Erro ao salvar alterações!');
            }
        });
    });

    // Funções auxiliares
    function addLevel(name, players, premium_players, owner_premium, image = null) {
        const newRow = `
            <tr data-id="${Date.now()}">
                <td><i class="fa fa-bars drag-handle"></i> ${name}</td>
                <td class="center-middle">
                    ${image ? `<img src="${image}" style="width: 32px; height: 32px; object-fit: contain;" alt="Imagem">` : ''}
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

    function updateLevel(id, name, players, premium_players, owner_premium) {
        const row = $(`tr[data-id="${id}"]`);
        row.find('td:eq(0)').html(`<i class="fa fa-bars drag-handle"></i> ${name}`);
        row.find('td:eq(2)').text(players);
        row.find('td:eq(3)').text(premium_players);
        row.find('td:eq(4)').text(owner_premium ? 'Sim' : 'Não');
        
        // Se tiver uma nova imagem selecionada
        if ($("#image").val()) {
            const file = $("#image")[0].files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    row.find('td:eq(1)').html(`<img src="${e.target.result}" style="width: 32px; height: 32px; object-fit: contain;" alt="Imagem">`);
                };
                reader.readAsDataURL(file);
            }
        } else {
            // Se não tiver nova imagem, mantém a existente
            const existingImage = $("#image-preview img");
            if (existingImage.length === 0) {
                // Se não tiver imagem no preview, limpa a célula
                row.find('td:eq(1)').empty();
            }
        }
        
        updatePremiosTable();
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
        const order = [];
        $("#table tbody tr").each(function() {
            order.push($(this).find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim());
        });
    }

    function updatePremiosTable() {
        const niveis = [];
        $("#table tbody tr").each(function() {
            niveis.push($(this).find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim());
        });

        const premiosHeader = $('#premios table thead tr');
        premiosHeader.find('th:gt(1):not(:last)').remove();
        niveis.forEach(nivel => {
            premiosHeader.find('th:last').before(`<th class="per15">${nivel}</th>`);
        });

        $('#premios table tbody tr').each(function() {
            const row = $(this);
            row.find('td:gt(1):not(:last)').remove();
            niveis.forEach(() => {
                row.find('td:last').before(`
                    <td>
                        <input type="number" class="form-control premio-valor" value="1000" min="0">
                    </td>
                `);
            });
        });
    }

    // Carrega dados iniciais
    $.ajax({
        url: '/futligas/jogadores/dados',
        method: 'GET',
        success: function(data) {
            data.niveis.forEach(nivel => {
                addLevel(
                    nivel.nome,
                    nivel.participantes,
                    nivel.craques,
                    nivel.dono_craque,
                    nivel.imagem
                );
            });

            $("#dia-premiacao").val(data.premiacao.semanal.dia);
            $("#hora-premiacao").val(data.premiacao.semanal.horario);
            $("#mes-ano-premiacao").val(data.premiacao.temporada.mes);
            $("#dia-ano-premiacao").val(data.premiacao.temporada.dia);
            
            updatePremiosTable();

            data.premios.forEach((premio, index) => {
                const row = $('#premios table tbody tr').eq(index);
                Object.entries(premio.valores).forEach((nivel, colIndex) => {
                    row.find('td').eq(colIndex + 2).find('input').val(nivel[1]);
                });
            });
            
            // Inicializa o drag and drop após carregar os dados
            initDragAndDrop();
        },
        error: function() {
            toastr.error('Erro ao carregar dados!');
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
        `)
        .appendTo("head");
}); 