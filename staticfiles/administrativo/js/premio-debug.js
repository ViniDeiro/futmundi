// Script de depuração para Futligas Jogadores

// Interceptar requisições AJAX para o endpoint de salvar prêmios
console.log("[DEBUG-PREMIO-JS] Inicializando interceptação de requisições AJAX");

// Armazena a função original
const originalAjax = $.ajax;

// Substitui a função original por uma versão que adiciona logs
$.ajax = function(settings) {
    // Se for uma requisição de salvamento de futligas jogadores
    if (settings.url && settings.url.indexOf('/futligas/jogadores/salvar/') !== -1) {
        console.log("[DEBUG-PREMIO-JS] Interceptando requisição para " + settings.url);
        
        // Copia os dados e censura imagens base64 para não poluir o console
        let dataCopy = JSON.parse(JSON.stringify(settings.data));
        if (dataCopy.prizes) {
            dataCopy.prizes.forEach(premio => {
                if (premio.image && premio.image.startsWith('data:image')) {
                    premio.image = "[IMAGEM BASE64]";
                }
            });
        }
        
        console.log("[DEBUG-PREMIO-JS] Dados enviados: ", dataCopy);
        
        // Guarda callbacks originais
        const originalSuccess = settings.success;
        const originalError = settings.error;
        const originalComplete = settings.complete;
        
        // Substitui o callback de sucesso
        settings.success = function(response) {
            console.log("[DEBUG-PREMIO-JS] Resposta de sucesso: ", response);
            // Chamada do callback original
            if (originalSuccess) originalSuccess.apply(this, arguments);
        };
        
        // Substitui o callback de erro
        settings.error = function(xhr, status, error) {
            console.error("[DEBUG-PREMIO-JS] Erro na requisição:");
            console.error("Status: " + status);
            console.error("Erro: " + error);
            console.error("Resposta: " + xhr.responseText);
            
            // Tenta analisar a resposta se for JSON
            try {
                if (xhr.responseText && xhr.responseText.trim()) {
                    const responseData = JSON.parse(xhr.responseText);
                    console.error("Resposta analizada: ", responseData);
                }
            } catch (e) {
                console.error("Erro ao analisar resposta: " + e);
            }
            
            // Chamada do callback original
            if (originalError) originalError.apply(this, arguments);
        };
        
        // Substitui o callback de conclusão
        settings.complete = function(xhr, status) {
            console.log("[DEBUG-PREMIO-JS] Requisição concluída com status: " + status);
            // Chamada do callback original
            if (originalComplete) originalComplete.apply(this, arguments);
        };
    }
    
    // Chama o ajax original com as configurações modificadas
    return originalAjax.apply(this, arguments);
};

// Verificar se existe duplicação de eventos
function verificarEventosDuplicados() {
    console.log("[DEBUG-PREMIO-JS] Verificando eventos duplicados...");
    
    // Verifica eventos do botão de adicionar prêmio
    const addEvents = $._data($('.btn-adicionar-premio')[0], 'events');
    if (addEvents && addEvents.click) {
        console.log(`[DEBUG-PREMIO-JS] Botão adicionar prêmio: ${addEvents.click.length} handler(s) de clique`);
    } else {
        console.log("[DEBUG-PREMIO-JS] Botão adicionar prêmio: Nenhum handler de clique");
    }
    
    // Verifica eventos dos botões de excluir prêmio
    if ($('.delete-premio').length > 0) {
        const deleteEvents = $._data($('.delete-premio')[0], 'events');
        if (deleteEvents && deleteEvents.click) {
            console.log(`[DEBUG-PREMIO-JS] Botão excluir prêmio: ${deleteEvents.click.length} handler(s) de clique`);
        } else {
            console.log("[DEBUG-PREMIO-JS] Botão excluir prêmio: Nenhum handler de clique");
        }
    } else {
        console.log("[DEBUG-PREMIO-JS] Botão excluir prêmio: Não encontrado na página");
    }
    
    // Verifica eventos do botão de confirmação de exclusão
    const confirmEvents = $._data($('#confirmDeletePrize')[0], 'events');
    if (confirmEvents && confirmEvents.click) {
        console.log(`[DEBUG-PREMIO-JS] Botão confirmar exclusão: ${confirmEvents.click.length} handler(s) de clique`);
    } else {
        console.log("[DEBUG-PREMIO-JS] Botão confirmar exclusão: Nenhum handler de clique");
    }
    
    // Verifica eventos do botão salvar
    const saveEvents = $._data($('#successToast')[0], 'events');
    if (saveEvents && saveEvents.click) {
        console.log(`[DEBUG-PREMIO-JS] Botão salvar: ${saveEvents.click.length} handler(s) de clique`);
    } else {
        console.log("[DEBUG-PREMIO-JS] Botão salvar: Nenhum handler de clique");
    }
}

// Verificar quando a página estiver carregada
$(document).ready(function() {
    console.log("[DEBUG-PREMIO-JS] Página carregada, aguardando 1 segundo para verificar eventos...");
    setTimeout(verificarEventosDuplicados, 1000);
    
    // Identificar problemas com o modal
    if ($('#confirmDeletePrizeModal').length > 1) {
        console.error("[DEBUG-PREMIO-JS] PROBLEMA: Existem várias instâncias do modal de confirmação!");
    } else if ($('#confirmDeletePrizeModal').length === 0) {
        console.error("[DEBUG-PREMIO-JS] PROBLEMA: Modal de confirmação não encontrado!");
    } else {
        console.log("[DEBUG-PREMIO-JS] Modal de confirmação: OK");
    }
    
    // Informações sobre a tabela de prêmios
    const numRows = $('#premiosTable tbody tr').length;
    console.log(`[DEBUG-PREMIO-JS] Tabela de prêmios: ${numRows} prêmios`);
    
    // Verificar se os níveis existem
    const numLevels = $('#table tbody tr').length;
    console.log(`[DEBUG-PREMIO-JS] Níveis: ${numLevels} níveis`);
    
    // Adicionar handler para o modal ser exibido
    $('#confirmDeletePrizeModal').on('show.bs.modal', function (e) {
        console.log("[DEBUG-PREMIO-JS] Modal de confirmação está sendo exibido");
        const row = $(this).data('row-to-delete');
        if (row && row.length) {
            const position = row.find('td:first').text().trim();
            const prizeId = row.data('id');
            console.log(`[DEBUG-PREMIO-JS] Prêmio a ser excluído: Posição=${position}, ID=${prizeId || 'Novo'}`);
        } else {
            console.error("[DEBUG-PREMIO-JS] PROBLEMA: Modal não tem linha para excluir!");
        }
    });
});

console.log("[DEBUG-PREMIO-JS] Script de depuração carregado com sucesso!");
