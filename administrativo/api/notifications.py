from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, SerializerMethodField, CharField
from rest_framework.decorators import action
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ..models import Notifications, User

class NotificationSerializer(ModelSerializer):
    """Serializer para notificações."""
    image_url = SerializerMethodField()
    
    class Meta:
        model = Notifications
        fields = [
            'id', 'title', 'message', 'image_url', 'created_at', 
            'is_read', 'action_url', 'notification_type'
        ]
        read_only_fields = ['id', 'title', 'message', 'image_url', 'created_at', 'notification_type']
    
    def get_image_url(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class DeviceRegistrationSerializer(ModelSerializer):
    """Serializer para registro de dispositivos para notificações push."""
    token = CharField(required=True)
    platform = CharField(required=True)
    device_name = CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ['token', 'platform', 'device_name']


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint para visualizar notificações."""
    queryset = Notifications.objects.all().order_by('-created_at')
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retorna apenas notificações do usuário autenticado."""
        user = self.request.user
        queryset = Notifications.objects.filter(
            user=user,
        ).order_by('-created_at')
        
        # Filtro por status de leitura
        read_status = self.request.query_params.get('read', None)
        if read_status is not None:
            is_read = read_status.lower() == 'true'
            queryset = queryset.filter(is_read=is_read)
            
        # Filtro por tipo de notificação
        notification_type = self.request.query_params.get('type', None)
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
            
        return queryset
    
    def get_serializer_context(self):
        """Adiciona o request ao contexto do serializer."""
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    def update(self, request, *args, **kwargs):
        """Marcar como lida ou não lida."""
        notification = self.get_object()
        is_read = request.data.get('is_read', True)
        
        notification.is_read = is_read
        notification.save()
        
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Marcar todas as notificações como lidas",
        responses={
            200: openapi.Response(
                description="Notificações marcadas como lidas",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            )
        }
    )
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Marcar todas as notificações como lidas."""
        queryset = self.get_queryset().filter(is_read=False)
        count = queryset.count()
        
        queryset.update(is_read=True)
        
        return Response({
            "success": True,
            "message": f"{count} notificações marcadas como lidas.",
            "count": count
        })
    
    @swagger_auto_schema(
        operation_description="Registrar dispositivo para notificações push",
        request_body=DeviceRegistrationSerializer,
        responses={
            200: openapi.Response(
                description="Dispositivo registrado com sucesso",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: "Dados inválidos"
        }
    )
    @action(detail=False, methods=['post'], url_path='register')
    def register_device(self, request):
        """Registrar dispositivo para notificações push."""
        serializer = DeviceRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            
            # Aqui você pode salvar os dados do dispositivo no seu sistema
            # Pode usar um modelo específico para dispositivos ou adicionar ao usuário
            
            # Exemplo simples: armazenando token em user field
            user.push_token = serializer.validated_data['token']
            user.push_platform = serializer.validated_data['platform']
            user.push_device_name = serializer.validated_data.get('device_name', '')
            user.save(update_fields=['push_token', 'push_platform', 'push_device_name'])
            
            return Response({
                "success": True,
                "message": "Dispositivo registrado com sucesso para notificações."
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 