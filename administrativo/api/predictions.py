from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, IntegerField, ValidationError
from rest_framework.decorators import action
from django.db import transaction
from django.utils import timezone
from ..models import Prediction, ChampionshipMatch as Match, User
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .championships import TeamSerializer

class MatchForPredictionSerializer(ModelSerializer):
    """Serializer para partidas que podem receber palpites."""
    home_team = TeamSerializer(read_only=True)
    away_team = TeamSerializer(read_only=True)
    
    class Meta:
        model = Match
        fields = [
            'id', 'home_team', 'away_team', 'home_score', 'away_score', 
            'match_date', 'is_finished', 'round'
        ]
        read_only_fields = fields

class PredictionSerializer(ModelSerializer):
    """Serializer para palpites."""
    match = MatchForPredictionSerializer(read_only=True)
    match_id = IntegerField(write_only=True)
    
    class Meta:
        model = Prediction
        fields = [
            'id', 'match', 'match_id', 'home_score', 'away_score', 
            'created_at', 'modified_at', 'points_earned'
        ]
        read_only_fields = ['id', 'match', 'created_at', 'modified_at', 'points_earned']
    
    def validate_match_id(self, value):
        """Valida se a partida existe e ainda pode receber palpites."""
        try:
            match = Match.objects.get(pk=value)
            
            # Verifica se a partida já iniciou
            if match.match_date and match.match_date <= timezone.now():
                raise ValidationError(
                    "Não é possível fazer palpites para partidas que já iniciaram."
                )
                
            return value
        except Match.DoesNotExist:
            raise ValidationError("Partida não encontrada.")
    
    def validate(self, data):
        """Validação adicional para palpites."""
        user = self.context['request'].user
        match_id = data.get('match_id')
        
        # Verificar se já existe um palpite para esta partida
        if self.instance is None:  # apenas na criação
            if Prediction.objects.filter(user=user, match_id=match_id).exists():
                raise ValidationError(
                    "Você já fez um palpite para esta partida."
                )
        
        return data

class PredictionDetailSerializer(PredictionSerializer):
    """Serializer detalhado para palpites, usado em retrieve."""
    
    class Meta(PredictionSerializer.Meta):
        fields = PredictionSerializer.Meta.fields
        read_only_fields = fields  # Todos os campos são somente leitura no detail

class PredictionViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gerenciar palpites.
    
    list:
        Retorna uma lista paginada dos palpites do usuário atual.
    
    retrieve:
        Retorna os detalhes de um palpite específico.
    
    create:
        Cria um novo palpite para uma partida.
    
    update:
        Atualiza um palpite existente (apenas se a partida ainda não iniciou).
    
    partial_update:
        Atualiza parcialmente um palpite existente (apenas se a partida ainda não iniciou).
    
    upcoming:
        Retorna as próximas partidas disponíveis para palpites.
    """
    queryset = Prediction.objects.all().select_related('match', 'match__home_team', 'match__away_team')
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PredictionSerializer
    
    def get_queryset(self):
        """Retorna apenas os palpites do usuário autenticado."""
        return Prediction.objects.filter(
            user=self.request.user
        ).select_related('match', 'match__home_team', 'match__away_team').order_by('-created_at')
    
    def get_serializer_class(self):
        """Seleciona o serializer apropriado com base na ação."""
        if self.action == 'retrieve':
            return PredictionDetailSerializer
        return PredictionSerializer
    
    def perform_create(self, serializer):
        """Associa o usuário atual ao criar um palpite."""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """
        Retorna as próximas partidas disponíveis para palpites.
        Exclui partidas que já iniciaram e aquelas que o usuário já palpitou.
        """
        # Obtém partidas futuras
        now = timezone.now()
        upcoming_matches = Match.objects.filter(
            match_date__gt=now,
            # Apenas partidas de campeonatos ativos
            round__stage__championship__is_active=True
        ).order_by('match_date')
        
        # Exclui partidas que o usuário já palpitou
        user_prediction_matches = Prediction.objects.filter(
            user=request.user
        ).values_list('match_id', flat=True)
        
        available_matches = upcoming_matches.exclude(id__in=user_prediction_matches)
        
        # Limita a 10 próximas partidas
        available_matches = available_matches[:10]
        
        serializer = MatchForPredictionSerializer(available_matches, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Cria múltiplos palpites em uma única requisição",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['predictions'],
            properties={
                'predictions': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=['match_id', 'home_score', 'away_score'],
                        properties={
                            'match_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID da partida'),
                            'home_score': openapi.Schema(type=openapi.TYPE_INTEGER, description='Placar time mandante'),
                            'away_score': openapi.Schema(type=openapi.TYPE_INTEGER, description='Placar time visitante'),
                        }
                    )
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Resultado do processamento em massa",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_INTEGER, description='Número de palpites criados com sucesso'),
                        'failed': openapi.Schema(type=openapi.TYPE_INTEGER, description='Número de palpites que falharam'),
                        'predictions': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT, description='Dados dos palpites criados')
                        ),
                        'errors': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'match_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'errors': openapi.Schema(type=openapi.TYPE_OBJECT)
                                }
                            )
                        )
                    }
                )
            ),
            400: "Formato inválido",
            401: "Não autenticado"
        }
    )
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Permite criar múltiplos palpites em uma única requisição."""
        predictions = request.data.get('predictions', [])
        if not predictions or not isinstance(predictions, list):
            return Response(
                {"error": "É necessário fornecer uma lista de palpites"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = []
        errors = []
        
        with transaction.atomic():
            for pred_data in predictions:
                serializer = self.get_serializer(data=pred_data)
                if serializer.is_valid():
                    prediction = serializer.save(user=request.user)
                    results.append(serializer.data)
                else:
                    # Adiciona os erros com o ID da partida para referência
                    errors.append({
                        "match_id": pred_data.get("match_id"),
                        "errors": serializer.errors
                    })
        
        return Response({
            "success": len(results),
            "failed": len(errors),
            "predictions": results,
            "errors": errors if errors else None
        }) 