from rest_framework import status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView as BaseTokenRefreshView, TokenVerifyView as BaseTokenVerifyView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.conf import settings
from ..models import User
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
import requests
import json
from django.db import transaction

class LoginSerializer(serializers.Serializer):
    """Serializer para autenticação de usuários."""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

class SocialLoginSerializer(serializers.Serializer):
    """Serializer para autenticação social de usuários."""
    provider = serializers.ChoiceField(choices=['facebook', 'google', 'apple'], required=True)
    token = serializers.CharField(required=True)
    aceitaTermos = serializers.BooleanField(required=True)

class TokenSerializer(serializers.Serializer):
    """Serializer para o retorno do token após login bem-sucedido."""
    access = serializers.CharField()
    refresh = serializers.CharField()
    user_id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField()

class LoginView(APIView):
    """
    API endpoint para login de usuários.
    
    Autentica um usuário através de email e senha, retornando tokens JWT (access e refresh).
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    # Definir parâmetros para documentação Swagger
    @swagger_auto_schema(
        operation_description="Endpoint para autenticação de usuários e obtenção de tokens JWT",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email do usuário'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Senha do usuário'),
            }
        ),
        responses={
            200: openapi.Response(
                description="Login bem-sucedido",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Token de refresh'),
                        'access': openapi.Schema(type=openapi.TYPE_STRING, description='Token de acesso'),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'name': openapi.Schema(type=openapi.TYPE_STRING),
                                'futcoins': openapi.Schema(type=openapi.TYPE_INTEGER),
                            }
                        )
                    }
                )
            ),
            400: "Requisição inválida - dados incompletos",
            401: "Credenciais inválidas",
            500: "Erro interno do servidor"
        }
    )
    def post(self, request):
        """
        Realiza o login do usuário e retorna os tokens de acesso.
        
        Args:
            email: Email do usuário
            password: Senha do usuário
            
        Returns:
            access: Token de acesso JWT
            refresh: Token de atualização JWT
            user_id: ID do usuário
            name: Nome do usuário
            email: Email do usuário
        """
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            password = serializer.validated_data.get('password')
            
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                refresh = RefreshToken.for_user(user)
                
                response_data = {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user_id': user.id,
                    'name': user.get_full_name(),
                    'email': user.email
                }
                
                return Response(
                    response_data,
                    status=status.HTTP_200_OK
                )
            return Response(
                {'detail': 'Credenciais inválidas.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class SocialLoginView(APIView):
    """
    API endpoint para login social de usuários (Facebook, Google, Apple).
    
    Autentica um usuário através de token de autenticação social, retornando tokens JWT.
    """
    permission_classes = [AllowAny]
    serializer_class = SocialLoginSerializer

    @swagger_auto_schema(
        operation_description="Endpoint para autenticação social de usuários e obtenção de tokens JWT",
        request_body=SocialLoginSerializer,
        responses={
            200: openapi.Response(
                description="Login social bem-sucedido",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'token': openapi.Schema(type=openapi.TYPE_STRING, description='Token de acesso'),
                        'refreshToken': openapi.Schema(type=openapi.TYPE_STRING, description='Token de refresh'),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'nome': openapi.Schema(type=openapi.TYPE_STRING),
                                'sobrenome': openapi.Schema(type=openapi.TYPE_STRING),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'planoCraque': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'futcoins': openapi.Schema(type=openapi.TYPE_INTEGER),
                            }
                        )
                    }
                )
            ),
            400: "Requisição inválida - dados incompletos ou token inválido",
            401: "Falha na autenticação social",
            500: "Erro interno do servidor"
        }
    )
    def post(self, request):
        """
        Realiza o login social do usuário e retorna os tokens de acesso.
        
        Args:
            provider: Provedor de autenticação (facebook, google, apple)
            token: Token de autenticação do provedor
            aceitaTermos: Se o usuário aceita os termos de uso
            
        Returns:
            token: Token de acesso JWT
            refreshToken: Token de atualização JWT
            user: Dados do usuário
        """
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        provider = serializer.validated_data.get('provider')
        token = serializer.validated_data.get('token')
        aceita_termos = serializer.validated_data.get('aceitaTermos')

        if not aceita_termos:
            return Response(
                {'detail': 'É necessário aceitar os termos de uso.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Verificar o token com o provedor e obter informações do usuário
            user_info = self._get_social_user_info(provider, token)
            
            if not user_info or 'email' not in user_info:
                return Response(
                    {'detail': f'Não foi possível obter as informações do usuário com o token {provider}.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Criar ou atualizar usuário
            with transaction.atomic():
                user = self._get_or_create_user(provider, user_info)
                
                # Gerar tokens JWT
                refresh = RefreshToken.for_user(user)
                
                response_data = {
                    'token': str(refresh.access_token),
                    'refreshToken': str(refresh),
                    'user': {
                        'id': user.id,
                        'nome': user.first_name,
                        'sobrenome': user.last_name,
                        'email': user.email,
                        'planoCraque': user.is_star,
                        'futcoins': user.futcoins,
                    }
                }
                
                return Response(response_data, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response(
                {'detail': f'Erro na autenticação social: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_social_user_info(self, provider, token):
        """Obtém informações do usuário a partir do token de autenticação social."""
        if provider == 'facebook':
            return self._get_facebook_user_info(token)
        elif provider == 'google':
            return self._get_google_user_info(token)
        elif provider == 'apple':
            return self._get_apple_user_info(token)
        return None
    
    def _get_facebook_user_info(self, token):
        """Obtém informações do usuário do Facebook."""
        url = f"https://graph.facebook.com/me?fields=id,name,email,first_name,last_name&access_token={token}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None
    
    def _get_google_user_info(self, token):
        """Obtém informações do usuário do Google."""
        url = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    
    def _get_apple_user_info(self, token):
        """
        Obtém informações do usuário da Apple.
        
        Apple ID Token é um JWT - precisamos decodificar para obter informações
        ou confiar nas informações enviadas pelo cliente.
        """
        # Para Apple, geralmente as informações são enviadas pelo cliente
        # no primeiro login, então podemos precisar utilizar informações adicionais
        try:
            # Tenta extrair email do token (JWT)
            import jwt
            from jwt.algorithms import RSAAlgorithm
            
            # Isso é simplificado - em produção você deveria buscar as chaves públicas da Apple
            token_parts = token.split('.')
            if len(token_parts) == 3:
                payload = token_parts[1]
                # Adicionar padding se necessário
                padding = '=' * (4 - len(payload) % 4)
                payload += padding
                import base64
                decoded = base64.b64decode(payload)
                return json.loads(decoded)
        except Exception as e:
            print(f"Erro ao decodificar token Apple: {str(e)}")
        
        # Se não conseguirmos decodificar, retornamos None ou 
        # utilizamos as informações suplementares enviadas pelo cliente
        return None
    
    def _get_or_create_user(self, provider, user_info):
        """Obtém ou cria um usuário com base nas informações sociais."""
        email = user_info.get('email')
        
        try:
            user = User.objects.get(email=email)
            
            # Atualizar informações sociais
            if provider == 'facebook':
                user.facebook_linked = True
            elif provider == 'google':
                user.google_linked = True
                
            # Atualizar nome se ainda não estiver definido
            if not user.first_name and 'first_name' in user_info:
                user.first_name = user_info.get('first_name', '')
            if not user.last_name and 'last_name' in user_info:
                user.last_name = user_info.get('last_name', '')
                
            user.save()
            
        except User.DoesNotExist:
            # Criar novo usuário
            first_name = user_info.get('first_name', '') or user_info.get('given_name', '')
            last_name = user_info.get('last_name', '') or user_info.get('family_name', '')
            
            # Se o nome completo estiver em 'name' mas não temos first/last name
            if not first_name and 'name' in user_info:
                parts = user_info['name'].split(' ', 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ''
                
            user = User.objects.create(
                username=email,  # Email como username
                email=email,
                first_name=first_name,
                last_name=last_name,
                futcoins=0,  # Começa com zero futcoins
            )
            
            # Marcar conta como vinculada ao provedor
            if provider == 'facebook':
                user.facebook_linked = True
            elif provider == 'google':
                user.google_linked = True
                
            user.save()
            
        return user


# Usando as classes base do JWT com customizações se necessário
class TokenRefreshView(BaseTokenRefreshView):
    """
    API endpoint para atualizar tokens JWT expirados.
    """
    @swagger_auto_schema(
        operation_description="Renovar token de acesso usando token de refresh",
        responses={
            200: openapi.Response(
                description="Token renovado com sucesso",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING, description='Novo token de acesso'),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Novo token de refresh (se ROTATE_REFRESH_TOKENS estiver ativado)'),
                    }
                )
            ),
            401: "Token de refresh inválido ou expirado"
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TokenVerifyView(BaseTokenVerifyView):
    """
    API endpoint para verificar se um token JWT é válido.
    """
    @swagger_auto_schema(
        operation_description="Verificar se um token JWT é válido",
        responses={
            200: "Token válido",
            401: "Token inválido ou expirado"
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs) 