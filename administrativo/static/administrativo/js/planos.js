$(document).ready(function() {
    // Verifica se as URLs necessárias estão definidas
    if (typeof toggleStatusUrl === 'undefined' || typeof deleteUrl === 'undefined' || typeof deleteMassUrl === 'undefined') {
        console.error('URLs necessárias não estão definidas');
        return;
    }

    // Verifica se o token CSRF está definido
    if (typeof csrfToken === 'undefined') {
        console.error('Token CSRF não está definido');
        return;
    }

    // Variável para controlar cliques múltiplos
    var clickTimeout = {};

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

    // Função para garantir que a URL termine com barra
    function ensureTrailingSlash(url) {
        return url.endsWith('/') ? url : url + '/';
    }

    // Função para inicializar os handlers dos botões
    function initializeButtonHandlers() {
        // Remove quaisquer data attributes de modal dos botões de toggle
        $('.btn-toggle-plan').removeAttr('data-toggle').removeAttr('data-target');
        
        // Garante que os botões de delete tenham os atributos corretos
        $('.delete-btn').attr('data-toggle', 'modal').attr('data-target', '#modalAlert2');
    }

    // Inicializa DataTable
    var table;
    try {
        // Destrói a tabela se já existir
        if ($.fn.DataTable.isDataTable('.dataTables-vigencias')) {
            $('.dataTables-vigencias').DataTable().destroy();
        }

        table = $('.dataTables-vigencias').DataTable({
            pageLength: 25,
            responsive: true,
            dom: '<"html5buttons"B>lTfgitp',
            buttons: [],
            stateSave: false, // Desativa o salvamento de estado
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
            },
            drawCallback: function() {
                initializeButtonHandlers();
            }
        });

    } catch (error) {
        console.error('Erro ao inicializar DataTable:', error);
    }

    // Inicializa os handlers quando a página carrega
    initializeButtonHandlers();

    // Re-inicializa os handlers após qualquer operação que possa modificar a tabela
    $(document).ajaxComplete(function(event, xhr, settings) {
        if (settings.url.includes('toggle_status') || 
            settings.url.includes('excluir')) {
            initializeButtonHandlers();
        }
    });

    // Excluir plano individual
    var planIdToDelete = null;
    $(document).on('click', '.delete-btn', function(e) {
        e.preventDefault();
        e.stopPropagation();
        planIdToDelete = $(this).data('id');
        $('#modalAlert2').modal('show');
    });

    $('#modalAlert2 .btn-danger').off('click').on('click', function() {
        if (!planIdToDelete) {
            toastr.error('Plano não identificado');
            return;
        }

        var row = $('.delete-btn[data-id="' + planIdToDelete + '"]').closest('tr');
        var btn = row.find('.delete-btn');
        
        btn.prop('disabled', true);
        row.addClass('processing');

        // Garante que a URL termine com barra
        var url = ensureTrailingSlash(deleteUrl.replace('0', planIdToDelete));

        $.ajax({
            url: url,
            type: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            success: function(response) {
                $('#modalAlert2').modal('hide');
                if (response.success) {
                    toastr.success('Plano excluído com sucesso');
                    // Remove a linha da tabela
                    row.fadeOut(400, function() {
                        $(this).remove();
                    });
                } else {
                    toastr.error(response.message || 'Erro ao excluir plano');
                    btn.prop('disabled', false);
                }
            },
            error: function(xhr, status, error) {
                $('#modalAlert2').modal('hide');
                console.error('Erro ao excluir plano:', error);
                toastr.error('Erro ao excluir plano. Por favor, tente novamente.');
                btn.prop('disabled', false);
            },
            complete: function() {
                row.removeClass('processing');
            }
        });
    });

    // Excluir planos em massa
    function excluirSelecionados() {
        var selectedIds = [];
        $('.check-item:checked').each(function() {
            selectedIds.push($(this).val());
        });

        if (selectedIds.length === 0) {
            toastr.warning('Selecione pelo menos um plano para excluir');
            return;
        }

        $('#modalAlert').modal('show');
    }

    $('#modalAlert .btn-danger').off('click').on('click', function() {
        var selectedIds = [];
        $('.check-item:checked').each(function() {
            selectedIds.push($(this).val());
        });

        if (selectedIds.length === 0) {
            toastr.warning('Selecione pelo menos um plano para excluir');
            return;
        }

        var btn = $(this);
        btn.prop('disabled', true);

        // Adiciona classe de processamento nas linhas selecionadas
        var selectedRows = [];
        selectedIds.forEach(function(id) {
            var row = $('.check-item[value="' + id + '"]').closest('tr');
            row.addClass('processing');
            selectedRows.push(row);
        });

        $.ajax({
            url: deleteMassUrl,
            type: 'POST',
            data: { ids: selectedIds },
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            success: function(response) {
                $('#modalAlert').modal('hide');
                if (response.success) {
                    toastr.success('Planos excluídos com sucesso');
                    // Atualiza a tabela após exclusão em massa
                    $('.dataTables-vigencias').DataTable().ajax.reload();
                    // Desmarca o checkbox principal
                    $('.checkAll').prop('checked', false);
                } else {
                    toastr.error(response.message || 'Erro ao excluir planos');
                }
            },
            error: function(xhr, status, error) {
                $('#modalAlert').modal('hide');
                console.error('Erro ao excluir planos:', {xhr: xhr, status: status, error: error});
                toastr.error(xhr.responseJSON?.message || 'Erro ao excluir planos. Por favor, tente novamente.');
            },
            complete: function() {
                btn.prop('disabled', false);
                selectedRows.forEach(function(row) {
                    row.removeClass('processing');
                });
            }
        });
    });

    // Checkbox "Selecionar todos"
    $('.checkAll').on('change', function() {
        $('.check-item').prop('checked', $(this).prop('checked'));
    });

    // Expor função para uso global
    window.excluirSelecionados = excluirSelecionados;

    // Ativar/Desativar plano
    $(document).on('click', '.btn-toggle-plan:not([disabled])', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        // Previne explicitamente que qualquer modal seja aberto
        e.stopImmediatePropagation();
        $('.modal').modal('hide');
        
        var btn = $(this);
        var planId = btn.data('id');
        
        // Previne múltiplos cliques
        if (clickTimeout[planId]) {
            return false;
        }
        
        if (!planId) {
            toastr.error('ID do plano não encontrado');
            return false;
        }
        
        var isEnabled = btn.data('enabled') === 'true';
        var row = btn.closest('tr');
        
        // Adiciona classe de loading
        btn.prop('disabled', true);
        row.addClass('processing');
        clickTimeout[planId] = true;

        $.ajax({
            url: toggleStatusUrl,
            type: 'POST',
            data: {
                id: planId
            },
            timeout: 10000,
            success: function(response) {
                if (response.success) {
                    var newEnabled = response.enabled;
                    btn.data('enabled', newEnabled ? 'true' : 'false');
                    
                    if (newEnabled) {
                        btn.removeClass('btn-success').addClass('btn-danger');
                        btn.attr('title', 'Desativar');
                        btn.find('i').removeClass('glyphicon-ok').addClass('glyphicon-remove');
                    } else {
                        btn.removeClass('btn-danger').addClass('btn-success');
                        btn.attr('title', 'Ativar');
                        btn.find('i').removeClass('glyphicon-remove').addClass('glyphicon-ok');
                    }
                    
                    toastr.success(response.message);
                    
                    // Atualiza a linha na tabela se necessário
                    if (table) {
                        table.draw(false);
                    }

                    // Destaca brevemente a linha atualizada
                    row.addClass('highlight');
                    setTimeout(function() {
                        row.removeClass('highlight');
                    }, 2000);
                } else {
                    toastr.error(response.message || 'Erro ao alterar status do plano');
                }
            },
            error: function(xhr, status, error) {
                console.error('Erro na requisição:', {xhr: xhr, status: status, error: error});
                
                if (status === 'timeout') {
                    toastr.error('A operação excedeu o tempo limite. Tente novamente.');
                } else {
                    toastr.error(xhr.responseJSON?.message || 'Erro ao alterar status do plano');
                }
                
                // Reverte o estado visual do botão em caso de erro
                if (isEnabled) {
                    btn.removeClass('btn-success').addClass('btn-danger');
                    btn.attr('title', 'Desativar');
                    btn.find('i').removeClass('glyphicon-ok').addClass('glyphicon-remove');
                } else {
                    btn.removeClass('btn-danger').addClass('btn-success');
                    btn.attr('title', 'Ativar');
                    btn.find('i').removeClass('glyphicon-remove').addClass('glyphicon-ok');
                }
            },
            complete: function() {
                btn.prop('disabled', false);
                row.removeClass('processing');
                
                // Remove o timeout após 1 segundo
                setTimeout(function() {
                    delete clickTimeout[planId];
                }, 1000);
            }
        });
        
        return false;
    });
}); 