// Função para excluir um continente
function excluirContinente(id) {
    $('#modalAlert2').modal('show');
    $('#modalAlert2 .btn-danger').off('click').on('click', function() {
        $.ajax({
            url: `/continente/excluir/${id}/`,
            type: 'POST',
            headers: {
                'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                $('#modalAlert2').modal('hide');
                if (response.success) {
                    toastr.success(response.message);
                    setTimeout(function() {
                        window.location.reload();
                    }, 1000);
                } else {
                    toastr.error(response.message);
                }
            },
            error: function(xhr, status, error) {
                $('#modalAlert2').modal('hide');
                toastr.error('Erro ao excluir continente: ' + error);
            }
        });
    });
}

// Função para excluir múltiplos continentes
function excluirSelecionados() {
    const ids = [];
    $('.check-item:checked').each(function() {
        ids.push($(this).val());
    });

    if (ids.length === 0) {
        toastr.warning('Selecione pelo menos um continente para excluir');
        return;
    }

    $('#modalAlert').modal('show');
    $('#modalAlert .btn-danger').off('click').on('click', function() {
        $.ajax({
            url: "/continente/excluir-em-massa/",
            type: 'POST',
            data: {
                'ids[]': ids,
                'csrfmiddlewaretoken': $('[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                $('#modalAlert').modal('hide');
                if (response.success) {
                    toastr.success(response.message);
                    setTimeout(function() {
                        window.location.reload();
                    }, 1000);
                } else {
                    toastr.error(response.message);
                }
            },
            error: function() {
                $('#modalAlert').modal('hide');
                toastr.error('Erro ao excluir continentes');
            }
        });
    });
}

// Event listeners
$(document).ready(function() {
    var table = $('.dataTables-continentes');
    if (!$.fn.DataTable.isDataTable(table)) {
        table.DataTable({
            pageLength: 10,
            responsive: true,
            dom: '<"html5buttons"B>lTfgitp',
            buttons: [],
            language: {
                url: "//cdn.datatables.net/plug-ins/1.10.19/i18n/Portuguese-Brasil.json"
            }
        });
    }

    // Handler para excluir continente
    $(document).on('click', '.delete-btn', function() {
        var continenteId = $(this).data('id');
        excluirContinente(continenteId);
    });

    // Botão de excluir em massa
    $('#delete-selected').click(function() {
        if (confirm('Tem certeza que deseja excluir os continentes selecionados?')) {
            excluirSelecionados();
        }
    });

    // Checkbox para selecionar todos
    $('#check-all').change(function() {
        $('.check-item').prop('checked', $(this).prop('checked'));
    });

    // Configurações do toastr
    toastr.options = {
        closeButton: true,
        debug: false,
        progressBar: true,
        preventDuplicates: false,
        positionClass: "toast-top-right",
        onclick: null,
        showDuration: "400",
        hideDuration: "1000",
        timeOut: 4000,
        extendedTimeOut: "400",
        showEasing: "swing",
        hideEasing: "linear",
        showMethod: 'slideDown'
    };
});

// Função para confirmar exclusão individual
function confirmDelete(id) {
    if (confirm('Tem certeza que deseja excluir este continente?')) {
        excluirContinente(id);
    }
}

// Função para mostrar modal de confirmação de exclusão em massa
function deleteSelected() {
    var selected = $("input[name='selected_items']:checked");
    if (selected.length > 0) {
        $("#modalDeleteSelected").modal('show');
    } else {
        toastr.warning('Selecione pelo menos um continente para excluir.');
    }
}

// Função para executar a exclusão em massa
function executeDeleteSelected() {
    var ids = [];
    $("input[name='selected_items']:checked").each(function() {
        ids.push($(this).val());
    });

    $.ajax({
        url: "/continente/excluir-em-massa/",
        type: "POST",
        data: {
            ids: ids,
            csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
        },
        success: function(response) {
            $("#modalDeleteSelected").modal('hide');
            if (response.success) {
                toastr.success(response.message);
                setTimeout(function() {
                    window.location.reload();
                }, 1000);
            } else {
                toastr.error(response.message);
            }
        },
        error: function() {
            $("#modalDeleteSelected").modal('hide');
            toastr.error('Erro ao excluir continentes.');
        }
    });
}

// Checkbox "Selecionar todos"
$('.checkAll').on('change', function() {
    $('.check-item').prop('checked', $(this).prop('checked'));
}); 