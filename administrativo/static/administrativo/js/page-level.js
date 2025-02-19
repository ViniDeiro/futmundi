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
    pageLength: 25,
    responsive: true,
    order: [[3, 'desc']],
    dom: '<"html5buttons"B>lTfgitp',
    buttons: [
      { extend: 'copy', text: 'Copiar' },
      { extend: 'csv' },
      { extend: 'excel', title: 'Templates' },
      { extend: 'pdf', title: 'Templates' },
      { extend: 'print', text: 'Imprimir',
        customize: function (win) {
          $(win.document.body).addClass('white-bg');
          $(win.document.body).find('table')
            .addClass('compact')
            .css('font-size', 'inherit');
        }
      }
    ],
    language: {
      url: "//cdn.datatables.net/plug-ins/1.10.19/i18n/Portuguese-Brasil.json"
    }
  });

  // Manipulação de checkboxes
  $('.checkAll').on('change', function() {
    $('input[type="checkbox"]').not(this).prop('checked', $(this).prop('checked'));
    toggleDeleteButton();
  });

  $('input[type="checkbox"]').not('.checkAll').on('change', function() {
    toggleDeleteButton();
  });

  function toggleDeleteButton() {
    var checkedCount = $('input[type="checkbox"]:checked').not('.checkAll').length;
    $('.btn-delete').prop('disabled', checkedCount === 0);
  }

  // Exclusão em massa
  $('.btn-delete').on('click', function() {
    var ids = [];
    $('input[type="checkbox"]:checked').not('.checkAll').each(function() {
      ids.push($(this).val());
    });

    if (ids.length > 0) {
      $('#modalAlert').modal('show');
    }
  });

  // Exclusão individual
  $('.btn-danger').on('click', function() {
    $('#modalAlert2').modal('show');
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
