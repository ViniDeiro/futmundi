$(document).ready(function() {
    // Setup CSRF token for AJAX requests
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
        headers: {
            'X-CSRFToken': csrftoken
        }
    });

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

    // Inicializa os colorpickers
    $('.colorpicker-component').colorpicker();

    // Inicializa os datetimepickers
    moment.locale('pt-br');

    // Função para formatar a data no padrão brasileiro
    function formatDateToBR(date) {
        if (!date) return '';
        return moment(date).format('DD/MM/YYYY HH:mm');
    }

    // Função para converter data do formato DD/MM/YYYY HH:mm para YYYY-MM-DD HH:mm
    function convertDateFormat(dateStr) {
        console.log('Data original:', dateStr); // Debug
        
        if (!dateStr || dateStr.trim() === '') {
            console.log('Data vazia ou nula'); // Debug
            return null;
        }
        
        try {
            // Converte a data usando moment.js com parsing estrito
            const momentDate = moment(dateStr, 'DD/MM/YYYY HH:mm', true);
            
            if (!momentDate.isValid()) {
                console.error('Data inválida:', dateStr);
                toastr.error('Data inválida. Use o formato DD/MM/YYYY HH:mm (exemplo: 26/02/2025 19:48)');
                return null;
            }
            
            // Formata no padrão do Django
            const formattedDate = momentDate.format('YYYY-MM-DD HH:mm');
            console.log('Data convertida:', formattedDate); // Debug
            
            return formattedDate;
        } catch (error) {
            console.error('Erro ao converter data:', error);
            toastr.error('Erro ao processar a data. Use o formato DD/MM/YYYY HH:mm');
            return null;
        }
    }

    // Configuração dos datetimepickers
    // Inicializando um de cada vez para evitar conflitos
    $('#datetimepicker').datetimepicker({
        format: 'DD/MM/YYYY HH:mm',
        locale: 'pt-br',
        icons: {
            time: 'fa fa-clock-o',
            date: 'fa fa-calendar',
            up: 'fa fa-chevron-up',
            down: 'fa fa-chevron-down',
            previous: 'fa fa-chevron-left',
            next: 'fa fa-chevron-right',
            today: 'fa fa-screenshot',
            clear: 'fa fa-trash',
            close: 'fa fa-remove'
        },
        stepping: 5,
        sideBySide: true,
        useCurrent: false
    });
    
    $('#datetimepicker2').datetimepicker({
        format: 'DD/MM/YYYY HH:mm',
        locale: 'pt-br',
        icons: {
            time: 'fa fa-clock-o',
            date: 'fa fa-calendar',
            up: 'fa fa-chevron-up',
            down: 'fa fa-chevron-down',
            previous: 'fa fa-chevron-left',
            next: 'fa fa-chevron-right',
            today: 'fa fa-screenshot',
            clear: 'fa fa-trash',
            close: 'fa fa-remove'
        },
        stepping: 5,
        sideBySide: true,
        useCurrent: false
    });

    // Lógica para garantir que a data final não seja menor que a inicial
    $("#datetimepicker").on("change.datetimepicker", function (e) {
        if (e.date) {
            $('#datetimepicker2').datetimepicker('minDate', e.date);
        }
    });
    
    $("#datetimepicker2").on("change.datetimepicker", function (e) {
        if (e.date) {
            $('#datetimepicker').datetimepicker('maxDate', e.date);
        }
    });

    // Controle de visibilidade baseado no tipo
    $('#tipo').change(function() {
        var tipo = $(this).val();
        
        if (tipo === '') {
            // Quando for Selecione, oculta todos os campos
            $('.date-fields').hide();
            $('.label-fields').hide();
            $('.beneficio-fields').hide();
            $('.novos-usuarios-fields').hide();
            $('#etiqueta').closest('.form-group').hide();
            $('#bloco-beneficio-futcoins').hide();
        } else if (tipo === 'Padrão') {
            // Quando for Padrão, mostra etiqueta mas oculta campos de data
            $('.date-fields').hide();
            $('.label-fields').show();
            $('.beneficio-fields').hide();
            $('.novos-usuarios-fields').hide();
            $('#etiqueta').closest('.form-group').show();
            $('#bloco-beneficio-futcoins').hide();
            
            // Limpa os valores da etiqueta
            $('#etiqueta').val('');
            
            // Define as cores e atualiza os colorpickers
            setTimeout(function() {
                $('#id3 input').val('#FFFFFF');
                $('#id4 input').val('#FFFFFF');
                $('#id3').colorpicker('setValue', '#FFFFFF');
                $('#id4').colorpicker('setValue', '#FFFFFF');
                
                // Atualiza também o fundo do indicador de cor
                $('#id3 .input-group-addon i').css('background-color', '#FFFFFF');
                $('#id4 .input-group-addon i').css('background-color', '#FFFFFF');
            }, 100);
        } else if (tipo === 'Promocional') {
            // Quando for Promocional, mostra todos os campos e define valores padrão
            $('.date-fields').show();
            $('.label-fields').show();
            $('.beneficio-fields').hide();
            $('.novos-usuarios-fields').hide();
            $('#etiqueta').closest('.form-group').show();
            $('#bloco-beneficio-futcoins').hide();
            
            // Define valores padrão para a etiqueta
            $('#etiqueta').val('OFERTA ESPECIAL');
            
            // Define as cores e atualiza os colorpickers
            setTimeout(function() {
                $('#id3 input').val('#FFFFFF');
                $('#id4 input').val('#CC000C');
                $('#id3').colorpicker('setValue', '#FFFFFF');
                $('#id4').colorpicker('setValue', '#CC000C');
                
                // Atualiza também o fundo do indicador de cor
                $('#id3 .input-group-addon i').css('background-color', '#FFFFFF');
                $('#id4 .input-group-addon i').css('background-color', '#CC000C');
            }, 100);
        } else if (tipo === 'Novos Jogadores') {
            // Quando for Novos Jogadores, mostra campos específicos
            $('.date-fields').hide(); // Oculta campos de data
            $('.label-fields').show();
            $('.beneficio-fields').hide();
            $('.novos-usuarios-fields').show();
            $('#etiqueta').closest('.form-group').show();
            $('#bloco-beneficio-futcoins').show();
            
            // Define valores padrão para a etiqueta
            $('#etiqueta').val('NOVOS JOGADORES');
            
            // Define as cores e atualiza os colorpickers
            setTimeout(function() {
                $('#id3 input').val('#FFFFFF');
                $('#id4 input').val('#CCA53F');
                $('#id3').colorpicker('setValue', '#FFFFFF');
                $('#id4').colorpicker('setValue', '#CCA53F');
                
                // Atualiza também o fundo do indicador de cor
                $('#id3 .input-group-addon i').css('background-color', '#FFFFFF');
                $('#id4 .input-group-addon i').css('background-color', '#CCA53F');
            }, 100);
            
            // Define valores padrão para os campos específicos
            $('#dias-promocao').val(30);
            
            // Carrega os pacotes de futcoins ativos em ordem alfabética
            carregarPacotesFutcoins();
            
            $('#renovacoes-pacote').val(1);
            
            // Garante que não haja valores negativos
            $('#dias-promocao, #renovacoes-pacote').on('input', function() {
                var value = parseInt($(this).val());
                if (value < 0 || isNaN(value)) {
                    $(this).val(1);
                }
            });
        }
    });

    // Dispara o evento change do tipo para configurar visibilidade inicial
    $('#tipo').trigger('change');

    // Preview da imagem
    $('#image').on('change', function() {
        const file = this.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                $('#image-preview').html(`
                    <img src="${e.target.result}" style="width: 48px; height: 48px; object-fit: contain; cursor: pointer;" onclick="document.getElementById('image').click()">
                    <button type="button" class="btn btn-danger btn-xs" id="remove_image_btn" style="position: absolute; bottom: -7px; right: -30px;">
                        <i class="fa fa-trash"></i>
                    </button>
                `);
                $('#image-preview').css('margin-top', '-7px');
            }
            reader.readAsDataURL(file);
        }
    });

    // Remover imagem
    $(document).on('click', '#remove_image_btn', function() {
        $('#image').val('');
        $('#should_remove_image').val('yes');
        $('#image-preview').html('<i class="fa fa-file-image-o" style="font-size: 48px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>');
    });

    // Botão Cancelar
    $('.btn-danger').click(function() {
        // Redireciona para a URL de cancelamento
        window.location.href = $('#cancel-url').data('url');
    });

    // Botão Salvar
    $('#btn-salvar').click(function() {
        // Cria um objeto FormData para enviar os dados, incluindo arquivos
        var formData = new FormData();
        
        // Dados do pacote
        var nome = $('#nome').val();
        var enabled = $('#enabled').is(':checked');
        var tipo = $('#tipo').val();
        
        // Converter o valor "Novos Jogadores" para um valor válido no backend
        if (tipo === 'Novos Jogadores') {
            console.log('Convertendo "Novos Jogadores" para valor válido aceito pelo backend');
            tipo = 'Dias Promoção Novos Jogadores'; // Valor que o backend aceita
        }
        
        var plano = $('#plano').val();
        var ciclo = $('#vigencia').val();
        var etiqueta = $('#etiqueta').val();
        
        // Log dos valores para depuração
        console.log('--- DEPURAÇÃO DOS CAMPOS ---');
        console.log('Nome:', nome);
        console.log('Enabled:', enabled);
        console.log('Tipo selecionado:', $('#tipo').val());
        console.log('Tipo (package_type) enviado:', tipo);
        console.log('Plano:', plano);
        console.log('Ciclo de Faturamento (billing_cycle):', ciclo);
        console.log('Etiqueta:', etiqueta);
        console.log('Elementos no DOM:');
        console.log('- #nome existe:', $('#nome').length > 0);
        console.log('- #enabled existe:', $('#enabled').length > 0);
        console.log('- #tipo existe:', $('#tipo').length > 0);
        console.log('- #plano existe:', $('#plano').length > 0);
        console.log('- #vigencia existe:', $('#vigencia').length > 0);
        console.log('- #etiqueta existe:', $('#etiqueta').length > 0);
        
        formData.append('name', nome);
        formData.append('enabled', enabled);
        
        // Garantir que o tipo seja enviado com ambos os nomes possíveis
        // para compatibilidade com o backend
        formData.append('package_type', tipo);
        formData.append('tipo', tipo);  // Adiciona uma cópia com este nome alternativo
        
        // Log dos campos de package_type
        console.log('Valor final do package_type:', tipo);
        console.log('Valor no DOM (#tipo):', $('#tipo').val());
        
        formData.append('plan', plano);
        formData.append('billing_cycle', ciclo);
        formData.append('label', etiqueta);
        
        // Validação para package_type e billing_cycle (campos que estavam faltando)
        if (!tipo) {
            toastr.error('O campo Tipo é obrigatório');
            $('#tipo').focus();
            return;
        }
        
        if (!ciclo) {
            toastr.error('O campo Vigência é obrigatório');
            $('#vigencia').focus();
            return;
        }
        
        // Obter os valores diretamente dos inputs dentro dos colorpickers
        const colorTextLabelRaw = $('#id3 input').val();
        const colorBackgroundLabelRaw = $('#id4 input').val();
        
        console.log('Valores brutos dos colorpickers:');
        console.log('Cor texto etiqueta (raw):', colorTextLabelRaw);
        console.log('Cor fundo etiqueta (raw):', colorBackgroundLabelRaw);
        
        // Garante que as cores estejam no formato hexadecimal correto
        var colorTextLabel = validateColor(colorTextLabelRaw);
        var colorBackgroundLabel = validateColor(colorBackgroundLabelRaw);
        var colorTextBillingCycle = $('#id5').length ? validateColor($('#id5 input').val()) : '#192639';
        
        console.log('Valores dos colorpickers após validação:');
        console.log('Cor texto etiqueta:', colorTextLabelRaw, '→', colorTextLabel);
        console.log('Cor fundo etiqueta:', colorBackgroundLabelRaw, '→', colorBackgroundLabel);
        
        // Verifica se as cores estão no formato correto antes de enviar
        if (!/^#[0-9A-Fa-f]{6}$/.test(colorTextLabel)) {
            colorTextLabel = '#FFFFFF'; // Valor padrão se inválido
            console.log('Cor texto etiqueta inválida, usando padrão:', colorTextLabel);
        }
        if (!/^#[0-9A-Fa-f]{6}$/.test(colorBackgroundLabel)) {
            colorBackgroundLabel = '#CC000C'; // Valor padrão se inválido
            console.log('Cor fundo etiqueta inválida, usando padrão:', colorBackgroundLabel);
        }
        if (!/^#[0-9A-Fa-f]{6}$/.test(colorTextBillingCycle)) {
            colorTextBillingCycle = '#192639'; // Valor padrão se inválido
        }
        
        // Adiciona o token CSRF explicitamente
        formData.append('csrfmiddlewaretoken', $('meta[name="csrf-token"]').attr('content'));
        
        // Adiciona as cores ao formData
        formData.append('color_text_label', colorTextLabel);
        formData.append('color_background_label', colorBackgroundLabel);
        
        // Preços
        formData.append('full_price', $('#preco-padrao').val());
        formData.append('promotional_price', $('#preco-promocional').val());
        formData.append('promotional_price_validity', $('#val-preco-prom').val());
        
        // Configurações adicionais
        formData.append('color_text_billing_cycle', colorTextBillingCycle);
        formData.append('show_to', $('#exibir-para').val());
        formData.append('android_product_code', $('#codigo-android').val() || '');
        formData.append('apple_product_code', $('#codigo-apple').val() || '');
        
        // Validação das datas para pacotes promocionais e Dias Promoção Novos Jogadores
        if ($('#tipo').val() === 'Promocional' || $('#tipo').val() === 'Novos Jogadores' || tipo === 'Dias Promoção Novos Jogadores') {
            var startDate = $('#datetimepicker').val();
            var endDate = $('#datetimepicker2').val();
            
            console.log('Valores das datas:', {
                startDate: startDate,
                endDate: endDate,
                startDateElement: $('#datetimepicker').length,
                endDateElement: $('#datetimepicker2').length,
                startDateValue: $('#datetimepicker').val(),
                endDateValue: $('#datetimepicker2').val()
            });
            
            // Para o tipo "Novos Jogadores", definir datas padrão se não estiverem preenchidas
            if ($('#tipo').val() === 'Novos Jogadores' && (!startDate || !endDate)) {
                console.log('Definindo datas padrão para Novos Jogadores');
                
                // Data de início: hoje
                var hoje = moment().format('DD/MM/YYYY HH:mm');
                
                // Data de término: 1 ano no futuro
                var umAnoFuturo = moment().add(1, 'year').format('DD/MM/YYYY HH:mm');
                
                if (!startDate) {
                    startDate = hoje;
                    $('#datetimepicker').val(startDate);
                    console.log('Data de início definida como:', startDate);
                }
                
                if (!endDate) {
                    endDate = umAnoFuturo;
                    $('#datetimepicker2').val(endDate);
                    console.log('Data de término definida como:', endDate);
                }
            } else {
                // Validação normal para outros tipos
                if (!startDate) {
                    toastr.error('A Data de Início é obrigatória para este tipo de pacote');
                    $('#datetimepicker').focus();
                    return;
                }
                if (!endDate) {
                    toastr.error('A Data de Término é obrigatória para este tipo de pacote');
                    $('#datetimepicker2').focus();
                    return;
                }
            }
            
            // Adiciona as datas ao formData
            formData.append('start_date', startDate);
            formData.append('end_date', endDate);
        }
        
        // Validação específica por tipo
        if ($('#tipo').val() === 'Promocional' || $('#tipo').val() === 'Novos Jogadores') {
            if (!$('#etiqueta').val()) {
                toastr.error('O campo Etiqueta é obrigatório para este tipo de pacote');
                $('#etiqueta').focus();
                return;
            }
        }
        
        // Validação específica para Novos Jogadores
        if ($('#tipo').val() === 'Novos Jogadores') {
            var diasPromocao = $('#dias-promocao').val();
            var beneficioFutcoins = $('#beneficio-futcoins').val();
            var qtdRenovacoesNovos = $('#renovacoes-pacote').val();
            
            if (!diasPromocao) {
                toastr.error('O campo Dias Promoção é obrigatório para este tipo de pacote');
                $('#dias-promocao').focus();
                return;
            }
            if (!beneficioFutcoins) {
                toastr.error('O campo Benefício Pacote Futcoins é obrigatório para este tipo de pacote');
                $('#beneficio-futcoins').focus();
                return;
            }
            if (!qtdRenovacoesNovos) {
                toastr.error('O campo Qtde Renovações Pacote é obrigatório para este tipo de pacote');
                $('#renovacoes-pacote').focus();
                return;
            }
            
            // Verifica se os valores são positivos
            if (parseInt(diasPromocao) <= 0) {
                toastr.error('O campo Dias Promoção deve ser maior que zero');
                $('#dias-promocao').focus();
                return;
            }
            if (parseInt(qtdRenovacoesNovos) <= 0) {
                toastr.error('O campo Qtde Renovações Pacote deve ser maior que zero');
                $('#renovacoes-pacote').focus();
                return;
            }
            
            // Adiciona os campos específicos ao formData
            formData.append('promotion_days', diasPromocao);
            formData.append('futcoins_package_benefit', beneficioFutcoins);
            formData.append('package_renewals', qtdRenovacoesNovos);
        }
        
        // Imagem
        const imageFile = $('#image')[0].files[0];
        if (imageFile) {
            formData.append('image', imageFile);
        }
        
        // Adiciona o campo para remoção de imagem
        formData.append('should_remove_image', $('#should_remove_image').val());

        // Validação dos campos obrigatórios
        if (!$('#nome').val()) {
            toastr.error('O campo Nome é obrigatório');
            $('#nome').focus();
            return;
        }
        if (!$('#tipo').val()) {
            toastr.error('O campo Tipo é obrigatório');
            $('#tipo').focus();
            return;
        }
        if (!$('#preco-padrao').val()) {
            toastr.error('O campo Preço Padrão é obrigatório');
            $('#preco-padrao').focus();
            return;
        }
        if (!$('#preco-promocional').val()) {
            toastr.error('O campo Preço Promocional é obrigatório');
            $('#preco-promocional').focus();
            return;
        }
        
        // Desabilita o botão durante o envio
        const btn = $(this);
        btn.prop('disabled', true);
        
        // Log dos dados antes do envio
        console.log('Dados do FormData:');
        for (let pair of formData.entries()) {
            console.log(pair[0] + ': ' + pair[1]);
        }
        
        // Verificação final dos campos obrigatórios
        console.log('Verificação final de campos obrigatórios:');
        var temTipo = false;
        var temCiclo = false;
        
        for (let pair of formData.entries()) {
            if ((pair[0] === 'package_type' || pair[0] === 'tipo') && pair[1]) {
                temTipo = true;
                console.log(pair[0] + ' está presente com valor:', pair[1]);
            }
            if (pair[0] === 'billing_cycle' && pair[1]) {
                temCiclo = true;
                console.log('billing_cycle está presente com valor:', pair[1]);
            }
        }
        
        if (!temTipo || !temCiclo) {
            console.error('CAMPOS OBRIGATÓRIOS FALTANDO NA SUBMISSÃO:');
            if (!temTipo) console.error('- package_type/tipo está ausente');
            if (!temCiclo) console.error('- billing_cycle está ausente');
            
            // Adicionando manualmente se estiver faltando
            if (!temTipo && $('#tipo').val()) {
                formData.append('package_type', $('#tipo').val());
                formData.append('tipo', $('#tipo').val());
                console.log('Adicionando package_type e tipo manualmente:', $('#tipo').val());
            }
            if (!temCiclo && $('#vigencia').val()) {
                formData.append('billing_cycle', $('#vigencia').val());
                console.log('Adicionando billing_cycle manualmente:', $('#vigencia').val());
            }
        }
        
        // Envia os dados
        $.ajax({
            url: window.location.pathname,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                console.log('Resposta do servidor:', response);
                if (response.success) {
                    toastr.success(response.message);
                    setTimeout(function() {
                        window.location.href = $('#cancel-url').data('url');
                    }, 1500);
                } else {
                    console.error('Erro na resposta:', response); // Debug
                    toastr.error(response.message || 'Erro ao salvar plano');
                    btn.prop('disabled', false);
                }
            },
            error: function(xhr) {
                console.error('Erro na requisição:', xhr.responseJSON); // Debug
                console.error('Status:', xhr.status);
                console.error('Texto do status:', xhr.statusText);
                console.error('Resposta completa:', xhr.responseText);
                toastr.error(xhr.responseJSON?.message || 'Erro ao salvar plano');
                btn.prop('disabled', false);
            }
        });
    });

    // Função para validar e formatar cores
    function validateColor(color) {
        console.log('Validando cor:', color);
        if (!color) return '#000000';
        
        // Remove espaços e converte para minúsculas
        color = color.trim().toLowerCase();
        console.log('Cor após trim e lowercase:', color);
        
        // Se já estiver no formato #RRGGBB, retorna como está
        if (/^#[0-9a-f]{6}$/.test(color)) {
            console.log('Cor já está no formato #RRGGBB:', color.toUpperCase());
            return color.toUpperCase();
        }
        
        // Se estiver no formato RGB(r,g,b), converte para hex
        let rgbMatch = color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
        if (rgbMatch) {
            let r = parseInt(rgbMatch[1]);
            let g = parseInt(rgbMatch[2]);
            let b = parseInt(rgbMatch[3]);
            let hexColor = '#' + 
                r.toString(16).padStart(2, '0') + 
                g.toString(16).padStart(2, '0') + 
                b.toString(16).padStart(2, '0');
            console.log('Cor convertida de RGB para hex:', hexColor.toUpperCase());
            return hexColor.toUpperCase();
        }
        
        // Se for rgba, remove o canal alpha e converte para hex
        let rgbaMatch = color.match(/rgba\((\d+),\s*(\d+),\s*(\d+),\s*[\d.]+\)/);
        if (rgbaMatch) {
            let r = parseInt(rgbaMatch[1]);
            let g = parseInt(rgbaMatch[2]);
            let b = parseInt(rgbaMatch[3]);
            let hexColor = '#' + 
                r.toString(16).padStart(2, '0') + 
                g.toString(16).padStart(2, '0') + 
                b.toString(16).padStart(2, '0');
            console.log('Cor convertida de RGBA para hex:', hexColor.toUpperCase());
            return hexColor.toUpperCase();
        }
        
        // Se não estiver em nenhum formato válido, retorna preto
        console.log('Formato de cor não reconhecido, retornando preto');
        return '#000000';
    }

    // Inicialização dos color pickers
    $('#id3, #id4, #id5').each(function() {
        $(this).spectrum({
            type: "component",
            showInput: true,
            showInitial: true,
            showAlpha: false,
            allowEmpty: false,
            preferredFormat: "hex",
            change: function(color) {
                $(this).val(color.toHexString().toUpperCase());
            }
        });
    });

    // Função para carregar pacotes de futcoins ativos
    function carregarPacotesFutcoins(callback) {
        console.log('Iniciando carregamento de pacotes futcoins...');
        $.ajax({
            url: '/administrativo/api/pacotes-futcoins-ativos/',
            type: 'GET',
            dataType: 'json',
            success: function(response) {
                if (response.success) {
                    console.log('Pacotes futcoins carregados com sucesso:', response);
                    
                    // Limpa o dropdown e adiciona a opção padrão
                    $('#beneficio-futcoins').empty();
                    $('#beneficio-futcoins').append('<option value="">Selecione um pacote</option>');
                    
                    // Verifica se os pacotes estão em "packages" ou "pacotes"
                    var listaPacotes = response.packages || response.pacotes || [];
                    console.log('Lista de pacotes encontrada:', listaPacotes);
                    
                    // Adiciona os pacotes em ordem alfabética
                    var pacotes = listaPacotes.sort(function(a, b) {
                        return a.name.localeCompare(b.name);
                    });
                    
                    // Adiciona cada pacote ao dropdown
                    pacotes.forEach(function(pacote) {
                        $('#beneficio-futcoins').append(`<option value="${pacote.id}">${pacote.name}</option>`);
                    });
                    
                    console.log('Dropdown de pacotes futcoins preenchido com', pacotes.length, 'pacotes');
                    
                    // Se houver um callback, chama-o após o carregamento
                    if (typeof callback === 'function') {
                        console.log('Chamando callback após carregar pacotes futcoins');
                        callback();
                    }
                } else {
                    console.error('Erro ao carregar pacotes futcoins:', response.message);
                }
            },
            error: function(xhr, status, error) {
                console.error('Erro na requisição de pacotes futcoins:', error);
            }
        });
    }
}); 