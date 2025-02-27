$(document).ready(function() {
    // Referência à tabela já inicializada pelo page-level.js
    var table = $('#levels-table');

    var isEditing = false;
    var editingId = null;

    // Configuração do Sortable para permitir arrastar e soltar
    $("#levels-table tbody").sortable({
        handle: ".drag-handle",
        update: function(event, ui) {
            updateLevelsOrder();
        }
    });

    // Função para atualizar a ordem dos níveis
    function updateLevelsOrder() {
        $("#levels-table tbody tr").each(function(index) {
            $(this).attr('data-order', index + 1);
        });
    }

    // Função para validar os campos obrigatórios
    function validateFields() {
        var name = $("#nome").val();
        var players = $("#participantes").val();
        var premiumPlayers = $("#craques").val();

        if (!name || !players || !premiumPlayers) {
            toastr.error('Os campos Nome, Participantes e Craques são obrigatórios');
            return false;
        }

        // Verifica se já existe um nível com o mesmo nome
        var duplicateName = false;
        $("#levels-table tbody tr").each(function() {
            var rowName = $(this).find("td:eq(1)").text();
            var rowId = $(this).data('id');
            if (rowName === name && rowId !== editingId) {
                duplicateName = true;
                return false;
            }
        });

        if (duplicateName) {
            toastr.error('Já existe um nível com este nome');
            return false;
        }

        return true;
    }

    // Função para limpar o formulário
    function clearForm() {
        $("#nome").val('');
        $("#participantes").val('');
        $("#craques").val('');
        $("#owner_premium").prop('checked', false);
        $("#image").val('');
        $("#image-preview").html('<i class="fa fa-file-image-o" style="font-size: 48px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>');
        isEditing = false;
        editingId = null;
        $("#btnAdicionar").html('<i class="fa fa-plus mr5"></i> Adicionar');
    }

    // Preview da imagem
    $("#image").change(function() {
        var file = this.files[0];
        if (file) {
            var reader = new FileReader();
            reader.onload = function(e) {
                $("#image-preview").html(`
                    <img src="${e.target.result}" style="max-width: 50px; max-height: 50px; object-fit: contain; cursor: pointer;" onclick="document.getElementById('image').click()">
                    <button type="button" class="btn btn-danger btn-xs" id="remove_image_btn" style="position: absolute; bottom: -7px; right: -30px;">
                        <i class="fa fa-trash"></i>
                    </button>
                `);
                
                // Adiciona handler para o botão de remover
                $('#remove_image_btn').on('click', function() {
                    $('#image').val('');
                    $('#image-preview').html('<i class="fa fa-file-image-o" style="font-size: 48px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>');
                });
            }
            reader.readAsDataURL(file);
        }
    });

    // Adicionar/Editar nível - modificando para escutar o envio do formulário
    $("#nivelForm").on('submit', function(e) {
        e.preventDefault();
        
        if (!validateFields()) return;

        var formData = new FormData(this);
        
        var url = isEditing ? 
            '/administrativo/futligas/niveis/editar/' + editingId + '/' :
            '/administrativo/futligas/niveis/novo/';

        $.ajax({
            url: url,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.success) {
                    toastr.success(isEditing ? 'Nível atualizado com sucesso!' : 'Nível adicionado com sucesso!');
                    // Atualiza a tabela
                    if (isEditing) {
                        var row = $("#levels-table tbody tr[data-id='" + editingId + "']");
                        updateRow(row, response.level);
                    } else {
                        addRow(response.level);
                    }
                    clearForm();
                } else {
                    toastr.error(response.message);
                }
            },
            error: function() {
                toastr.error('Erro ao processar a requisição');
            }
        });
    });

    // Função para adicionar uma nova linha na tabela
    function addRow(level) {
        var row = `
            <tr data-id="${level.id}" data-order="${level.order}">
                <td><i class="fa fa-bars drag-handle"></i></td>
                <td>${level.name}</td>
                <td>${level.players}</td>
                <td>${level.premium_players}</td>
                <td>${level.owner_premium ? 'Sim' : 'Não'}</td>
                <td class="center-middle">
                    ${level.image ? `<img src="${level.image}" style="width: 48px; height: 48px; object-fit: contain;">` : '<i class="fa fa-image"></i>'}
                </td>
                <td>
                    <button type="button" class="btn btn-info btn-xs edit-level" title="Editar">
                        <i class="fa fa-pencil"></i>
                    </button>
                    <button type="button" class="btn btn-danger btn-xs delete-level" title="Excluir">
                        <i class="fa fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
        $("#levels-table tbody").append(row);
    }

    // Função para atualizar uma linha existente
    function updateRow(row, level) {
        row.find("td:eq(1)").text(level.name);
        row.find("td:eq(2)").text(level.players);
        row.find("td:eq(3)").text(level.premium_players);
        row.find("td:eq(4)").text(level.owner_premium ? 'Sim' : 'Não');
        if (level.image) {
            row.find("td:eq(5)").html(`<img src="${level.image}" style="width: 48px; height: 48px; object-fit: contain;">`);
        }
    }

    // Editar nível
    $(document).on('click', '.edit-level', function() {
        var row = $(this).closest('tr');
        editingId = row.data('id');
        isEditing = true;

        $("#nome").val(row.find("td:eq(1)").text());
        $("#participantes").val(row.find("td:eq(2)").text());
        $("#craques").val(row.find("td:eq(3)").text());
        $("#owner_premium").prop('checked', row.find("td:eq(4)").text() === 'Sim');
        
        var imgElement = row.find("td:eq(5) img");
        if (imgElement.length) {
            $("#image-preview").html(`<img src="${imgElement.attr('src')}" style="max-width: 50px; max-height: 50px; object-fit: contain; cursor: pointer;" onclick="document.getElementById('image').click()">
                <button type="button" class="btn btn-danger btn-xs" id="remove_image_btn" style="position: absolute; bottom: -7px; right: -30px;">
                    <i class="fa fa-trash"></i>
                </button>`);
            
            // Adiciona handler para o botão de remover
            $('#remove_image_btn').on('click', function() {
                $('#image').val('');
                $('#image-preview').html('<i class="fa fa-file-image-o" style="font-size: 48px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>');
            });
        }

        $("#btnAdicionar").html('<i class="fa fa-save mr5"></i> Salvar Alterações');
    });

    // Excluir nível
    $(document).on('click', '.delete-level', function() {
        if (!confirm('Tem certeza que deseja excluir este nível?')) return;

        var row = $(this).closest('tr');
        var id = row.data('id');

        $.ajax({
            url: '/administrativo/futligas/niveis/excluir/' + id + '/',
            type: 'POST',
            success: function(response) {
                if (response.success) {
                    toastr.success('Nível excluído com sucesso!');
                    row.remove();
                    updateLevelsOrder();
                } else {
                    toastr.error(response.message);
                }
            },
            error: function() {
                toastr.error('Erro ao excluir nível');
            }
        });
    });

    // Importar níveis
    $("#import-levels").click(function() {
        var input = $('<input type="file" accept=".xls,.xlsx">');
        input.click();

        input.change(function() {
            var file = this.files[0];
            var formData = new FormData();
            formData.append('file', file);

            $.ajax({
                url: '/administrativo/futligas/niveis/importar/',
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {
                    if (response.success) {
                        toastr.success('Níveis importados com sucesso!');
                        // Atualiza a tabela com os novos níveis
                        $("#levels-table tbody").empty();
                        response.levels.forEach(function(level) {
                            addRow(level);
                        });
                    } else {
                        toastr.error(response.message);
                    }
                },
                error: function() {
                    toastr.error('Erro ao importar níveis');
                }
            });
        });
    });

    // Exportar níveis
    $("#export-levels").click(function() {
        window.location.href = '/administrativo/futligas/niveis/exportar/';
    });

    // Salvar todas as alterações
    $("#save-all").click(function() {
        var levels = [];
        $("#levels-table tbody tr").each(function() {
            levels.push({
                id: $(this).data('id'),
                order: $(this).data('order')
            });
        });

        $.ajax({
            url: '/administrativo/futligas/niveis/salvar/',
            type: 'POST',
            data: JSON.stringify({ levels: levels }),
            contentType: 'application/json',
            success: function(response) {
                if (response.success) {
                    toastr.success('Alterações salvas com sucesso!');
                } else {
                    toastr.error(response.message);
                }
            },
            error: function() {
                toastr.error('Erro ao salvar alterações');
            }
        });
    });
}); 