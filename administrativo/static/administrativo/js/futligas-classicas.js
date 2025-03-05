// Configuração do CSRF Token para requisições AJAX
const csrfToken = $('meta[name="csrf-token"]').attr('content');
console.log('CSRF Token:', csrfToken);

$.ajaxSetup({
    headers: {
        'X-CSRFToken': csrfToken
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

    // Inicialização da DataTable para a tabela de futligas clássicas
    $('.dataTables-futligas-padrao').DataTable({
        pageLength: 10,
        responsive: true,
        dom: 'lfrtip',
        language: {
            search: "Buscar:",
            lengthMenu: "_MENU_ resultados por página",
            info: "Mostrando _START_ a _END_ de _TOTAL_ resultados",
            infoEmpty: "Mostrando 0 a 0 de 0 resultados",
            infoFiltered: "(filtrado de _MAX_ resultados no total)",
            zeroRecords: "Nenhum resultado correspondente encontrado",
            paginate: {
                first: "Primeiro",
                last: "Último",
                next: "Próximo",
                previous: "Anterior"
            }
        }
    });

    // Detecta o prefixo da URL dinamicamente
    const ADMIN_URL_PREFIX = '/administrativo';

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
                    
                    // Remove o campo hidden de remoção se existir
                    var tr = preview.closest('tr');
                    if (tr.length) {
                        var rowIndex = tr.index();
                        $('#remove_prize_image_' + rowIndex).remove();
                        tr.find('.prize-image-container').removeClass('image-removed');
                    }
                    
                    // Handler para limpar a imagem
                    preview.find('.image-remove-btn').on('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        var container = $(this).closest('.prize-image-container');
                        container.find('.prize-image').val('');
                        container.find('.prize-image-preview').html(
                            '<i class="fa fa-file-image-o" style="font-size: 24px; color: #ccc; cursor: pointer;" onclick="$(this).closest(\'.prize-image-container\').find(\'.prize-image\').click()"></i>'
                        );
                        
                        // Adiciona o campo hidden para remoção
                        var tr = container.closest('tr');
                        if (tr.length) {
                            var rowIndex = tr.index();
                            if (!$('#remove_prize_image_' + rowIndex).length) {
                                $('form').append('<input type="hidden" id="remove_prize_image_' + rowIndex + '" name="remove_prize_image[]" value="' + rowIndex + '">');
                            }
                            container.addClass('image-removed');
                        }
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

    // Função para restaurar o estado das imagens removidas após recarregar a página
    function restoreRemovedImagesState() {
        try {
            var removedImages = JSON.parse(localStorage.getItem('removedPrizeImages') || '{}');
            Object.keys(removedImages).forEach(function(index) {
                if (removedImages[index]) {
                    var tr = $('#prizes-table tbody tr').eq(index);
                    if (tr.length) {
                        var container = tr.find('.prize-image-container');
                        container.addClass('image-removed');
                        if (!$('#remove_prize_image_' + index).length) {
                            $('form').append('<input type="hidden" id="remove_prize_image_' + index + '" name="remove_prize_image[]" value="' + index + '">');
                        }
                    }
                }
            });
        } catch (e) {
            console.error('Erro ao restaurar estado de remoção de imagens:', e);
        }
    }

    // Função para limpar o estado de remoção quando uma nova imagem é adicionada
    function clearRemovedImageState(index) {
        try {
            var removedImages = JSON.parse(localStorage.getItem('removedPrizeImages') || '{}');
            delete removedImages[index];
            localStorage.setItem('removedPrizeImages', JSON.stringify(removedImages));
        } catch (e) {
            console.error('Erro ao limpar estado de remoção:', e);
        }
    }

    // Inicializa o estado das imagens removidas
    restoreRemovedImagesState();

    // Handler para remoção de imagens
    $(document).on('click', '.image-remove-btn', function(e) {
        e.preventDefault();
        e.stopPropagation();
        var container = $(this).closest('.prize-image-container');
        container.find('.prize-image').val('');
        container.find('.prize-image-preview').html(
            '<i class="fa fa-file-image-o" style="font-size: 24px; color: #ccc; cursor: pointer;" onclick="$(this).closest(\'.prize-image-container\').find(\'.prize-image\').click()"></i>'
        );
        
        var tr = $(this).closest('tr');
        if (tr.length) {
            var rowIndex = tr.index();
            // Adiciona ou atualiza o campo hidden para remoção
            var hiddenInput = $('#remove_prize_image_' + rowIndex);
            if (hiddenInput.length === 0) {
                $('form').append('<input type="hidden" id="remove_prize_image_' + rowIndex + '" name="remove_prize_image[]" value="' + rowIndex + '">');
            } else {
                hiddenInput.val(rowIndex);
            }
            
            // Adiciona uma classe para indicar que a imagem foi removida
            container.addClass('image-removed');
            
            // Salva o estado da remoção no localStorage
            try {
                var removedImages = JSON.parse(localStorage.getItem('removedPrizeImages') || '{}');
                removedImages[rowIndex] = true;
                localStorage.setItem('removedPrizeImages', JSON.stringify(removedImages));
            } catch (e) {
                console.error('Erro ao salvar estado de remoção no localStorage:', e);
            }
        }
    });

    // Handler para mudança de imagem
    $(document).on('change', '.prize-image', function() {
        var tr = $(this).closest('tr');
        if (tr.length) {
            var index = tr.index();
            clearRemovedImageState(index);
            
            // Remove a classe de remoção e o campo hidden
            tr.find('.prize-image-container').removeClass('image-removed');
            $('#remove_prize_image_' + index).remove();
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
        
        // Antes de enviar, verifica se há imagens que devem ser preservadas
        $('#prizes-table tbody tr').each(function(index) {
            var container = $(this).find('.prize-image-container');
            var preview = container.find('.prize-image-preview');
            var img = preview.find('img');
            
            // Se tem imagem e não está marcada para remoção
            if (img.length && !container.hasClass('image-removed')) {
                var imgSrc = img.attr('src');
                // Adiciona um campo hidden para preservar a imagem
                if (!$('#preserve_prize_image_' + index).length) {
                    $('form').append('<input type="hidden" id="preserve_prize_image_' + index + '" name="preserve_prize_image[]" value="' + imgSrc + '">');
                }
            }
        });
        
        var formData = new FormData();
        
        // Nome é obrigatório
        var nome = $('#nome').val();
        if (!nome) {
            toastr.remove();
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
        
        // Verifica se a imagem principal foi removida
        if ($('#remove_image').length && $('#remove_image').val() === '1') {
            formData.append('remove_image', '1');
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
        $('#prizes-table tbody tr').each(function(index) {
            var position = $(this).find('.position-input').val();
            var prize = $(this).find('.prize-input').val();
            var prizeImage = $(this).find('.prize-image')[0].files[0];
            var existingImage = $(this).find('.prize-image-preview img').attr('src');
            var preserveImage = $('#preserve_prize_image_' + index).val();
            
            if (position && prize) {
                formData.append('prize_positions[]', position);
                formData.append('prize_descriptions[]', prize);
                
                // Verifica se há uma imagem nova para enviar
                if (prizeImage) {
                    formData.append('prize_images[]', prizeImage);
                    formData.append('prize_image_positions[]', index);
                }
                // Se não há nova imagem mas existe uma imagem atual e não foi marcada para remoção
                else if ((existingImage || preserveImage) && !$('#remove_prize_image_' + index).length) {
                    formData.append('prize_existing_images[]', existingImage || preserveImage);
                    formData.append('prize_existing_image_positions[]', index);
                }
                // Se a imagem foi marcada para remoção
                else if ($('#remove_prize_image_' + index).length) {
                    formData.append('remove_prize_images[]', index);
                }
            }
        });
        
        // Limpa o localStorage após enviar o formulário
        localStorage.removeItem('removedPrizeImages');
        
        // Envia os dados para o servidor
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
                    toastr.success('Futliga clássica salva com sucesso!');
                    setTimeout(function() {
                        window.location.href = $('#form-futliga').data('list-url');
                    }, 2000);
                } else {
                    toastr.remove();
                    toastr.error(response.message || 'Erro ao salvar futliga clássica');
                }
            },
            error: function(xhr, status, error) {
                toastr.remove();
                var errorMessage = xhr.responseJSON ? xhr.responseJSON.message : 'Erro ao salvar futliga clássica';
                toastr.error(errorMessage);
            }
        });
    });

    // Exclusão individual
    let futligaIdToDelete = null;

    // Usando delegação de eventos para garantir que funcione mesmo com elementos dinâmicos
    $(document).on('click', '.delete-btn', function(e) {
        e.preventDefault();
        futligaIdToDelete = $(this).data('id');
        console.log('ID da Futliga para excluir:', futligaIdToDelete);
        
        if (!futligaIdToDelete) {
            console.error('ID da Futliga não encontrado no botão');
            toastr.error('Erro ao identificar a Futliga para exclusão');
            return;
        }
        
        $('#modalAlert2').modal('show');
    });

    $(document).on('click', '#confirm-delete', function() {
        if (!futligaIdToDelete) {
            console.error('ID da Futliga não definido');
            toastr.error('Erro ao identificar a Futliga para exclusão');
            return;
        }

        // Adiciona indicador visual de que a exclusão está em andamento
        $(this).html('<i class="fa fa-spinner fa-spin"></i> Excluindo...');
        $(this).prop('disabled', true);
        
        console.log(`Iniciando exclusão da futliga ID: ${futligaIdToDelete}`);
        
        // Obtém a URL do botão que iniciou a exclusão
        const url = $(`.delete-btn[data-id="${futligaIdToDelete}"]`).data('url');
        console.log('URL da requisição:', url);
        
        $.ajax({
            url: url,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ id: futligaIdToDelete }),
            headers: {
                'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
            },
            success: function(response) {
                $('#modalAlert2').modal('hide');
                
                console.log('Resposta do servidor:', response);
                
                if (response.success) {
                    toastr.success('Futliga Clássica excluída com sucesso!');
                    setTimeout(function() {
                        window.location.reload();
                    }, 2000);
                } else {
                    // Restaura o botão
                    $('#confirm-delete').html('Excluir');
                    $('#confirm-delete').prop('disabled', false);
                    
                    const errorMsg = response.message || 'Erro ao excluir Futliga Clássica';
                    console.error('Erro na exclusão:', errorMsg);
                    toastr.error(errorMsg);
                }
            },
            error: function(xhr, status, error) {
                $('#modalAlert2').modal('hide');
                
                // Restaura o botão
                $('#confirm-delete').html('Excluir');
                $('#confirm-delete').prop('disabled', false);
                
                console.error('Erro na requisição AJAX:', status, error);
                console.error('Resposta do servidor:', xhr.responseText);
                console.error('Status da requisição:', xhr.status);
                console.error('URL tentada:', url);
                
                let errorMessage = 'Erro ao excluir Futliga Clássica';
                
                try {
                    if (xhr.responseJSON && xhr.responseJSON.message) {
                        errorMessage = xhr.responseJSON.message;
                    } else if (xhr.responseText) {
                        const responseObj = JSON.parse(xhr.responseText);
                        if (responseObj.message) {
                            errorMessage = responseObj.message;
                        }
                    }
                } catch (e) {
                    console.error('Erro ao processar resposta de erro:', e);
                }
                
                toastr.error(errorMessage);
            }
        });
    });

    // Exclusão em massa
    $(document).on('click', '#delete-selected', function() {
        const selectedCount = $('.check-item:checked').length;
        if (selectedCount > 0) {
            console.log(`Selecionadas ${selectedCount} Futliga(s) Clássica(s) para exclusão`);
            
            // Mostra o modal de confirmação
            $('#modalAlert').modal('show');
            
            // Atualiza o texto do modal para refletir a quantidade
            $('#modalAlert .modal-body p').text(`Tem certeza que deseja excluir ${selectedCount} Futliga(s) Clássica(s) selecionada(s)?`);
        } else {
            console.log('Nenhuma Futliga selecionada para exclusão');
            toastr.error('Selecione pelo menos uma Futliga para excluir');
        }
    });
    
    // Confirmação da exclusão em massa
    $(document).on('click', '#confirm-mass-delete', function() {
        // Desabilita o botão para evitar múltiplos cliques
        $(this).prop('disabled', true);
        $(this).html('<i class="fa fa-spinner fa-spin"></i> Processando...');
        
        // Coleta os IDs dos itens selecionados
        const selectedIds = [];
        $('.check-item:checked').each(function() {
            selectedIds.push($(this).val());
        });
        
        console.log('IDs selecionados para exclusão em massa:', selectedIds);
        
        if (selectedIds.length === 0) {
            toastr.error('Nenhuma Futliga selecionada para exclusão');
            $('#modalAlert').modal('hide');
            return;
        }
        
        // Obter a URL do botão de exclusão em massa
        const url = $('#delete-selected').data('url');
        console.log('URL da requisição de exclusão em massa:', url);
        
        // Envia a requisição AJAX
        $.ajax({
            url: url,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ ids: selectedIds }),
            headers: {
                'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
            },
            success: function(response) {
                $('#modalAlert').modal('hide');
                
                console.log('Resposta do servidor:', response);
                
                if (response.success) {
                    toastr.success(response.message || 'Futligas excluídas com sucesso!');
                    setTimeout(function() {
                        window.location.reload();
                    }, 2000);
                } else {
                    // Restaura o botão
                    $('#confirm-mass-delete').html('Excluir');
                    $('#confirm-mass-delete').prop('disabled', false);
                    
                    const errorMsg = response.message || 'Erro ao excluir Futligas Clássicas';
                    console.error('Erro na exclusão em massa:', errorMsg);
                    toastr.error(errorMsg);
                }
            },
            error: function(xhr, status, error) {
                $('#modalAlert').modal('hide');
                
                // Restaura o botão
                $('#confirm-mass-delete').html('Excluir');
                $('#confirm-mass-delete').prop('disabled', false);
                
                console.error('Erro na requisição AJAX de exclusão em massa:', status, error);
                console.error('Resposta do servidor:', xhr.responseText);
                
                let errorMessage = 'Erro ao excluir Futligas Clássicas';
                
                try {
                    if (xhr.responseJSON && xhr.responseJSON.message) {
                        errorMessage = xhr.responseJSON.message;
                    } else if (xhr.responseText) {
                        const responseObj = JSON.parse(xhr.responseText);
                        if (responseObj.message) {
                            errorMessage = responseObj.message;
                        }
                    }
                } catch (e) {
                    console.error('Erro ao processar resposta de erro:', e);
                }
                
                toastr.error(errorMessage);
            }
        });
    });
});