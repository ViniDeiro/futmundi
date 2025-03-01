$(document).ready(function() {
    // Setup CSRF token for AJAX requests
    $.ajaxSetup({
        headers: {
            'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
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

    // Função para marcar inputs preenchidos
    function markFilledInputs() {
        $('input, select').each(function() {
            if ($(this).val()) {
                $(this).addClass('filled');
            } else {
                $(this).removeClass('filled');
            }
        });
    }

    // Função para validar e formatar cor
    function validateColor(color) {
        if (!color) return '#000000';
        
        // Remove espaços e converte para minúsculas
        color = color.trim().toLowerCase();
        
        // Se já estiver no formato #RRGGBB, retorna como está
        if (/^#[0-9a-f]{6}$/.test(color)) {
            return color.toUpperCase();
        }
        
        // Se estiver no formato RGB(r,g,b), converte para hex
        var rgbMatch = color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
        if (rgbMatch) {
            var r = parseInt(rgbMatch[1]);
            var g = parseInt(rgbMatch[2]);
            var b = parseInt(rgbMatch[3]);
            return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`.toUpperCase();
        }
        
        // Se for rgba, remove o canal alpha e converte para hex
        var rgbaMatch = color.match(/rgba\((\d+),\s*(\d+),\s*(\d+),\s*[\d.]+\)/);
        if (rgbaMatch) {
            var r = parseInt(rgbaMatch[1]);
            var g = parseInt(rgbaMatch[2]);
            var b = parseInt(rgbaMatch[3]);
            return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`.toUpperCase();
        }
        
        // Se não estiver em nenhum formato válido, retorna preto
        return '#000000';
    }

    // Inicialização dos colorpickers
    $('.colorpicker-component').colorpicker({
        format: 'hex'
    }).on('colorpickerChange', function(event) {
        // Atualiza o valor do input quando a cor mudar
        $(this).find('input').val(event.color.toString());
        console.log('Cor alterada:', $(this).attr('id'), event.color.toString());
    });
    
    // Inicialização do iCheck
    $('.i-checks').iCheck({
        checkboxClass: 'icheckbox_square-green',
        radioClass: 'iradio_square-green'
    });
    
    // Chama a função inicialmente e adiciona evento para inputs
    markFilledInputs();
    $('input, select').on('change keyup', markFilledInputs);
    
    // Preview da imagem
    $('#image').change(function() {
        var file = this.files[0];
        if (file) {
            var reader = new FileReader();
            reader.onload = function(e) {
                $('#image-preview').attr('src', e.target.result);
            }
            reader.readAsDataURL(file);
        }
    });
    
    // Controle de visibilidade baseado no tipo
    $('#tipo').change(function() {
        var tipo = $(this).val();
        
        if (tipo === '') {
            // Quando for Selecione, oculta todos os campos
            $('.date-fields').hide();
            $('.label-fields').hide();
            $('#etiqueta').closest('.row').hide();
        } else if (tipo === 'Padrão') {
            // Quando for Padrão, mostra etiqueta mas oculta campos de data
            $('.date-fields').hide();
            $('.label-fields').show();
            $('#etiqueta').closest('.row').show();
        } else if (tipo === 'Promocional') {
            // Quando for Promocional, mostra todos os campos e define valores padrão
            $('.date-fields').show();
            $('.label-fields').show();
            $('#etiqueta').closest('.row').show();
            
            // Define valores padrão para a etiqueta
            $('#etiqueta').val('OFERTA ESPECIAL');
            $('#id3 input').val('#FFFFFF');
            $('#id4 input').val('#CC000C');
            
            // Atualiza a visualização dos colorpickers
            $('#id3').colorpicker('setValue', '#FFFFFF');
            $('#id4').colorpicker('setValue', '#CC000C');
        }
    });
    
    // Dispara o evento change do tipo para configurar visibilidade inicial
    $('#tipo').trigger('change');
    
    // Inicialização dos datepickers
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
        }
    });
    
    // Salvar plano
    $('#btn-salvar').click(function() {
        var $btn = $(this);
        
        // Validação dos campos obrigatórios
        var nome = $('#nome').val();
        var plano = $('#plano').val();
        var vigencia = $('#vigencia').val();
        var tipo = $('#tipo').val();
        var precoPadrao = $('#preco-padrao').val();
        var precoPromocional = $('#preco-promocional').val();
        
        // Verifica campos obrigatórios
        if (!nome) {
            toastr.error('O campo Nome é obrigatório');
            $('#nome').focus();
            return;
        }
        if (!plano) {
            toastr.error('O campo Plano é obrigatório');
            $('#plano').focus();
            return;
        }
        if (!vigencia) {
            toastr.error('O campo Vigência é obrigatório');
            $('#vigencia').focus();
            return;
        }
        if (!tipo) {
            toastr.error('O campo Tipo é obrigatório');
            $('#tipo').focus();
            return;
        }
        if (!precoPadrao) {
            toastr.error('O campo Preço Padrão é obrigatório');
            $('#preco-padrao').focus();
            return;
        }
        
        // Validação das datas para pacotes promocionais
        var dataInicio = $('#datetimepicker').val();
        var dataTermino = $('#datetimepicker2').val();
        
        if (tipo === 'Promocional') {
            if (!dataInicio) {
                toastr.error('A Data de Início é obrigatória para pacotes promocionais');
                $('#datetimepicker').focus();
                return;
            }
            if (!dataTermino) {
                toastr.error('A Data de Término é obrigatória para pacotes promocionais');
                $('#datetimepicker2').focus();
                return;
            }
        }
        
        if (dataInicio && dataTermino) {
            try {
                var inicio = moment(dataInicio, 'DD/MM/YYYY HH:mm');
                var termino = moment(dataTermino, 'DD/MM/YYYY HH:mm');
                if (inicio.isAfter(termino)) {
                    toastr.error('A data de início não pode ser posterior à data de término');
                    return;
                }
            } catch (e) {
                console.error('Erro ao validar datas:', e);
                toastr.error('Formato de data inválido. Use DD/MM/YYYY HH:mm');
                return;
            }
        }

        // Adiciona os dados do formulário
        var formData = new FormData();
        formData.append('name', nome);
        formData.append('plan', document.getElementById('plano').value);
        formData.append('billing_cycle', document.getElementById('vigencia').value);
        formData.append('enabled', document.getElementById('enabled').checked);
        formData.append('tipo', document.getElementById('tipo').value);
        
        // Campo da Etiqueta e cores
        var tipo = document.getElementById('tipo').value;
        var etiqueta = document.getElementById('etiqueta').value;
        
        // Se for tipo Promocional, a etiqueta é obrigatória
        if (tipo === 'Promocional' && !etiqueta) {
            toastr.error('O campo Etiqueta é obrigatório para pacotes promocionais');
            return;
        }
        
        formData.append('label', etiqueta);
        
        // Obtém os valores dos colorpickers - Testando diferentes métodos
        var corTextoEtiqueta, corFundoEtiqueta;
        
        // Método 1: Obter diretamente do input
        var corTextoInput = $('#id3 input').val();
        var corFundoInput = $('#id4 input').val();
        
        // Método 2: Obter do colorpicker
        try {
            var corTextoColorpicker = $('#id3').colorpicker('getValue');
            var corFundoColorpicker = $('#id4').colorpicker('getValue');
        } catch (e) {
            console.error('Erro ao obter valor do colorpicker:', e);
            var corTextoColorpicker = null;
            var corFundoColorpicker = null;
        }
        
        // Método 3: Obter do atributo value do input
        var corTextoAttr = $('#id3 input').attr('value');
        var corFundoAttr = $('#id4 input').attr('value');
        
        // Método 4: Obter do estilo do addon
        var corTextoAddon = $('#id3 .input-group-append i').css('background-color');
        var corFundoAddon = $('#id4 .input-group-append i').css('background-color');
        
        // Método 5: Obter do data-color do colorpicker
        var corTextoData = $('#id3').data('colorpicker') ? $('#id3').data('colorpicker').color.toString() : null;
        var corFundoData = $('#id4').data('colorpicker') ? $('#id4').data('colorpicker').color.toString() : null;
        
        console.log('Método 1 - Input value:', corTextoInput, corFundoInput);
        console.log('Método 2 - Colorpicker getValue:', corTextoColorpicker, corFundoColorpicker);
        console.log('Método 3 - Input attr value:', corTextoAttr, corFundoAttr);
        console.log('Método 4 - Addon background-color:', corTextoAddon, corFundoAddon);
        console.log('Método 5 - Data color:', corTextoData, corFundoData);
        
        // Usar o primeiro método disponível
        corTextoEtiqueta = corTextoInput || corTextoColorpicker || corTextoAttr || corTextoData || corTextoAddon || '#FFFFFF';
        corFundoEtiqueta = corFundoInput || corFundoColorpicker || corFundoAttr || corFundoData || corFundoAddon || '#CC000C';
        
        console.log('Elementos colorpicker:', $('#id3').length, $('#id4').length);
        console.log('Inputs dentro dos colorpickers:', $('#id3 input').length, $('#id4 input').length);
        console.log('Valores finais - Cor do texto da etiqueta:', corTextoEtiqueta);
        console.log('Valores finais - Cor de fundo da etiqueta:', corFundoEtiqueta);
        
        formData.append('color_text_label', validateColor(corTextoEtiqueta));
        formData.append('color_background_label', validateColor(corFundoEtiqueta));
        
        // Preços
        formData.append('full_price', precoPadrao.replace(',', '.'));
        if (precoPromocional) {
            formData.append('promotional_price', precoPromocional.replace(',', '.'));
        }
        
        // Datas
        if (dataInicio) formData.append('start_date', dataInicio);
        if (dataTermino) formData.append('end_date', dataTermino);
        
        formData.append('show_to', document.getElementById('exibir-para').value);
        
        // Códigos dos produtos
        var androidCode = document.getElementById('codigo-android').value;
        var appleCode = document.getElementById('codigo-apple').value;
        formData.append('android_product_code', androidCode || '');
        formData.append('apple_product_code', appleCode || '');

        // Debug - Mostrando os valores específicos no console
        console.log('Dados do FormData:');
        for (let pair of formData.entries()) {
            console.log(pair[0] + ': ' + pair[1]);
        }

        // Adiciona a imagem se houver
        var imageFile = document.getElementById('image').files[0];
        if (imageFile) {
            formData.append('image', imageFile);
        }

        $btn.prop('disabled', true);

        // Envia os dados
        $.ajax({
            url: window.location.pathname,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.success) {
                    toastr.success(response.message);
                    setTimeout(function() {
                        window.location.href = $('#cancel-url').data('url');
                    }, 1500);
                } else {
                    console.error('Erro na resposta:', response);
                    toastr.error(response.message || 'Erro ao salvar plano');
                    $btn.prop('disabled', false);
                }
            },
            error: function(xhr, status, error) {
                console.error('Erro na requisição:', error);
                console.error('Status:', xhr.status);
                console.error('Resposta:', xhr.responseText);
                toastr.error('Erro ao salvar plano');
                $btn.prop('disabled', false);
            }
        });
    });
    
    // Botão cancelar
    $('.btn-danger').click(function() {
        window.location.href = $('#cancel-url').data('url');
    });
}); 