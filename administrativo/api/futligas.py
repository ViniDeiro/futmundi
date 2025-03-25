from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, CharField, SerializerMethodField, ValidationError
from rest_framework.decorators import action
from django.db import transaction
from django.utils import timezone
from ..models import StandardLeague, CustomLeague, LeagueMember, User
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class StandardLeagueSerializer(ModelSerializer):
    """Serializer para Futligas Clássicas (criadas pelo sistema)."""
    members_count = SerializerMethodField()
    image_url = SerializerMethodField()
    
    class Meta:
        model = StandardLeague
        fields = [
            'id', 'name', 'description', 'image_url', 'championship', 
            'max_members', 'members_count', 'entry_fee', 'prize_pool',
            'start_date', 'end_date', 'is_active'
        ]
        read_only_fields = fields
    
    def get_members_count(self, obj):
        return obj.members.count()
    
    def get_image_url(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class CustomLeagueSerializer(ModelSerializer):
    """Serializer para Futligas criadas por usuários."""
    members_count = SerializerMethodField()
    owner_name = SerializerMethodField()
    image_url = SerializerMethodField()
    is_member = SerializerMethodField()
    
    class Meta:
        model = CustomLeague
        fields = [
            'id', 'name', 'description', 'image_url', 'championship', 
            'max_members', 'members_count', 'entry_fee', 'invitation_code',
            'owner', 'owner_name', 'is_member', 'is_private'
        ]
        read_only_fields = ['id', 'owner', 'members_count', 'invitation_code', 'owner_name', 'is_member']
        extra_kwargs = {
            'invitation_code': {'write_only': True}
        }
    
    def get_members_count(self, obj):
        return obj.members.count()
    
    def get_owner_name(self, obj):
        return obj.owner.get_full_name() if obj.owner else None
    
    def get_image_url(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def get_is_member(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.members.filter(user=request.user).exists()
    
    def create(self, validated_data):
        """Cria uma nova Futliga customizada."""
        # Define o usuário atual como dono
        validated_data['owner'] = self.context['request'].user
        
        # Gera um código de convite único
        import random
        import string
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        validated_data['invitation_code'] = code
        
        # Cria a liga
        league = super().create(validated_data)
        
        # Adiciona o dono como membro automaticamente
        LeagueMember.objects.create(
            league=league,
            user=league.owner,
            is_admin=True
        )
        
        return league


class LeagueMemberSerializer(ModelSerializer):
    """Serializer para membros de Futligas."""
    user_name = SerializerMethodField()
    
    class Meta:
        model = LeagueMember
        fields = ['id', 'user', 'user_name', 'league', 'joined_at', 'is_admin', 'total_points']
        read_only_fields = ['id', 'joined_at', 'user_name', 'total_points']
    
    def get_user_name(self, obj):
        return obj.user.get_full_name() if obj.user else None


class FutligaViewSet(viewsets.ModelViewSet):
    """API endpoint para gerenciar Futligas."""
    queryset = CustomLeague.objects.all().select_related('championship', 'owner')
    serializer_class = CustomLeagueSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'entry_fee', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filtra ligas com base nos parâmetros."""
        queryset = super().get_queryset()
        
        # Filtrar por campeonato
        championship_id = self.request.query_params.get('championship', None)
        if championship_id:
            queryset = queryset.filter(championship_id=championship_id)
        
        # Filtrar por tipo
        league_type = self.request.query_params.get('type', None)
        if league_type == 'standard':
            queryset = StandardLeague.objects.all()
        elif league_type == 'my':
            # Filtrar apenas ligas que o usuário é membro
            user = self.request.user
            league_ids = LeagueMember.objects.filter(user=user).values_list('league_id', flat=True)
            queryset = queryset.filter(id__in=league_ids)
        elif league_type == 'owned':
            # Filtrar apenas ligas que o usuário é dono
            queryset = queryset.filter(owner=self.request.user)
            
        return queryset
    
    def get_serializer_class(self):
        """Seleciona o serializer com base no tipo de liga."""
        league_type = self.request.query_params.get('type', None)
        if league_type == 'standard':
            return StandardLeagueSerializer
        return CustomLeagueSerializer
    
    def get_serializer_context(self):
        """Adiciona o request ao contexto do serializer."""
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    @swagger_auto_schema(
        operation_description="Entrar em uma Futliga",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'invitation_code': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='Código de convite (obrigatório para ligas privadas)'
                ),
            }
        ),
        responses={
            201: LeagueMemberSerializer,
            400: "Erro ao entrar na liga - já é membro, liga cheia ou código inválido",
            401: "Não autenticado",
            404: "Liga não encontrada"
        }
    )
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Endpoint para entrar em uma liga."""
        league = self.get_object()
        user = request.user
        
        # Verificar se o usuário já é membro
        if LeagueMember.objects.filter(league=league, user=user).exists():
            return Response(
                {"error": "Você já é membro desta Futliga"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar se a liga está cheia
        if league.members.count() >= league.max_members:
            return Response(
                {"error": "Esta Futliga já atingiu o número máximo de membros"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Se for liga privada, verificar código de convite
        if league.is_private:
            invitation_code = request.data.get('invitation_code')
            if not invitation_code or invitation_code != league.invitation_code:
                return Response(
                    {"error": "Código de convite inválido"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Adicionar usuário como membro
        member = LeagueMember.objects.create(
            league=league,
            user=user,
            is_admin=False
        )
        
        return Response(
            LeagueMemberSerializer(member).data,
            status=status.HTTP_201_CREATED
        )
    
    @swagger_auto_schema(
        operation_description="Sair de uma Futliga",
        responses={
            204: "Saiu da liga com sucesso",
            400: "Erro ao sair da liga - não é membro ou é o dono",
            401: "Não autenticado",
            404: "Liga não encontrada"
        }
    )
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Endpoint para sair de uma liga."""
        league = self.get_object()
        user = request.user
        
        # Verificar se o usuário é membro
        try:
            member = LeagueMember.objects.get(league=league, user=user)
        except LeagueMember.DoesNotExist:
            return Response(
                {"error": "Você não é membro desta Futliga"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar se o usuário é o dono (não pode sair)
        if league.owner == user:
            return Response(
                {"error": "Você é o dono desta Futliga e não pode sair. Transfira a propriedade primeiro."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remover membro
        member.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class FutligaMemberViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gerenciar membros de Futligas.
    
    list:
        Retorna uma lista de membros de uma liga específica.
    
    retrieve:
        Retorna os detalhes de um membro específico.
    
    create:
        Adiciona um novo membro à liga (apenas para administradores).
    
    destroy:
        Remove um membro da liga (apenas para administradores ou o próprio membro).
    """
    serializer_class = LeagueMemberSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = LeagueMember.objects.all()
    basename = 'league-members'
    
    def get_queryset(self):
        """Filtra membros pelo ID da Futliga."""
        futliga_id = self.kwargs.get('futliga_id')
        if not futliga_id:
            return LeagueMember.objects.none()
        
        return LeagueMember.objects.filter(
            league_id=futliga_id
        ).select_related('user', 'league')
    
    def perform_create(self, serializer):
        """Associa a Futliga ao criar um novo membro."""
        futliga_id = self.kwargs.get('futliga_id')
        serializer.save(league_id=futliga_id) 