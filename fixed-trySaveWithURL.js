function trySaveWithURL(urlIndex = 0, formatoIndex = 0) {
    console.log('[DEBUG] Iniciando salvamento com URL correta');
    console.log('[DEBUG] URL da página atual:', window.location.href);
    console.log('[DEBUG] Pathname:', window.location.pathname);
    
    // Referência ao botão
    const $btn = $('#successToast');
    const originalHtml = $btn.html();
    
    // Atualizar botão
    $btn.html('<i class="fa fa-spinner fa-spin"></i> Salvando...').prop('disabled', true);
    
    // Definir timeout para garantir que o botão será restaurado
    const buttonRestoreTimeout = setTimeout(function() {
        $btn.html(originalHtml).prop('disabled', false);
        console.log('[DEBUG] Timer de segurança acionado - restaurando botão');
        toastr.error('A operação demorou muito tempo. Tente novamente.');
    }, 15000); // 15 segundos é tempo suficiente
    
    try {
        // Coletar dados de níveis
        const level_data = [];
        $('#table tbody tr').each(function() {
            const id = $(this).data('id');
            // CORREÇÃO: Remover o ícone de barras do nome
            const fullName = $(this).find('td:eq(0)').text().trim();
            // Extrair apenas o nome real, removendo o ícone de barras "☰"
            const name = fullName.replace(/^[\s\u2630]+/, '').trim();
            
            const players = $(this).find('td:eq(2)').text().trim();
            const premium_players = $(this).find('td:eq(3)').text().trim();
            const owner_premium = $(this).find('td:eq(4)').text().trim() === 'Sim';
            
            let image = null;
            const imageElement = $(this).find('td:eq(1) img');
            if (imageElement.length) {
                image = imageElement.attr('src');
            }
            
            level_data.push({
                id: id,
                name: name,
                players: players,
                premium_players: premium_players,
                owner_premium: owner_premium,
                image: image
            });
        });
        
        // Coletar prêmios do modo antigo - compatível com o servidor
        const prizes = [];
        $('#premiosTable tbody tr').each(function() {
            const $row = $(this);
            const position = $row.data('position') || parseInt($row.find('td:first').text().replace('°', '')) || 0;
            const id = $row.data('id') || null;
            
            const values = {};
            
            // Procurar a imagem do prêmio
            let image = null;
            const $imageElement = $row.find('td.center-middle img');
            if ($imageElement.length) {
                image = $imageElement.attr('src');
            }
            
            // Coletar valores para cada nível
            $row.find('input.premio-input').each(function() {
                const $input = $(this);
                let nivel = $input.data('nivel');
                
                // Remover o prefixo ☰ do nome do nível
                if (nivel) {
                    nivel = nivel.replace(/^[\s\u2630☰]+/, '').trim();
                    
                    let value = parseInt($input.val() || "0");
                    if (isNaN(value)) value = 0;
                    values[nivel] = value;
                    
                    console.log(`[DEBUG-PREMIO] Coletado valor ${value} para nível ${nivel} na posição ${position}`);
                }
            });
            
            prizes.push({
                id: id,
                position: position,
                image: image,
                values: values
            });
        });
        
        // Premiação
        const weekRewardDay = $('#dia-premiacao').val();
        const weekRewardTime = $('.clockpicker input').eq(0).val();
        const seasonRewardMonth = $('#mes-ano-premiacao').val();
        const seasonRewardDay = $('#dia-ano-premiacao').val();
        const seasonRewardTime = $('.clockpicker input').eq(1).val();
        
        const award_config = {
            weekly: {
                day: weekRewardDay,
                time: weekRewardTime
            },
            season: {
                month: seasonRewardMonth,
                day: seasonRewardDay,
                time: seasonRewardTime
            }
        };
        
        // Dados completos - formato original
        const data = {
            levels: level_data,
            prizes: prizes,
            award_config: award_config,
            deleted_prize_ids: []
        };
        
        // URL correta conforme configurado no urls.py
        const url = '/futligas/jogadores/salvar/';
        console.log('[DEBUG] Usando URL correta:', url);
        
        // Fazer a requisição
        $.ajax({
            url: url,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(data),
            headers: {
                'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            success: function(response) {
                clearTimeout(buttonRestoreTimeout);
                $btn.html(originalHtml).prop('disabled', false);
                
                console.log('[DEBUG] Sucesso! URL funcionou:', url);
                console.log('[DEBUG] Resposta do servidor:', response);
                
                if (response && response.success) {
                    toastr.success('Dados salvos com sucesso!');
                    
                    if (typeof window.fixColumnOrder === 'function') {
                        setTimeout(window.fixColumnOrder, 500);
                    }
                } else {
                    const errorMsg = response && response.error ? response.error : 'Erro ao salvar dados.';
                    toastr.error(errorMsg);
                    console.error('[DEBUG] Erro retornado pelo servidor:', errorMsg);
                }
            },
            error: function(xhr, status, error) {
                console.error('[DEBUG] Erro na requisição para URL ' + url + ':', status, error);
                console.error('[DEBUG] Status HTTP:', xhr.status);
                clearTimeout(buttonRestoreTimeout);
                $btn.html(originalHtml).prop('disabled', false);
                toastr.error('Erro ao salvar dados. Verifique o console para detalhes.');
            },
            complete: function() {
                clearTimeout(buttonRestoreTimeout);
                // Sempre restaurar o botão no complete
                $btn.html(originalHtml).prop('disabled', false);
            }
        });
    } catch (e) {
        console.error('[DEBUG] Erro ao tentar salvar:', e);
        clearTimeout(buttonRestoreTimeout);
        $btn.html(originalHtml).prop('disabled', false);
        toastr.error('Erro ao processar dados para salvamento.');
    }
}
