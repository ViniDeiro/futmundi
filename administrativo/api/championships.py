from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from ..models import Championship, Team, ChampionshipMatch as Match, ChampionshipRound as Round, ChampionshipStage as Stage
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class TeamSerializer(ModelSerializer):
    """Serializer para times."""
    image_url = SerializerMethodField()
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'abbreviation', 'image_url', 'is_national_team']
    
    def get_image_url(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class MatchSerializer(ModelSerializer):
    """Serializer para partidas."""
    home_team = TeamSerializer()
    away_team = TeamSerializer()
    stage_name = SerializerMethodField()
    round_number = SerializerMethodField()
    
    class Meta:
        model = Match
        fields = [
            'id', 'home_team', 'away_team', 'home_score', 'away_score',
            'match_date', 'stage_name', 'round_number', 'status'
        ]
    
    def get_stage_name(self, obj):
        return obj.round.stage.name if obj.round and obj.round.stage else None
    
    def get_round_number(self, obj):
        return obj.round.number if obj.round else None


class ChampionshipSerializer(ModelSerializer):
    """Serializer para campeonatos."""
    teams_count = SerializerMethodField()
    matches_count = SerializerMethodField()
    teams = TeamSerializer(many=True, read_only=True)
    
    class Meta:
        model = Championship
        fields = [
            'id', 'name', 'season', 'scope', 'is_active', 
            'teams_count', 'matches_count', 'teams'
        ]
    
    def get_teams_count(self, obj):
        return obj.teams.count()
    
    def get_matches_count(self, obj):
        return Match.objects.filter(round__stage__championship=obj).count()


class ChampionshipViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint para gerenciar campeonatos."""
    queryset = Championship.objects.all()
    serializer_class = ChampionshipSerializer
    
    @swagger_auto_schema(
        operation_description="Retorna todos os times participantes de um campeonato",
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID do time'),
                        'name': openapi.Schema(type=openapi.TYPE_STRING, description='Nome do time'),
                        'short_name': openapi.Schema(type=openapi.TYPE_STRING, description='Nome abreviado do time'),
                        'logo_url': openapi.Schema(type=openapi.TYPE_STRING, description='URL do logo do time'),
                        'country': openapi.Schema(type=openapi.TYPE_STRING, description='País do time'),
                        'founded': openapi.Schema(type=openapi.TYPE_INTEGER, description='Ano de fundação')
                    }
                )
            ),
            404: "Campeonato não encontrado"
        }
    )
    @action(detail=True, methods=['get'])
    def teams(self, request, pk=None):
        """Retorna todos os times participantes de um campeonato."""
        championship = self.get_object()
        
        # Buscar times associados ao campeonato
        teams = championship.teams.all()
        
        serializer = TeamSerializer(teams, many=True, context={'request': request})
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Retorna todas as partidas de um campeonato",
        responses={
            200: MatchSerializer(many=True),
            404: "Campeonato não encontrado"
        }
    )
    @action(detail=True, methods=['get'])
    def matches(self, request, pk=None):
        """Retorna todas as partidas de um campeonato."""
        championship = self.get_object()
        matches = Match.objects.filter(
            round__stage__championship=championship
        ).select_related('home_team', 'away_team', 'round', 'round__stage')
        
        # Adicionar filtros opcionais
        status = request.query_params.get('status')
        if status:
            matches = matches.filter(status=status)
        
        # Ordenar por data
        matches = matches.order_by('match_date')
        
        serializer = MatchSerializer(matches, many=True, context={'request': request})
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Retorna a classificação de um campeonato",
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'team': openapi.Schema(
                            type=openapi.TYPE_OBJECT, 
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'name': openapi.Schema(type=openapi.TYPE_STRING),
                                'logo_url': openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        ),
                        'position': openapi.Schema(type=openapi.TYPE_INTEGER, description='Posição na tabela'),
                        'played': openapi.Schema(type=openapi.TYPE_INTEGER, description='Jogos disputados'),
                        'won': openapi.Schema(type=openapi.TYPE_INTEGER, description='Vitórias'),
                        'drawn': openapi.Schema(type=openapi.TYPE_INTEGER, description='Empates'),
                        'lost': openapi.Schema(type=openapi.TYPE_INTEGER, description='Derrotas'),
                        'goals_for': openapi.Schema(type=openapi.TYPE_INTEGER, description='Gols marcados'),
                        'goals_against': openapi.Schema(type=openapi.TYPE_INTEGER, description='Gols sofridos'),
                        'goal_difference': openapi.Schema(type=openapi.TYPE_INTEGER, description='Saldo de gols'),
                        'points': openapi.Schema(type=openapi.TYPE_INTEGER, description='Pontos')
                    }
                )
            ),
            404: "Campeonato não encontrado ou tabela não disponível"
        }
    )
    @action(detail=True, methods=['get'])
    def standings(self, request, pk=None):
        """Retorna a classificação de um campeonato."""
        championship = self.get_object()
        
        # Verificar se o campeonato tem suporte para tabela de classificação
        if not championship.has_standings:
            return Response({"error": "Este campeonato não possui tabela de classificação"}, status=404)
        
        # Aqui iria a lógica para calcular ou buscar a classificação
        # Para simplificar, retornamos dados fictícios
        standings = []
        
        # Buscar times do campeonato
        home_teams = Match.objects.filter(championship=championship).values_list('home_team', flat=True).distinct()
        away_teams = Match.objects.filter(championship=championship).values_list('away_team', flat=True).distinct()
        team_ids = set(list(home_teams) + list(away_teams))
        teams = Team.objects.filter(id__in=team_ids)
        
        # Para cada time, calcular estatísticas
        for position, team in enumerate(teams, 1):
            # Partidas como mandante
            home_matches = Match.objects.filter(
                championship=championship,
                home_team=team,
                status='completed'
            )
            
            # Partidas como visitante
            away_matches = Match.objects.filter(
                championship=championship,
                away_team=team,
                status='completed'
            )
            
            # Estatísticas
            played = home_matches.count() + away_matches.count()
            won = home_matches.filter(home_score__gt=Match.objects.values('away_score')).count() + \
                  away_matches.filter(away_score__gt=Match.objects.values('home_score')).count()
            drawn = home_matches.filter(home_score=Match.objects.values('away_score')).count() + \
                    away_matches.filter(away_score=Match.objects.values('home_score')).count()
            lost = played - won - drawn
            
            # Gols marcados/sofridos (simplificado)
            goals_for = 0
            goals_against = 0
            
            standings.append({
                'team': {
                    'id': team.id,
                    'name': team.name,
                    'logo_url': team.logo_url
                },
                'position': position,
                'played': played,
                'won': won,
                'drawn': drawn,
                'lost': lost,
                'goals_for': goals_for,
                'goals_against': goals_against,
                'goal_difference': goals_for - goals_against,
                'points': (won * 3) + drawn
            })
        
        # Ordenar por pontos (depois por saldo de gols, etc.)
        standings.sort(key=lambda x: (x['points'], x['goal_difference']), reverse=True)
        
        return Response(standings)


class MatchViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint para visualizar partidas de um campeonato."""
    queryset = Match.objects.all().select_related(
        'home_team', 'away_team', 'round', 'round__stage'
    )
    serializer_class = MatchSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtra partidas pelo ID do campeonato."""
        championship_id = self.kwargs.get('championship_id')
        if not championship_id:
            return Match.objects.none()
        
        queryset = Match.objects.filter(
            round__stage__championship_id=championship_id
        ).select_related(
            'home_team', 'away_team', 'round', 'round__stage'
        )
        
        # Filtro por estágio/fase
        stage_id = self.request.query_params.get('stage', None)
        if stage_id:
            queryset = queryset.filter(round__stage_id=stage_id)
        
        # Filtro por rodada
        round_id = self.request.query_params.get('round', None)
        if round_id:
            queryset = queryset.filter(round_id=round_id)
            
        return queryset 