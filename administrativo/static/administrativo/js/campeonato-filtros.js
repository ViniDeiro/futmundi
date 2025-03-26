/**
 * Script para gerenciar filtros geográficos nos formulários de campeonato
 * Implementação simplificada e direta
 */

$(document).ready(function() {
    console.log("Inicializando filtros geográficos (versão simplificada)...");
    
    // SOLUÇÃO RADICAL: Mecanismo de emergência para forçar a seleção do estado
    // Executar após um atraso para garantir que tudo esteja carregado
    setTimeout(function() {
        var $estado = $('#estado');
        var $estadoContainer = $estado.next('.select2-container');
        var estadoId = $estado.attr('data-selected-state') || $estado.data('selected-state');
        
        console.log("=== INÍCIO DA SOLUÇÃO RADICAL ===");
        console.log("Estado ID para forçar:", estadoId);
        
        if (estadoId) {
            // 1. Verificar se a opção existe e obtém seu texto
            var $option = $estado.find('option[value="' + estadoId + '"]');
            if ($option.length) {
                var estadoTexto = $option.text();
                console.log("Texto do estado encontrado:", estadoTexto);
                
                // 2. Selecionar manualmente no DOM
                document.getElementById('estado').value = estadoId;
                
                // 3. Forçar o texto no Select2
                if ($estadoContainer.length) {
                    // Encontrar o elemento onde o texto é mostrado
                    var $rendered = $estadoContainer.find('.select2-selection__rendered');
                    if ($rendered.length) {
                        $rendered.text(estadoTexto).attr('title', estadoTexto);
                        console.log("Texto do Select2 forçado para:", estadoTexto);
                    } else {
                        console.log("Elemento rendered não encontrado");
                    }
                } else {
                    console.log("Container do Select2 não encontrado");
                }
                
                // 4. Tentar destruir e recriar o Select2 também
                if ($.fn.select2 && $estado.hasClass('select2-hidden-accessible')) {
                    $estado.select2('destroy');
                    
                    // Reselecionar o valor
                    $estado.val(estadoId);
                    
                    // Recriar o Select2
                    $estado.select2({
                        width: '100%',
                        placeholder: "Selecione..."
                    });
                    
                    console.log("Select2 recriado com valor", estadoId);
                }
            } else {
                console.log("ERRO: Option para estado ID", estadoId, "não encontrada!");
                
                // Debug para ver todas as opções disponíveis
                console.log("Opções disponíveis:");
                $estado.find('option').each(function() {
                    console.log(" - ID:", $(this).val(), "Texto:", $(this).text());
                });
            }
        }
        
        console.log("=== FIM DA SOLUÇÃO RADICAL ===");
    }, 1500);
    
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
    
    // Forçar seleção do estado após carregamento completo
    setTimeout(function() {
        var estadoId = $estado.data('selected-state');
        if (estadoId) {
            console.log("FORÇANDO seleção do estado ID:", estadoId);
            
            // Forçar seleção via DOM
            document.getElementById('estado').value = estadoId;
            
            // Atualizar interface Select2
            if ($.fn.select2 && $estado.hasClass('select2-hidden-accessible')) {
                var estadoTexto = $estado.find('option:selected').text();
                $estado.select2('destroy').select2({
                    width: '100%',
                    placeholder: "Selecione...",
                    allowClear: true
                });
                
                // Forçar atualização do texto visível no Select2
                setTimeout(function() {
                    $estado.next('.select2-container').find('.select2-selection__rendered').text(estadoTexto);
                }, 50);
            }
        }
    }, 1000);
    
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
        
        // Verificar se há um ID de estado pré-selecionado
        var estadoSelecionadoId = $estado.data('selected-state');
        if (estadoSelecionadoId) {
            console.log("ID do estado pré-selecionado:", estadoSelecionadoId);
        }
        
        // Desabilitar país e estado inicialmente
        $pais.prop('disabled', true);
        $estado.prop('disabled', true);
        
        // Configurar seletores com Select2 se disponível
        if ($.fn.select2) {
            inicializarSelect2();
        }
        
        // Aplicar visibilidade inicial com base no âmbito atual
        atualizarCamposVisibilidade();
        
        // Tentar restaurar estado salvo automaticamente
        setTimeout(function() {
            restaurarEstadoSalvo();
        }, 500);
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
        
        // COMENTADO: Não inicializar o estado aqui, pois agora é feito diretamente no HTML
        // para garantir que o valor selected seja respeitado
        /*
        $estado.select2({
            width: '100%',
            placeholder: "Selecione...",
            allowClear: true
        });
        */
    }
    
    // Atualiza a visibilidade/disponibilidade dos campos com base no âmbito
    function atualizarCamposVisibilidade() {
        var ambitoTexto = $ambito.find('option:selected').text().trim().toLowerCase();
        console.log("Atualizando campos por âmbito:", ambitoTexto);
        
        // IMPORTANTE: Preservar ID do estado antes de qualquer operação
        var estadoId = $estado.val() || $estado.data('selected-state') || $estado.attr('data-selected-state');
        console.log("ID do estado a preservar:", estadoId);
        
        // Limpar apenas país, NÃO limpar estado se houver um valor selecionado
        limparSelect($pais);
        if (!estadoId) {
            limparSelect($estado);
        }
        
        // Lógica específica por âmbito
        switch(ambitoTexto) {
            case 'estadual':
                // Para âmbito estadual:
                // Continente: habilitado
                // País: depende de ter continente selecionado
                // Estado: depende de ter país selecionado
                $continente.prop('disabled', false);
                $pais.prop('disabled', !$continente.val());
                
                // NÃO desabilitar o estado se ele tiver um valor selecionado
                if (!estadoId) {
                    $estado.prop('disabled', true); // Apenas inicia desabilitado se não tiver valor
                }
                
                // Se tem continente selecionado, preparar lista de países
                if ($continente.val()) {
                    preencherPaisesPorContinente($continente.val(), true); // true = preservar estado
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
    function preencherPaisesPorContinente(continenteId, preservarEstado) {
        console.log("Preenchendo países para o continente ID:", continenteId);
        
        if (!continenteId) return;
        
        // IMPORTANTE: Preservar ID do estado antes de qualquer operação
        var estadoId = $estado.val() || $estado.data('selected-state') || $estado.attr('data-selected-state');
        if (preservarEstado && estadoId) {
            console.log("Preservando estado ID:", estadoId);
        }
        
        // Remover Select2 temporariamente se estiver ativo
        var temSelect2 = $.fn.select2 && $pais.hasClass('select2-hidden-accessible');
        if (temSelect2) {
            $pais.select2('destroy');
        }
        
        // Guardar o país atual selecionado para tentar restaurá-lo depois
        var paisAtual = $pais.val();
        console.log("País atualmente selecionado:", paisAtual);
        
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
        
        console.log("Total de países encontrados:", totalPaises);
        
        // Habilitar o campo de país se tivermos países disponíveis
        $pais.prop('disabled', totalPaises === 0);
        
        // Tentar restaurar o país selecionado anteriormente, se estiver disponível
        if (paisAtual && $pais.find('option[value="' + paisAtual + '"]').length > 0) {
            $pais.val(paisAtual);
            console.log("País restaurado:", paisAtual);
            
            // Se o país foi restaurado e NÃO estamos preservando o estado, recarregar os estados
            if (!preservarEstado) {
                preencherEstadosPorPais(paisAtual);
            }
        } else {
            // Se não conseguimos restaurar o país e NÃO estamos preservando o estado, limpar o campo
            if (!preservarEstado && !estadoId) {
                limparSelect($estado);
                console.log("País não pôde ser restaurado, estado foi limpo");
            } else {
                console.log("País não pôde ser restaurado, mas estado foi preservado");
            }
        }
        
        // Restaurar Select2 se estava ativo
        if (temSelect2) {
            $pais.select2({
                width: '100%',
                placeholder: "Selecione...",
                allowClear: true
            });
        }
        
        // Se estamos preservando o estado, garantir que ele continue visível
        if (preservarEstado && estadoId) {
            // Garantir que o estado permaneça com seu valor e habilitado
            setTimeout(function() {
                forcarSelecaoEstado(estadoId);
            }, 100);
        }
    }
    
    // Preenche o select de estados baseado no país selecionado
    function preencherEstadosPorPais(paisId) {
        console.log("Preenchendo estados para o país ID:", paisId);
        
        if (!paisId) return;
        
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
        
        console.log("Total de estados encontrados:", totalEstados);
        
        // Reabilitar o campo se tiver estados disponíveis
        var ambitoTexto = $ambito.find('option:selected').text().trim().toLowerCase();
        if (ambitoTexto === 'estadual') {
            $estado.prop('disabled', totalEstados === 0);
        }
        
        // Se tiver apenas um estado, pré-selecionar automaticamente
        if (totalEstados === 1) {
            $estado.val($estado.find('option:not([value=""])').val());
        }
        
        // Verificar se já existe um estado selecionado no campo
        var estadoSelecionadoId = $estado.attr('data-selected-state');
        if (estadoSelecionadoId) {
            console.log("Tentando restaurar estado selecionado ID:", estadoSelecionadoId);
            // Verificar se o estado selecionado existe nas opções atuais
            if ($estado.find('option[value="' + estadoSelecionadoId + '"]').length > 0) {
                $estado.val(estadoSelecionadoId);
                console.log("Estado restaurado com sucesso");
            } else {
                console.log("Estado selecionado não encontrado nas opções disponíveis");
            }
        }
        
        // Restaurar Select2 se estava ativo
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
    
    // Função para restaurar o estado com base no ID salvo
    function restaurarEstadoSalvo() {
        var estadoId = $estado.data('selected-state') || $estado.attr('data-selected-state');
        if (!estadoId) return false;
        
        console.log("=== RESTAURANDO ESTADO FORÇADAMENTE ===");
        console.log("ID do estado a restaurar:", estadoId);
        
        // Encontrar país do estado
        var paisDoEstado = null;
        $.each(todasOpcoesOriginais.estados, function(i, estado) {
            if (estado.value == estadoId) {
                paisDoEstado = estado.country;
                console.log("Encontrado país ID", paisDoEstado, "do estado ID", estadoId);
                return false; // quebra o loop
            }
        });
        
        if (!paisDoEstado) {
            console.log("Não foi possível encontrar o país do estado", estadoId);
            return false;
        }
        
        // Verificar se o país está disponível para seleção e se está selecionado
        if ($pais.val() != paisDoEstado) {
            console.log("País", paisDoEstado, "ainda não está selecionado, selecionando...");
            
            // Encontrar continente do país
            var continenteDoPais = null;
            $.each(todasOpcoesOriginais.paises, function(i, pais) {
                if (pais.value == paisDoEstado) {
                    continenteDoPais = pais.continent;
                    console.log("Encontrado continente ID", continenteDoPais, "do país ID", paisDoEstado);
                    return false; // quebra o loop
                }
            });
            
            // Selecionar continente primeiro, se necessário
            if (continenteDoPais && $continente.val() != continenteDoPais) {
                console.log("Selecionando continente ID", continenteDoPais);
                $continente.val(continenteDoPais).trigger('change');
                
                // Aguardar mudança de continente para selecionar país
                setTimeout(function() {
                    console.log("Selecionando país ID", paisDoEstado);
                    $pais.val(paisDoEstado).trigger('change');
                    
                    // Aguardar mudança de país para selecionar estado
                    setTimeout(function() {
                        console.log("Selecionando estado ID", estadoId);
                        forcarSelecaoEstado(estadoId);
                    }, 300);
                }, 300);
            } else {
                // Selecionar país diretamente se continente já estiver certo
                console.log("Selecionando país ID", paisDoEstado);
                $pais.val(paisDoEstado).trigger('change');
                
                // Aguardar mudança de país para selecionar estado
                setTimeout(function() {
                    console.log("Selecionando estado ID", estadoId);
                    forcarSelecaoEstado(estadoId);
                }, 300);
            }
        } else {
            // País já está selecionado, apenas selecionar estado
            console.log("País já selecionado, selecionando estado ID", estadoId);
            forcarSelecaoEstado(estadoId);
        }
        
        return true;
    }
    
    // Função para forçar a seleção do estado incluindo a interface do Select2
    function forcarSelecaoEstado(estadoId) {
        if (!estadoId) return;
        
        console.log("Forçando seleção do estado ID:", estadoId);
        
        // Verificar se estado existe nas opções disponíveis
        if ($estado.find('option[value="' + estadoId + '"]').length === 0) {
            console.log("Estado ID", estadoId, "não disponível nas opções atuais");
            return;
        }
        
        // 1. Forçar valor diretamente no elemento DOM
        document.getElementById('estado').value = estadoId;
        
        // 2. Garantir que o Select2 seja atualizado
        if ($.fn.select2 && $estado.hasClass('select2-hidden-accessible')) {
            var estadoTexto = $estado.find('option[value="' + estadoId + '"]').text();
            console.log("Texto do estado a selecionar:", estadoTexto);
            
            $estado.select2('destroy').select2({
                width: '100%',
                placeholder: "Selecione...",
                allowClear: true
            });
            
            // Forçar atualização do texto visível
            setTimeout(function() {
                $estado.next('.select2-container').find('.select2-selection__rendered').text(estadoTexto);
                console.log("Texto visível do Select2 atualizado para:", estadoTexto);
            }, 50);
        }
    }
}); 