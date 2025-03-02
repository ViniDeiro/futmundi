$(document).ready(function() {
    // Detecta o prefixo da URL dinamicamente
    const ADMIN_URL_PREFIX = (function() {
        const metaElement = document.querySelector('meta[name="url-prefix"]');
        if (metaElement && metaElement.getAttribute('content')) {
            return metaElement.getAttribute('content');
        }
        return '/administrativo'; // Valor padrão caso não encontre a meta tag
    })();

    // Configuração do CSRF token para requisições AJAX
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const csrftoken = getCookie('csrftoken');

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    // Configuração do Toastr
    toastr.options = {
        closeButton: true,
        progressBar: true,
        showMethod: 'slideDown',
        timeOut: 4000
    };

    // Configuração da DataTable
    $('.dataTables-example').DataTable({
        pageLength: 25,
        responsive: true,
        dom: '<"html5buttons"B>lTfgitp',
        buttons: [
            { extend: 'copy', text: 'Copiar' },
            { extend: 'csv' },
            { extend: 'excel', title: 'Notificações' },
            { extend: 'pdf', title: 'Notificações' },
            {
                extend: 'print',
                text: 'Imprimir',
                customize: function (win){
                    $(win.document.body).addClass('white-bg');
                    $(win.document.body).css('font-size', '10px');
                    $(win.document.body).find('table')
                        .addClass('compact')
                        .css('font-size', 'inherit');
                }
            }
        ],
        language: {
            processing: "Processando...",
            search: "Buscar:",
            lengthMenu: "Mostrar _MENU_ registros",
            info: "Mostrando _START_ até _END_ de _TOTAL_ registros",
            infoEmpty: "Mostrando 0 até 0 de 0 registros",
            infoFiltered: "(Filtrados de _MAX_ registros)",
            infoPostFix: "",
            loadingRecords: "Carregando...",
            zeroRecords: "Nenhum registro encontrado",
            emptyTable: "Nenhum registro disponível",
            paginate: {
                first: "Primeiro",
                previous: "Anterior",
                next: "Próximo",
                last: "Último"
            }
        }
    });

    // Função para excluir uma notificação
    function deleteNotification(id) {
        $.ajax({
            url: `${ADMIN_URL_PREFIX}/notificacao/${id}/excluir/`,
            type: 'POST',
            success: function(response) {
                if (response.success) {
                    toastr.success('Notificação excluída com sucesso!');
                    setTimeout(function() {
                        window.location.reload();
                    }, 1000);
                } else {
                    toastr.error(response.message || 'Erro ao excluir notificação');
                }
            },
            error: function() {
                toastr.error('Erro ao excluir notificação');
            }
        });
    }

    // Função para excluir múltiplas notificações
    function deleteMultipleNotifications(ids) {
        $.ajax({
            url: `${ADMIN_URL_PREFIX}/notificacao/excluir-em-massa/`,
            type: 'POST',
            data: { ids: ids },
            success: function(response) {
                if (response.success) {
                    toastr.success('Notificações excluídas com sucesso!');
                    setTimeout(function() {
                        window.location.reload();
                    }, 1000);
                } else {
                    toastr.error(response.message || 'Erro ao excluir notificações');
                }
            },
            error: function() {
                toastr.error('Erro ao excluir notificações');
            }
        });
    }

    // Evento para excluir uma única notificação
    $('.delete-notification').click(function(e) {
        e.preventDefault();
        const id = $(this).data('id');
        $('#deleteModal').modal('show');
        
        $('#confirmDelete').off('click').on('click', function() {
            deleteNotification(id);
            $('#deleteModal').modal('hide');
        });
    });

    // Evento para selecionar/deselecionar todos os checkboxes
    $('.checkAll').change(function() {
        $('.checkItem').prop('checked', $(this).prop('checked'));
    });

    // Evento para excluir múltiplas notificações
    $('#deleteSelected').click(function(e) {
        e.preventDefault();
        const selectedIds = $('.checkItem:checked').map(function() {
            return $(this).val();
        }).get();

        if (selectedIds.length === 0) {
            toastr.warning('Selecione pelo menos uma notificação para excluir');
            return;
        }

        $('#deleteModal').modal('show');
        
        $('#confirmDelete').off('click').on('click', function() {
            deleteMultipleNotifications(selectedIds);
            $('#deleteModal').modal('hide');
        });
    });

    // Evento para carregar informações da notificação
    $('.info-notification').click(function(e) {
        e.preventDefault();
        const id = $(this).data('id');
        
        $.ajax({
            url: `${ADMIN_URL_PREFIX}/notificacoes/`,
            type: 'GET',
            data: {
                action: 'get_info',
                id: id
            },
            success: function(response) {
                if (response.success) {
                    $('#infoModal .modal-body').html(`
                        <p><strong>Status:</strong> ${response.status}</p>
                        <p><strong>Data de Envio:</strong> ${response.send_at || '-'}</p>
                        ${response.error_message ? `<p><strong>Mensagem de Erro:</strong> ${response.error_message}</p>` : ''}
                    `);
                    $('#infoModal').modal('show');
                } else {
                    toastr.error('Erro ao carregar informações da notificação');
                }
            },
            error: function() {
                toastr.error('Erro ao carregar informações da notificação');
            }
        });
    });
}); 