from django.urls import path
from . import views
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from .api.auth import LoginView, TokenRefreshView, TokenVerifyView
from .api.users import UserViewSet
from .api.predictions import PredictionViewSet
from .api.matches import MatchViewSet
from .api.championships import ChampionshipViewSet
from .api.futligas import FutligaViewSet
from .api.leaderboards import LeaderboardViewSet
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

app_name = 'administrativo'

# Configurar Swagger/OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="Futmundi API",
        default_version='v1',
        description="API para o aplicativo de bolão de futebol Futmundi",
        terms_of_service="https://www.futmundi.com.br/terms/",
        contact=openapi.Contact(email="suporte@futmundi.com.br"),
        license=openapi.License(name="Proprietário"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'predictions', PredictionViewSet)
router.register(r'matches', MatchViewSet)
router.register(r'championships', ChampionshipViewSet)
router.register(r'futligas', FutligaViewSet)
router.register(r'leaderboards', LeaderboardViewSet, basename='leaderboards')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include(router.urls)),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Documentação Swagger/OpenAPI
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    
    path('', views.usuarios, name='index'),
    path('usuarios/', views.usuarios, name='usuarios'),
    path('usuario-editar/', views.usuario_editar, name='usuario_editar'),
    
    # Campeonatos
    path('ambitos/', views.ambitos, name='ambitos'),
    path('ambito/editar/<int:id>/', views.ambito_editar, name='ambito_editar'),
    path('campeonatos/', views.campeonatos, name='campeonatos'),
    path('campeonato/novo/', views.campeonato_novo, name='campeonato_novo'),
    path('campeonato/editar/<int:championship_id>/', views.campeonato_editar, name='campeonato_editar'),
    path('campeonato/excluir/<int:id>/', views.campeonato_excluir, name='campeonato_excluir'),
    path('campeonato/excluir-em-massa/', views.campeonato_excluir_em_massa, name='campeonato_excluir_em_massa'),
    path('campeonato/resultados/<int:id>/', views.campeonato_resultados, name='campeonato_resultados'),
    path('campeonato/toggle-status/', views.campeonato_toggle_status, name='campeonato_toggle_status'),
    path('campeonato/importar-rodadas', views.campeonato_importar_jogos, name='campeonato_importar_rodadas'),
    path('campeonato/get-rounds-by-stage', views.get_rounds_by_stage, name='get_rounds_by_stage'),
    path('campeonato/get-matches-by-round', views.get_matches_by_round, name='get_matches_by_round'),
    path('campeonato/get-stages-by-template', views.get_stages_by_template, name='get_stages_by_template'),
    path('campeonato/get-stages-by-championship', views.get_stages_by_championship, name='get_stages_by_championship'),
    path('campeonato/check-matches/', views.check_championship_matches, name='check_championship_matches'),
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
    path('time/por-ambito/', views.times_por_ambito, name='times_por_ambito'),
    path('get-countries-by-continent/', views.get_countries_by_continent, name='get_countries_by_continent'),
    
    # Pacotes
    path('futcoins/', views.futcoins, name='futcoins'),
    path('pacote-futcoin-novo/', views.pacote_futcoin_novo, name='pacote_futcoin_novo'),
    path('planos/', views.planos, name='planos'),
    path('pacote-plano-novo/', views.pacote_plano_novo, name='pacote_plano_novo'),
    path('pacote-plano-editar/<int:id>/', views.plano_editar, name='plano_editar'),
    path('pacote-plano-excluir/<int:id>/', views.plano_excluir, name='plano_excluir'),
    path('pacote-plano-excluir-em-massa/', views.plano_excluir_em_massa, name='plano_excluir_em_massa'),
    path('plano-toggle-status/', views.plano_toggle_status, name='plano_toggle_status'),
    path('plano/excluir/<int:id>/', views.plano_excluir, name='plano_excluir'),
    path('plano/excluir-em-massa/', views.plano_excluir_em_massa, name='plano_excluir_em_massa'),
    path('futcoin/excluir/<int:id>/', views.futcoin_excluir, name='futcoin_excluir'),
    path('futcoin/excluir-em-massa/', views.futcoin_excluir_em_massa, name='futcoin_excluir_em_massa'),
    path('futcoin/toggle-status/', views.futcoin_toggle_status, name='futcoin_toggle_status'),
    path('futcoin/editar/<int:id>/', views.futcoin_editar, name='futcoin_editar'),
    
    # Futligas
    path('futligas/', views.futligas_classicas, name='futligas_classicas'),
    path('futliga/classica/novo/', views.futliga_classica_novo, name='futliga_classica_novo'),
    path('futliga/classica/editar/<int:futliga_id>/', views.futliga_classica_editar, name='futliga_classica_editar'),
    path('futliga/classica/excluir/<int:id>/', views.futliga_classica_excluir, name='futliga_classica_excluir'),
    path('futliga/classica/excluir-em-massa/', views.futliga_classica_excluir_em_massa, name='futliga_classica_excluir_em_massa'),
    path('futligas/jogadores/', views.futligas_jogadores, name='futligas_jogadores'),
    path('futligas/jogadores/dados/', views.futliga_jogador_dados, name='futliga_jogador_dados'),
    path('administrativo/futligas/jogadores/salvar/', views.futliga_jogador_salvar, name='futliga_jogador_salvar_full'),
    path('futligas/jogadores/salvar/', views.futliga_jogador_salvar, name='futliga_jogador_salvar'),
    path('futligas/jogadores/excluir/', views.futliga_jogador_excluir, name='futliga_jogador_excluir_json'),
    path('futligas/jogadores/nivel/<int:nivel_id>/', views.futliga_jogador_nivel_excluir, name='futliga_jogador_nivel_excluir'),
    path('futligas/jogadores/novo/', views.futliga_jogador_novo, name='futliga_jogador_novo'),
    path('futligas/jogadores/editar/<int:id>/', views.futliga_jogador_editar, name='futliga_jogador_editar'),
    path('futligas/jogadores/excluir/<int:id>/', views.futliga_jogador_excluir, name='futliga_jogador_excluir'),
    path('futligas/jogadores/importar/', views.futliga_jogador_importar, name='futliga_jogador_importar'),
    path('futligas/jogadores/exportar/', views.futliga_jogador_exportar, name='futliga_jogador_exportar'),
    path('futligas/jogadores/premio/<int:premio_id>/', views.futliga_premio_excluir, name='futliga_premio_excluir'),
    path('futligas/jogadores/premios/excluir/', views.futliga_jogador_premio_excluir, name='futliga_jogador_premio_excluir'),
    path('futligas/niveis/', views.futliga_niveis, name='futligas_niveis'),
    path('futligas/premiacao/salvar/', views.futliga_premiacao_salvar, name='futliga_premiacao_salvar'),
    path('futligas/premio/novo/', views.futliga_premio_novo, name='futliga_premio_novo'),
    path('futligas/premio/<int:premio_id>/excluir/', views.futliga_premio_excluir, name='futliga_premio_excluir'),
    path('futligas/niveis/novo/', views.futliga_nivel_novo, name='futliga_nivel_novo'),
    path('futligas/niveis/editar/<int:id>/', views.futliga_nivel_editar, name='futliga_nivel_editar'),
    path('futligas/niveis/excluir/<int:id>/', views.futliga_nivel_excluir, name='futliga_nivel_excluir'),
    path('futligas/niveis/importar/', views.futliga_nivel_importar, name='futliga_nivel_importar'),
    path('futligas/niveis/exportar/', views.futliga_nivel_exportar, name='futliga_nivel_exportar'),
    path('futligas/niveis/importar-imagens/', views.futliga_nivel_importar_imagens, name='futliga_nivel_importar_imagens'),
    path('futligas/niveis/ordem/', views.futliga_nivel_ordem, name='futliga_nivel_ordem'),
    
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
    path('notificacao/editar/<int:id>/', views.notificacao_editar, name='notificacao_editar'),
    path('notificacao/excluir/<int:id>/', views.notificacao_excluir, name='notificacao_excluir'),
    path('notificacao/excluir-em-massa/', views.notificacao_excluir_em_massa, name='notificacao_excluir_em_massa'),
    path('notificacao/get-packages/', views.get_packages, name='get_packages'),
    
    # Outros
    path('relatorios/', views.relatorios, name='relatorios'),
    path('administradores/', views.administradores, name='administradores'),
    path('administrador/novo/', views.administrador_novo, name='administrador_novo'),
    path('administrador/editar/<int:id>/', views.administrador_editar, name='administrador_editar'),
    path('administrador/excluir/<int:id>/', views.administrador_excluir, name='administrador_excluir'),
    path('administradores/excluir-massa/', views.administradores_excluir_massa, name='administradores_excluir_massa'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('api/pacotes-futcoins-ativos/', views.pacotes_futcoins_ativos, name='pacotes_futcoins_ativos'),

    path('administrativo/api/pacotes-futcoins-ativos/', views.pacotes_futcoins_ativos, name='pacotes_futcoins_ativos_alt'),
]

# Servir arquivos estáticos durante o desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 