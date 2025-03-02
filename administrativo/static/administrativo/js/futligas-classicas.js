// Configuração do CSRF Token para requisições AJAX
$.ajaxSetup({
    headers: {
        'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
    }
});

// Configuração do Toastr - agora garantindo que seja aplicada antes de qualquer uso
$(document).ready(function() {
    toastr.options = {
        "closeButton": true,
        "debug": false,
        "newestOnTop": true,
        "progressBar": true,
        "positionClass": "toast-top-right",
        "preventDuplicates": false,
        "onclick": null,
        "showDuration": "300",
        "hideDuration": "1000",
        "timeOut": "5000",
        "extendedTimeOut": "1000",
        "showEasing": "swing",
        "hideEasing": "linear",
        "showMethod": "fadeIn",
        "hideMethod": "fadeOut"
    };

    // Detecta o prefixo da URL dinamicamente
    const ADMIN_URL_PREFIX = (function() {
        const metaElement = document.querySelector('meta[name="url-prefix"]');
        if (metaElement && metaElement.getAttribute('content')) {
            return metaElement.getAttribute('content');
        }
        return '/administrativo'; // Valor padrão caso não encontre a meta tag
    })();

    // Preview de imagem
    $('#image').on('change', function() {
        var file = this.files[0];
        if (file) {
            var reader = new FileReader();
            reader.onload = function(e) {
                $('#image-preview').html(
                    '<img src="' + e.target.result + '" style="width: 48px; height: 48px; object-fit: contain; cursor: pointer;" onclick="document.getElementById(\'image\').click()">' +
                    '<button type="button" class="btn btn-danger btn-xs" id="remove_image_btn" style="position: absolute; bottom: -7px; right: -30px;">' +
                    '<i class="fa fa-trash"></i>' +
                    '</button>'
                );
                
                // Adiciona handler para o botão de remover
                $('#remove_image_btn').on('click', function() {
                    $('#image').val('');
                    $('#image-preview').html('<i class="fa fa-file-image-o" style="font-size: 48px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>');
                    if (!$('#remove_image').length) {
                        $('form').append('<input type="hidden" id="remove_image" name="remove_image" value="1">');
                    } else {
                        $('#remove_image').val('1');
                    }
                });
            };
            reader.readAsDataURL(file);
        }
    });

    // Remove imagem (delegate event para funcionar com elementos criados dinamicamente)
    $(document).on('click', '.remove-image, .image-remove-btn, #remove_image_btn', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $("#image").val('');
        $("#image-preview").html('<i class="fa fa-file-image-o" style="font-size: 48px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>');
        return false;
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
        
        // Coluna Posição
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
        
        // Preview de imagem quando altera
        imageCell.find('.prize-image').change(function() {
            var file = this.files[0];
            var preview = $(this).siblings('.prize-image-preview');
            
            if (file) {
                var reader = new FileReader();
                reader.onload = function(e) {
                    preview.html(
                        '<div class="image-container" style="position: relative; width: 32px; height: 32px; display: inline-block;">' +
                        '<img src="' + e.target.result + '" height="32" width="32" alt="Imagem" style="object-fit: contain; cursor: pointer;" onclick="$(this).closest(\'.prize-image-container\').find(\'.prize-image\').click()">' +
                        '<div class="image-remove-btn" style="position: absolute; bottom: 0; right: 0; background-color: #f8f8f8; border-radius: 50%; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 1px 3px rgba(0,0,0,0.2);">' +
                        '<i class="fa fa-trash" style="font-size: 10px; color: #FF5252;"></i>' +
                        '</div>' +
                        '</div>'
                    );
                    
                    // Handler para limpar a imagem
                    preview.find('.image-remove-btn').on('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        var container = $(this).closest('.prize-image-container');
                        container.find('.prize-image').val('');
                        container.find('.prize-image-preview').html(
                            '<i class="fa fa-file-image-o" style="font-size: 24px; color: #ccc; cursor: pointer;" onclick="$(this).closest(\'.prize-image-container\').find(\'.prize-image\').click()"></i>'
                        );
                    });
                };
                reader.readAsDataURL(file);
            }
        });
        
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
    });

    // Configurar handler para todos os elementos image-remove-btn que possam ser adicionados dinamicamente
    $(document).on('click', '.image-remove-btn', function(e) {
        e.preventDefault();
        e.stopPropagation();
        var container = $(this).closest('.prize-image-container');
        container.find('.prize-image').val('');
        container.find('.prize-image-preview').html(
            '<i class="fa fa-file-image-o" style="font-size: 24px; color: #ccc; cursor: pointer;" onclick="$(this).closest(\'.prize-image-container\').find(\'.prize-image\').click()"></i>'
        );
        
        // Se estiver na página de edição, adicione o campo hidden para remoção
        var tr = $(this).closest('tr');
        if (tr.length) {
            var rowIndex = tr.index();
            if (window.location.href.indexOf('editar') > -1) {
                if (!$('#remove_prize_image_' + rowIndex).length) {
                    $('form').append('<input type="hidden" id="remove_prize_image_' + rowIndex + '" name="remove_prize_image[]" value="' + rowIndex + '">');
                }
            }
        }
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
            toastr.remove(); // Limpa mensagens anteriores
            toastr.error('O nome é obrigatório');
            return;
        }
        formData.append('name', nome);
        
        // Participantes
        var participantes = $('#participantes').val();
        if (participantes === 'Comum') {
            formData.append('players', 'Comum');
        } else if (participantes === 'Craque') {
            formData.append('players', 'Craque');
        } else {
            formData.append('players', 'Todos'); // Todos
        }
        
        // Converte a frequência para o formato do backend
        var frequencia = $('#frequencia').val();
        
        // Mapeia os valores de frequência para o formato do backend
        var frequencyMap = {
            'Semanal': 'weekly',
            'Mensal': 'monthly',
            'Anual': 'annual'
        };
        
        formData.append('award_frequency', frequencyMap[frequencia]);
        
        // Imagem principal
        var mainImage = $('#image')[0].files[0];
        if (mainImage) {
            formData.append('image', mainImage);
        }
        
        // Dia/horário de premiação
        if (frequencia === 'Semanal') {
            var weekday = parseInt($('#dia-premiacao').val());
            formData.append('weekday', weekday);
        } else if (frequencia === 'Mensal') {
            var monthday = parseInt($('#mes-premiacao').val());
            if (monthday >= 1 && monthday <= 31) {
                formData.append('monthday', monthday);
            } else {
                toastr.error('O dia do mês deve estar entre 1 e 31');
                return;
            }
        } else if (frequencia === 'Anual') {
            var monthYearValue = parseInt($('#mes-ano-premiacao').val());
            var dayYearValue = parseInt($('#dia-ano-premiacao').val());
            
            if (dayYearValue >= 1 && dayYearValue <= 31) {
                formData.append('monthday', dayYearValue);
            } else {
                toastr.error('O dia do ano deve estar entre 1 e 31');
                return;
            }
            // Também enviamos o mês do ano (não usado no modelo atual, mas pode ser útil)
            formData.append('month_value', monthYearValue);
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
                    toastr.remove();
                    toastr.success('Futliga clássica criada com sucesso!');
                    setTimeout(function() {
                        window.location.href = $('#form-futliga').data('list-url');
                    }, 2000);
                } else {
                    toastr.remove();
                    toastr.error(response.message || 'Erro ao criar futliga clássica');
                }
            },
            error: function(xhr, status, error) {
                toastr.remove();
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
                url: `${ADMIN_URL_PREFIX}/futliga/classica/excluir/${futligaIdToDelete}/`,
                type: 'POST',
                headers: {
                    'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
                },
                success: function(response) {
                    $('#modalAlert2').modal('hide');
                    if (response.success) {
                        toastr.remove();
                        toastr.success('Futliga Clássica excluída com sucesso!');
                        setTimeout(function() {
                            window.location.reload();
                        }, 2000);
                    } else {
                        toastr.remove();
                        toastr.error(response.message || 'Erro ao excluir Futliga Clássica');
                    }
                },
                error: function(xhr) {
                    $('#modalAlert2').modal('hide');
                    toastr.remove();
                    toastr.error(xhr.responseJSON?.message || 'Erro ao excluir Futliga Clássica');
                }
            });
        }
    });

    // Exclusão em massa
    $('#delete-selected').click(function() {
        if ($('.check-item:checked').length > 0) {
            $('#modalAlert').modal('show');
        } else {
            toastr.remove();
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
                url: `${ADMIN_URL_PREFIX}/futliga/classica/excluir-em-massa/`,
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {
                    $('#modalAlert').modal('hide');
                    if (response.success) {
                        toastr.remove();
                        toastr.success('Futligas Clássicas excluídas com sucesso!');
                        setTimeout(function() {
                            window.location.reload();
                        }, 2000);
                    } else {
                        toastr.remove();
                        toastr.error(response.message || 'Erro ao excluir Futligas Clássicas');
                    }
                },
                error: function(xhr) {
                    $('#modalAlert').modal('hide');
                    toastr.remove();
                    toastr.error(xhr.responseJSON?.message || 'Erro ao excluir Futligas Clássicas');
                }
            });
        }
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