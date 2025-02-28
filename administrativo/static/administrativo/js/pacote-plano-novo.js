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
    $('#datetimepicker, #datetimepicker2').datetimepicker({
        format: 'DD/MM/YYYY HH:mm',
        locale: 'pt-br'
    });

    // Handler para mudança no tipo do plano
    $('#tipo').on('change', function() {
        if ($(this).val() === 'Promocional') {
            $('.label-fields').show();
        } else {
            $('.label-fields').hide();
        }
    });

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
        $('#image-preview').html('<i class="fa fa-file-image-o" style="font-size: 48px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>');
    });

    // Botão Cancelar
    $('.btn-danger').on('click', function() {
        window.location.href = $('#cancel-url').data('url');
    });

    // Botão Salvar
    $('#successToast').on('click', function() {
        const formData = new FormData();
        
        // Função para converter data do formato DD/MM/YYYY HH:mm para YYYY-MM-DD HH:mm
        function convertDateFormat(dateStr) {
            console.log('Data original:', dateStr); // Debug
            
            if (!dateStr || dateStr.trim() === '') {
                console.log('Data vazia ou nula'); // Debug
                return null;
            }
            
            try {
                // Converte a data usando moment.js
                const momentDate = moment(dateStr, 'DD/MM/YYYY HH:mm', true);
                
                // Verifica se a data é válida
                if (!momentDate.isValid()) {
                    console.error('Data inválida:', dateStr);
                    return null;
                }
                
                // Formata no padrão do Django
                const formattedDate = momentDate.format('YYYY-MM-DD HH:mm');
                console.log('Data convertida:', formattedDate); // Debug
                return formattedDate;
                
            } catch (error) {
                console.error('Erro ao converter data:', error);
                return null;
            }
        }
        
        // Dados básicos
        formData.append('name', $('#nome').val());
        formData.append('plan', $('#plano').val());
        formData.append('billing_cycle', $('#vigencia').val());
        formData.append('enabled', $('#enabled').prop('checked'));
        formData.append('tipo', $('#tipo').val());
        
        // Etiqueta (se tipo for promocional)
        if ($('#tipo').val() === 'Promocional') {
            formData.append('label', $('#etiqueta').val());
            formData.append('color_text_label', $('#id3 input').val());
            formData.append('color_background_label', $('#id4 input').val());
        }
        
        // Preços
        formData.append('full_price', $('#preco-padrao').val());
        formData.append('promotional_price', $('#preco-promocional').val());
        formData.append('promotional_price_validity', $('#val-preco-prom').val());
        
        // Configurações adicionais
        formData.append('color_text_billing_cycle', $('#id5 input').val());
        formData.append('show_to', $('#exibir-para').val());
        
        // Datas - Convertendo para o formato correto
        const startDateStr = $('#datetimepicker').val();
        const endDateStr = $('#datetimepicker2').val();
        
        console.log('Data início (original):', startDateStr); // Debug
        console.log('Data término (original):', endDateStr); // Debug
        
        const startDate = convertDateFormat(startDateStr);
        const endDate = convertDateFormat(endDateStr);
        
        console.log('Data início (convertida):', startDate); // Debug
        console.log('Data término (convertida):', endDate); // Debug
        
        // Só adiciona as datas se forem válidas
        if (startDate) formData.append('start_date', startDate);
        if (endDate) formData.append('end_date', endDate);
        
        // Códigos dos produtos
        formData.append('android_product_code', $('#codigo-android').val());
        formData.append('apple_product_code', $('#codigo-apple').val());
        
        // Imagem
        const imageFile = $('#image')[0].files[0];
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
            if (!startDateStr || !endDateStr) {
                toastr.error('As datas de início e término são obrigatórias para pacotes promocionais');
                return;
            }
            if (!startDate || !endDate) {
                toastr.error('As datas informadas são inválidas. Use o formato DD/MM/YYYY HH:mm');
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
                toastr.error(xhr.responseJSON?.message || 'Erro ao salvar plano');
                btn.prop('disabled', false);
            }
        });
    });
}); 