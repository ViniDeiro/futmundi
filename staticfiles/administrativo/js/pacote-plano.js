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
        
        // Se nenhum tipo selecionado, esconde todos os campos
        if (!tipo) {
            $('.label-fields').hide();
            return;
        }
        
        // Campos de etiqueta e cores sempre visíveis para tipo Promocional
        if (tipo === 'Promocional') {
            $('.label-fields').show();
            // Define valores padrão para promoção se os campos estiverem vazios
            if (!$('#etiqueta').val()) {
                $('#etiqueta').val('OFERTA ESPECIAL');
            }
            if (!$('#id3 input').val()) {
                $('#id3 input').val('#FFFFFF');
            }
            if (!$('#id4 input').val()) {
                $('#id4 input').val('#FF0000');
            }
        } else {
            $('.label-fields').hide();
        }
        
        // Atualiza os colorpickers
        $('#id3, #id4').colorpicker('update');
    });

    // Handler para o botão Salvar
    $('.btn-success').click(function() {
        var $btn = $(this);
        var formData = new FormData();

        // Coleta os dados do formulário
        formData.append('name', $('#nome').val());
        formData.append('plan', $('#plano').val());
        formData.append('billing_cycle', $('#vigencia').val());
        formData.append('enabled', $('#enabled').is(':checked'));
        formData.append('tipo', $('#tipo').val());
        formData.append('label', $('#etiqueta').val());
        formData.append('color_text_label', $('#id3').colorpicker('getValue'));
        formData.append('color_background_label', $('#id4').colorpicker('getValue'));
        formData.append('full_price', $('#preco-padrao').val());
        formData.append('promotional_price', $('#preco-promocional').val());
        formData.append('color_text_billing_cycle', $('#id5').colorpicker('getValue'));
        formData.append('show_to', $('#exibir-para').val());
        formData.append('promotional_price_validity', $('#val-preco-prom').val());
        formData.append('start_date', $('#datetimepicker').val());
        formData.append('end_date', $('#datetimepicker2').val());
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
        if ($('#tipo').val() === 'Promocional' && !$('#etiqueta').val()) {
            toastr.error('O campo Etiqueta é obrigatório para pacotes promocionais');
            return;
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