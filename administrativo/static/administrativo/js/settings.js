// Arquivo usado para colocar todos os scripts personalizados


//Toastr
$("#successToast").closest("form").on("submit", function(event) {
  // Não previne o envio do formulário
  toastr.success("Salvando...", "Aguarde");
  toastr.options = {
    closeButton: true,
    debug: false,
    progressBar: false,
    preventDuplicates: false,
    positionClass: "toast-top-right",
    onclick: null,
    showDuration: "400",
    hideDuration: "1000",
    timeOut: "1000",
    extendedTimeOut: "400",
    showEasing: "swing",
    hideEasing: "linear",
    showMethod: "fadeIn",
    hideMethod: "fadeOut"
  };
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
