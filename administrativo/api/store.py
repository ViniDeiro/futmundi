from rest_framework import viewsets, serializers, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from ..models import FutcoinPackage, Plan, User
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class FutcoinPackageSerializer(serializers.ModelSerializer):
    """Serializer para pacotes de Futcoins."""
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = FutcoinPackage
        fields = [
            'id', 'name', 'content', 'image_url', 'full_price',
            'promotional_price', 'bonus', 'enabled', 'color_background_label',
            'color_text_label', 'label'
        ]
        read_only_fields = fields
        
    def get_image_url(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class PlanSerializer(serializers.ModelSerializer):
    """Serializer para planos de assinatura."""
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'content', 'image_url', 
            'full_price', 'promotional_price', 'end_date', 
            'enabled', 'color_background_label', 'color_text_label'
        ]
        read_only_fields = fields
        
    def get_image_url(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class PackageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint para visualizar pacotes de Futcoins e planos de assinatura.
    
    list:
        Retorna uma lista paginada de pacotes de Futcoins ativos.
    
    retrieve:
        Retorna os detalhes de um pacote específico.
    
    plans:
        Retorna uma lista de planos de assinatura ativos.
    
    purchase:
        Simula a compra de um pacote (usado para fluxo de pagamento).
    """
    queryset = FutcoinPackage.objects.filter(enabled=True).order_by('full_price')
    serializer_class = FutcoinPackageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    @swagger_auto_schema(
        operation_description="Lista os planos de assinatura disponíveis",
        responses={
            200: PlanSerializer(many=True),
            401: "Não autenticado"
        }
    )
    @action(detail=False, methods=['get'])
    def plans(self, request):
        """Retorna os planos de assinatura disponíveis."""
        plans = Plan.objects.filter(enabled=True).order_by('full_price')
        serializer = PlanSerializer(plans, many=True, context=self.get_serializer_context())
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Inicia o processo de compra de um pacote",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'payment_method': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='Método de pagamento (card, pix, etc)'
                ),
            },
            required=['payment_method']
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'transaction_id': openapi.Schema(type=openapi.TYPE_STRING),
                    'payment_url': openapi.Schema(type=openapi.TYPE_STRING),
                }
            ),
            400: "Dados inválidos ou erro no pagamento",
            404: "Pacote não encontrado"
        }
    )
    @action(detail=True, methods=['post'])
    def purchase(self, request, pk=None):
        """
        Inicia o processo de compra de um pacote.
        
        Esta é uma simulação para o fluxo de integração com a API do app.
        Na implementação real, integraria com um gateway de pagamento.
        """
        package = self.get_object()
        payment_method = request.data.get('payment_method')
        
        if not payment_method:
            return Response(
                {"detail": "Método de pagamento é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Simular uma transação iniciada
        # Em um cenário real, chamaríamos a API do gateway de pagamento
        
        if payment_method == 'pix':
            # Simular dados de PIX
            return Response({
                'transaction_id': f'pix_{package.id}_{request.user.id}',
                'payment_url': 'https://api.example.com/payments/pix/123456',
                'qr_code': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='
            })
        elif payment_method == 'card':
            # Simular dados de cartão
            return Response({
                'transaction_id': f'card_{package.id}_{request.user.id}',
                'payment_url': 'https://api.example.com/payments/card/123456'
            })
        else:
            return Response(
                {"detail": f"Método de pagamento '{payment_method}' não suportado."},
                status=status.HTTP_400_BAD_REQUEST
            ) 