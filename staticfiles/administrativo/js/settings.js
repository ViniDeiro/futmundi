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
    format: "DD/MM/YYYY, HH:mm"
  });
  $("#datetimepicker2").datetimepicker({
    format: "DD/MM/YYYY, HH:mm",
    useCurrent: false // Precisa para ajudar na lógica abaixo.
  });
  $("#datetimepicker3").datetimepicker({
    format: "DD/MM/YYYY, HH:mm"
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
