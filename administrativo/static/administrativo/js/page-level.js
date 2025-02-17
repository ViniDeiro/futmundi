$(document).ready(function() {
  $(".dataTables-ambitos").DataTable({
    lengthChange: false,
    responsive: true,
    searching: false,
    paginate: false,
    info: false,
    ordering: false,
    dom: '<"html5buttons"B>lTfgitp',
    buttons: []
  });
});

$(document).ready(function() {
  $(".dataTables-campeonatos").DataTable({
    pageLength: 10,
    responsive: true,
    dom: '<"html5buttons"B>lTfgitp',
    buttons: [],
    columnDefs: [{ orderable: false, targets: [0, 7] }]
  });
});

$(document).ready(function() {
  $(".dataTables-continentes").DataTable({
    pageLength: 10,
    responsive: true,
    dom: '<"html5buttons"B>lTfgitp',
    buttons: [],
    columnDefs: [{ orderable: false, targets: [0, 3] }]
  });
});

$(document).ready(function() {
  $(".dataTables-estados").DataTable({
    pageLength: 10,
    responsive: true,
    dom: '<"html5buttons"B>lTfgitp',
    buttons: [],
    columnDefs: [{ orderable: false, targets: [0, 4] }]
  });
});

$(document).ready(function() {
  $(".dataTables-futligas-padrao").DataTable({
    pageLength: 10,
    responsive: true,
    dom: '<"html5buttons"B>lTfgitp',
    buttons: [],
    columnDefs: [{ orderable: false, targets: [0, 2, 5] }]
  });
});

$(document).ready(function() {
  $(".dataTables-notificacoes").DataTable({
    pageLength: 10,
    responsive: true,
    dom: '<"html5buttons"B>lTfgitp',
    buttons: [],
    columnDefs: [{ orderable: false, targets: [0, 5] }]
  });
});

$(document).ready(function() {
  $(".dataTables-pacotes").DataTable({
    pageLength: 10,
    responsive: true,
    dom: '<"html5buttons"B>lTfgitp',
    buttons: [],
    columnDefs: [{ orderable: false, targets: [0, 6] }]
  });
});

$(document).ready(function() {
  $(".dataTables-paises").DataTable({
    pageLength: 10,
    responsive: true,
    dom: '<"html5buttons"B>lTfgitp',
    buttons: [],
    columnDefs: [{ orderable: false, targets: [0, 4] }]
  });
});

$(document).ready(function() {
  $(".dataTables-relatorios").DataTable({
    pageLength: 10,
    responsive: true,
    dom: '<"html5buttons"B>lTfgtp',
    buttons: []
  });
});

$(document).ready(function() {
  $(".dataTables-templates").DataTable({
    pageLength: 10,
    responsive: true,
    dom: '<"html5buttons"B>lTfgitp',
    buttons: [],
    columnDefs: [{ orderable: false, targets: [0, 4] }]
  });
});

$(document).ready(function() {
  $(".dataTables-times").DataTable({
    pageLength: 10,
    responsive: true,
    dom: '<"html5buttons"B>lTfgitp',
    buttons: [],
    columnDefs: [{ orderable: false, targets: [0, 3, 5] }]
  });
});

$(document).ready(function() {
  $(".dataTables-usuarios-internos").DataTable({
    pageLength: 10,
    responsive: true,
    dom: '<"html5buttons"B>lTfgitp',
    buttons: [],
    columnDefs: [{ orderable: false, targets: [0, 4] }]
  });
});

$(document).ready(function() {
  $(".dataTables-usuarios").DataTable({
    pageLength: 10,
    responsive: true,
    dom: '<"html5buttons"B>lTfgitp',
    buttons: [],
    columnDefs: [{ orderable: false, targets: [0, 6] }]
  });
});

$(document).ready(function() {
  $(".dataTables-vigencias").DataTable({
    pageLength: 10,
    responsive: true,
    dom: '<"html5buttons"B>lTfgitp',
    buttons: [],
    columnDefs: [{ orderable: false, targets: [0, 6] }]
  });
});
