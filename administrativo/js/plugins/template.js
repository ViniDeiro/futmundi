$(document).ready(function() {
    // Ativar as abas
    $('.nav-tabs a').on('click', function (e) {
        e.preventDefault();
        $(this).tab('show');
    });

    // Adicionar nova fase
    $('#add-stage').on('click', function() {
        var name = $('#stage-name').val();
        var rounds = $('#stage-rounds').val();
        var matchesPerRound = $('#stage-matches-per-round').val();

        if (!name || !rounds || !matchesPerRound) {
            toastr.error('Por favor, preencha todos os campos da fase');
            return;
        }

        // Verificar se já existe uma fase com o mesmo nome
        var duplicateName = false;
        $('#stages-table tbody tr').each(function() {
            if ($(this).find('td:first').text() === name) {
                duplicateName = true;
                return false;
            }
        });

        if (duplicateName) {
            toastr.error('Já existe uma fase com este nome');
            return;
        }

        // Adicionar nova linha na tabela
        var newRow = `<tr>
            <td>${name}</td>
            <td>${rounds}</td>
            <td>${matchesPerRound}</td>
            <td>
                <button type="button" class="btn btn-info btn-xs" title="Editar"><i class="fa fa-pencil"></i></button>
                <button type="button" class="btn btn-danger btn-xs" title="Excluir"><i class="fa fa-trash"></i></button>
            </td>
        </tr>`;
        $('#stages-table tbody').append(newRow);

        // Limpar campos
        $('#stage-name').val('');
        $('#stage-rounds').val('');
        $('#stage-matches-per-round').val('');

        toastr.success('Fase adicionada com sucesso');
    });

    // Editar fase
    $(document).on('click', '.btn-info', function() {
        var row = $(this).closest('tr');
        var name = row.find('td:eq(0)').text();
        var rounds = row.find('td:eq(1)').text();
        var matchesPerRound = row.find('td:eq(2)').text();

        $('#stage-name').val(name);
        $('#stage-rounds').val(rounds);
        $('#stage-matches-per-round').val(matchesPerRound);

        // Remover a linha antiga
        row.remove();
    });

    // Excluir fase
    $(document).on('click', '.btn-danger', function() {
        var row = $(this).closest('tr');
        row.remove();
        toastr.success('Fase removida com sucesso');
    });

    // Salvar template
    $('form').on('submit', function(e) {
        e.preventDefault();

        var stages = [];
        $('#stages-table tbody tr').each(function() {
            stages.push({
                name: $(this).find('td:eq(0)').text(),
                rounds: $(this).find('td:eq(1)').text(),
                matches_per_round: $(this).find('td:eq(2)').text()
            });
        });

        var formData = {
            name: $('#name').val(),
            enabled: $('#enabled').is(':checked'),
            stages: stages
        };

        $.ajax({
            url: $(this).attr('action'),
            type: 'POST',
            data: JSON.stringify(formData),
            contentType: 'application/json',
            headers: {
                'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                if (response.success) {
                    toastr.success('Template salvo com sucesso');
                    window.location.href = response.redirect_url;
                } else {
                    toastr.error(response.message || 'Erro ao salvar template');
                }
            },
            error: function() {
                toastr.error('Erro ao salvar template');
            }
        });
    });

    // Duplicar template
    $('.btn-duplicate').click(function(e) {
        e.preventDefault();
        var url = $(this).attr('href');
        
        $.ajax({
            url: url,
            type: 'GET',
            success: function(response) {
                if (response.success) {
                    toastr.success(response.message);
                    if (response.redirect) {
                        window.location.href = response.redirect;
                    }
                } else {
                    toastr.error(response.message);
                }
            },
            error: function() {
                toastr.error('Erro ao duplicar template');
            }
        });
    });
}); 