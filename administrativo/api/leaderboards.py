from rest_framework import viewsets, serializers, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from ..models import User, Championship, LeagueMember, CustomLeague
from django.db.models import Sum, Count, F, Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class UserScoreSerializer(serializers.ModelSerializer):
    """Serializador para informações básicas de usuário com pontuação."""
    full_name = serializers.CharField()
    points = serializers.IntegerField()
    position = serializers.IntegerField()
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'points', 'position']

class LeaderboardViewSet(viewsets.ViewSet):
    """API endpoint para rankings e classificações de usuários."""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Retorna o ranking global de todos os usuários",
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID do usuário'),
                        'full_name': openapi.Schema(type=openapi.TYPE_STRING, description='Nome completo do usuário'),
                        'points': openapi.Schema(type=openapi.TYPE_INTEGER, description='Pontuação total do usuário'),
                        'position': openapi.Schema(type=openapi.TYPE_INTEGER, description='Posição no ranking')
                    }
                )
            )
        }
    )
    @action(detail=False, methods=['get'])
    def global_ranking(self, request):
        """Retorna o ranking global de todos os usuários."""
        # Calcula ranking global baseado no total de pontos de previsões
        users = User.objects.annotate(
            points=Sum('predictions__points', filter=Q(predictions__match__status='completed'))
        ).order_by('-points')
        
        # Adicionar posição no ranking
        result = []
        for position, user in enumerate(users, 1):
            result.append({
                'id': user.id,
                'full_name': user.get_full_name(),
                'points': user.points or 0,
                'position': position
            })
        
        return Response(result)
    
    @swagger_auto_schema(
        operation_description="Retorna o ranking de usuários para um campeonato específico",
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID do usuário'),
                        'full_name': openapi.Schema(type=openapi.TYPE_STRING, description='Nome completo do usuário'),
                        'points': openapi.Schema(type=openapi.TYPE_INTEGER, description='Pontuação do usuário neste campeonato'),
                        'position': openapi.Schema(type=openapi.TYPE_INTEGER, description='Posição no ranking do campeonato')
                    }
                )
            ),
            404: "Campeonato não encontrado"
        }
    )
    @action(detail=False, methods=['get'])
    def championship_ranking(self, request):
        """Retorna o ranking de usuários para um campeonato específico."""
        championship_id = request.query_params.get('championship_id')
        if not championship_id:
            return Response({"error": "É necessário fornecer um championship_id"}, status=400)
        
        try:
            championship = Championship.objects.get(id=championship_id)
        except Championship.DoesNotExist:
            return Response({"error": "Campeonato não encontrado"}, status=404)
        
        # Calcula ranking para o campeonato específico
        users = User.objects.annotate(
            points=Sum(
                'predictions__points', 
                filter=Q(
                    predictions__match__status='completed',
                    predictions__match__championship=championship
                )
            )
        ).order_by('-points')
        
        # Adicionar posição no ranking
        result = []
        for position, user in enumerate(users, 1):
            result.append({
                'id': user.id,
                'full_name': user.get_full_name(),
                'points': user.points or 0,
                'position': position
            })
        
        return Response(result)
    
    @swagger_auto_schema(
        operation_description="Retorna o ranking de usuários para uma Futliga específica",
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID do usuário'),
                        'full_name': openapi.Schema(type=openapi.TYPE_STRING, description='Nome completo do usuário'),
                        'points': openapi.Schema(type=openapi.TYPE_INTEGER, description='Pontuação do usuário nesta Futliga'),
                        'position': openapi.Schema(type=openapi.TYPE_INTEGER, description='Posição no ranking da Futliga')
                    }
                )
            ),
            400: "ID da liga não fornecido",
            404: "Liga não encontrada"
        }
    )
    @action(detail=False, methods=['get'])
    def league_ranking(self, request):
        """Retorna o ranking de usuários para uma Futliga específica."""
        league_id = request.query_params.get('league_id')
        if not league_id:
            return Response({"error": "É necessário fornecer um league_id"}, status=400)
        
        try:
            league = CustomLeague.objects.get(id=league_id)
        except CustomLeague.DoesNotExist:
            return Response({"error": "Liga não encontrada"}, status=404)
        
        # Obter membros da liga
        members = LeagueMember.objects.filter(league=league).select_related('user')
        
        # Para cada membro, calcular pontos
        result = []
        for position, member in enumerate(members, 1):
            user = member.user
            
            # Se a liga é baseada em um campeonato específico
            if league.championship:
                points = user.predictions.filter(
                    match__championship=league.championship,
                    match__status='completed'
                ).aggregate(total=Sum('points'))['total'] or 0
            else:
                # Liga global (todos os campeonatos)
                points = user.predictions.filter(
                    match__status='completed'
                ).aggregate(total=Sum('points'))['total'] or 0
            
            result.append({
                'id': user.id,
                'full_name': user.get_full_name(),
                'points': points,
                'position': position
            })
        
        # Ordenar por pontos
        result.sort(key=lambda x: x['points'], reverse=True)
        
        # Atualizar posições após ordenação
        for i, item in enumerate(result, 1):
            item['position'] = i
        
        return Response(result)
    
    @swagger_auto_schema(
        operation_description="Retorna a posição do usuário autenticado nos diferentes rankings",
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'global': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'position': openapi.Schema(type=openapi.TYPE_INTEGER, description='Posição no ranking global'),
                            'points': openapi.Schema(type=openapi.TYPE_INTEGER, description='Pontuação total do usuário'),
                            'total_users': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total de usuários no ranking')
                        }
                    ),
                    'championships': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'championship': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'name': openapi.Schema(type=openapi.TYPE_STRING)
                                    }
                                ),
                                'position': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'points': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'total_users': openapi.Schema(type=openapi.TYPE_INTEGER)
                            }
                        )
                    ),
                    'leagues': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'league': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'name': openapi.Schema(type=openapi.TYPE_STRING)
                                    }
                                ),
                                'position': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'points': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'total_users': openapi.Schema(type=openapi.TYPE_INTEGER)
                            }
                        )
                    )
                }
            )
        }
    )
    @action(detail=False, methods=['get'])
    def my_rankings(self, request):
        """Retorna a posição do usuário autenticado nos diferentes rankings."""
        user = request.user
        
        # Ranking global
        global_points = user.predictions.filter(
            match__status='completed'
        ).aggregate(total=Sum('points'))['total'] or 0
        
        # Contar todos os usuários
        total_users = User.objects.count()
        
        # Encontrar posição global
        users_above = User.objects.annotate(
            points=Sum('predictions__points', filter=Q(predictions__match__status='completed'))
        ).filter(points__gt=global_points).count()
        
        global_position = users_above + 1
        
        # Rankings por campeonato
        championship_rankings = []
        championships = Championship.objects.filter(matches__predictions__user=user).distinct()
        
        for championship in championships:
            # Pontos do usuário neste campeonato
            points = user.predictions.filter(
                match__championship=championship,
                match__status='completed'
            ).aggregate(total=Sum('points'))['total'] or 0
            
            # Contar usuários que fizeram previsões neste campeonato
            championship_users = User.objects.filter(
                predictions__match__championship=championship
            ).distinct().count()
            
            # Encontrar posição
            users_above = User.objects.annotate(
                ch_points=Sum(
                    'predictions__points', 
                    filter=Q(
                        predictions__match__status='completed',
                        predictions__match__championship=championship
                    )
                )
            ).filter(ch_points__gt=points).count()
            
            championship_rankings.append({
                'championship': {
                    'id': championship.id,
                    'name': championship.name
                },
                'position': users_above + 1,
                'points': points,
                'total_users': championship_users
            })
        
        # Rankings por liga
        league_rankings = []
        leagues = CustomLeague.objects.filter(members__user=user)
        
        for league in leagues:
            # Se a liga é baseada em um campeonato específico
            if league.championship:
                points = user.predictions.filter(
                    match__championship=league.championship,
                    match__status='completed'
                ).aggregate(total=Sum('points'))['total'] or 0
            else:
                # Liga global (todos os campeonatos)
                points = user.predictions.filter(
                    match__status='completed'
                ).aggregate(total=Sum('points'))['total'] or 0
            
            # Total de membros da liga
            league_users = league.members.count()
            
            # Encontrar posição
            if league.championship:
                # Para ligas baseadas em campeonatos específicos
                members_above = LeagueMember.objects.filter(
                    league=league
                ).exclude(user=user).select_related('user').annotate(
                    member_points=Sum(
                        'user__predictions__points',
                        filter=Q(
                            user__predictions__match__status='completed',
                            user__predictions__match__championship=league.championship
                        )
                    )
                ).filter(member_points__gt=points).count()
            else:
                # Para ligas globais
                members_above = LeagueMember.objects.filter(
                    league=league
                ).exclude(user=user).select_related('user').annotate(
                    member_points=Sum(
                        'user__predictions__points',
                        filter=Q(
                            user__predictions__match__status='completed'
                        )
                    )
                ).filter(member_points__gt=points).count()
            
            league_rankings.append({
                'league': {
                    'id': league.id,
                    'name': league.name
                },
                'position': members_above + 1,
                'points': points,
                'total_users': league_users
            })
        
        return Response({
            'global': {
                'position': global_position,
                'points': global_points,
                'total_users': total_users
            },
            'championships': championship_rankings,
            'leagues': league_rankings
        })