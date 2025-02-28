$(document).ready(function() {
    // Referência à tabela
    var table = $('#table');

    var isEditing = false;
    var editingId = null;

    // Configuração do Sortable para permitir arrastar e soltar
    $("#table tbody").sortable({
        handle: ".drag-handle",
        update: function(event, ui) {
            updateLevelsOrder();
        }
    });

    // Função para atualizar a ordem dos níveis
    function updateLevelsOrder() {
        $("#table tbody tr").each(function(index) {
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
        $("#table tbody tr").each(function() {
            var rowName = $(this).find("td:eq(0)").text();
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

    // Adicionar/Editar nível
    $("#nivelForm").on('submit', function(e) {
        e.preventDefault();
        
        if (!validateFields()) return;

        var formData = new FormData(this);
        formData.set('owner_premium', $('#owner_premium').prop('checked'));
        
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
                    window.location.reload(); // Recarrega a página para mostrar as alterações
                } else {
                    toastr.error(response.message || 'Erro ao processar requisição');
                }
            },
            error: function(xhr) {
                toastr.error(xhr.responseJSON?.message || 'Erro ao processar a requisição');
            }
        });
    });

    // Editar nível
    $(document).on('click', '.btnEditar', function() {
        var row = $(this).closest('tr');
        editingId = $(this).data('id');
        isEditing = true;

        $("#nome").val(row.find("td:eq(0)").text());
        $("#participantes").val(row.find("td:eq(2)").text());
        $("#craques").val(row.find("td:eq(3)").text());
        $("#owner_premium").prop('checked', row.find("td:eq(4)").text() === 'Sim');
        
        var imgElement = row.find("td:eq(1) img");
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
    $(document).on('click', '.btnExcluir', function() {
        if (!confirm('Tem certeza que deseja excluir este nível?')) return;

        var id = $(this).data('id');

        $.ajax({
            url: '/administrativo/futligas/niveis/excluir/' + id + '/',
            type: 'POST',
            data: {
                csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                if (response.success) {
                    toastr.success('Nível excluído com sucesso!');
                    window.location.reload(); // Recarrega a página para mostrar as alterações
                } else {
                    toastr.error(response.message || 'Erro ao excluir nível');
                }
            },
            error: function(xhr) {
                toastr.error(xhr.responseJSON?.message || 'Erro ao excluir nível');
            }
        });
    });

    // Importar níveis
    $("#importFile").change(function() {
        var formData = new FormData($('#importForm')[0]);
        
        $.ajax({
            url: '/administrativo/futligas/niveis/importar/',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.success) {
                    toastr.success('Níveis importados com sucesso!');
                    window.location.reload(); // Recarrega a página para mostrar as alterações
                } else {
                    toastr.error(response.message || 'Erro ao importar níveis');
                }
            },
            error: function(xhr) {
                toastr.error(xhr.responseJSON?.message || 'Erro ao importar níveis');
            }
        });
    });

    // Exportar níveis
    $("#export-levels").click(function() {
        window.location.href = '/administrativo/futligas/niveis/exportar/';
    });

    // Salvar todas as alterações
    $("#save-all").click(function() {
        var levels = [];
        $("#table tbody tr").each(function() {
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
                    toastr.error(response.message || 'Erro ao salvar alterações');
                }
            },
            error: function(xhr) {
                toastr.error(xhr.responseJSON?.message || 'Erro ao salvar alterações');
            }
        });
    });
}); 