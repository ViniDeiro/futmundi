from rest_framework import viewsets, permissions
from .models import Scope, ScopeLevel
from .serializers import ScopeSerializer, ScopeLevelSerializer

class ScopeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows scopes to be viewed.
    """
    queryset = Scope.objects.filter(is_active=True).prefetch_related('levels')
    serializer_class = ScopeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        scope_type = self.request.query_params.get('type', None)
        if scope_type:
            queryset = queryset.filter(type=scope_type)
        return queryset

class ScopeLevelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows scope levels to be viewed.
    """
    queryset = ScopeLevel.objects.filter(is_active=True)
    serializer_class = ScopeLevelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        scope_id = self.request.query_params.get('scope', None)
        level_type = self.request.query_params.get('type', None)
        
        if scope_id:
            queryset = queryset.filter(scope_id=scope_id)
        if level_type:
            queryset = queryset.filter(type=level_type)
            
        return queryset 