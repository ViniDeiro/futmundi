/**
 * Script para gerenciar filtros geográficos nos formulários de campeonato
 */

$(document).ready(function() {
    console.log("Inicializando filtros geográficos...");
    
    // Adicionar delay para garantir que todos os elementos estejam carregados
    setTimeout(function() {
        console.log("Verificando elementos necessários:");
        console.log("- Continente:", $('#continente').length ? "Encontrado" : "Não encontrado");
        console.log("- País:", $('#pais').length ? "Encontrado" : "Não encontrado");
        console.log("- Estado:", $('#estado').length ? "Encontrado" : "Não encontrado");
        
        inicializarFiltros();
        
        // Configurar eventos de change
        $('#continente').off('change').on('change', function() {
            console.log("Continente alterado:", $(this).val());
            atualizarPaises();
        });
        
        $('#pais').off('change').on('change', function() {
            console.log("País alterado:", $(this).val());
            atualizarEstados();
        });
        
        // Escutar o evento personalizado para forçar atualização dos filtros
        $(document).off('filtersInitialized').on('filtersInitialized', function() {
            console.log("Recebido evento filtersInitialized, atualizando filtros");
            atualizarPaises();
            atualizarEstados();
        });
    }, 1200);
    
    // Inicializar filtros com base nos valores existentes
    function inicializarFiltros() {
        console.log("Inicializando filtros com valores atuais");
        
        // Verificar valores iniciais
        var continenteId = $('#continente').val();
        var paisId = $('#pais').val();
        
        console.log("Valores iniciais - Continente:", continenteId, "País:", paisId);
        
        // Aplicar filtros iniciais
        atualizarPaises();
        atualizarEstados();
    }
    
    // Atualizar lista de países com base no continente selecionado
    function atualizarPaises() {
        var continenteId = $('#continente').val();
        var $pais = $('#pais');
        var paisId = $pais.val(); // Preservar valor atual
        
        console.log("Atualizando países. Continente:", continenteId, "País atual:", paisId);
        
        // Verificar se o select de país existe
        if ($pais.length === 0) {
            console.error("Elemento select de país não encontrado!");
            return;
        }
        
        // Verificar se há opções com data-continent
        var temAtributoDataContinent = $pais.find('option[data-continent]').length > 0;
        console.log("Opções com atributo data-continent:", temAtributoDataContinent ? "Sim" : "Não");
        
        if (!temAtributoDataContinent) {
            console.warn("Nenhuma opção com atributo data-continent encontrada. A filtragem não funcionará corretamente.");
        }
        
        // Se estamos usando Select2, destruir temporariamente para manipular as opções
        var usingSelect2 = $.fn.select2 && $pais.hasClass('select2-hidden-accessible');
        if (usingSelect2) {
            $pais.select2('destroy');
        }
        
        // Ocultar todos os países primeiro
        $pais.find('option').not('[value=""]').hide();
        
        // Sempre mostrar a opção vazia/placeholder
        $pais.find('option[value=""]').show();
        
        if (continenteId) {
            // Mostrar países do continente selecionado
            var paisesDosContinentes = $pais.find('option[data-continent="' + continenteId + '"]');
            paisesDosContinentes.show();
            console.log("Filtrando países por continente:", continenteId, "- Encontrados:", paisesDosContinentes.length);
        } else {
            // Se nenhum continente selecionado, mostrar todos
            $pais.find('option').show();
            console.log("Mostrando todos os países");
        }
        
        // Verificar se o país atual ainda é válido
        var paisValido = !paisId || $pais.find('option[value="' + paisId + '"]:visible').length > 0;
        if (!paisValido && paisId) {
            console.log("País atual não é válido para o continente selecionado, resetando");
            $pais.val('').trigger('change');
        }
        
        // Recriar o Select2 se estava sendo usado
        if (usingSelect2) {
            $pais.select2({
                width: '100%',
                placeholder: 'Selecione...',
                allowClear: true
            });
        }
    }
    
    // Atualizar lista de estados com base no país selecionado
    function atualizarEstados() {
        var paisId = $('#pais').val();
        var $estado = $('#estado');
        var estadoId = $estado.val(); // Preservar valor atual
        var ambitoPermiteEstado = $('#ambito').val() ? 
                                  $('#ambito option:selected').text().trim() === 'Estadual' : 
                                  false;
        
        console.log("Atualizando estados. País:", paisId, "Estado atual:", estadoId, "Âmbito permite estado:", ambitoPermiteEstado);
        
        // Verificar se o select de estado existe
        if ($estado.length === 0) {
            console.error("Elemento select de estado não encontrado!");
            return;
        }
        
        // Verificar se há opções com data-country
        var temAtributoDataCountry = $estado.find('option[data-country]').length > 0;
        console.log("Opções com atributo data-country:", temAtributoDataCountry ? "Sim" : "Não");
        
        if (!temAtributoDataCountry) {
            console.warn("Nenhuma opção com atributo data-country encontrada. A filtragem não funcionará corretamente.");
        }
        
        // Se estamos usando Select2, destruir temporariamente para manipular as opções
        var usingSelect2 = $.fn.select2 && $estado.hasClass('select2-hidden-accessible');
        if (usingSelect2) {
            $estado.select2('destroy');
        }
        
        // Habilitar/desabilitar o select de estado
        if (paisId && ambitoPermiteEstado) {
            $estado.prop('disabled', false);
        } else {
            $estado.prop('disabled', !ambitoPermiteEstado);
        }
        
        // Ocultar todos os estados primeiro
        $estado.find('option').not('[value=""]').hide();
        
        // Sempre mostrar a opção vazia/placeholder
        $estado.find('option[value=""]').show();
        
        if (paisId) {
            // Mostrar estados do país selecionado
            var estadosDoPais = $estado.find('option[data-country="' + paisId + '"]');
            estadosDoPais.show();
            console.log("Filtrando estados por país:", paisId, "- Encontrados:", estadosDoPais.length);
        } else {
            // Se nenhum país selecionado, mostrar todos
            $estado.find('option').show();
            console.log("Mostrando todos os estados");
        }
        
        // Verificar se o estado atual ainda é válido
        var estadoValido = !estadoId || $estado.find('option[value="' + estadoId + '"]:visible').length > 0;
        if (!estadoValido && estadoId) {
            console.log("Estado atual não é válido para o país selecionado, resetando");
            $estado.val('').trigger('change');
        }
        
        // Recriar o Select2 se estava sendo usado
        if (usingSelect2) {
            $estado.select2({
                width: '100%',
                placeholder: 'Selecione...',
                allowClear: true
            });
        }
    }
}); 