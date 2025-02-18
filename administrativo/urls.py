from django.urls import path
from . import views

app_name = 'administrativo'

urlpatterns = [
    path('', views.usuarios, name='usuarios'),
    path('usuarios/', views.usuarios, name='usuarios'),
    path('usuario-editar/', views.usuario_editar, name='usuario_editar'),
    
    # Campeonatos
    path('ambitos/', views.ambitos, name='ambitos'),
    path('ambito/editar/<int:id>/', views.ambito_editar, name='ambito_editar'),
    path('campeonatos/', views.campeonatos, name='campeonatos'),
    path('campeonato-novo/', views.campeonato_novo, name='campeonato_novo'),
    path('templates/', views.templates, name='templates'),
    path('template-novo/', views.template_novo, name='template_novo'),
    path('times/', views.times, name='times'),
    path('time-novo/', views.time_novo, name='time_novo'),
    
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
    path('estados/', views.estados, name='estados'),
    path('estado-novo/', views.estado_novo, name='estado_novo'),
    
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