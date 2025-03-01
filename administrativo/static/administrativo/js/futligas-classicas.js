// Configuração do CSRF Token para requisições AJAX
$.ajaxSetup({
    headers: {
        'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
    }
});

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

$(document).ready(function() {
    // Preview de imagem
    $('#image').on('change', function() {
        var file = this.files[0];
        if (file) {
            var reader = new FileReader();
            reader.onload = function(e) {
                $('#image-preview').html(`
                    <img src="${e.target.result}" style="width: 48px; height: 48px; object-fit: contain; cursor: pointer;" onclick="document.getElementById('image').click()">
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

    // Gerenciamento de prêmios
    var prizeCounter = 0;
    
    // Função para atualizar as posições
    function updatePositions() {
        $('#prizes-table tbody tr').each(function(index) {
            $(this).find('.position-input').val(index + 1);
        });
    }

    // Função para validar número inteiro positivo
    function validatePositiveInteger(value) {
        return /^\d+$/.test(value) && parseInt(value) > 0;
    }

    $('#add-prize').click(function() {
        prizeCounter++;
        var newPosition = $('#prizes-table tbody tr').length + 1;
        
        var newRow = $('<tr>').attr('id', 'prize-row-' + prizeCounter);
        
        // Coluna Posição - readonly pois o sistema já reorganiza automaticamente
        newRow.append($('<td>').append(
            $('<input>').attr({
                'type': 'number',
                'class': 'form-control position-input',
                'required': true,
                'min': '1',
                'value': newPosition,
                'readonly': true,
                'style': 'background-color: #eee'
            })
        ));
        
        // Coluna Imagem
        var imageCell = $('<td>').addClass('center-middle').append(
            $('<div>').attr('class', 'prize-image-container').append(
                $('<input>').attr({
                    'type': 'file',
                    'class': 'prize-image',
                    'accept': 'image/*',
                    'style': 'display: none;'
                }),
                $('<div>').attr('class', 'prize-image-preview').append(
                    $('<i>').attr({
                        'class': 'fa fa-file-image-o',
                        'style': 'font-size: 24px; color: #ccc; cursor: pointer;'
                    }).click(function() {
                        $(this).closest('.prize-image-container').find('.prize-image').click();
                    })
                )
            )
        );
        newRow.append(imageCell);
        
        // Coluna Prêmio
        newRow.append($('<td>').append(
            $('<input>').attr({
                'type': 'number',
                'class': 'form-control prize-input',
                'required': true,
                'min': '0'
            }).on('input', function() {
                var value = $(this).val();
                if (!validatePositiveInteger(value)) {
                    $(this).val('');
                    toastr.error('O prêmio deve ser um número inteiro positivo');
                }
            })
        ));
        
        // Coluna Ações
        newRow.append($('<td>').append(
            $('<button>').attr({
                'type': 'button',
                'class': 'btn btn-danger btn-xs remove-prize',
                'title': 'Excluir'
            }).html('<i class="fa fa-trash"></i>').click(function() {
                $(this).closest('tr').remove();
                updatePositions();
            })
        ));
        
        $('#prizes-table tbody').append(newRow);
        
        // Preview da imagem do prêmio
        newRow.find('.prize-image').change(function() {
            var file = this.files[0];
            var preview = $(this).siblings('.prize-image-preview');
            
            if (file) {
                var reader = new FileReader();
                reader.onload = function(e) {
                    preview.html(`
                        <img src="${e.target.result}" style="width: 32px; height: 32px; object-fit: contain; cursor: pointer;" onclick="$(this).closest('.prize-image-container').find('.prize-image').click()">
                        <button type="button" class="btn btn-danger btn-xs clear-prize-image" style="position: absolute; bottom: -5px; right: -5px;">
                            <i class="fa fa-trash"></i>
                        </button>
                    `);
                    
                    // Handler para limpar a imagem
                    preview.find('.clear-prize-image').on('click', function(e) {
                        e.stopPropagation();
                        var container = $(this).closest('.prize-image-container');
                        container.find('.prize-image').val('');
                        container.find('.prize-image-preview').html(`
                            <i class="fa fa-file-image-o" style="font-size: 24px; color: #ccc; cursor: pointer;"></i>
                        `);
                    });
                }
                reader.readAsDataURL(file);
            }
        });
    });

    // Frequência de premiação
    $('#frequencia').change(function() {
        var value = $(this).val();
        
        // Esconde todos os campos primeiro
        $('#campo-dia-semana').hide();
        $('#campo-dia-mes').hide();
        $('#campo-mes-ano').hide();
        $('#campo-dia-ano').hide();
        
        if (value === 'Semanal') {
            // Mostra apenas seleção do dia da semana
            $('#campo-dia-semana').show();
        } else if (value === 'Mensal') {
            // Mostra apenas seleção do dia do mês
            $('#campo-dia-mes').show();
        } else if (value === 'Anual') {
            // Mostra seleção do mês e dia do ano
            $('#campo-mes-ano').show();
            $('#campo-dia-ano').show();
        }
    });

    // Handler para o botão Salvar
    $('#btn-save').click(function(e) {
        e.preventDefault();
        
        var formData = new FormData();
        
        // Nome é obrigatório
        var nome = $('#nome').val();
        if (!nome) {
            toastr.error('O nome é obrigatório');
            return;
        }
        formData.append('name', nome);
        
        // Participantes
        var participantes = $('#participantes').val();
        if (participantes === 'Comum') {
            formData.append('players', 1);
        } else if (participantes === 'Craque') {
            formData.append('players', 2);
        } else {
            formData.append('players', 0); // Todos
        }
        
        // Converte a frequência para o formato do backend
        var frequencia = $('#frequencia').val();
        formData.append('award_frequency', frequencia);
        
        // Imagem principal
        var mainImage = $('#image')[0].files[0];
        if (mainImage) {
            formData.append('image', mainImage);
        }
        
        // Dia/horário de premiação
        if (frequencia === 'Semanal') {
            var weekday = parseInt($('#dia-premiacao').val());
            formData.append('weekday', weekday);
            formData.append('monthday', '1'); // Valor padrão para ligas semanais
        } else if (frequencia === 'Mensal' || frequencia === 'Anual') {
            var monthday = parseInt($('#mes-premiacao').val());
            if (monthday >= 1 && monthday <= 31) {
                formData.append('monthday', monthday);
                formData.append('weekday', '0'); // Valor padrão para ligas mensais/anuais
            } else {
                toastr.error('O dia do mês deve estar entre 1 e 31');
                return;
            }
        }
        
        // Horário é sempre enviado
        formData.append('award_time', $('.clockpicker input').val());
        
        // Prêmios
        $('#prizes-table tbody tr').each(function() {
            var position = $(this).find('.position-input').val();
            var prize = $(this).find('.prize-input').val();
            var prizeImage = $(this).find('.prize-image')[0].files[0];
            
            if (position && prize) {
                formData.append('prize_positions[]', position);
                formData.append('prize_descriptions[]', prize);
                if (prizeImage) {
                    formData.append('prize_images[]', prizeImage);
                }
            }
        });

        $.ajax({
            url: $('#form-futliga').data('url'),
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
            },
            success: function(response) {
                if (response.success) {
                    toastr.success('Futliga clássica criada com sucesso!');
                    window.location.href = $('#form-futliga').data('list-url');
                } else {
                    toastr.error(response.message || 'Erro ao criar futliga clássica');
                }
            },
            error: function(xhr, status, error) {
                var errorMessage = xhr.responseJSON ? xhr.responseJSON.message : 'Erro ao criar futliga clássica';
                toastr.error(errorMessage);
            }
        });
    });

    // Exclusão individual
    let futligaIdToDelete = null;

    $('.delete-btn').click(function() {
        futligaIdToDelete = $(this).data('id');
        $('#modalAlert2').modal('show');
    });

    $('#confirm-delete').click(function() {
        if (futligaIdToDelete) {
            $.ajax({
                url: `/administrativo/futliga/classica/excluir/${futligaIdToDelete}/`,
                type: 'POST',
                headers: {
                    'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
                },
                success: function(response) {
                    if (response.success) {
                        toastr.success('Futliga Clássica excluída com sucesso!');
                        setTimeout(function() {
                            window.location.href = '/administrativo/futligas/';
                        }, 1500);
                    } else {
                        toastr.error(response.message || 'Erro ao excluir Futliga Clássica');
                    }
                },
                error: function(xhr) {
                    toastr.error(xhr.responseJSON?.message || 'Erro ao excluir Futliga Clássica');
                }
            });
        }
        $('#modalAlert2').modal('hide');
    });

    // Exclusão em massa
    $('#delete-selected').click(function() {
        if ($('.check-item:checked').length > 0) {
            $('#modalAlert').modal('show');
        } else {
            toastr.warning('Selecione pelo menos uma Futliga Clássica para excluir');
        }
    });

    $('#confirm-mass-delete').click(function() {
        var selectedIds = [];
        $('.check-item:checked').each(function() {
            selectedIds.push($(this).val());
        });

        if (selectedIds.length > 0) {
            var formData = new FormData();
            selectedIds.forEach(function(id) {
                formData.append('ids[]', id);
            });

            $.ajax({
                url: '/administrativo/futliga/classica/excluir-em-massa/',
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {
                    if (response.success) {
                        toastr.success('Futligas Clássicas excluídas com sucesso!');
                        setTimeout(function() {
                            window.location.href = '/administrativo/futligas/';
                        }, 1500);
                    } else {
                        toastr.error(response.message || 'Erro ao excluir Futligas Clássicas');
                    }
                },
                error: function(xhr) {
                    toastr.error(xhr.responseJSON?.message || 'Erro ao excluir Futligas Clássicas');
                }
            });
        }
        $('#modalAlert').modal('hide');
    });

    // Checkbox "Selecionar todos"
    $('.checkAll').change(function() {
        $('.check-item').prop('checked', $(this).prop('checked'));
    });

    // Inicialização do DataTable
    $('.dataTables-futligas-padrao').DataTable({
        pageLength: 25,
        responsive: true,
        dom: '<"html5buttons"B>lTfgitp',
        buttons: [],
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
            },
            "oAria": {
                "sSortAscending": ": Ordenar colunas de forma ascendente",
                "sSortDescending": ": Ordenar colunas de forma descendente"
            }
        }
    });
}); 