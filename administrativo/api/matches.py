from rest_framework import viewsets, serializers, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from ..models import ChampionshipMatch as Match, Team, Championship, Prediction
from django.utils import timezone
import datetime
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .championships import MatchSerializer
from .predictions import PredictionSerializer

class MatchViewSet(viewsets.ModelViewSet):
    """API endpoint para gerenciar partidas (matches)."""
    queryset = Match.objects.all().select_related('championship', 'home_team', 'away_team')
    serializer_class = MatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # ... código existente ...
        return queryset
    
    @swagger_auto_schema(
        operation_description="Retorna estatísticas de previsões para uma partida específica",
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'home_team_name': openapi.Schema(type=openapi.TYPE_STRING, description='Nome do time da casa'),
                    'away_team_name': openapi.Schema(type=openapi.TYPE_STRING, description='Nome do time visitante'),
                    'total_predictions': openapi.Schema(type=openapi.TYPE_INTEGER, description='Número total de previsões'),
                    'prediction_stats': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'home_score': openapi.Schema(type=openapi.TYPE_INTEGER, description='Placar do time da casa'),
                                'away_score': openapi.Schema(type=openapi.TYPE_INTEGER, description='Placar do time visitante'),
                                'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Número de previsões com este placar'),
                                'percentage': openapi.Schema(type=openapi.TYPE_NUMBER, description='Porcentagem de previsões com este placar')
                            }
                        ),
                        description='Estatísticas de previsões agrupadas por placar'
                    )
                }
            ),
            404: "Partida não encontrada"
        }
    )
    @action(detail=True, methods=['get'])
    def prediction_stats(self, request, pk=None):
        """Retorna estatísticas sobre previsões para uma partida específica."""
        match = self.get_object()
        
        # Obter todas as previsões para esta partida
        predictions = Prediction.objects.filter(match=match)
        total_predictions = predictions.count()
        
        # Agrupar previsões por placar
        prediction_stats = {}
        for prediction in predictions:
            key = f"{prediction.home_score}-{prediction.away_score}"
            if key not in prediction_stats:
                prediction_stats[key] = 0
            prediction_stats[key] += 1
        
        # Converter para o formato desejado com percentagens
        result_stats = []
        for key, count in prediction_stats.items():
            home_score, away_score = map(int, key.split('-'))
            result_stats.append({
                'home_score': home_score,
                'away_score': away_score,
                'count': count,
                'percentage': round((count / total_predictions * 100), 1) if total_predictions > 0 else 0
            })
        
        # Ordenar por contagem (do mais comum para o menos comum)
        result_stats.sort(key=lambda x: x['count'], reverse=True)
        
        return Response({
            'home_team_name': match.home_team.name,
            'away_team_name': match.away_team.name,
            'total_predictions': total_predictions,
            'prediction_stats': result_stats
        })
    
    @swagger_auto_schema(
        operation_description="Retorna a previsão do usuário para uma partida específica",
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID da previsão'),
                    'match': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID da partida'),
                    'user': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID do usuário'),
                    'home_score': openapi.Schema(type=openapi.TYPE_INTEGER, description='Placar previsto para o time da casa'),
                    'away_score': openapi.Schema(type=openapi.TYPE_INTEGER, description='Placar previsto para o time visitante'),
                    'points': openapi.Schema(type=openapi.TYPE_INTEGER, description='Pontos ganhos com esta previsão')
                }
            ),
            404: "Previsão não encontrada para esta partida"
        }
    )
    @action(detail=True, methods=['get'])
    def my_prediction(self, request, pk=None):
        """Retorna a previsão do usuário autenticado para uma partida específica."""
        match = self.get_object()
        user = request.user
        
        try:
            prediction = Prediction.objects.get(match=match, user=user)
            return Response(PredictionSerializer(prediction).data)
        except Prediction.DoesNotExist:
            return Response({"error": "Você ainda não fez uma previsão para esta partida"}, status=404) 