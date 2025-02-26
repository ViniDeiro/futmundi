$(document).ready(function() {
  // Configuração padrão para todas as tabelas
  const defaultConfig = {
    pageLength: 10,
    responsive: true,
    dom: '<"html5buttons"B>lTfgitp',
    buttons: [],
    language: {
      url: "//cdn.datatables.net/plug-ins/1.10.19/i18n/Portuguese-Brasil.json"
    }
  };

  // Níveis
  if ($("#levels-table").length) {
    $("#levels-table").DataTable({
      ...defaultConfig,
      columnDefs: [{ orderable: false, targets: [0, 5, 6] }]
    });
  }

  // Âmbitos
  if ($(".dataTables-ambitos").length) {
    $(".dataTables-ambitos").DataTable({
      ...defaultConfig,
      lengthChange: false,
      searching: false,
      paginate: false,
      info: false,
      ordering: false
    });
  }

  // Campeonatos
  if ($(".dataTables-campeonatos").length) {
    $(".dataTables-campeonatos").DataTable({
      ...defaultConfig,
      columnDefs: [{ orderable: false, targets: [0, 7] }]
    });
  }

  // Continentes
  if ($(".dataTables-continentes").length) {
    $(".dataTables-continentes").DataTable({
      ...defaultConfig,
      columnDefs: [{ orderable: false, targets: [0, 3] }]
    });
  }

  // Estados
  if ($(".dataTables-estados").length) {
    $(".dataTables-estados").DataTable({
      ...defaultConfig,
      columnDefs: [{ orderable: false, targets: [0, 4] }]
    });
  }

  // Futligas Padrão
  if ($(".dataTables-futligas-padrao").length) {
    $(".dataTables-futligas-padrao").DataTable({
      ...defaultConfig,
      columnDefs: [{ orderable: false, targets: [0, 2, 5] }]
    });
  }

  // Notificações
  if ($(".dataTables-notificacoes").length) {
    $(".dataTables-notificacoes").DataTable({
      ...defaultConfig,
      columnDefs: [{ orderable: false, targets: [0, 5] }]
    });
  }

  // Pacotes
  if ($(".dataTables-pacotes").length) {
    $(".dataTables-pacotes").DataTable({
      ...defaultConfig,
      columnDefs: [{ orderable: false, targets: [0, 6] }]
    });
  }

  // Países
  if ($(".dataTables-paises").length) {
    $(".dataTables-paises").DataTable({
      ...defaultConfig,
      columnDefs: [{ orderable: false, targets: [0, 4] }]
    });
  }

  // Relatórios
  if ($(".dataTables-relatorios").length) {
    $(".dataTables-relatorios").DataTable({
      ...defaultConfig,
      dom: '<"html5buttons"B>lTfgtp'
    });
  }

  // Templates
  if ($(".dataTables-templates").length) {
    $(".dataTables-templates").DataTable({
      ...defaultConfig,
      pageLength: 25,
      order: [[3, 'desc']],
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
  }

  // Times
  if ($(".dataTables-times").length) {
    $(".dataTables-times").DataTable({
      ...defaultConfig,
      columnDefs: [{ orderable: false, targets: [0, 3, 5] }]
    });
  }

  // Usuários Internos
  if ($(".dataTables-usuarios-internos").length) {
    $(".dataTables-usuarios-internos").DataTable({
      ...defaultConfig,
      columnDefs: [{ orderable: false, targets: [0, 4] }]
    });
  }

  // Usuários
  if ($(".dataTables-usuarios").length) {
    $(".dataTables-usuarios").DataTable({
      ...defaultConfig,
      columnDefs: [{ orderable: false, targets: [0, 6] }]
    });
  }

  // Vigências
  if ($(".dataTables-vigencias").length) {
    $(".dataTables-vigencias").DataTable({
      ...defaultConfig,
      columnDefs: [{ orderable: false, targets: [0, 6] }]
    });
  }
});
