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
        "showDuration": "300",
        "hideDuration": "500",
        "timeOut": "1500",
        "extendedTimeOut": "500",
        "showEasing": "swing",
        "hideEasing": "linear",
        "showMethod": "fadeIn",
        "hideMethod": "fadeOut"
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
            $('#etiqueta').closest('.form-group').hide();
            $('#id3, #id4').closest('.form-group').hide();
            $('#datetimepicker, #datetimepicker2').closest('.form-group').hide();
            return;
        }
        
        // Campos de etiqueta e cores sempre visíveis
        $('#etiqueta').closest('.form-group').show();
        $('#id3, #id4').closest('.form-group').show();
        
        // Datas de exibição apenas para tipo Promocional
        if (tipo === 'Promocional') {
            $('#datetimepicker, #datetimepicker2').closest('.form-group').show();
            // Define valores padrão para promoção
            $('#etiqueta').val('OFERTA ESPECIAL');
            $('#id3 input').val('#FFFFFF').trigger('change');
            $('#id4 input').val('#FF0000').trigger('change');
            // Atualiza os colorpickers
            $('#id3, #id4').colorpicker('update');
        } else {
            $('#datetimepicker, #datetimepicker2').closest('.form-group').hide();
            // Limpa os campos se não for promocional
            $('#etiqueta').val('');
            $('#id3 input').val('#192639').trigger('change');
            $('#id4 input').val('#FFFFFF').trigger('change');
            // Atualiza os colorpickers
            $('#id3, #id4').colorpicker('update');
        }
    });

    // Validação e envio do formulário
    $('.btn-success').click(function() {
        // Validação dos campos obrigatórios
        var nome = $('#nome').val();
        var precoPadrao = $('#preco-padrao').val();
        var precoPromocional = $('#preco-promocional').val();

        if (!nome || !precoPadrao || !precoPromocional) {
            toastr.error('Por favor, preencha todos os campos obrigatórios');
            return;
        }

        // Cria o FormData com os dados do formulário
        var formData = new FormData();
        formData.append('name', nome);
        formData.append('plan', $('#plano').val());
        formData.append('billing_cycle', $('#vigencia').val());
        formData.append('enabled', $('.i-checks input').is(':checked').toString());
        formData.append('package_type', $('#tipo').val());
        formData.append('label', $('#etiqueta').val());
        formData.append('color_text_label', $('#id3 input').val());
        formData.append('color_background_label', $('#id4 input').val());
        formData.append('full_price', precoPadrao);
        formData.append('promotional_price', precoPromocional);
        formData.append('color_text_billing_cycle', $('#id5 input').val());
        formData.append('show_to', $('#exibir-para').val());
        formData.append('promotional_price_validity', $('#val-preco-prom').val());
        
        var startDate = $('#datetimepicker').val();
        var endDate = $('#datetimepicker2').val();
        
        if (startDate) {
            formData.append('start_date', moment(startDate, 'DD/MM/YYYY HH:mm').format('YYYY-MM-DD HH:mm'));
        }
        if (endDate) {
            formData.append('end_date', moment(endDate, 'DD/MM/YYYY HH:mm').format('YYYY-MM-DD HH:mm'));
        }

        // Adiciona a imagem se houver
        var imageFile = $('#image')[0].files[0];
        if (imageFile) {
            formData.append('image', imageFile);
        }

        // Desabilita o botão durante o envio
        var $btn = $(this);
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