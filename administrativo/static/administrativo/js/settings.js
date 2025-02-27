// Arquivo usado para colocar todos os scripts personalizados

// Configurações do toastr
toastr.options = {
    closeButton: true,
    debug: false,
    progressBar: true,
    preventDuplicates: true,
    positionClass: "toast-top-right",
    onclick: null,
    showDuration: "400",
    hideDuration: "1000",
    timeOut: 1000,
    extendedTimeOut: "1000",
    showEasing: "swing",
    hideEasing: "linear",
    showMethod: 'slideDown'
};

// Limpa todas as mensagens antigas ao carregar a página
$(document).ready(function() {
    // Remove imediatamente qualquer alerta existente
    $('.alert').remove();
    
    // Limpa o container do toastr
    toastr.clear();
});

//Toastr para formulários
$("#successToast").closest("form").on("submit", function(event) {
  if (this.checkValidity()) {
    event.preventDefault();
    toastr.success("Salvo com sucesso!");
    setTimeout(() => {
      event.target.submit();
    }, 1000);
  }
});

// Converter alertas do Bootstrap para toastr e limpar as mensagens
$(document).ready(function() {
    $('.alert').each(function() {
        var message = $(this).text().trim();
        var type = $(this).hasClass('alert-success') ? 'success' : 
                   $(this).hasClass('alert-info') ? 'info' :
                   $(this).hasClass('alert-warning') ? 'warning' : 'error';
        
        if (message) {
            toastr[type](message);
        }
        
        // Remove o alerta original
        $(this).remove();
    });
    
    // Limpa as mensagens do Django após exibi-las
    setTimeout(() => {
        $('.alert').remove();
    }, 1000);
});

//TableDND
$(document).ready(function() {
  // Initialise the table
  $("#table").tableDnD();
});

// Colorpicker
$(".formcolorpicker").each(function() {
  $(this).colorpicker();
});

//DateTimePicker
$(function() {
  $("#datetimepicker").datetimepicker({
    format: "DD/MM/YYYY HH:mm",
    locale: 'pt-br'
  });
  $("#datetimepicker2").datetimepicker({
    format: "DD/MM/YYYY HH:mm",
    locale: 'pt-br',
    useCurrent: false // Precisa para ajudar na lógica abaixo.
  });
  $("#datetimepicker3").datetimepicker({
    format: "DD/MM/YYYY HH:mm",
    locale: 'pt-br'
  });

  // Lógica Datetimepicker linkado para não permitir que a segunda data seja maior que a primeira
  $("#datetimepicker").on("change.datetimepicker", function(e) {
    $("#datetimepicker2").datetimepicker("minDate", e.date);
  });
  $("#datetimepicker2").on("change.datetimepicker", function(e) {
    $("#datetimepicker").datetimepicker("maxDate", e.date);
  });
});

//ICheck
$(document).ready(function() {
  $(".i-checks").iCheck({
    checkboxClass: "icheckbox_square-green",
    radioClass: "iradio_square-green"
  });
});

//Select2
$(".js-basic-single").select2({
  width: "resolve"
});

//DualListBox
$(".dual_select").bootstrapDualListbox({
  selectorMinimalHeight: 160
});

$(".js-templating").select2({
  templateResult: formatState,
  templateSelection: formatState
});

// Lógica Dropdown com imagens + texto
// Referência: https://select2.org/dropdown
function formatState(state) {
  if (!state.id) {
    return state.text;
  }
  var baseUrl = "img/times";
  var $state = $(
    '<span><img src="' +
      baseUrl +
      "/" +
      state.element.value.toLowerCase() +
      '.png" class="img-xm" /> ' +
      state.text +
      "</span>"
  );
  return $state;
}

// Função para garantir que redirecionamentos mantenham o estilo
$(document).ready(function() {
    console.log("Inicializando captura de formulários...");
    
    // Alterar tempo do toastr para ser mais lento
    toastr.options.timeOut = 3000; // 3 segundos
    toastr.options.extendedTimeOut = 3000;
    
    // IMPORTANTE: Desativar AJAX explicitamente para formulários de campeonato
    // Seleciona qualquer formulário relacionado a campeonatos de forma abrangente
    $('form#form-campeonato, form[action*="campeonato/editar"], form[action*="campeonato_editar"]').each(function() {
        $(this).removeClass('ajax-form');
        $(this).addClass('no-ajax-form');
        $(this).attr('data-no-ajax', 'true');
        console.log("Formulário de campeonato excluído da interceptação AJAX:", $(this).attr('id') || $(this).attr('action'));
    });
    
    // Aplicar a classe ajax-form a todos os formulários de edição
    // que não tenham a classe no-ajax-form e não sejam formulários de campeonato
    $('form[id*="editar"], form[id*="edit"], form[action*="editar"], form[action*="edit"]')
        .not('.no-ajax-form')
        .not('#form-campeonato')
        .not('[action*="campeonato/editar"]')
        .not('[action*="campeonato_editar"]')
        .each(function() {
            $(this).addClass('ajax-form');
            console.log("Formulário interceptado:", $(this).attr('id') || $(this).attr('action'));
        });
    
    // Interceptar todos os formulários com classe .ajax-form
    $(document).on('submit', '.ajax-form', function(e) {
        // VERIFICAÇÃO TRIPLA PARA FORMULÁRIOS DE CAMPEONATO
        // 1. Pelo ID
        if ($(this).attr('id') === 'form-campeonato') {
            console.log("Formulário de campeonato detectado pelo ID - IGNORANDO AJAX");
            return true; // Permitir submissão normal
        }
        
        // 2. Pela URL de action
        if ($(this).attr('action') && 
            ($(this).attr('action').indexOf('campeonato/editar') !== -1 || 
             $(this).attr('action').indexOf('campeonato_editar') !== -1)) {
            console.log("Formulário de campeonato detectado pela URL - IGNORANDO AJAX");
            return true; // Permitir submissão normal
        }
        
        // 3. Pela classe ou atributo
        if ($(this).hasClass('no-ajax-form') || $(this).attr('data-no-ajax') === 'true') {
            console.log("Formulário .no-ajax-form detectado - permitindo submissão normal");
            return true; // Permitir submissão normal
        }
        
        console.log("Formulário AJAX sendo enviado:", $(this).attr('id') || $(this).attr('action'));
        e.preventDefault();
        
        var form = $(this);
        var formData = new FormData(this);
        
        // Mostrar indicador de carregamento
        var loadingHtml = '<div class="ajax-loading-overlay"><div class="spinner-border text-primary" role="status"><span class="sr-only">Carregando...</span></div></div>';
        $('body').append(loadingHtml);
        
        $.ajax({
            url: form.attr('action'),
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                console.log("Resposta do servidor:", response);
                
                // Remover indicador de carregamento
                $('.ajax-loading-overlay').remove();
                
                if (response.success) {
                    if (response.message) {
                        toastr.success(response.message);
                    }
                    
                    // Redirecionamento direto após pequeno atraso para mostrar a mensagem
                    if (response.redirect_url) {
                        console.log("Redirecionando para:", response.redirect_url);
                        
                        setTimeout(function() {
                            // Redirecionamento direto com parâmetro para forçar recarregamento
                            if (typeof window.redirectSafely === 'function') {
                                window.redirectSafely(response.redirect_url);
                            } else {
                                // Adicionar parâmetro de recarregamento se não estiver presente
                                var url = response.redirect_url;
                                if (url.indexOf('_reload=') === -1) {
                                    var separator = url.indexOf('?') !== -1 ? '&' : '?';
                                    url = url + separator + '_reload=' + Date.now();
                                }
                                window.location.replace(url);
                            }
                        }, 800);
                    }
                } else {
                    if (response.message) {
                        toastr.error(response.message);
                    } else {
                        toastr.error('Ocorreu um erro ao processar sua solicitação.');
                    }
                }
            },
            error: function(xhr) {
                // Remover indicador de carregamento
                $('.ajax-loading-overlay').remove();
                
                console.error("Erro AJAX:", xhr);
                toastr.error('Erro ao salvar: ' + (xhr.responseJSON && xhr.responseJSON.message ? xhr.responseJSON.message : 'Ocorreu um erro desconhecido.'));
            }
        });
    });
});

// Estilos para o overlay de carregamento
$(document).ready(function() {
    // Adicionar estilo para o indicador de carregamento
    $('<style>')
        .prop('type', 'text/css')
        .html(`
        .ajax-loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .ajax-loading-overlay .spinner-border {
            width: 3rem;
            height: 3rem;
        }
        `)
        .appendTo('head');
});
