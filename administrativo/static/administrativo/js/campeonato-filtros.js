/**
 * Script para gerenciar filtros geográficos nos formulários de campeonato
 * Implementação simplificada e direta
 */

$(document).ready(function() {
    console.log("Inicializando filtros geográficos (versão simplificada)...");
    
    // Referências aos elementos DOM principais
    var $ambito = $('#ambito');
    var $continente = $('#continente');
    var $pais = $('#pais');
    var $estado = $('#estado');
    
    // Armazenar todas as opções originais para poder reconstruir
    var todasOpcoesOriginais = {
        continentes: [],
        paises: [],
        estados: []
    };
    
    // Inicialização
    inicializar();
    
    // Configurar listeners de eventos
    $ambito.on('change', function() {
        console.log("Âmbito alterado para:", $(this).find('option:selected').text());
        atualizarCamposVisibilidade();
    });
    
    $continente.on('change', function() {
        var continenteTexto = $(this).find('option:selected').text();
        var continenteId = $(this).val();
        console.log("Continente alterado para:", continenteTexto, "(ID:", continenteId, ")");
        
        // Como o continente mudou, limpar país e estado
        limparSelect($pais);
        limparSelect($estado);
        
        // Preencher países com base no continente selecionado
        if (continenteId) {
            preencherPaisesPorContinente(continenteId);
        }
    });
    
    $pais.on('change', function() {
        var paisTexto = $(this).find('option:selected').text();
        var paisId = $(this).val();
        console.log("País alterado para:", paisTexto, "(ID:", paisId, ")");
        
        // Como o país mudou, limpar estado
        limparSelect($estado);
        
        // Preencher estados com base no país selecionado
        if (paisId) {
            preencherEstadosPorPais(paisId);
        }
    });
    
    // Função principal de inicialização
    function inicializar() {
        console.log("Inicializando componentes...");
        
        // Capturar todas as opções originais
        guardarOpcoesOriginais();
        
        // Desabilitar país e estado inicialmente
        $pais.prop('disabled', true);
        $estado.prop('disabled', true);
        
        // Configurar seletores com Select2 se disponível
        if ($.fn.select2) {
            inicializarSelect2();
        }
        
        // Aplicar visibilidade inicial com base no âmbito atual
        atualizarCamposVisibilidade();
    }
    
    // Guarda todas as opções originais para poder reconstruir
    function guardarOpcoesOriginais() {
        // Guardar opções de continentes
        $continente.find('option').each(function() {
            var $option = $(this);
            todasOpcoesOriginais.continentes.push({
                value: $option.val(),
                text: $option.text()
            });
        });
        
        // Guardar opções de países com seus atributos
        $pais.find('option').each(function() {
            var $option = $(this);
            todasOpcoesOriginais.paises.push({
                value: $option.val(),
                text: $option.text(),
                continent: $option.data('continent')
            });
        });
        
        // Guardar opções de estados com seus atributos
        $estado.find('option').each(function() {
            var $option = $(this);
            todasOpcoesOriginais.estados.push({
                value: $option.val(),
                text: $option.text(),
                country: $option.data('country')
            });
        });
        
        console.log("Opções originais guardadas:", 
                    todasOpcoesOriginais.continentes.length, "continentes,",
                    todasOpcoesOriginais.paises.length, "países,", 
                    todasOpcoesOriginais.estados.length, "estados");
    }
    
    // Inicializa todos os selects com Select2
    function inicializarSelect2() {
        $ambito.select2({
            width: '100%',
            minimumResultsForSearch: -1 // Desabilita a busca para âmbito
        });
        
        $continente.select2({
            width: '100%',
            placeholder: "Selecione...",
            allowClear: true
        });
        
        $pais.select2({
            width: '100%',
            placeholder: "Selecione...",
            allowClear: true
        });
        
        $estado.select2({
            width: '100%',
            placeholder: "Selecione...",
            allowClear: true
        });
    }
    
    // Atualiza a visibilidade/disponibilidade dos campos com base no âmbito
    function atualizarCamposVisibilidade() {
        var ambitoTexto = $ambito.find('option:selected').text().trim().toLowerCase();
        console.log("Atualizando campos por âmbito:", ambitoTexto);
        
        // Limpar todos os campos para começar do zero
        limparSelect($pais);
        limparSelect($estado);
        
        // Lógica específica por âmbito
        switch(ambitoTexto) {
            case 'estadual':
                // Para âmbito estadual:
                // Continente: habilitado
                // País: depende de ter continente selecionado
                // Estado: depende de ter país selecionado
                $continente.prop('disabled', false);
                $pais.prop('disabled', !$continente.val());
                $estado.prop('disabled', true); // Sempre inicia desabilitado
                
                // Se tem continente selecionado, preparar lista de países
                if ($continente.val()) {
                    preencherPaisesPorContinente($continente.val());
                    
                    // Se tem país selecionado, preparar lista de estados
                    if ($pais.val()) {
                        preencherEstadosPorPais($pais.val());
                    }
                }
                break;
                
            case 'nacional':
                // Para âmbito nacional:
                // Continente: habilitado
                // País: depende de ter continente selecionado
                // Estado: sempre desabilitado
                $continente.prop('disabled', false);
                $pais.prop('disabled', !$continente.val());
                $estado.prop('disabled', true);
                
                // Se tem continente selecionado, preparar lista de países
                if ($continente.val()) {
                    preencherPaisesPorContinente($continente.val());
                }
                break;
                
            case 'continental':
                // Para âmbito continental:
                // Continente: habilitado
                // País e Estado: sempre desabilitados
                $continente.prop('disabled', false);
                $pais.prop('disabled', true);
                $estado.prop('disabled', true);
                break;
                
            case 'mundial':
                // Para âmbito mundial:
                // Tudo desabilitado
                $continente.prop('disabled', true);
                $pais.prop('disabled', true);
                $estado.prop('disabled', true);
                break;
                
            default:
                // Comportamento padrão
                $continente.prop('disabled', false);
                $pais.prop('disabled', !$continente.val());
                $estado.prop('disabled', !$pais.val());
                
                if ($continente.val()) {
                    preencherPaisesPorContinente($continente.val());
                    
                    if ($pais.val()) {
                        preencherEstadosPorPais($pais.val());
                    }
                }
        }
    }
    
    // Preenche o select de países baseado no continente selecionado
    function preencherPaisesPorContinente(continenteId) {
        console.log("Preenchendo países para o continente ID:", continenteId);
        
        if (!continenteId) return;
        
        // Remover Select2 temporariamente se estiver ativo
        var temSelect2 = $.fn.select2 && $pais.hasClass('select2-hidden-accessible');
        if (temSelect2) {
            $pais.select2('destroy');
        }
        
        // Limpar o select e adicionar a opção vazia inicial
        $pais.empty();
        $pais.append('<option value="">Selecione...</option>');
        
        // Adicionar apenas os países do continente selecionado
        var totalPaises = 0;
        
        $.each(todasOpcoesOriginais.paises, function(i, pais) {
            if (pais.value && pais.continent == continenteId) {
                $pais.append(
                    $('<option>', {
                        value: pais.value,
                        text: pais.text,
                        'data-continent': pais.continent
                    })
                );
                totalPaises++;
            }
        });
        
        console.log("Total de", totalPaises, "países adicionados para o continente", continenteId);
        
        // Se não temos países para este continente, manter desabilitado
        if (totalPaises === 0) {
            $pais.prop('disabled', true);
        } else {
            $pais.prop('disabled', false);
        }
        
        // Restaurar Select2 se necessário
        if (temSelect2) {
            $pais.select2({
                width: '100%',
                placeholder: "Selecione...",
                allowClear: true
            });
        }
    }
    
    // Preenche o select de estados baseado no país selecionado
    function preencherEstadosPorPais(paisId) {
        console.log("Preenchendo estados para o país ID:", paisId);
        
        if (!paisId) return;
        
        // Primeiro verificar se o âmbito permite estados
        var ambitoTexto = $ambito.find('option:selected').text().trim().toLowerCase();
        if (ambitoTexto !== 'estadual') {
            console.log("Âmbito", ambitoTexto, "não permite estados");
            $estado.prop('disabled', true);
            return;
        }
        
        // Remover Select2 temporariamente se estiver ativo
        var temSelect2 = $.fn.select2 && $estado.hasClass('select2-hidden-accessible');
        if (temSelect2) {
            $estado.select2('destroy');
        }
        
        // Limpar o select e adicionar a opção vazia inicial
        $estado.empty();
        $estado.append('<option value="">Selecione...</option>');
        
        // Adicionar apenas os estados do país selecionado
        var totalEstados = 0;
        
        $.each(todasOpcoesOriginais.estados, function(i, estado) {
            if (estado.value && estado.country == paisId) {
                $estado.append(
                    $('<option>', {
                        value: estado.value,
                        text: estado.text,
                        'data-country': estado.country
                    })
                );
                totalEstados++;
            }
        });
        
        console.log("Total de", totalEstados, "estados adicionados para o país", paisId);
        
        // Se não temos estados para este país, manter desabilitado
        if (totalEstados === 0) {
            $estado.prop('disabled', true);
        } else {
            $estado.prop('disabled', false);
        }
        
        // Restaurar Select2 se necessário
        if (temSelect2) {
            $estado.select2({
                width: '100%',
                placeholder: "Selecione...",
                allowClear: true
            });
        }
    }
    
    // Limpa um select, deixando apenas a opção "Selecione..."
    function limparSelect($select) {
        // Remover Select2 temporariamente se estiver ativo
        var temSelect2 = $.fn.select2 && $select.hasClass('select2-hidden-accessible');
        if (temSelect2) {
            $select.select2('destroy');
        }
        
        // Limpar o select e adicionar apenas a opção "Selecione..."
        $select.empty();
        $select.append('<option value="">Selecione...</option>');
        
        // Restaurar Select2 se necessário
        if (temSelect2) {
            $select.select2({
                width: '100%',
                placeholder: "Selecione...",
                allowClear: true,
                disabled: $select.prop('disabled')
            });
        }
    }
}); 