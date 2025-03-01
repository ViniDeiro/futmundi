$(document).ready(function() {
    // Configuração do CSRF token para requisições AJAX
    var csrftoken = $('meta[name="csrf-token"]').attr('content');
    
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!(/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type)) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
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
        "showDuration": "400",
        "hideDuration": "1000",
        "timeOut": 4000,
        "extendedTimeOut": "400",
        "showEasing": "swing",
        "hideEasing": "linear",
        "showMethod": 'slideDown'
    };

    // Função para marcar os campos preenchidos
    function markFilledInputs() {
        $('input.form-control, select.form-control').each(function() {
            if ($(this).val() && $(this).val() !== '') {
                $(this).addClass('has-value');
            } else {
                $(this).removeClass('has-value');
            }
        });
    }
    
    // Aplica a marcação inicial e sempre que um campo mudar
    markFilledInputs();
    $(document).on('change keyup', 'input.form-control, select.form-control', markFilledInputs);

    // Manipulação da imagem
    $('#image').on('change', function() {
        var file = this.files[0];
        if (file) {
            if (!file.type.startsWith('image/')) {
                toastr.error('Por favor, selecione apenas arquivos de imagem.');
                this.value = '';
                return;
            }
            
            if (file.size > 2 * 1024 * 1024) {
                toastr.error('A imagem não pode ter mais que 2MB');
                this.value = '';
                return;
            }
            
            var reader = new FileReader();
            reader.onload = function(e) {
                $('#image-preview').html(`
                    <img src="${e.target.result}" style="width: 48px; height: 48px; object-fit: contain; cursor: pointer;" onclick="document.getElementById('image').click()">
                    <button type="button" class="btn btn-danger btn-xs" id="remove_image_btn" style="position: absolute; bottom: -7px; right: -30px;">
                        <i class="fa fa-trash"></i>
                    </button>
                `);
                $('#image-preview').css('margin-top', '-7px');
                
                // Adiciona handler para o botão de remover
                $('#remove_image_btn').on('click', function() {
                    $('#image').val('');
                    $('#image-preview').html('<i class="fa fa-file-image-o" style="font-size: 48px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>');
                });
            }
            reader.readAsDataURL(file);
        }
    });

    // Limpar imagem
    $('.clear-image').click(function() {
        $('.input-image').val('');
        $('.image-preview').html('<i class="fa fa-file-image-o label-content" style="cursor:pointer; font-size: 24px;"></i>');
    });

    // Controle de visibilidade dos campos baseado no tipo
    $('#tipo').change(function() {
        var tipo = $(this).val();
        
        // Esconde todos os campos especiais
        $('.label-fields, #etiqueta, .date-fields').hide();
        
        // Limpa os valores
        $('#etiqueta').val('');
        $('#id3').colorpicker('setValue', '#FFFFFF');
        $('#id4').colorpicker('setValue', '#CC000C');
        
        if (tipo === 'Padrão') {
            // Mostra campos para tipo Padrão
            $('#etiqueta, .label-fields').show();
        } else if (tipo === 'Promocional') {
            // Mostra campos para tipo Promocional
            $('#etiqueta, .label-fields, .date-fields').show();
            
            // Define valores padrão
            $('#etiqueta').val('OFERTA ESPECIAL');
            $('#id3').colorpicker('setValue', '#FFFFFF');
            $('#id4').colorpicker('setValue', '#FF0000');
        }
        
        // Força atualização dos campos
        markFilledInputs();
    });
    
    // Dispara o evento change do tipo para configurar visibilidade inicial
    $(document).ready(function() {
        // Esconde todos os campos especiais inicialmente
        $('.label-fields, #etiqueta, .date-fields').hide();
        
        // Dispara o evento change para configurar baseado no valor inicial
        $('#tipo').trigger('change');
    });

    // Função para validar e formatar cores
    function validateColor(color) {
        if (!color) return '#000000';
        
        // Remove espaços e converte para minúsculas
        color = color.trim().toLowerCase();
        
        // Se já estiver no formato #RRGGBB, retorna como está
        if (/^#[0-9a-f]{6}$/.test(color)) {
            return color.toUpperCase();
        }
        
        // Se estiver no formato RGB(r,g,b), converte para hex
        let rgbMatch = color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
        if (rgbMatch) {
            let r = parseInt(rgbMatch[1]);
            let g = parseInt(rgbMatch[2]);
            let b = parseInt(rgbMatch[3]);
            return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`.toUpperCase();
        }
        
        // Se for rgba, remove o canal alpha e converte para hex
        let rgbaMatch = color.match(/rgba\((\d+),\s*(\d+),\s*(\d+),\s*[\d.]+\)/);
        if (rgbaMatch) {
            let r = parseInt(rgbaMatch[1]);
            let g = parseInt(rgbaMatch[2]);
            let b = parseInt(rgbaMatch[3]);
            return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`.toUpperCase();
        }
        
        // Se não estiver em nenhum formato válido, retorna preto
        return '#000000';
    }

    // Botão Cancelar
    $('.btn-danger').click(function(e) {
        e.preventDefault();
        window.location.href = $('#cancel-url').data('url');
    });

    // Botão Salvar
    $('#btn-salvar').on('click', function() {
        console.log('Botão salvar clicado');
        // Validação dos campos obrigatórios
        var nome = $('#nome').val();
        var precoPadrao = $('#preco-padrao').val();
        var precoPromocional = $('#preco-promocional').val();

        if (!nome) {
            toastr.error('O campo Nome é obrigatório');
            return;
        }
        if (!precoPadrao) {
            toastr.error('O campo Preço Padrão é obrigatório');
            return;
        }

        // Validação do preço promocional
        if (precoPromocional && parseFloat(precoPromocional.replace(',', '.')) >= parseFloat(precoPadrao.replace(',', '.'))) {
            toastr.error('O preço promocional deve ser menor que o preço padrão');
            return;
        }

        // Validação das datas para planos promocionais
        if ($('#tipo').val() === 'Promocional') {
            var dataInicio = $('#datetimepicker').val();
            var dataTermino = $('#datetimepicker2').val();
            
            if (!dataInicio) {
                toastr.error('A data de início é obrigatória para pacotes promocionais');
                return;
            }
            if (!dataTermino) {
                toastr.error('A data de término é obrigatória para pacotes promocionais');
                return;
            }
        }

        // Desabilita o botão durante o envio
        var $btn = $(this);
        $btn.prop('disabled', true);
        
        // Cria o FormData para envio
        var formData = new FormData();
        
        // Adiciona os dados do formulário
        formData.append('name', nome);
        formData.append('plan', $('#plano').val());
        formData.append('billing_cycle', $('#vigencia').val());
        formData.append('enabled', $('#enabled').prop('checked'));
        formData.append('tipo', $('#tipo').val());
        formData.append('label', $('#etiqueta').val() || '');
        
        // Cores
        formData.append('color_text_label', validateColor($('#id3').val() || $('#id3 input').val()));
        formData.append('color_background_label', validateColor($('#id4').val() || $('#id4 input').val()));
        formData.append('color_text_billing_cycle', validateColor($('#id5').val() || $('#id5 input').val()));
        
        // Preços
        formData.append('full_price', precoPadrao.replace(',', '.'));
        formData.append('promotional_price', precoPromocional ? precoPromocional.replace(',', '.') : '');
        formData.append('promotional_price_validity', $('#val-preco-prom').val() || '');
        
        // Datas
        if (dataInicio) formData.append('start_date', dataInicio);
        if (dataTermino) formData.append('end_date', dataTermino);
        
        // Outros campos
        formData.append('show_to', $('#exibir-para').val());
        formData.append('android_product_code', $('#codigo-android').val() || '');
        formData.append('apple_product_code', $('#codigo-apple').val() || '');
        
        // Imagem
        var imageFile = $('#image')[0].files[0];
        if (imageFile) {
            formData.append('image', imageFile);
        }
        
        // Envia os dados
        $.ajax({
            url: window.location.pathname,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
            },
            success: function(response) {
                if (response.success) {
                    toastr.success(response.message);
                    setTimeout(function() {
                        window.location.href = $('#cancel-url').data('url');
                    }, 1500);
                } else {
                    toastr.error(response.message || 'Erro ao salvar plano');
                    $btn.prop('disabled', false);
                }
            },
            error: function(xhr) {
                toastr.error(xhr.responseJSON?.message || 'Erro ao salvar plano');
                $btn.prop('disabled', false);
            }
        });
    });

    // Inicialização dos componentes
    $('.i-checks').iCheck({
        checkboxClass: 'icheckbox_square-green',
        radioClass: 'iradio_square-green'
    });

    // Inicialização dos colorpickers
    $('#id3, #id4, #id5').colorpicker({
        format: 'hex'
    }).on('colorpickerChange', function(event) {
        // Atualiza o valor do input quando a cor mudar
        $(this).find('input').val(event.color.toString());
    });

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

    // Inicializa os color pickers com formato fixo
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