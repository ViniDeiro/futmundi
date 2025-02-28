$(document).ready(function() {
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
        
        if (tipo === '') {
            // Quando for Selecione, oculta todos os campos
            $('.date-fields').hide();
            $('.label-fields').hide();
            $('#etiqueta').closest('.form-group').hide();
        } else if (tipo === 'Padrão') {
            // Quando for Padrão, mostra etiqueta mas oculta campos de data
            $('.date-fields').hide();
            $('.label-fields').show();
            $('#etiqueta').closest('.form-group').show();
        } else if (tipo === 'Promocional') {
            // Quando for Promocional, mostra todos os campos e define valores padrão
            $('.date-fields').show();
            $('.label-fields').show();
            $('#etiqueta').closest('.form-group').show();
            
            // Define valores padrão para a etiqueta
            $('#etiqueta').val('OFERTA ESPECIAL');
            $('#id3 input').val('#FFFFFF');
            $('#id4 input').val('#FF0000');
        }
    });
    
    // Dispara o evento change do tipo para configurar visibilidade inicial
    $('#tipo').trigger('change');

    // Handler para o botão Salvar
    $('.btn-success').click(function() {
        var $btn = $(this);
        var formData = new FormData();

        // Função para validar e formatar cor
        function validateColor(color) {
            // Remove espaços e converte para minúsculas
            color = color.trim().toLowerCase();
            
            // Se já estiver no formato #RRGGBB, retorna como está
            if (/^#[0-9a-f]{6}$/.test(color)) {
                return color;
            }
            
            // Se estiver no formato RGB(r,g,b), converte para hex
            var rgbMatch = color.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);
            if (rgbMatch) {
                var r = parseInt(rgbMatch[1]).toString(16).padStart(2, '0');
                var g = parseInt(rgbMatch[2]).toString(16).padStart(2, '0');
                var b = parseInt(rgbMatch[3]).toString(16).padStart(2, '0');
                return `#${r}${g}${b}`;
            }
            
            // Se não estiver em nenhum formato válido, retorna preto
            return '#000000';
        }

        // Função para converter data do formato DD/MM/YYYY HH:mm para YYYY-MM-DD HH:mm
        function convertDateFormat(dateStr) {
            if (!dateStr) return '';
            return moment(dateStr, 'DD/MM/YYYY HH:mm').format('YYYY-MM-DD HH:mm');
        }

        // Coleta os dados do formulário
        formData.append('name', $('#nome').val());
        formData.append('plan', $('#plano').val());
        formData.append('billing_cycle', $('#vigencia').val());
        formData.append('enabled', $('#enabled').is(':checked'));
        formData.append('tipo', $('#tipo').val());
        formData.append('label', $('#etiqueta').val());
        formData.append('color_text_label', validateColor($('#id3').colorpicker('getValue')));
        formData.append('color_background_label', validateColor($('#id4').colorpicker('getValue')));
        formData.append('full_price', $('#preco-padrao').val());
        formData.append('promotional_price', $('#preco-promocional').val());
        formData.append('color_text_billing_cycle', validateColor($('#id5').colorpicker('getValue')));
        formData.append('show_to', $('#exibir-para').val());
        formData.append('promotional_price_validity', $('#val-preco-prom').val());
        formData.append('start_date', convertDateFormat($('#datetimepicker').val()));
        formData.append('end_date', convertDateFormat($('#datetimepicker2').val()));
        formData.append('android_product_code', $('#android-product-code').val());
        formData.append('ios_product_code', $('#ios-product-code').val());
        formData.append('gateway_product_code', $('#gateway-product-code').val());

        // Adiciona a imagem se houver
        var imageFile = $('#image')[0].files[0];
        if (imageFile) {
            formData.append('image', imageFile);
        }

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

        $btn.prop('disabled', true);

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
                    toastr.error(response.message);
                    $btn.prop('disabled', false);
                }
            },
            error: function() {
                toastr.error('Erro ao salvar plano');
                $btn.prop('disabled', false);
            }
        });
    });

    // Botão Cancelar
    $('.btn-danger').click(function(e) {
        e.preventDefault();
        window.location.href = $('#cancel-url').data('url');
    });

    // Inicialização dos componentes
    $('.i-checks').iCheck({
        checkboxClass: 'icheckbox_square-green',
        radioClass: 'iradio_square-green'
    });

    // Inicialização dos colorpickers
    $('#id3, #id4, #id5').colorpicker();

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
}); 