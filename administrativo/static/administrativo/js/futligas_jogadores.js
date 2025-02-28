$(document).ready(function() {
    // Configuração do Toastr
    toastr.options = {
        "closeButton": true,
        "debug": false,
        "newestOnTop": false,
        "progressBar": true,
        "positionClass": "toast-top-right",
        "preventDuplicates": false,
        "onclick": null,
        "showDuration": "300",
        "hideDuration": "500",
        "timeOut": "1500",
        "extendedTimeOut": "500",
        "showEasing": "swing",
        "hideEasing": "linear",
        "showMethod": "fadeIn",
        "hideMethod": "fadeOut"
    };

    // Configuração do CSRF token
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    $.ajaxSetup({
        beforeSend: function(xhr) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    });

    // Inicialização do DataTable
    const table = $('#table-futligas').DataTable({
        pageLength: 25,
        responsive: true,
        dom: '<"html5buttons"B>lTfgitp',
        buttons: [
            { extend: 'copy', text: 'Copiar' },
            { extend: 'csv' },
            { extend: 'excel', title: 'Futligas' },
            { extend: 'pdf', title: 'Futligas' },
            { 
                extend: 'print',
                text: 'Imprimir',
                customize: function (win) {
                    $(win.document.body).addClass('white-bg');
                    $(win.document.body).css('font-size', '10px');
                }
            }
        ],
        language: {
            "sEmptyTable": "Nenhum registro encontrado",
            "sInfo": "Mostrando de _START_ até _END_ de _TOTAL_ registros",
            "sInfoEmpty": "Mostrando 0 até 0 de 0 registros",
            "sInfoFiltered": "(Filtrados de _MAX_ registros)",
            "sInfoPostFix": "",
            "sInfoThousands": ".",
            "sLengthMenu": "_MENU_ resultados por página",
            "sLoadingRecords": "Carregando...",
            "sProcessing": "Processando...",
            "sZeroRecords": "Nenhum registro encontrado",
            "sSearch": "Pesquisar",
            "oPaginate": {
                "sNext": "Próximo",
                "sPrevious": "Anterior",
                "sFirst": "Primeiro",
                "sLast": "Último"
            }
        }
    });

    // Handler para preview de imagem
    function handleImagePreview(input) {
        if (input.files && input.files[0]) {
            const file = input.files[0];
            
            // Validações
            if (!file.type.match('image.*')) {
                toastr.error('Por favor, selecione uma imagem válida');
                input.value = '';
                return;
            }

            if (file.size > 2 * 1024 * 1024) {
                toastr.error('A imagem não pode ter mais que 2MB');
                input.value = '';
                return;
            }

            const reader = new FileReader();
            reader.onload = function(e) {
                $("#image-preview").html(`
                    <div class="position-relative">
                        <img src="${e.target.result}" class="img-preview" style="width: 100px; height: 100px; object-fit: contain;">
                        <button type="button" class="btn btn-danger btn-xs remove-image">
                            <i class="fa fa-trash"></i>
                        </button>
                    </div>
                `);
            };
            reader.readAsDataURL(file);
        }
    }

    // Event listeners para imagem
    $(document).on('change', '#image', function() {
        handleImagePreview(this);
    });

    $(document).on('click', '.remove-image', function(e) {
        e.preventDefault();
        $("#image").val('');
        $("#image-preview").html(`
            <label class="label-card label-card-small">
                <i class="fa fa-file-image-o label-content" style="cursor:pointer;"></i>
                <input accept="image/*" type="file" name="image" id="image" class="input-image">
            </label>
        `);
    });

    // Função para validar formulário
    function validateForm(formData) {
        const name = formData.get('name');
        const players = formData.get('players');
        const premium_players = formData.get('premium_players');

        if (!name || name.trim() === '') {
            toastr.error('O nome é obrigatório');
            return false;
        }

        if (!players || isNaN(players) || players < 0) {
            toastr.error('Número de participantes inválido');
            return false;
        }

        if (!premium_players || isNaN(premium_players) || premium_players < 0) {
            toastr.error('Número de craques inválido');
            return false;
        }

        return true;
    }

    // Handler para submissão do formulário
    $("#form-futliga").on('submit', function(e) {
        e.preventDefault();
        
        const form = $(this);
        const formData = new FormData(this);
        
        $.ajax({
            url: form.data('create-url'),
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.success) {
                    toastr.success('Futliga adicionada com sucesso!');
                    
                    // Adiciona a nova linha na tabela
                    const imageHtml = response.image_url ? 
                        `<img src="${response.image_url}" class="img-sm" alt="Imagem">` : 
                        '';

                    const newRow = `
                        <tr>
                            <td>${formData.get('name')}</td>
                            <td class="center-middle">${imageHtml}</td>
                            <td>${formData.get('players')}</td>
                            <td>${formData.get('premium_players')}</td>
                            <td>${formData.get('owner_premium') ? 'Sim' : 'Não'}</td>
                            <td>
                                <div>
                                    <button type="button" class="btn btn-info btn-xs mr5" title="Editar">
                                        <i class="glyphicon glyphicon-pencil"></i>
                                    </button>
                                    <button type="button" class="btn btn-danger btn-xs mr5" title="Excluir">
                                        <i class="glyphicon glyphicon-trash"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `;
                    
                    $("table tbody").prepend(newRow);
                    
                    // Limpa o formulário
                    form[0].reset();
                    $("#image-preview").html(`
                        <label class="label-card label-card-small">
                            <i class="fa fa-file-image-o label-content" style="cursor:pointer;"></i>
                            <input accept="image/*" type="file" name="image" id="image" class="input-image">
                        </label>
                    `);
                } else {
                    toastr.error(response.message || 'Erro ao adicionar Futliga');
                }
            },
            error: function(xhr) {
                toastr.error(xhr.responseJSON?.message || 'Erro ao adicionar Futliga');
            }
        });
    });

    // Handler para exclusão
    $(document).on('click', '.btn-delete', function(e) {
        e.preventDefault();
        const id = $(this).data('id');
        const row = $(this).closest('tr');
        const url = $(this).data('delete-url');

        if (confirm('Tem certeza que deseja excluir esta Futliga?')) {
            $.ajax({
                url: url,
                type: 'POST',
                beforeSend: function() {
                    row.addClass('processing');
                },
                success: function(response) {
                    if (response.success) {
                        toastr.success('Futliga excluída com sucesso!');
                        row.fadeOut(400, function() {
                            $(this).remove();
                        });
                    } else {
                        toastr.error(response.message || 'Erro ao excluir Futliga');
                    }
                },
                error: function(xhr) {
                    toastr.error(xhr.responseJSON?.message || 'Erro ao excluir Futliga');
                },
                complete: function() {
                    row.removeClass('processing');
                }
            });
        }
    });

    // Handler para importação
    $("#import-form").on('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const file = $('#import-file')[0].files[0];

        if (!file) {
            toastr.error('Selecione um arquivo para importar');
            return;
        }

        if (!file.name.match(/\.(xls|xlsx)$/i)) {
            toastr.error('O arquivo deve ser do tipo Excel (.xls ou .xlsx)');
            return;
        }

        $.ajax({
            url: $(this).data('import-url'),
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            beforeSend: function() {
                $('#import-btn').prop('disabled', true);
                $('#import-spinner').show();
            },
            success: function(response) {
                if (response.success) {
                    toastr.success('Importação realizada com sucesso!');
                    window.location.reload();
                } else {
                    toastr.error(response.message || 'Erro na importação');
                }
            },
            error: function(xhr) {
                toastr.error(xhr.responseJSON?.message || 'Erro na importação');
            },
            complete: function() {
                $('#import-btn').prop('disabled', false);
                $('#import-spinner').hide();
                $('#modalImportar').modal('hide');
            }
        });
    });

    // Reset do formulário de importação quando o modal for fechado
    $('#modalImportar').on('hidden.bs.modal', function() {
        $('#import-form')[0].reset();
        $('#import-spinner').hide();
    });

    // Handler para edição
    $(document).on('click', '.btn-edit', function(e) {
        e.preventDefault();
        const id = $(this).data('id');
        const row = $(this).closest('tr');
        
        // Preenche o formulário com os dados da linha
        const form = $('#form-futliga');
        form.data('editing-id', id);
        form.find('input[name="name"]').val(row.find('td:eq(0)').text());
        form.find('input[name="players"]').val(row.find('td:eq(2)').text());
        form.find('input[name="premium_players"]').val(row.find('td:eq(3)').text());
        form.find('#owner_premium').prop('checked', row.find('td:eq(4)').text().trim() === 'Sim');

        // Se houver imagem, mostra no preview
        const imgElement = row.find('td:eq(1) img');
        if (imgElement.length) {
            $("#image-preview").html(`
                <div class="position-relative">
                    <img src="${imgElement.attr('src')}" class="img-preview" style="width: 100px; height: 100px; object-fit: contain;">
                    <button type="button" class="btn btn-danger btn-xs remove-image">
                        <i class="fa fa-trash"></i>
                    </button>
                </div>
            `);
        }

        // Atualiza o botão de submit
        $('#submit-btn').html('<i class="fa fa-save mr5"></i> Salvar');
    });

    // Reset do formulário
    function resetForm() {
        const form = $('#form-futliga');
        form[0].reset();
        form.removeData('editing-id');
        $('#image-preview').html(`
            <label class="label-card label-card-small">
                <i class="fa fa-file-image-o label-content" style="cursor:pointer;"></i>
                <input accept="image/*" type="file" name="image" id="image" class="input-image">
            </label>
        `);
        $('#submit-btn').html('<i class="fa fa-plus mr5"></i> Adicionar');
    }
}); 