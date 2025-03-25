from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from ..models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer, CharField, EmailField, ValidationError as SerializerValidationError
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import datetime
from django.utils import timezone

class UserSerializer(ModelSerializer):
    """Serializer para o modelo de usuário."""
    password = CharField(write_only=True, required=True)
    email = EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'password', 'futcoins']
        read_only_fields = ['id', 'futcoins']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }
    
    def validate_email(self, value):
        """Valida se o email já está em uso."""
        if User.objects.filter(email=value).exists():
            raise SerializerValidationError("Este email já está em uso.")
        return value
    
    def validate_password(self, value):
        """Valida a senha usando os validadores do Django."""
        try:
            validate_password(value)
        except ValidationError as e:
            raise SerializerValidationError(e.messages)
        return value
    
    def create(self, validated_data):
        """Cria um novo usuário com senha criptografada."""
        with transaction.atomic():
            user = User.objects.create(
                username=validated_data['email'],  # Usando email como username
                email=validated_data['email'],
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                futcoins=0  # Inicia com zero futcoins
            )
            
            user.set_password(validated_data['password'])
            user.save()
            
            return user


class UserProfileSerializer(ModelSerializer):
    """Serializer para perfil de usuário."""
    full_name = CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'futcoins']
        read_only_fields = ['id', 'email', 'futcoins']


class RewardResponseSerializer(ModelSerializer):
    """Serializer para resposta de recompensas."""
    message = CharField(read_only=True)
    
    class Meta:
        model = User
        fields = ['futcoins', 'message']
        read_only_fields = ['futcoins']


class UserViewSet(viewsets.ModelViewSet):
    """API endpoint para gerenciar usuários."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']  # Não permite PUT
    
    def get_permissions(self):
        """Define permissões com base na ação."""
        if self.action == 'create':
            return [permissions.AllowAny()]  # Registro é público
        return [permissions.IsAuthenticated()]
    
    def get_serializer_class(self):
        """Seleciona o serializer apropriado com base na ação."""
        if self.action in ['me', 'update', 'partial_update']:
            return UserProfileSerializer
        elif self.action in ['daily_reward', 'video_reward']:
            return RewardResponseSerializer
        return UserSerializer
    
    @swagger_auto_schema(
        operation_description="Retorna o perfil do usuário autenticado",
        responses={
            200: openapi.Response(
                description="Perfil do usuário",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'email': openapi.Schema(type=openapi.TYPE_STRING),
                        'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                        'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                        'full_name': openapi.Schema(type=openapi.TYPE_STRING),
                        'futcoins': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            ),
            401: "Não autenticado"
        }
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Retorna o perfil do usuário autenticado."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Registra um novo usuário",
        request_body=UserSerializer,
        responses={
            201: UserProfileSerializer,
            400: "Dados inválidos"
        }
    )
    def create(self, request, *args, **kwargs):
        """Cria um novo usuário (registro)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response(
            UserProfileSerializer(user).data,
            status=status.HTTP_201_CREATED
        )
    
    @swagger_auto_schema(
        operation_description="Recebe recompensa diária",
        responses={
            200: RewardResponseSerializer,
            400: "Recompensa já coletada hoje",
            401: "Não autenticado"
        }
    )
    @action(detail=False, methods=['post'], url_path='rewards/daily')
    def daily_reward(self, request):
        """Recompensa diária para o usuário."""
        user = request.user
        
        # Verificar último acesso e se já recebeu a recompensa hoje
        last_daily_reward = getattr(user, 'last_daily_reward', None)
        today = timezone.now().date()
        
        if last_daily_reward and last_daily_reward.date() == today:
            return Response(
                {"error": "Você já coletou sua recompensa diária hoje."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Adicionar futcoins (valor configurável)
        daily_reward_amount = 50  # Valor fixo para exemplo, poderia vir de configuração
        user.futcoins += daily_reward_amount
        user.last_daily_reward = timezone.now()
        user.save()
        
        return Response({
            "futcoins": user.futcoins,
            "message": f"Você recebeu {daily_reward_amount} Futcoins como recompensa diária!"
        })
    
    @swagger_auto_schema(
        operation_description="Recebe recompensa por assistir vídeo",
        responses={
            200: RewardResponseSerializer,
            400: "Limite de recompensas por vídeo atingido",
            401: "Não autenticado"
        }
    )
    @action(detail=False, methods=['post'], url_path='rewards/video')
    def video_reward(self, request):
        """Recompensa por assistir vídeo."""
        user = request.user
        
        # Verificar número de recompensas por vídeo hoje
        video_rewards_today = getattr(user, 'video_rewards_today', 0)
        last_video_reward_date = getattr(user, 'last_video_reward_date', None)
        today = timezone.now().date()
        
        # Resetar contador se for um novo dia
        if last_video_reward_date is None or last_video_reward_date != today:
            video_rewards_today = 0
        
        # Verificar limite diário (exemplo: 5 vídeos por dia)
        max_daily_videos = 5
        if video_rewards_today >= max_daily_videos:
            return Response(
                {"error": f"Você já atingiu o limite de {max_daily_videos} recompensas por vídeo hoje."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Adicionar futcoins
        video_reward_amount = 20  # Valor fixo para exemplo
        user.futcoins += video_reward_amount
        user.video_rewards_today = video_rewards_today + 1
        user.last_video_reward_date = today
        user.save()
        
        return Response({
            "futcoins": user.futcoins,
            "message": f"Você recebeu {video_reward_amount} Futcoins como recompensa por assistir o vídeo!"
        }) 