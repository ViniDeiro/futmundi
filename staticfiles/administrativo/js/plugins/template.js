$(document).ready(function() {
    // Ativar as abas
    $('.nav-tabs a').on('click', function (e) {
        e.preventDefault();
        $(this).tab('show');
    });

    // Adicionar/Editar fase
    $('#add-stage').on('click', function() {
        var name = $('#stage-name').val();
        var rounds = $('#stage-rounds').val();
        var matchesPerRound = $('#stage-matches-per-round').val();
        var stageId = $(this).data('editing');

        if (!name || !rounds || !matchesPerRound) {
            toastr.error('Por favor, preencha todos os campos da fase');
            return;
        }

        // Criar formData para enviar
        var formData = new FormData();
        formData.append('name', name);
        formData.append('rounds', rounds);
        formData.append('matches_per_round', matchesPerRound);
        formData.append('csrfmiddlewaretoken', $('[name=csrfmiddlewaretoken]').val());

        // Determinar URL baseado se é edição ou adição
        var url = stageId ? 
            window.location.href.replace(/\/$/, '') + '/edit-stage/' + stageId + '/' :
            window.location.href.replace(/\/$/, '') + '/add-stage/';

        // Enviar requisição
        $.ajax({
            url: url,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.success) {
                    toastr.success(response.message);
                    // Limpar campos e resetar botão
                    $('#stage-name').val('');
                    $('#stage-rounds').val('');
                    $('#stage-matches-per-round').val('');
                    $('#add-stage').text('Adicionar Fase').removeData('editing');
                    window.location.reload();
                } else {
                    toastr.error(response.message || 'Erro ao processar fase');
                }
            },
            error: function() {
                toastr.error('Erro ao processar fase');
            }
        });
    });

    // Editar fase (ao clicar no botão de editar)
    $(document).on('click', '.btn-info', function() {
        var row = $(this).closest('tr');
        var stageId = row.data('id');
        var name = row.find('td:eq(1)').text();
        var rounds = row.find('td:eq(2)').text();
        var matchesPerRound = row.find('td:eq(3)').text();

        $('#stage-name').val(name);
        $('#stage-rounds').val(rounds);
        $('#stage-matches-per-round').val(matchesPerRound);
        $('#add-stage').text('Atualizar Fase').data('editing', stageId);
        
        // Mudar para a aba de fases
        $('.nav-tabs a[href="#fases"]').tab('show');
    });

    // Salvar template (apenas informações gerais)
    $('#form-template').on('submit', function(e) {
        e.preventDefault();

        var formData = new FormData(this);

        $.ajax({
            url: $(this).attr('action'),
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.success) {
                    toastr.success('Template atualizado com sucesso');
                    window.location.href = response.redirect_url;
                } else {
                    toastr.error(response.message || 'Erro ao atualizar template');
                }
            },
            error: function() {
                toastr.error('Erro ao atualizar template');
            }
        });
    });

    // Inicializar Sortable para drag and drop
    var el = document.getElementById('phases-table').getElementsByTagName('tbody')[0];
    if (el) {
        var sortable = new Sortable(el, {
            handle: '.drag-handle',
            animation: 150,
            onEnd: function(evt) {
                var order = [];
                $('#phases-table tbody tr').each(function(index) {
                    order.push({
                        id: $(this).data('id'),
                        order: index
                    });
                });

                fetch(window.location.href.replace(/\/$/, '') + '/reorder-stages', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    },
                    body: JSON.stringify({ order: order })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        toastr.success('Ordem das fases atualizada com sucesso');
                    } else {
                        toastr.error(data.message || 'Erro ao atualizar ordem das fases');
                    }
                })
                .catch(() => {
                    toastr.error('Erro ao atualizar ordem das fases');
                });
            }
        });
    }
}); 