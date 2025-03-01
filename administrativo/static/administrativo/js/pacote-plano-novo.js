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
    $('#datetimepicker, #datetimepicker2').datetimepicker({
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
        $('#datetimepicker2').datetimepicker('minDate', e.date);
    });
    $("#datetimepicker2").on("change.datetimepicker", function (e) {
        $('#datetimepicker').datetimepicker('maxDate', e.date);
    });

    // Eventos para garantir o formato correto
    $('#datetimepicker, #datetimepicker2').on('change.datetimepicker', function(e) {
        if (e.date) {
            const formattedDate = formatDateToBR(e.date);
            $(this).find('input').val(formattedDate);
            console.log('Data atualizada:', formattedDate); // Debug
        }
    });

    // Handler para mudança no tipo do plano
    function atualizarCamposTipo() {
        var tipo = $('#tipo').val();
        
        console.log('Atualizando campos para o tipo:', tipo);
        
        // Esconde todos os campos especiais sempre
        $('.label-fields, #etiqueta, .date-fields, label[for="etiqueta"]').hide();
        $('#etiqueta').val('');
        
        // Reseta cores para padrão
        $('#id3').colorpicker('setValue', '#FFFFFF');
        $('#id4').colorpicker('setValue', '#CC000C');
        
        // Só mostra campos se tiver um tipo selecionado
        if (tipo === 'Padrão') {
            console.log('Tipo Padrão: mostrando campos de etiqueta');
            $('#etiqueta, label[for="etiqueta"]').show();
            $('.label-fields').show();
        } 
        else if (tipo === 'Promocional') {
            console.log('Tipo Promocional: mostrando campos de etiqueta e data');
            $('#etiqueta, label[for="etiqueta"]').show();
            $('.label-fields').show();
            $('.date-fields').show();
            $('#etiqueta').val('OFERTA ESPECIAL');
            
            // Define valores padrão para as cores
            $('#id3').colorpicker('setValue', '#FFFFFF');
            $('#id4').colorpicker('setValue', '#CC000C');
            
            // Atualiza o visual dos colorpickers
            $('#id3 .input-group-addon i').css('background-color', '#FFFFFF');
            $('#id4 .input-group-addon i').css('background-color', '#CC000C');
            
            console.log('Valores definidos para colorpickers:');
            console.log('Cor texto etiqueta:', $('#id3 input').val());
            console.log('Cor fundo etiqueta:', $('#id4 input').val());
        }
    }

    // Registra o handler de mudança
    $('#tipo').on('change', atualizarCamposTipo);
    
    // Executa a função quando a página carrega
    atualizarCamposTipo();

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
    $('.btn-danger').on('click', function() {
        window.location.href = $('#cancel-url').data('url');
    });

    // Botão Salvar
    $('#btn-salvar').on('click', function() {
        const formData = new FormData();
        
        // Dados básicos
        formData.append('name', $('#nome').val());
        formData.append('plan', $('#plano').val());
        formData.append('billing_cycle', $('#vigencia').val());
        formData.append('enabled', $('#enabled').prop('checked'));
        formData.append('tipo', $('#tipo').val());
        
        // Etiqueta e cores (sempre envia, independente do tipo)
        const etiqueta = $('#etiqueta').val() || '';
        formData.append('label', etiqueta);
        console.log('Valor da etiqueta:', etiqueta);
        
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
        
        // Validação das datas para planos promocionais
        if ($('#tipo').val() === 'Promocional') {
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
            
            if (!startDate) {
                toastr.error('A Data de Início é obrigatória para pacotes promocionais');
                $('#datetimepicker').focus();
                return;
            }
            if (!endDate) {
                toastr.error('A Data de Término é obrigatória para pacotes promocionais');
                $('#datetimepicker2').focus();
                return;
            }
            
            // Adiciona as datas ao formData sem conversão
            formData.append('start_date', startDate);
            formData.append('end_date', endDate);
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
            return;
        }
        if (!$('#preco-padrao').val()) {
            toastr.error('O campo Preço Padrão é obrigatório');
            return;
        }
        if ($('#tipo').val() === 'Promocional') {
            if (!$('#etiqueta').val()) {
                toastr.error('O campo Etiqueta é obrigatório para pacotes promocionais');
                return;
            }
            if (!$('#preco-promocional').val()) {
                toastr.error('O campo Preço Promocional é obrigatório para pacotes promocionais');
                return;
            }
        }

        // Desabilita o botão durante o envio
        const btn = $(this);
        btn.prop('disabled', true);
        
        // Log dos dados antes do envio
        console.log('Dados do FormData:');
        for (let pair of formData.entries()) {
            console.log(pair[0] + ': ' + pair[1]);
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
}); 