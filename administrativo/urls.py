from django.urls import path
from . import views

app_name = 'administrativo'

urlpatterns = [
    path('', views.usuarios, name='index'),
    path('usuarios/', views.usuarios, name='usuarios'),
    path('usuario-editar/', views.usuario_editar, name='usuario_editar'),
    
    # Campeonatos
    path('ambitos/', views.ambitos, name='ambitos'),
    path('ambito/editar/<int:id>/', views.ambito_editar, name='ambito_editar'),
    path('campeonatos/', views.campeonatos, name='campeonatos'),
    path('campeonato/novo/', views.campeonato_novo, name='campeonato_novo'),
    path('campeonato/editar/<int:id>/', views.campeonato_editar, name='campeonato_editar'),
    path('campeonato/excluir/<int:id>/', views.campeonato_excluir, name='campeonato_excluir'),
    path('campeonato/excluir-em-massa/', views.campeonato_excluir_em_massa, name='campeonato_excluir_em_massa'),
    path('campeonato/resultados/<int:id>/', views.campeonato_resultados, name='campeonato_resultados'),
    path('campeonato/toggle-status/', views.campeonato_toggle_status, name='campeonato_toggle_status'),
    path('templates/', views.templates, name='templates'),
    path('template/novo/', views.template_novo, name='template_novo'),
    path('template/editar/<int:id>/', views.template_editar, name='template_editar'),
    path('template/excluir/<int:id>/', views.template_excluir, name='template_excluir'),
    path('template/excluir-em-massa/', views.template_excluir_em_massa, name='template_excluir_em_massa'),
    path('template/duplicar/<int:id>/', views.template_duplicar, name='template_duplicar'),
    path('template/importar/', views.template_importar, name='template_importar'),
    path('template/exportar/', views.template_exportar, name='template_exportar'),
    path('template/toggle-status/', views.template_toggle_status, name='template_toggle_status'),
    path('templates/<int:id>/reorder-stages', views.template_reorder_stages, name='template_reorder_stages'),
    path('template/<int:template_id>/stage/<int:stage_id>/delete/', views.template_delete_stage, name='template_delete_stage'),
    path('template/<int:template_id>/add-stage/', views.template_add_stage, name='template_add_stage'),
    path('template/<int:template_id>/edit-stage/<int:stage_id>/', views.template_edit_stage, name='template_edit_stage'),
    path('times/', views.times, name='times'),
    path('time/novo/', views.time_novo, name='time_novo'),
    path('time/editar/<int:id>/', views.time_editar, name='time_editar'),
    path('time/excluir/<int:id>/', views.time_excluir, name='time_excluir'),
    path('time/excluir-em-massa/', views.time_excluir_em_massa, name='time_excluir_em_massa'),
    path('time/importar/', views.time_importar, name='time_importar'),
    path('time/exportar/', views.time_exportar, name='time_exportar'),
    path('time/importar-imagens/', views.time_importar_imagens, name='time_importar_imagens'),
    path('time/get-states-by-country/', views.get_states_by_country, name='get_states_by_country'),
    path('time/por-tipo/', views.times_por_tipo, name='times_por_tipo'),
    
    # Pacotes
    path('futcoins/', views.futcoins, name='futcoins'),
    path('pacote-futcoin-novo/', views.pacote_futcoin_novo, name='pacote_futcoin_novo'),
    path('planos/', views.planos, name='planos'),
    path('pacote-plano-novo/', views.pacote_plano_novo, name='pacote_plano_novo'),
    
    # Futligas
    path('futligas-classicas/', views.futligas_classicas, name='futligas_classicas'),
    path('futliga-classica-novo/', views.futliga_classica_novo, name='futliga_classica_novo'),
    path('futligas-jogadores/', views.futligas_jogadores, name='futligas_jogadores'),
    
    # Locais
    path('continentes/', views.continentes, name='continentes'),
    path('continente/novo/', views.continente_novo, name='continente_novo'),
    path('continente/editar/<int:id>/', views.continente_editar, name='continente_editar'),
    path('continente/excluir/<int:id>/', views.continente_excluir, name='continente_excluir'),
    path('continente/excluir-em-massa/', views.continente_excluir_em_massa, name='continente_excluir_em_massa'),
    path('continente/exportar/', views.continente_exportar, name='continente_exportar'),
    path('continente/importar/', views.continente_importar, name='continente_importar'),
    path('paises/', views.paises, name='paises'),
    path('pais-novo/', views.pais_novo, name='pais_novo'),
    path('pais/editar/<int:id>/', views.pais_editar, name='pais_editar'),
    path('pais/excluir/<int:id>/', views.pais_excluir, name='pais_excluir'),
    path('pais/excluir-em-massa/', views.pais_excluir_em_massa, name='pais_excluir_em_massa'),
    path('pais/exportar/', views.pais_exportar, name='pais_exportar'),
    path('pais/importar/', views.pais_importar, name='pais_importar'),
    path('estados/', views.estados, name='estados'),
    path('estado-novo/', views.estado_novo, name='estado_novo'),
    path('estado/editar/<int:id>/', views.estado_editar, name='estado_editar'),
    path('estado/excluir/<int:id>/', views.estado_excluir, name='estado_excluir'),
    path('estado/excluir-em-massa/', views.estado_excluir_em_massa, name='estado_excluir_em_massa'),
    path('estado/exportar/', views.estado_exportar, name='estado_exportar'),
    path('estado/importar/', views.estado_importar, name='estado_importar'),
    
    # Configurações
    path('parametros/', views.parametros, name='parametros'),
    path('termo/', views.termo, name='termo'),
    path('notificacoes/', views.notificacoes, name='notificacoes'),
    path('notificacao-novo/', views.notificacao_novo, name='notificacao_novo'),
    
    # Outros
    path('relatorios/', views.relatorios, name='relatorios'),
    path('administradores/', views.administradores, name='administradores'),
    path('administrador/novo/', views.administrador_novo, name='administrador_novo'),
    path('administrador/editar/<int:id>/', views.administrador_editar, name='administrador_editar'),
    path('administrador/excluir/<int:id>/', views.administrador_excluir, name='administrador_excluir'),
    path('administradores/excluir-massa/', views.administradores_excluir_massa, name='administradores_excluir_massa'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
] 