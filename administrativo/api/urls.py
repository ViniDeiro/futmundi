from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .auth import LoginView, TokenRefreshView, TokenVerifyView, SocialLoginView
from .users import UserViewSet
from .championships import ChampionshipViewSet, MatchViewSet
from .predictions import PredictionViewSet
from .futligas import FutligaViewSet, FutligaMemberViewSet
from .store import PackageViewSet
from .notifications import NotificationViewSet

# Configurar os routers para recursos que usam viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'championships', ChampionshipViewSet)
router.register(r'predictions', PredictionViewSet)
router.register(r'futligas', FutligaViewSet)
router.register(r'store/packages', PackageViewSet)
router.register(r'notifications', NotificationViewSet)

# URLs da API
urlpatterns = [
    # Autenticação
    path('auth/login/', LoginView.as_view(), name='api_login'),
    path('auth/social/', SocialLoginView.as_view(), name='api_social_login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('auth/register/', UserViewSet.as_view({'post': 'create'}), name='api_register'),
    
    # Perfil de usuário
    path('users/profile/', UserViewSet.as_view({'get': 'me'}), name='api_user_profile'),
    
    # Futligas (membros)
    path('futligas/<int:futliga_id>/members/', FutligaMemberViewSet.as_view({'get': 'list', 'post': 'create'}), name='futliga_members'),
    path('futligas/<int:futliga_id>/members/<int:pk>/', FutligaMemberViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'}), name='futliga_member_detail'),
    
    # Matches de campeonato
    path('championships/<int:championship_id>/matches/', MatchViewSet.as_view({'get': 'list'}), name='championship_matches'),
    
    # Compra de pacotes
    path('store/packages/<int:pk>/purchase/', PackageViewSet.as_view({'post': 'purchase'}), name='package_purchase'),
    
    # Incluir todas as rotas do router
    path('', include(router.urls)),
] 