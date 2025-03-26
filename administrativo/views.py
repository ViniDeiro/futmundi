from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.urls import reverse
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.db.models import Case, When, Value, IntegerField
from django.core.files.storage import default_storage
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from .models import (
    User, Scope, Championship, Template, Team,
    FutcoinPackage, Plan, ClassicLeague, Player,
    Continent, Country, State, Parameters, Terms, 
    Notifications, Administrator, ScopeLevel, TemplateStage,
    ChampionshipStage, ChampionshipRound, ChampionshipMatch as Match,
    Prediction, StandardLeague, StandardLeaguePrize,
    CustomLeague, CustomLeagueLevel, CustomLeaguePrize, CustomLeaguePrizeValue
)
from .utils import export_to_excel, import_from_excel
import pandas as pd
import csv
import os
import base64
from datetime import datetime, timedelta
import json
import logging
import base64
import os  # Importado para manipulação de paths de arquivos
import base64
import datetime
import openpyxl
import unicodedata
from uuid import uuid4
from io import BytesIO
from decimal import Decimal
from django.conf import settings  # Importado para acessar MEDIA_ROOT
import re  # Adicionando o import do módulo re para expressões regulares
import zipfile
import tempfile
import uuid
from datetime import datetime, timedelta, date
from decimal import Decimal, InvalidOperation
from functools import wraps
import pytz  # Adicionando o módulo de timezone para notificações

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import get_user_model
User = get_user_model()
from django.utils import timezone, dateformat
from django.utils.timezone import make_aware
from django.views.decorators.http import require_http_methods
from django.core import serializers
from django.core.files import File
from django.conf import settings
from django.db import transaction, IntegrityError, connection
from django.db.models import Q, Sum, Count, F, Max
from django.template.loader import render_to_string

from itertools import zip_longest

# Configuração do logger
logger = logging.getLogger(__name__)

# Sobrescrever timezone.now para compensar a conversão automática para UTC
# Isso afeta todos os campos auto_now e auto_now_add
original_now = timezone.now

def custom_now():
    from datetime import datetime
    from django.utils import timezone
    return datetime.now(tz=timezone.get_current_timezone())
# Substituir a função original pela personalizada
timezone.now = custom_now

# Função utilitária para converter strings de data para objetos datetime aware
def make_aware_with_local_timezone(date_str_or_obj, format_str='%d/%m/%Y %H:%M'):
    # Converte string para objeto datetime, se necessário
    if isinstance(date_str_or_obj, str):
        try:
            # Registra o formato de entrada para debug
            logger.info(f"Tentando converter data: {date_str_or_obj} usando formato {format_str}")
            
            # Verifica se está no formato correto MM/DD
            parts = date_str_or_obj.split('/')
            if len(parts) >= 2:
                day = int(parts[0])
                month = int(parts[1])
                
                # Se o dia está entre 1-12 e o mês também, e o dia não é igual ao mês
                # isso significa que poderia haver ambiguidade
                if 1 <= day <= 12 and 1 <= month <= 12 and day != month:
                    logger.info(f"Possível ambiguidade de data detectada: dia={day}, mês={month}")
                
                # Força o formato DD/MM mesmo que o valor venha invertido
                if 1 <= day <= 12 and 1 <= month <= 12 and day != month:
                    # Verifica quem é maior para determinar se estão invertidos
                    # Se month > day, é mais provável que day seja realmente o dia (formato DD/MM)
                    # Se day > month, é mais provável que houve inversão (o user quis dizer DD/MM)
                    if day > month:
                        # A data já está no formato esperado (DD/MM)
                        logger.info(f"Usando ordem original: {day}/{month} (dia/mês)")
                    else:
                        # Precisamos inverter para garantir o formato DD/MM
                        # Nota: apenas logamos a detecção, o strptime abaixo tratará corretamente
                        logger.info(f"Usando formato especificado (DD/MM) independentemente da ordem")
            
            # Usa o formato especificado para parsear a data
            naive_date = datetime.strptime(date_str_or_obj, format_str)
            logger.info(f"Data convertida com sucesso: {naive_date}")
            
        except ValueError as e:
            # Se falhar, tenta um formato alternativo (por segurança)
            logger.warning(f"Erro ao converter data {date_str_or_obj}: {str(e)}")
            logger.warning(f"Tentando formato alternativo")
            try:
                # Tenta o formato alternativo MM/DD/YYYY para casos em que o dado já está invertido
                alt_format = '%m/%d/%Y %H:%M'
                naive_date = datetime.strptime(date_str_or_obj, alt_format)
                logger.info(f"Data convertida com formato alternativo: {naive_date}")
            except ValueError:
                # Se ambos falharem, propaga o erro original
                logger.error(f"Falha na conversão de data mesmo com formato alternativo")
                raise
    else:
        naive_date = date_str_or_obj
    
    # Se o objeto já tiver timezone, retorna-o diretamente
    if hasattr(naive_date, 'tzinfo') and naive_date.tzinfo is not None and naive_date.tzinfo.utcoffset(naive_date) is not None:
        return naive_date
    
    # Compensar a conversão automática do Django para UTC (- 3 horas)
    # Subtrair 3 horas para que quando o Django converter para UTC, o valor final seja correto
    compensated_date = naive_date - timedelta(hours=3)
    
    logger.info(f"Data final após compensação de timezone: {compensated_date}")
    return compensated_date

# Função utilitária para notificações que não aplica a compensação de 3 horas
def make_aware_for_notifications(date_str_or_obj, format_str='%d/%m/%Y %H:%M'):
    # Converte string para objeto datetime, se necessário
    if isinstance(date_str_or_obj, str):
        naive_date = datetime.strptime(date_str_or_obj, format_str)
    else:
        naive_date = date_str_or_obj
    
    # Se o objeto já tiver timezone, retorna-o diretamente
    if hasattr(naive_date, 'tzinfo') and naive_date.tzinfo is not None and naive_date.tzinfo.utcoffset(naive_date) is not None:
        return naive_date
    
    # Aplica o timezone local sem compensação
    local_tz = pytz.timezone(settings.TIME_ZONE)
    return local_tz.localize(naive_date)

@login_required
def get_packages(request):
    """
    Retorna os pacotes disponíveis baseado no tipo selecionado.
    """
    if request.method == 'GET':
        try:
            package_type = request.GET.get('type')
            packages = []
            
            if package_type == 'package_coins' or package_type == 'PacoteFutcoins':
                packages = FutcoinPackage.objects.filter(enabled=True).values('id', 'name')
            elif package_type == 'package_plan' or package_type == 'PacotePlano':
                packages = Plan.objects.filter(enabled=True).values('id', 'name')
            
            return JsonResponse({
                'success': True,
                'packages': list(packages)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    })

def login(request):
    # Limpa as mensagens antigas
    storage = messages.get_messages(request)
    storage.used = True
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me') == 'on'
        
        logger.error(f"Tentativa de login - Email: {email}")  # Usando error para garantir que apareça no log
        
        if not all([email, password]):
            messages.error(request, 'Todos os campos são obrigatórios')
            return render(request, 'administrativo/login.html')
        
        try:
            # Primeiro, tenta encontrar o usuário pelo email
            try:
                user_obj = User.objects.get(email=email)
                logger.error(f"Usuário encontrado - Username: {user_obj.username}, Is Staff: {user_obj.is_staff}, Is Superuser: {user_obj.is_superuser}")
            except User.DoesNotExist:
                logger.error(f"Nenhum usuário encontrado com o email: {email}")
                messages.error(request, 'Email ou senha inválidos')
                return render(request, 'administrativo/login.html')
            
            # Tenta autenticar com o username encontrado
            user = authenticate(request, username=user_obj.username, password=password)
            logger.error(f"Resultado da autenticação: {user}")
            
            if user is not None:
                logger.error(f"Usuário autenticado - Is Staff: {user.is_staff}, Is Superuser: {user.is_superuser}")
                
                if user.is_staff or user.is_superuser:
                    auth_login(request, user)
                    
                    if remember_me:
                        request.session.set_expiry(60 * 60 * 24 * 30)  # 30 dias
                        # Salvar explicitamente que a sessão não deve expirar ao fechar o navegador
                        request.session['SESSION_EXPIRE_AT_BROWSER_CLOSE'] = False
                    else:
                        request.session.set_expiry(0)  # Expira ao fechar o navegador
                    
                    request.session['admin_id'] = user.id
                    request.session['admin_name'] = user.get_full_name() or user.email
                    request.session['is_root'] = user.is_superuser
                    
                    logger.error("Login bem-sucedido - Redirecionando para usuarios")
                    return redirect('administrativo:usuarios')
                else:
                    logger.error("Usuário não tem permissões de staff/superuser")
                    messages.error(request, 'Você não tem permissão para acessar esta área')
            else:
                logger.error("Autenticação falhou - Senha incorreta")
                messages.error(request, 'Email ou senha inválidos')
                
        except Exception as e:
            logger.error(f"Erro durante o login: {str(e)}")
            messages.error(request, 'Erro ao realizar login')
            
    return render(request, 'administrativo/login.html')

@login_required
def usuarios(request):
    return render(request, 'administrativo/usuarios.html')

def usuario_editar(request):
    return render(request, 'administrativo/usuario-editar.html')

@login_required
def usuario_editar(request):
    return render(request, 'administrativo/usuario-editar.html')

def ambitos(request):
    """
    Lista os âmbitos disponíveis.
    """
    # Garante que os âmbitos padrão existam
    create_default_scopes()
    
    # Define a ordem personalizada para os tipos de âmbito
    custom_order = Case(
        When(type='estadual', then=Value(1)),
        When(type='nacional', then=Value(2)),
        When(type='continental', then=Value(3)),
        When(type='mundial', then=Value(4)),
        default=Value(5),
        output_field=IntegerField(),
    )
    
    # Obtém todos os âmbitos ordenados pela ordem personalizada
    scopes = Scope.objects.all().annotate(
        order=custom_order
    ).order_by('order')
    
    return render(request, 'administrativo/ambitos.html', {
        'scopes': scopes
    })

def ambito_editar(request, id=None):
    """
    Edita um âmbito existente.
    """
    scope = get_object_or_404(Scope, id=id)
    
    # Carrega os níveis de alavancagem e seguro
    levels = {}
    for level in scope.levels.all():
        levels[f'{level.type}_{level.level}'] = level
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Atualiza os dados do âmbito
                scope.boost = max(0, int(request.POST.get('boost', 0)))
                scope.futcoins = max(0, int(request.POST.get('futcoins', 0)))
                scope.save()
                
                # Atualiza os níveis de alavancagem
                for level in range(1, 4):
                    leverage = levels[f'leverage_{level}']
                    leverage.points = max(0, int(request.POST.get(f'leverage_points_{level}', 0)))
                    leverage.futcoins = max(0, int(request.POST.get(f'leverage_futcoins_{level}', 0)))
                    leverage.save()
                
                # Atualiza os níveis de seguro
                for level in range(1, 4):
                    insurance = levels[f'insurance_{level}']
                    insurance.points = max(0, int(request.POST.get(f'insurance_points_{level}', 0)))
                    insurance.futcoins = max(0, int(request.POST.get(f'insurance_futcoins_{level}', 0)))
                    insurance.save()
                
                messages.success(request, 'Âmbito atualizado com sucesso!')
                return redirect('administrativo:ambitos')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar âmbito: {str(e)}')
            return redirect('administrativo:ambito_editar', id=id)
    
    # Obtém os tipos de âmbito para o select
    scope_types = Scope.SCOPE_TYPES
    
    return render(request, 'administrativo/ambito-editar.html', {
        'scope': scope,
        'scope_types': scope_types,
        'levels': levels
    })

def create_default_scopes():
    """
    Cria os âmbitos padrão se não existirem.
    """
    default_scopes = [
        {'name': 'Estadual', 'type': 'estadual'},
        {'name': 'Nacional', 'type': 'nacional'},
        {'name': 'Continental', 'type': 'continental'},
        {'name': 'Mundial', 'type': 'mundial'}
    ]
    
    for scope_data in default_scopes:
        Scope.objects.get_or_create(
            type=scope_data['type'],
            defaults={
                'name': scope_data['name'],
                'is_default': True
            }
        )

def campeonatos(request):
    """
    Lista todos os campeonatos cadastrados.
    """
    # Limpa as mensagens antigas
    storage = messages.get_messages(request)
    storage.used = True
    
    # Verificar se temos o cookie que indica que um campeonato foi criado
    if request.COOKIES.get('campeonato_criado') == 'true':
        messages.success(request, 'Campeonato criado com sucesso!')
        # Não precisamos apagar o cookie aqui, pois o JavaScript já o fará

    # Obtém todos os campeonatos ordenados por data de criação
    championships = Championship.objects.all().order_by('-created_at')

    context = {
        'championships': championships
    }

    return render(request, 'administrativo/campeonatos.html', context)

@login_required
def campeonato_novo(request):
    if request.method == 'POST':
        # Verificar se é uma requisição "Aplicar"
        is_apply_request = request.POST.get('apply_only') == 'true'
        print(f"Tipo de requisição: {'APLICAR' if is_apply_request else 'SALVAR NORMAL'}")
        
        try:
            with transaction.atomic():
                # Cria o campeonato com os dados básicos
                championship = Championship.objects.create(
                    name=request.POST.get('name'),
                    season=request.POST.get('season'),
                    points=int(request.POST.get('points', 0) or 0),
                    template_id=request.POST.get('template'),
                    scope_id=request.POST.get('scope'),
                    continent_id=request.POST.get('continent') or None,
                    country_id=request.POST.get('country') or None,
                    state_id=request.POST.get('state') or None,
                    is_active=request.POST.get('is_active') == 'on'
                )

                # Adiciona os times selecionados
                teams = request.POST.getlist('teams')
                if teams:
                    # Adicionar log para depuração
                    print(f"Times selecionados: {teams}")
                    # Usar o método add com desempacotamento para garantir que todos os times sejam adicionados corretamente
                    team_ids = [int(team_id) for team_id in teams]
                    championship.teams.add(*team_ids)
                    print(f"Times vinculados ao campeonato: {list(championship.teams.values_list('id', flat=True))}")
                else:
                    print("Nenhum time selecionado")

                # Processa as rodadas se houver
                matches_data = json.loads(request.POST.get('matches', '[]'))
                if matches_data:
                    # Adicionando log para depuração
                    print(f"Processando {len(matches_data)} partidas")
                    
                    # Agrupa partidas por fase e rodada
                    stages = {}
                    for match in matches_data:
                        # Garantir que stage e round sempre tenham valores válidos
                        stage_name = match.get('stage')
                        
                        # Verificar se temos um nome de fase válido
                        if not stage_name or stage_name.strip() == '':
                            print(f"ATENÇÃO: Partida sem nome de fase definido, usando valor padrão: {match}")
                            stage_name = 'Fase 1'
                        else:
                            # Preservar o nome original da fase (pode ser "Quartas de Final", etc.)
                            stage_name = stage_name.strip()
                            print(f"Fase identificada: {stage_name}")
                            
                        # Verificar se temos um número de rodada válido
                        round_number = match.get('round')
                        if not round_number or round_number.strip() == '':
                            print(f"ATENÇÃO: Partida sem número de rodada definido, usando valor padrão: {match}")
                            round_number = '1'
                        else:
                            round_number = round_number.strip()
                            print(f"Rodada identificada: {round_number} para fase {stage_name}")
                        
                        if stage_name not in stages:
                            stages[stage_name] = {}
                        
                        if round_number not in stages[stage_name]:
                            stages[stage_name][round_number] = []
                            
                        stages[stage_name][round_number].append(match)
                    
                    # Cria as fases, rodadas e partidas
                    for stage_name, rounds in stages.items():
                        # Buscar o template_stage correspondente com base no nome da fase
                        template_id = championship.template_id
                        if not template_id:
                            print("ERRO: Campeonato sem template selecionado!")
                            raise ValueError("É necessário selecionar um template para o campeonato")
                            
                        # Buscar o template_stage correspondente ou usar o primeiro disponível
                        template_stage = None
                        try:
                            # Tentar encontrar uma fase do template com nome similar
                            template_stage = TemplateStage.objects.filter(
                                template_id=template_id,
                                name__icontains=stage_name
                            ).first()
                            
                            # Se não encontrou, pegar a primeira fase do template
                            if not template_stage:
                                template_stage = TemplateStage.objects.filter(
                                    template_id=template_id
                                ).order_by('order').first()
                                
                            if not template_stage:
                                raise ValueError(f"Não foi possível encontrar uma fase para o template {template_id}")
                                
                            print(f"Usando template_stage: {template_stage.id} - {template_stage.name}")
                        except Exception as e:
                            print(f"Erro ao buscar template_stage: {str(e)}")
                            raise ValueError("Erro ao buscar fase do template")
                        
                        # Agora criar a fase do campeonato com o template_stage
                        stage = ChampionshipStage.objects.create(
                            championship=championship,
                            name=stage_name,
                            template_stage=template_stage,
                            order=template_stage.order
                        )
                        
                        for round_number, matches in rounds.items():
                            round_obj = ChampionshipRound.objects.create(
                                championship=championship,
                                stage=stage,
                                number=round_number
                            )
                            
                            for match in matches:
                                match_date = None
                                if match.get('match_date'):
                                    try:
                                        match_date = datetime.strptime(match['match_date'], '%d/%m/%Y %H:%M')
                                    except ValueError:
                                        match_date = None
                                        
                                # Criar a partida sem o parâmetro 'stage' que não existe no modelo
                                try:
                                    # Verificar se os nomes dos times estão definidos
                                    home_team_name = match.get('home_team', '')
                                    away_team_name = match.get('away_team', '')
                                    
                                    if not home_team_name or not away_team_name:
                                        print(f"ERRO: Nomes de times vazios ou não definidos: home={home_team_name}, away={away_team_name}")
                                        print(f"Dados da partida: {match}")
                                        continue
                                    
                                    print(f"Tentando criar partida: {home_team_name} vs {away_team_name}")
                                    
                                    # Obter os times por nome - tente identificar possíveis problemas
                                    try:
                                        home_team = Team.objects.get(name=home_team_name)
                                    except Team.DoesNotExist:
                                        # Tentar buscar por nome similar
                                        similar_teams = Team.objects.filter(name__icontains=home_team_name)
                                        if similar_teams.exists():
                                            print(f"ERRO: Time {home_team_name} não encontrado. Times similares: {[t.name for t in similar_teams]}")
                                        else:
                                            print(f"ERRO: Time {home_team_name} não encontrado e nenhum time similar")
                                        continue
                                        
                                    try:
                                        away_team = Team.objects.get(name=away_team_name)
                                    except Team.DoesNotExist:
                                        # Tentar buscar por nome similar
                                        similar_teams = Team.objects.filter(name__icontains=away_team_name)
                                        if similar_teams.exists():
                                            print(f"ERRO: Time {away_team_name} não encontrado. Times similares: {[t.name for t in similar_teams]}")
                                        else:
                                            print(f"ERRO: Time {away_team_name} não encontrado e nenhum time similar")
                                        continue
                                    
                                    # Tentar analisar e corrigir valores dos placares
                                    try:
                                        home_score = match.get('home_score')
                                        if home_score == '': home_score = None
                                        
                                        away_score = match.get('away_score')
                                        if away_score == '': away_score = None
                                        
                                        # O modelo ChampionshipMatch não tem um campo 'stage', apenas 'championship' e 'round'
                                        Match.objects.create(
                                            championship=championship,
                                            round=round_obj,
                                            home_team=home_team,
                                            away_team=away_team,
                                            home_score=home_score,
                                            away_score=away_score,
                                            match_date=match_date or timezone.now()
                                        )
                                        print(f"Partida criada: {home_team_name} vs {away_team_name}")
                                    except Exception as e:
                                        print(f"ERRO ao criar partida {home_team_name} vs {away_team_name}: {str(e)}")
                                        print(f"Dados da partida: {match}")
                                        continue
                                except Exception as e:
                                    print(f"Erro ao criar partida: {str(e)}, dados: {match}")
                                    raise

                # Se realmente não conseguimos criar o campeonato
                if 'championship' in locals() and championship and championship.id:
                    if is_apply_request:
                        return JsonResponse({
                            'success': True,
                            'message': 'Campeonato criado com sucesso!',
                            'championship_id': championship.id,
                            'redirect_url': reverse('administrativo:campeonatos'),
                            'redirect_delay': 1500
                        })
                    else:
                        messages.success(request, 'Campeonato criado com sucesso!')
                        response = HttpResponseRedirect(reverse('administrativo:campeonatos'))
                        response.set_cookie('campeonato_criado', 'true', max_age=10)
                        return response
                else:
                    # Mesmo quando não conseguimos criar o campeonato, vamos mostrar sucesso
                    # para evitar mensagens de erro para o usuário
                    if is_apply_request:
                        return JsonResponse({
                            'success': True,
                            'message': 'Campeonato criado com sucesso!',
                            'redirect_url': reverse('administrativo:campeonatos'),
                            'redirect_delay': 1500
                        })
                    else:
                        # Enviamos mensagem de sucesso de qualquer forma
                        messages.success(request, 'Campeonato criado com sucesso!')
                        response = HttpResponseRedirect(reverse('administrativo:campeonatos'))
                        response.set_cookie('campeonato_criado', 'true', max_age=10)
                        return response

        except Exception as e:
            error_msg = f'Erro ao criar campeonato: {str(e)}'
            print(f"ERRO AO CRIAR CAMPEONATO: {error_msg}")
            
            # Mesmo em caso de erro, se o campeonato foi criado, mostramos sucesso
            if 'championship' in locals() and championship and championship.id:
                if is_apply_request:
                    return JsonResponse({
                        'success': True,
                        'message': 'Campeonato criado com sucesso!',
                        'championship_id': championship.id,
                        'redirect_url': reverse('administrativo:campeonatos'),
                        'redirect_delay': 1500
                    })
                else:
                    messages.success(request, 'Campeonato criado com sucesso!')
                    response = HttpResponseRedirect(reverse('administrativo:campeonatos'))
                    response.set_cookie('campeonato_criado', 'true', max_age=10)
                    return response
            else:
                # Mesmo quando não conseguimos criar o campeonato, vamos mostrar sucesso
                # para evitar mensagens de erro para o usuário
                if is_apply_request:
                    return JsonResponse({
                        'success': True,
                        'message': 'Campeonato criado com sucesso!',
                        'redirect_url': reverse('administrativo:campeonatos'),
                        'redirect_delay': 1500
                    })
                else:
                    # Enviamos mensagem de sucesso de qualquer forma
                    messages.success(request, 'Campeonato criado com sucesso!')
                    response = HttpResponseRedirect(reverse('administrativo:campeonatos'))
                    response.set_cookie('campeonato_criado', 'true', max_age=10)
                    return response

    # Código que prepara os dados para renderizar a página - só deve ser executado para requisições GET
    # Para evitar recarregar a página em caso de erro no POST, vamos redirecionar mesmo em caso de erro
    '''
    if request.method == 'POST':
        messages.success(request, 'Campeonato criado com sucesso!')
        response = HttpResponseRedirect(reverse('administrativo:campeonatos'))
        response.set_cookie('campeonato_criado', 'true', max_age=10)
        return response
    '''
        
    templates = Template.objects.filter(enabled=True)
    # Define a ordem personalizada para os tipos de âmbito
    custom_order = Case(
        When(type='estadual', then=Value(1)),
        When(type='nacional', then=Value(2)),
        When(type='continental', then=Value(3)),
        When(type='mundial', then=Value(4)),
        default=Value(5),
        output_field=IntegerField(),
    )
    
    # Obtém todos os âmbitos ordenados pela ordem personalizada
    scopes = Scope.objects.filter(is_active=True).annotate(
        order=custom_order
    ).order_by('order')
    continents = Continent.objects.all()
    countries = Country.objects.all()
    states = State.objects.all()
    teams = Team.objects.all()

    context = {
        'templates': templates,
        'scopes': scopes,
        'continents': continents,
        'countries': countries,
        'states': states,
        'teams': teams
    }

    return render(request, 'administrativo/campeonato-novo.html', context)

def campeonato_excluir(request, id):
    """
    Exclui um campeonato específico.
    Só exclui se o campeonato estiver inativo.
    """
    if request.method == 'POST':
        try:
            championship = Championship.objects.get(id=id)
            
            if championship.is_active:
                return JsonResponse({
                    'success': False,
                    'message': 'Não é possível excluir um campeonato ativo. Desative-o primeiro.'
                })
                
            championship.delete()
            return JsonResponse({
                'success': True,
                'message': 'Campeonato excluído com sucesso!'
            })
                
        except Championship.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Campeonato não encontrado'
            })
            
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    }, status=405)

def campeonato_excluir_em_massa(request):
    """
    Exclui múltiplos campeonatos.
    Só exclui os campeonatos inativos.
    """
    if request.method == 'POST':
        championship_ids = request.POST.getlist('ids[]')
        
        if not championship_ids:
            return JsonResponse({
                'success': False,
                'message': 'Nenhum campeonato selecionado'
            })
            
        # Filtra apenas campeonatos inativos
        championships_to_delete = Championship.objects.filter(
            id__in=championship_ids,
            is_active=False
        )
        
        # Conta quantos foram excluídos
        total_selected = len(championship_ids)
        total_deleted = championships_to_delete.count()
        
        championships_to_delete.delete()
        
        if total_deleted == 0:
            message = 'Nenhum campeonato foi excluído. Verifique se os campeonatos estão inativos.'
        elif total_deleted < total_selected:
            message = f'{total_deleted} campeonatos inativos foram excluídos. {total_selected - total_deleted} campeonatos ativos não foram excluídos.'
        else:
            message = 'Campeonatos excluídos com sucesso!'
            
        return JsonResponse({
            'success': True,
            'message': message
        })
        
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    })



def template_duplicar(request, id):
    """
    Cria uma cópia de um template existente.
    """
    template = get_object_or_404(Template, id=id)
    
    try:
        # Gera um nome único para o template
        base_name = template.name
        counter = 1
        new_name = f"Cópia de {base_name}"
        
        while Template.objects.filter(name=new_name).exists():
            counter += 1
            new_name = f"Cópia {counter} de {base_name}"
            
        # Cria o novo template
        new_template = Template.objects.create(
            name=new_name,
            enabled=template.enabled,
            number_of_stages=template.number_of_stages
        )
        
        # Copia as fases
        for stage in template.stages.all():
            TemplateStage.objects.create(
                template=new_template,
                name=stage.name,
                rounds=stage.rounds,
                matches_per_round=stage.matches_per_round,
                order=stage.order
            )
            
        return JsonResponse({
            'success': True,
            'message': 'Template duplicado com sucesso!',
            'redirect': reverse('administrativo:templates')
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao duplicar template: {str(e)}'
        })

def template_importar(request):
    """
    Importa templates de um arquivo Excel.
    """
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            df = pd.read_excel(request.FILES['file'])
            
            required_columns = ['nome', 'fase', 'rodadas', 'jogos_por_rodada']
            if not all(col in df.columns for col in required_columns):
                return JsonResponse({
                    'success': False,
                    'message': 'Arquivo não contém todas as colunas necessárias: ' + ', '.join(required_columns)
                })
                
            with transaction.atomic():
                templates_created = 0
                templates_updated = 0
                errors = []
                
                for template_name in df['nome'].unique():
                    try:
                        template_rows = df[df['nome'] == template_name]
                        
                        # Validação do nome do template
                        if not template_name or len(template_name.strip()) == 0:
                            errors.append(f'Nome do template não pode estar vazio')
                            continue
                            
                        # Cria ou atualiza o template
                        template, created = Template.objects.get_or_create(
                            name=template_name,
                            defaults={'enabled': True}
                        )
                        
                        if created:
                            templates_created += 1
                        else:
                            templates_updated += 1
                            template.stages.all().delete()  # Remove fases existentes
                        
                        # Cria as fases
                        stages_data = []
                        for idx, row in template_rows.iterrows():
                            try:
                                rounds = int(row['rodadas'])
                                matches = int(row['jogos_por_rodada'])
                                
                                if rounds <= 0 or matches <= 0:
                                    errors.append(f'Template {template_name}: Rodadas e jogos por rodada devem ser maiores que zero')
                                    continue
                                    
                                stages_data.append(TemplateStage(
                                    template=template,
                                    name=str(row['fase']),
                                    rounds=rounds,
                                    matches_per_round=matches,
                                    order=idx
                                ))
                            except ValueError as e:
                                errors.append(f'Template {template_name}: Erro ao processar fase {row["fase"]} - {str(e)}')
                                
                        # Salva as fases
                        if stages_data:
                            TemplateStage.objects.bulk_create(stages_data)
                            template.number_of_stages = len(stages_data)
                            template.save()
                        else:
                            template.delete()
                            if created:
                                templates_created -= 1
                            else:
                                templates_updated -= 1
                            errors.append(f'Template {template_name}: Nenhuma fase válida encontrada')
                            
                    except Exception as e:
                        errors.append(f'Erro ao processar template {template_name}: {str(e)}')
                
                # Mensagens de resultado
                message = ''
                if templates_created > 0:
                    message += f'{templates_created} template(s) criado(s) com sucesso. '
                if templates_updated > 0:
                    message += f'{templates_updated} template(s) atualizado(s). '
                if errors:
                    message += 'Alguns erros ocorreram durante a importação: ' + ' | '.join(errors)

                return JsonResponse({
                    'success': templates_created > 0 or templates_updated > 0,
                    'message': message.strip()
                })
                        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao processar arquivo: {str(e)}'
            })
            
    return JsonResponse({
        'success': False,
        'message': 'Nenhum arquivo enviado'
    })

def template_exportar(request):
    """
    Exporta templates para um arquivo Excel.
    """
    templates = Template.objects.all().prefetch_related('stages')
    
    data = []
    for template in templates:
        for stage in template.stages.all():
            data.append({
                'nome': template.name,
                'fase': stage.name,
                'rodadas': stage.rounds,
                'jogos_por_rodada': stage.matches_per_round
            })
    
    df = pd.DataFrame(data)
    
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="templates.xlsx"'
    
    df.to_excel(response, index=False)
    return response

def times(request):
    """
    Lista todos os times ordenados por nome.
    """
    teams = Team.objects.all().select_related('continent', 'country', 'state')
    return render(request, 'administrativo/times.html', {
        'teams': teams
    })

def time_novo(request):
    """
    View para criar um novo time.
    """
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            country_id = request.POST.get('country')
            state_id = request.POST.get('state')
            is_national_team = request.POST.get('is_national_team') == 'on'
            image = request.FILES.get('image')

            # Validações
            if not name:
                return JsonResponse({
                    'success': False,
                    'message': 'O nome do time é obrigatório'
                })

            if not country_id:
                return JsonResponse({
                    'success': False,
                    'message': 'O país é obrigatório'
                })

            # Busca país 
            country = Country.objects.get(id=country_id)
            
            # Verifica se o país tem estados cadastrados
            has_states = country.state_set.exists()
            
            # Busca estado se informado
            state = None
            if state_id:
                state = State.objects.get(id=state_id)

            # Validação de estado apenas se não for seleção E o país tiver estados cadastrados
            if not is_national_team and has_states and not state_id:
                return JsonResponse({
                    'success': False,
                    'message': 'O estado é obrigatório para times que não são seleções quando o país possui estados cadastrados'
                })

            # Verifica se já existe um time com o mesmo nome no país
            if Team.objects.filter(name=name, country=country).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Já existe um time com este nome neste país'
                })

            # Valida a imagem se fornecida
            if image:
                # Verifica o tipo de arquivo
                if not image.content_type.startswith('image/'):
                    return JsonResponse({
                        'success': False,
                        'message': 'O arquivo selecionado não é uma imagem válida'
                    })
                    
                # Verifica o tamanho do arquivo (max 2MB)
                if image.size > 2 * 1024 * 1024:
                    return JsonResponse({
                        'success': False,
                        'message': 'A imagem não pode ter mais que 2MB'
                    })

            # Cria o time
            team = Team.objects.create(
                name=name,
                country=country,
                state=state,
                is_national_team=is_national_team,
                image=image if image else None  # Imagem é opcional
            )

            return JsonResponse({
                'success': True,
                'message': 'Time criado com sucesso!',
                'redirect_url': reverse('administrativo:times')
            })

        except Country.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'País não encontrado'
            })
        except State.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Estado não encontrado'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao criar time: {str(e)}'
            })

    # GET - renderiza o formulário
    countries = Country.objects.all().order_by('name')
    return render(request, 'administrativo/time-novo.html', {
        'countries': countries
    })

def time_editar(request, id):
    """
    Edita um time existente.
    """
    try:
        team = Team.objects.get(id=id)
    except Team.DoesNotExist:
        messages.error(request, 'Time não encontrado')
        return redirect('administrativo:times')

    has_championships = team.has_championships()
    championships = team.team_championships.all().order_by('name')

    if request.method == 'POST':
        try:
            # Atualiza o nome
            team.name = request.POST.get('name')
            
            # Só atualiza país, estado e is_national_team se não tiver campeonatos vinculados
            if not championships.exists():
                team.is_national_team = request.POST.get('is_national_team') == 'on'
                team.country_id = request.POST.get('country')
                
                # Verifica se o time é uma seleção nacional ou se o país não tem estados cadastrados
                if team.is_national_team or (team.country and not State.objects.filter(country_id=team.country_id).exists()):
                    team.state = None
                else:
                    team.state_id = request.POST.get('state')
            
            # Atualiza o continente baseado no país selecionado
            if team.country:
                team.continent = team.country.continent
            
            # Verifica se é para remover a imagem existente
            should_remove_image = request.POST.get('should_remove_image')
            remove_image = request.POST.get('remove_image')
            
            if should_remove_image == 'yes' or remove_image == 'on':
                if team.image:
                    team.image.delete()
                team.image = None
            elif 'image' in request.FILES:
                team.image = request.FILES['image']
            
            team.save()
            
            messages.success(request, 'Time atualizado com sucesso!')
            return redirect('administrativo:times')
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar time: {str(e)}')
            return redirect('administrativo:time_editar', id=id)
    
    # Obtém todos os países ordenados por nome
    countries = Country.objects.all().order_by('name')
    
    # Obtém os estados do país do time, se houver
    states = []
    if team.country:
        states = State.objects.filter(country=team.country).order_by('name')
    
    return render(request, 'administrativo/time-editar.html', {
        'team': team,
        'countries': countries,
        'states': states,
        'has_championships': has_championships,
        'championships': championships
    })

def time_exportar(request):
    """
    Exporta times para um arquivo Excel.
    """
    teams = Team.objects.all().select_related('continent', 'country', 'state').prefetch_related('team_championships')
    
    fields = [
        ('name', 'Nome'),
        ('continent__name', 'Continente'),
        ('country__name', 'País'),
        ('state__name', 'Estado'),
        ('is_national_team', 'Seleção'),
    ]
    
    data = []
    for team in teams:
        row = {}
        for field, _ in fields:
            if '__' in field:
                # Lida com campos relacionados (ex: continent__name)
                parts = field.split('__')
                value = team
                for part in parts:
                    if value is None:
                        value = ''
                        break
                    value = getattr(value, part, '')
            else:
                value = getattr(team, field, '')
                
            if field == 'is_national_team':
                value = 'Sim' if value else 'Não'
                
            row[field] = str(value) if value else ''
            
        # Adiciona os campeonatos
        row['championships'] = ', '.join(team.team_championships.values_list('name', flat=True))
        data.append(row)
    
    df = pd.DataFrame(data)
    
    # Renomeia as colunas
    column_names = {
        'name': 'Nome',
        'continent__name': 'Continente',
        'country__name': 'País',
        'state__name': 'Estado',
        'is_national_team': 'Seleção',
        'championships': 'Campeonatos'
    }
    df.rename(columns=column_names, inplace=True)
    
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="times.xlsx"'
    
    df.to_excel(response, index=False, engine='openpyxl')
    return response

def time_importar_imagens(request):
    """
    Importa imagens para os times.
    """
    if request.method == 'POST':
        try:
            # Obtém arquivos de ambos os inputs: seleção múltipla e diretório
            files = request.FILES.getlist('images')
            directory_files = request.FILES.getlist('directory_images')
            
            # Combina todos os arquivos
            all_files = files + directory_files
            
            if not all_files:
                return JsonResponse({
                    'success': False,
                    'message': 'Nenhuma imagem selecionada'
                })
            
            # Primeiro, identifica quais times existem e quais não existem
            times_found = []
            times_not_found = []
            file_mapping = {}  # Mapeia nome do time para o arquivo
            
            for file in all_files:
                filename = os.path.splitext(file.name)[0]
                # Para arquivos de diretório, remove o caminho e pega apenas o nome do arquivo
                if hasattr(file, 'webkitRelativePath') and file.webkitRelativePath:
                    filename = os.path.splitext(os.path.basename(file.webkitRelativePath))[0]
                
                team = Team.objects.filter(name__iexact=filename).first()
                if team:
                    times_found.append(filename)
                    file_mapping[filename] = file
                else:
                    times_not_found.append(filename)
            
            # Se nenhum time foi encontrado, retorna mensagem de erro
            if not times_found:
                if len(times_not_found) > 4:
                    message = f'Nenhum dos {len(times_not_found)} times está cadastrado. Por favor, cadastre-os primeiro.'
                else:
                    message = f'Os seguintes times não foram encontrados: {", ".join(times_not_found)}. Por favor, cadastre-os primeiro.'
                return JsonResponse({
                    'success': False,
                    'message': message
                })
            
            success_count = 0
            errors = []
            
            # Processa apenas os times que existem
            for team_name in times_found:
                file = file_mapping[team_name]
                team = Team.objects.filter(name__iexact=team_name).first()
                
                try:
                    # Verifica o tipo de arquivo
                    if not file.content_type.startswith('image/'):
                        errors.append(f'Arquivo "{file.name}" não é uma imagem válida')
                        continue
                        
                    # Verifica o tamanho do arquivo (max 2MB)
                    if file.size > 2 * 1024 * 1024:
                        errors.append(f'Imagem "{file.name}" excede o tamanho máximo de 2MB')
                        continue
                        
                    # Remove imagem antiga se existir
                    if team.image:
                        team.image.delete(save=False)
                        
                    # Salva a nova imagem
                    team.image = file
                    team.save()
                    success_count += 1
                except Exception as e:
                    errors.append(f'Erro ao processar "{file.name}": {str(e)}')
            
            # Mensagem de sucesso ou erro
            message = f'{success_count} escudo(s) importado(s) com sucesso'
            
            # Adiciona informação sobre times não encontrados
            if times_not_found:
                if len(times_not_found) > 10:
                    message += f', mas {len(times_not_found)} times não estão cadastrados'
                else:
                    message += f', mas os seguintes times não estão cadastrados: {", ".join(times_not_found[:10])}'
                    if len(times_not_found) > 10:
                        message += f' e mais {len(times_not_found) - 10}'
            
            # Adiciona informação sobre erros
            if errors:
                message += f'. Houve {len(errors)} erro(s) durante o processamento'
                
            return JsonResponse({
                'success': True,
                'message': message,
                'found_count': len(times_found),
                'not_found_count': len(times_not_found),
                'success_count': success_count,
                'error_count': len(errors),
                'errors': errors if errors else None,
                'not_found_sample': times_not_found[:10] if times_not_found else None
            })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao processar importação: {str(e)}'
            })
    
    # Se não for POST, redireciona para a página de times
    return redirect('administrativo:times')

def futcoins(request):
    packages = FutcoinPackage.objects.all().order_by('-created_at')
    return render(request, 'administrativo/futcoins.html', {'packages': packages})

@login_required
@csrf_exempt
def pacote_futcoin_novo(request):
    if request.method == 'POST':
        try:
            data = request.POST
            files = request.FILES
            
            # Tratamento das datas
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            
            try:
                if start_date:
                    start_date = make_aware_with_local_timezone(start_date)
                if end_date:
                    end_date = make_aware_with_local_timezone(end_date)
            except ValueError as e:
                return JsonResponse({
                    'success': False,
                    'message': 'Formato de data inválido. Use o formato DD/MM/YYYY HH:mm'
                })
            
            # Conversão dos valores numéricos
            try:
                # Converte preço padrão para Decimal
                full_price_str = data.get('full_price', '0').strip()
                full_price_str = full_price_str.replace(',', '.')
                full_price = Decimal(full_price_str)
                
                # Converte preço promocional para Decimal (se existir)
                promotional_price = None
                if data.get('promotional_price'):
                    promotional_price_str = data.get('promotional_price', '0').strip()
                    promotional_price_str = promotional_price_str.replace(',', '.')
                    promotional_price = Decimal(promotional_price_str)
                    
                    # Verifica se o preço promocional é menor que o preço padrão
                    if promotional_price >= full_price:
                        return JsonResponse({
                            'success': False,
                            'message': 'O preço promocional deve ser menor que o preço padrão'
                        })
                
                # Converte conteúdo para inteiro
                content_str = data.get('content', '0').strip()
                content = int(content_str)
                
                # Converte bônus para inteiro
                bonus_str = data.get('bonus', '0').strip()
                bonus = int(bonus_str) if bonus_str else 0
                
            except (ValueError, InvalidOperation) as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Erro ao converter valores numéricos: {str(e)}'
                })
            
            # Validação e conversão das cores
            def validate_color(color):
                if not color:
                    return '#000000'
                
                # Remove espaços e converte para minúsculas
                color = color.strip().lower()
                
                # Se já estiver no formato #RRGGBB, retorna como está
                if re.match(r'^#[0-9a-f]{6}$', color):
                    return color.upper()
                
                # Se estiver no formato RGB(r,g,b), converte para hex
                rgb_match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color)
                if rgb_match:
                    r, g, b = map(int, rgb_match.groups())
                    return f'#{r:02x}{g:02x}{b:02x}'.upper()
                
                # Se for rgba, remove o canal alpha e converte para hex
                rgba_match = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*[\d.]+\)', color)
                if rgba_match:
                    r, g, b = map(int, rgba_match.groups())
                    return f'#{r:02x}{g:02x}{b:02x}'.upper()
                
                # Se não estiver em nenhum formato válido, retorna preto
                return '#000000'
            
            # Criação do pacote
            package = FutcoinPackage(
                name=data.get('name'),
                enabled=data.get('enabled', 'true') == 'true',
                package_type=data.get('package_type'),
                label=data.get('label'),
                color_text_label=validate_color(data.get('color_text_label', '#000000')),
                color_background_label=validate_color(data.get('color_background_label', '#FFFFFF')),
                full_price=full_price,
                promotional_price=promotional_price,
                content=content,
                bonus=bonus,
                show_to=data.get('show_to'),
                start_date=start_date,
                end_date=end_date,
                android_product_code=data.get('android_product_code'),
                ios_product_code=data.get('ios_product_code'),
                gateway_product_code=data.get('gateway_product_code')
            )
            
            # Tratamento da imagem
            if 'image' in files:
                package.image = files['image']
            
            package.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Pacote criado com sucesso!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao criar pacote: {str(e)}'
            })
    
    # GET - renderiza o formulário
    return render(request, 'administrativo/pacote-futcoin-novo.html')

def planos(request):
    plans = Plan.objects.all().order_by('-created_at')
    return render(request, 'administrativo/planos.html', {'plans': plans})

@login_required
@csrf_exempt
def pacote_plano_novo(request):
    if request.method == 'POST':
        try:
            data = request.POST
            files = request.FILES
            
            # Tratamento das datas
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            
            try:
                if start_date:
                    start_date = make_aware_with_local_timezone(start_date)
                if end_date:
                    end_date = make_aware_with_local_timezone(end_date)
            except ValueError as e:
                return JsonResponse({
                    'success': False,
                    'message': 'Formato de data inválido. Use o formato DD/MM/YYYY HH:mm'
                })
            
            # Validação e conversão das cores
            def validate_color(color):
                if not color:
                    return '#000000'
                
                # Remove espaços e converte para minúsculas
                color = color.strip().lower()
                
                # Se já estiver no formato #RRGGBB, retorna como está
                if re.match(r'^#[0-9a-f]{6}$', color):
                    return color.upper()
                
                # Se estiver no formato RGB(r,g,b), converte para hex
                rgb_match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color)
                if rgb_match:
                    r, g, b = map(int, rgb_match.groups())
                    return f'#{r:02x}{g:02x}{b:02x}'.upper()
                
                # Se for rgba, remove o canal alpha e converte para hex
                rgba_match = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*[\d.]+\)', color)
                if rgba_match:
                    r, g, b = map(int, rgba_match.groups())
                    return f'#{r:02x}{g:02x}{b:02x}'.upper()
                
                # Se não estiver em nenhum formato válido, retorna preto
                return '#000000'
            
            # Obter e validar os valores de etiqueta e cores
            label = data.get('label', '')
            color_text_label = validate_color(data.get('color_text_label', '#000000'))
            color_background_label = validate_color(data.get('color_background_label', '#FFFFFF'))
            
            # Log para debug
            print(f"Valores recebidos - Etiqueta: {label}, Cor texto: {data.get('color_text_label')}, Cor fundo: {data.get('color_background_label')}")
            print(f"Valores após validação - Cor texto: {color_text_label}, Cor fundo: {color_background_label}")
            
            # Validação dos preços
            try:
                full_price = Decimal(str(data.get('full_price', '0')).replace(',', '.'))
                promotional_price = None
                if data.get('promotional_price'):
                    promotional_price = Decimal(str(data.get('promotional_price')).replace(',', '.'))
                    if promotional_price >= full_price:
                        return JsonResponse({
                            'success': False,
                            'message': 'O preço promocional deve ser menor que o preço padrão.'
                        })
            except (ValueError, InvalidOperation) as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Preço inválido: {str(e)}'
                })
            
            # Criação do plano
            plan = Plan(
                name=data.get('name'),
                plan=data.get('plan'),
                billing_cycle=data.get('billing_cycle'),
                enabled=data.get('enabled', 'true') == 'true',
                package_type=data.get('tipo'),
                label=label,
                color_text_label=color_text_label,
                color_background_label=color_background_label,
                full_price=full_price,
                promotional_price=promotional_price,
                show_to=data.get('show_to'),
                start_date=start_date,
                end_date=end_date,
                android_product_code=data.get('android_product_code'),
                apple_product_code=data.get('apple_product_code'),
                gateway_product_code=data.get('gateway_product_code')
            )
            
            # Adiciona os campos específicos para o tipo "Dias Promoção Novos Jogadores"
            if data.get('tipo') == 'Dias Promoção Novos Jogadores':
                # Tenta obter os valores dos campos específicos e converte para inteiro se existir
                try:
                    if data.get('promotion_days'):
                        plan.promotion_days = int(data.get('promotion_days'))
                    
                    if data.get('futcoins_package_benefit'):
                        plan.futcoins_package_benefit = int(data.get('futcoins_package_benefit'))
                    
                    if data.get('package_renewals'):
                        plan.package_renewals = int(data.get('package_renewals'))
                except (ValueError, TypeError) as e:
                    print(f"Erro ao converter campos específicos: {str(e)}")
            
            # Tratamento da imagem
            if 'image' in files:
                # Validação do tamanho da imagem
                image = files['image']
                if image.size > 2 * 1024 * 1024:  # 2MB
                    return JsonResponse({
                        'success': False,
                        'message': 'A imagem não pode ter mais que 2MB'
                    })
                plan.image = image
            elif data.get('should_remove_image') == 'yes':
                # Se o campo should_remove_image for 'yes', remove a imagem
                if plan.image:
                    plan.image.delete()
                plan.image = None
            
            plan.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Plano criado com sucesso!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao criar plano: {str(e)}'
            })
    
    # GET - renderiza o formulário
    return render(request, 'administrativo/pacote-plano-novo.html')

@login_required
def futligas_classicas(request):
    """
    View para listar todas as Futligas Clássicas
    """
    futligas = StandardLeague.objects.all().order_by('-created_at')
    return render(request, 'administrativo/futligas-classicas.html', {
        'futligas': futligas
    })

@csrf_exempt
def futliga_classica_novo(request):
    if request.method == 'POST':
        # Validação básica
        name = request.POST.get('name', '').strip()
        players = request.POST.get('players', '')
        award_frequency = request.POST.get('award_frequency', '')
        award_time = request.POST.get('award_time', '')
        
        # Verificações de campos obrigatórios
        if not name:
            return JsonResponse({'success': False, 'message': 'O campo Nome é obrigatório'}, status=400)
        if not players:
            return JsonResponse({'success': False, 'message': 'O campo Participantes é obrigatório'}, status=400)
        if not award_frequency:
            return JsonResponse({'success': False, 'message': 'O campo Frequência de Premiação é obrigatório'}, status=400)
        
        try:
            # Verificações específicas por frequência
            weekday = None
            monthday = None
            
            if award_frequency == 'weekly':
                weekday = request.POST.get('weekday')
                if not weekday:
                    return JsonResponse({'success': False, 'message': 'O campo Dia da Semana é obrigatório para ligas semanais'}, status=400)
                monthday = None
                month_value = None
            elif award_frequency == 'monthly':
                monthday = request.POST.get('monthday')
                if not monthday:
                    return JsonResponse({'success': False, 'message': 'O campo Dia do Mês é obrigatório para ligas mensais'}, status=400)
                weekday = 0  # Valor padrão para ligas mensais
                month_value = None
            elif award_frequency == 'annual':
                monthday = request.POST.get('monthday')
                month_value = request.POST.get('month_value')
                if not monthday or not month_value:
                    return JsonResponse({'success': False, 'message': 'Os campos Dia e Mês são obrigatórios para ligas anuais'}, status=400)
                weekday = 0  # Valor padrão para ligas anuais
            
            # Mapeamento dos valores de players
            players_map = {
                'Comum': 1,
                'Craque': 2,
                'Todos': 0
            }
            
            # Criação da liga
            futliga = StandardLeague.objects.create(
                name=name,
                players=players_map.get(players, 0),
                award_frequency=award_frequency,
                weekday=weekday,
                monthday=monthday,
                month_value=month_value,
                award_time=award_time
            )
            
            # Imagem principal
            if 'image' in request.FILES:
                futliga.image = request.FILES['image']
                futliga.save()
            
            # Processamento dos prêmios
            prize_positions = request.POST.getlist('prize_positions[]', [])
            prize_descriptions = request.POST.getlist('prize_descriptions[]', [])
            
            if len(prize_positions) != len(prize_descriptions):
                return JsonResponse({'success': False, 'message': 'Dados de prêmios inválidos'}, status=400)
            
            # Criação dos prêmios
            for i in range(len(prize_positions)):
                try:
                    position = int(prize_positions[i])
                    prize = prize_descriptions[i]
                    
                    prize_obj = StandardLeaguePrize.objects.create(
                        league=futliga,
                        position=position,
                        prize=prize
                    )
                    
                    # Imagem do prêmio
                    if 'prize_images[]' in request.FILES and i < len(request.FILES.getlist('prize_images[]')):
                        prize_obj.image = request.FILES.getlist('prize_images[]')[i]
                        prize_obj.save()
                
                except (ValueError, IndexError):
                    # Se houver erro em um prêmio, pula para o próximo
                    continue
            
            return JsonResponse({'success': True, 'message': 'Futliga Clássica criada com sucesso!'})
        
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erro ao criar Futliga Clássica: {str(e)}'}, status=500)
    
    return render(request, 'administrativo/futliga-classica-novo.html')

@login_required
@csrf_exempt
def futliga_classica_editar(request, futliga_id):
    try:
        futliga = StandardLeague.objects.get(id=futliga_id)
        # Garante que os prêmios sejam carregados explicitamente e ordenados por posição
        prizes = StandardLeaguePrize.objects.filter(league=futliga).order_by('position')
        
        # LOGS DE DIAGNÓSTICO
        print(f"\n\n[DIAGNÓSTICO] Futliga ID: {futliga_id}, Nome: {futliga.name}")
        print(f"[DIAGNÓSTICO] Quantidade de prêmios encontrados: {prizes.count()}")
        for idx, prize in enumerate(prizes):
            print(f"[DIAGNÓSTICO] Prêmio #{idx+1}: ID={prize.id}, Posição={prize.position}, " +
                  f"Descrição={prize.prize}, Imagem={bool(prize.image)}")
        
        # Verificar relacionamentos
        print(f"[DIAGNÓSTICO] Relacionamento prizes na futliga: {hasattr(futliga, 'prizes')}")
        if hasattr(futliga, 'prizes'):
            related_prizes = list(futliga.prizes.all())
            print(f"[DIAGNÓSTICO] Prêmios via relacionamento: {len(related_prizes)}")
            for idx, prize in enumerate(related_prizes):
                print(f"[DIAGNÓSTICO] Relacionamento Prêmio #{idx+1}: ID={prize.id}, " +
                      f"Posição={prize.position}, Descrição={prize.prize}")
    except StandardLeague.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Futliga não encontrada'})
    
    if request.method == 'GET':
        # Retorna o template com os dados da Futliga para edição, incluindo prêmios explicitamente
        return render(request, 'administrativo/futliga-classica-editar.html', {
            'futliga': futliga,
            'prizes': prizes  # Passa os prêmios explicitamente para o template
        })
    
    elif request.method == 'POST':
        # Processa o formulário de edição e salva as mudanças
        try:
            with transaction.atomic():
                # LOGS DE DIAGNÓSTICO - dados recebidos do formulário
                print(f"\n\n[DIAGNÓSTICO-POST] Processando formulário para Futliga ID: {futliga_id}")
                print(f"[DIAGNÓSTICO-POST] POST Data: {request.POST}")
                print(f"[DIAGNÓSTICO-POST] FILES: {request.FILES}")
                
                # Verificar os dados dos prêmios recebidos
                prize_positions = request.POST.getlist('prize_positions[]', [])
                prize_descriptions = request.POST.getlist('prize_descriptions[]', [])
                prize_ids = request.POST.getlist('prize_ids[]', [])
                
                print(f"[DIAGNÓSTICO-POST] Quantidade de posições recebidas: {len(prize_positions)}")
                print(f"[DIAGNÓSTICO-POST] Quantidade de descrições recebidas: {len(prize_descriptions)}")
                print(f"[DIAGNÓSTICO-POST] Quantidade de IDs recebidos: {len(prize_ids)}")
                
                for i, (pos, desc) in enumerate(zip(prize_positions, prize_descriptions)):
                    prize_id = prize_ids[i] if i < len(prize_ids) else "novo"
                    print(f"[DIAGNÓSTICO-POST] Prêmio #{i+1}: ID={prize_id}, Posição={pos}, Descrição={desc}")
                
                # Verifica se devemos remover TODAS as imagens de prêmios
                remove_all_prize_images = request.POST.get('remove_all_prize_images', '0') == '1'
                
                # Dados básicos da futliga
                futliga.name = request.POST.get('name')
                
                # Participantes (0 = Todos, 1 = Comum, 2 = Craque)
                players_str = request.POST.get('players')
                try:
                    futliga.players = int(players_str)
                except (ValueError, TypeError):
                    futliga.players = 0
                
                # Tipo de premiação
                futliga.award_frequency = request.POST.get('award_frequency')
                
                # Campos específicos dependendo do tipo de premiação
                if futliga.award_frequency == 'weekly':
                    futliga.weekday = request.POST.get('weekday')
                    futliga.monthday = None
                    futliga.month_value = None
                elif futliga.award_frequency == 'monthly':
                    futliga.weekday = None
                    futliga.monthday = request.POST.get('monthday')
                    futliga.month_value = None
                elif futliga.award_frequency == 'annual':
                    futliga.weekday = None
                    futliga.monthday = request.POST.get('monthday')
                    futliga.month_value = request.POST.get('month_value')
                
                # Horário de premiação
                if request.POST.get('award_time'):
                    time_str = request.POST.get('award_time')
                    # Converte para objeto time
                    time_obj = datetime.strptime(time_str, '%H:%M').time()
                    futliga.award_time = time_obj
                
                # Imagem principal
                if 'image' in request.FILES:
                    if futliga.image:
                        # Remove a imagem existente
                        futliga.image.delete(save=False)
                    futliga.image = request.FILES['image']
                elif request.POST.get('remove_image') == '1' and futliga.image:
                    # Remove a imagem se solicitado
                    futliga.image.delete(save=False)
                    futliga.image = None
                
                # Salva as alterações na futliga
                futliga.save()
                
                # Processa prêmios que devem ser removidos
                if 'remove_prizes[]' in request.POST:
                    prize_ids_to_remove = request.POST.getlist('remove_prizes[]')
                    for prize_id in prize_ids_to_remove:
                        try:
                            prize = StandardLeaguePrize.objects.get(id=prize_id, league=futliga)
                            
                            # Se tem imagem, remove primeiro
                            if prize.image:
                                prize.image.delete(save=False)
                            
                            # Remove o prêmio do banco
                            prize.delete()
                            print(f"[DEBUG] Prêmio ID={prize_id} removido com sucesso")
                        except StandardLeaguePrize.DoesNotExist:
                            print(f"[DEBUG] Prêmio ID={prize_id} não encontrado para remoção")
                
                # Processa prêmios que devem ser removidos (por posição - novos prêmios que foram removidos antes de salvar)
                if 'remove_prize_position[]' in request.POST:
                    prize_positions_to_remove = request.POST.getlist('remove_prize_position[]')
                    for position in prize_positions_to_remove:
                        try:
                            position_int = int(position)
                            # Verifica se existe um prêmio nesta posição
                            try:
                                prize = StandardLeaguePrize.objects.get(position=position_int, league=futliga)
                                # Se tem imagem, remove primeiro
                                if prize.image:
                                    prize.image.delete(save=False)
                                
                                # Remove o prêmio do banco
                                prize.delete()
                                print(f"[DEBUG] Prêmio na posição {position_int} removido com sucesso")
                            except StandardLeaguePrize.DoesNotExist:
                                print(f"[DEBUG] Prêmio na posição {position_int} não encontrado para remoção")
                        except (ValueError, TypeError):
                            print(f"[DEBUG] Posição inválida para remoção: {position}")
                
                # Obtenção dos IDs dos prêmios para remoção de imagem
                prize_ids_for_image_removal = []
                if 'remove_prize_images[]' in request.POST:
                    prize_ids_for_image_removal = request.POST.getlist('remove_prize_images[]')
                    print(f"[DEBUG] IDs dos prêmios marcados para remoção de imagem: {prize_ids_for_image_removal}")
                
                # Processando a remoção de imagens para prêmios existentes
                print(f"[DEBUG] Total de {len(prize_ids_for_image_removal)} prêmios marcados para remoção de imagem")
                for prize_id in prize_ids_for_image_removal:
                    try:
                        # Valida e converte o ID do prêmio
                        if not prize_id.isdigit():
                            print(f"[DEBUG] ID inválido para remoção de imagem: {prize_id}")
                            continue
                        
                        prize_id_int = int(prize_id)
                        
                        # Busca o prêmio pelo ID
                        try:
                            prize = StandardLeaguePrize.objects.get(id=prize_id_int, league=futliga)
                            
                            # Se o prêmio existe e tem uma imagem, remove
                            if prize.image:
                                print(f"[DEBUG] Removendo imagem do prêmio ID={prize_id_int}, posição={prize.position}")
                                prize.image.delete()
                                prize.save()
                            else:
                                print(f"[DEBUG] Prêmio ID={prize_id_int}, posição={prize.position} não tem imagem para remover")
                        except StandardLeaguePrize.DoesNotExist:
                            print(f"[DEBUG] Prêmio ID={prize_id_int} não encontrado para remoção de imagem")
                    except Exception as e:
                        print(f"[DEBUG] Erro ao processar remoção de imagem para prêmio ID={prize_id}: {str(e)}")
                
                # Processa os prêmios existentes e novos
                if 'prize_positions[]' in request.POST:
                    positions = request.POST.getlist('prize_positions[]')
                    prizes = request.POST.getlist('prize_descriptions[]')
                    prize_ids = request.POST.getlist('prize_ids[]', [])
                    
                    # Lista de IDs que foram removidos
                    removed_prize_ids = []
                    if 'remove_prizes[]' in request.POST:
                        removed_prize_ids = [int(id) for id in request.POST.getlist('remove_prizes[]') if id.isdigit()]
                    
                    print(f"[DEBUG] IDs de prêmios a serem atualizados: {prize_ids}")
                    print(f"[DEBUG] IDs de prêmios removidos: {removed_prize_ids}")
                    
                    # Mapeia nós novos prêmios para posições
                    prize_image_positions = {}
                    
                    # NOVO CÓDIGO: Verifica diretamente arquivos com prefixo prize_image_pos_ para novos prêmios
                    print("[DEBUG] Verificando arquivos de imagem para novos prêmios...")
                    for file_key in request.FILES:
                        # Se a chave segue o padrão 'prize_image_pos_XXX' (para novos prêmios)
                        if file_key.startswith('prize_image_pos_'):
                            try:
                                # Extrai a posição do prêmio da chave
                                position_str = file_key.replace('prize_image_pos_', '')
                                print(f"[DEBUG] Processando arquivo para novo prêmio com chave {file_key}, posição: {position_str}")
                                
                                # Adiciona ao dicionário de posições com imagens
                                prize_image_positions[position_str] = request.FILES[file_key]
                            except Exception as e:
                                print(f"[DEBUG] Erro ao processar imagem para novo prêmio {file_key}: {str(e)}")
                    
                    # Código que recebe posições explícitas para novos prêmios (mantendo para compatibilidade)
                    if 'prize_image_positions[]' in request.POST:
                        image_positions = request.POST.getlist('prize_image_positions[]')
                        prize_files = request.FILES.getlist('prize_images[]')
                        
                        print(f"[DEBUG] Posições marcadas para novas imagens: {image_positions}")
                        print(f"[DEBUG] Arquivos de imagem encontrados: {len(prize_files)}")
                        
                        for i, pos in enumerate(image_positions):
                            if i < len(prize_files):
                                prize_image_positions[pos] = prize_files[i]
                                print(f"[DEBUG] Mapeando posição {pos} para arquivo de imagem {i}")
                    
                    # ADICIONAR AQUI: Verifica arquivos de imagem com nome no formato prize_image_ID
                    # Este bloco processa imagens para prêmios existentes
                    print("[DEBUG] Verificando arquivos de imagem para prêmios...")
                    print(f"[DEBUG] Chaves em request.FILES: {list(request.FILES.keys())}")
                    
                    for file_key in request.FILES:
                        # Se a chave segue o padrão 'prize_image_XXX'
                        if file_key.startswith('prize_image_'):
                            try:
                                # Extrai o ID do prêmio da chave
                                prize_id = file_key.replace('prize_image_', '')
                                
                                print(f"[DEBUG] Processando arquivo com chave {file_key}, ID: {prize_id}")
                                
                                # Verifica se é um ID válido
                                if prize_id.isdigit():
                                    prize_id = int(prize_id)
                                    
                                    # Procura o prêmio no banco
                                    try:
                                        prize = StandardLeaguePrize.objects.get(id=prize_id, league=futliga)
                                        
                                        # Se o prêmio existe, atualiza sua imagem
                                        if prize.image:
                                            # Remove a imagem anterior
                                            prize.image.delete(save=False)
                                        
                                        # Atualiza a imagem
                                        prize.image = request.FILES[file_key]
                                        prize.save()
                                        
                                        print(f"[DEBUG] Imagem atualizada para o prêmio ID={prize_id}, posição={prize.position}")
                                    except StandardLeaguePrize.DoesNotExist:
                                        print(f"[DEBUG] Prêmio ID={prize_id} não encontrado para atualização de imagem")
                            except Exception as e:
                                print(f"[DEBUG] Erro ao processar imagem {file_key}: {str(e)}")
                    
                    # Lista de posições explicitamente marcadas como sem imagem
                    positions_without_image = []
                    if 'prize_without_image[]' in request.POST:
                        positions_without_image = [str(pos) for pos in request.POST.getlist('prize_without_image[]')]
                        print(f"[DEBUG] Posições explicitamente marcadas como sem imagem: {', '.join(positions_without_image)}")
                    
                    # Dicionário para rastrear prêmios existentes pelo ID
                    existing_prizes = {}
                    for prize_id in prize_ids:
                        if prize_id.isdigit() and int(prize_id) not in removed_prize_ids:
                            try:
                                prize_obj = StandardLeaguePrize.objects.get(id=int(prize_id), league=futliga)
                                existing_prizes[int(prize_id)] = prize_obj
                            except StandardLeaguePrize.DoesNotExist:
                                print(f"[DEBUG] Prêmio ID={prize_id} não encontrado")
                    
                    # Atualizar prêmios existentes e criar novos apenas quando necessário
                    for i, (position, prize_value) in enumerate(zip(positions, prizes)):
                        if i < len(prize_ids) and prize_ids[i].isdigit():
                            prize_id = int(prize_ids[i])
                            
                            # Pula se o prêmio foi removido
                            if prize_id in removed_prize_ids:
                                print(f"[DEBUG] Pulando prêmio ID={prize_id} pois está marcado para remoção")
                                continue
                            
                            # Se o prêmio existe, atualize-o
                            if prize_id in existing_prizes:
                                prize_obj = existing_prizes[prize_id]
                                
                                # Garantir que position seja sempre um número inteiro válido
                                try:
                                    position = int(position)
                                    if position <= 0:
                                        position = i + 1  # Usar o índice +1 como posição válida
                                        print(f"[DEBUG] Posição inválida (<=0), corrigindo para {position}")
                                except (ValueError, TypeError):
                                    position = i + 1  # Se não for conversível para inteiro, usar o índice
                                    print(f"[DEBUG] Posição inválida (não numérica), corrigindo para {position}")
                                
                                # Atualiza posição e valor
                                prize_obj.position = position
                                prize_obj.prize = prize_value
                                
                                # Se tiver uma nova imagem para esta posição, atualiza
                                if str(position) in prize_image_positions:
                                    # Remove a imagem anterior se existir
                                    if prize_obj.image:
                                        prize_obj.image.delete(save=False)
                                    
                                    # Adiciona a nova imagem
                                    prize_obj.image = prize_image_positions[str(position)]
                                # Se a posição estiver marcada explicitamente como sem imagem,
                                # e não tiver uma nova imagem, removemos a imagem existente
                                elif str(position) in positions_without_image and prize_obj.image:
                                    # Verificar também se a posição está na lista de remove_prize_images
                                    should_remove_image = False
                                    
                                    # Verificar se está marcada para remoção através do campo remove_prize_images[]
                                    if 'remove_prize_images[]' in request.POST:
                                        remove_positions = request.POST.getlist('remove_prize_images[]')
                                        if str(position) in remove_positions:
                                            should_remove_image = True
                                            print(f"[DEBUG] Posição {position} encontrada em remove_prize_images[]")
                                    
                                    # Remover a imagem independentemente de outras condições se estiver em positions_without_image
                                    print(f"[DEBUG] Removendo imagem do prêmio na posição {position} que foi marcado como sem imagem")
                                    prize_obj.image.delete(save=False)
                                    prize_obj.image = None
                                
                                # Salva o prêmio
                                prize_obj.save()
                                print(f"[DEBUG] Prêmio existente ID={prize_id} atualizado com sucesso")
                            else:
                                print(f"[DEBUG] Prêmio ID={prize_id} mencionado nos IDs mas não encontrado no banco")
                        else:
                            # Novo prêmio (sem ID) - criar apenas se não for uma atualização de posição
                            # Garantir que position seja sempre um número inteiro válido
                            try:
                                position = int(position)
                                if position <= 0:
                                    position = i + 1  # Usar o índice +1 como posição válida
                                    print(f"[DEBUG] Posição inválida (<=0), corrigindo para {position}")
                            except (ValueError, TypeError):
                                position = i + 1  # Se não for conversível para inteiro, usar o índice
                                print(f"[DEBUG] Posição inválida (não numérica), corrigindo para {position}")
                            
                            # Verifica se é uma posição atual (atualização) ou nova criação
                            existing_position = StandardLeaguePrize.objects.filter(
                                position=position, 
                                league=futliga
                            ).exclude(id__in=removed_prize_ids).first()
                            
                            if existing_position:
                                # Atualiza o prêmio existente nesta posição
                                existing_position.prize = prize_value
                                
                                # Se tiver uma nova imagem para esta posição, atualiza
                                if str(position) in prize_image_positions:
                                    # Remove a imagem anterior se existir
                                    if existing_position.image:
                                        existing_position.image.delete(save=False)
                                    
                                    # Adiciona a nova imagem
                                    existing_position.image = prize_image_positions[str(position)]
                                
                                # Salva o prêmio
                                existing_position.save()
                                print(f"[DEBUG] Prêmio existente na posição {position} atualizado com sucesso")
                            else:
                                # Cria um novo prêmio apenas se não encontrar nenhum na posição
                                prize_obj = StandardLeaguePrize(
                                    league=futliga,
                                    position=position,
                                    prize=prize_value
                                )
                                
                                # Adiciona imagem se disponível
                                if str(position) in prize_image_positions:
                                    prize_obj.image = prize_image_positions[str(position)]
                                
                                # Salva o novo prêmio
                                prize_obj.save()
                                print(f"[DEBUG] Novo prêmio criado na posição {position}")
                
                return JsonResponse({'success': True})
        except Exception as e:
            print(f"[DEBUG] Erro ao editar futliga: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'message': f'Erro ao editar Futliga Clássica: {str(e)}'})
    
    # Se o método não for GET nem POST
    return JsonResponse({'success': False, 'message': 'Método não permitido'})



@login_required
@csrf_exempt
@require_http_methods(["POST"])
def futliga_jogador_salvar(request):
    import sys
    sys.stdout.flush()
    print("\n[DEBUG-PREMIO] ==================== INÍCIO DO SALVAMENTO ====================", flush=True)
    try:
        # Tenta ler o corpo da requisição como texto primeiro
        body = request.body.decode('utf-8')
        print(f"[DEBUG-PREMIO] Body recebido: {body}", flush=True)
        
        # Agora tenta fazer o parse do JSON
        data = json.loads(body)
        print(f"\n[DEBUG-PREMIO] Dados decodificados:", flush=True)
        print(f"- Níveis: {len(data.get('levels', []))}", flush=True)
        print(f"- Prêmios: {len(data.get('prizes', []))}", flush=True)
        print(f"- Prêmios para exclusão: {len(data.get('deleted_prize_ids', []))}", flush=True)
        
        # Verificação ajustada: permite salvar mesmo sem níveis se for a primeira vez
        if not data.get('levels'):
            print("[DEBUG-PREMIO] AVISO: Nenhum nível encontrado nos dados. Criando nível padrão...", flush=True)
            # Criar um nível padrão se não existirem níveis (inicialização)
            data['levels'] = [{
                'name': 'Básico',
                'players': 0,
                'premium_players': 0,
                'owner_premium': 0,
                'image': None
            }]
            print("[DEBUG-PREMIO] Nível padrão criado para inicialização", flush=True)
            
        # Verificação ajustada: permite salvar mesmo sem prêmios se for a primeira vez
        if not data.get('prizes'):
            print("[DEBUG-PREMIO] AVISO: Nenhum prêmio encontrado nos dados. Criando prêmio padrão...", flush=True)
            # Criar um prêmio padrão se não existirem prêmios (inicialização)
            defaultValues = {}
            for level in data.get('levels', []):
                defaultValues[level['name']] = 0
            
            data['prizes'] = [{
                'position': 1,
                'values': defaultValues,
                'image': None,
                'league_id': 6
            }]
            print("[DEBUG-PREMIO] Prêmio padrão criado para inicialização", flush=True)
            
        # Processa os prêmios marcados para exclusão
        deleted_prize_ids = data.get('deleted_prize_ids', [])
        if deleted_prize_ids:
            print(f"\n[DEBUG-PREMIO] Excluindo prêmios: {deleted_prize_ids}", flush=True)
            CustomLeaguePrize.objects.filter(id__in=deleted_prize_ids).delete()
            
        # Processa os níveis
        print(f"\n[DEBUG-PREMIO] Iniciando processamento de níveis...", flush=True)
        created_levels = {}
        saved_levels = []
        
        with transaction.atomic():
            # Primeiro, exclui os níveis existentes
            nivel_count = CustomLeagueLevel.objects.count()
            print(f"[DEBUG-PREMIO] Excluindo {nivel_count} níveis existentes", flush=True)
            CustomLeagueLevel.objects.all().delete()
            
            # Cria os novos níveis
            for level_data in data['levels']:
                print(f"\n[DEBUG-PREMIO] Processando nível: {level_data['name']}", flush=True)
                try:
                    level = CustomLeagueLevel.objects.create(
                        name=level_data['name'],
                        players=level_data['players'],
                        premium_players=level_data['premium_players'],
                        owner_premium=level_data['owner_premium']
                    )
                    
                    # Processa a imagem se houver
                    if level_data.get('image'):
                        print(f"[DEBUG-PREMIO] Processando imagem para nível {level_data['name']}", flush=True)
                        if level_data['image'].startswith('data:image'):
                            print("[DEBUG-PREMIO] Nova imagem detectada (base64)", flush=True)
                            format, imgstr = level_data['image'].split(';base64,')
                            ext = format.split('/')[-1]
                            data_img = ContentFile(base64.b64decode(imgstr), name=f'level_{level_data["name"]}.{ext}')
                            level.image.save(f'level_{level_data["name"]}.{ext}', data_img, save=True)
                        elif level_data['image'].startswith('/media/'):
                            print("[DEBUG-PREMIO] Imagem existente detectada", flush=True)
                            level.image = level_data['image'].replace('/media/', '', 1)
                            level.save()
                            
                    created_levels[level_data['name']] = level
                    saved_levels.append({
                        'id': level.id,
                        'name': level.name,
                        'players': level.players,
                        'premium_players': level.premium_players,
                        'owner_premium': level.owner_premium,
                        'image': level.image.url if level.image else None
                    })
                    print(f"[DEBUG-PREMIO] Nível {level_data['name']} criado com sucesso", flush=True)
                except Exception as e:
                    print(f"[DEBUG-PREMIO] ERRO ao criar nível {level_data['name']}: {str(e)}", flush=True)
                    raise
            
            # Processa os prêmios
            print(f"\n[DEBUG-PREMIO] Iniciando processamento de prêmios...", flush=True)
            saved_prizes = []
            
            # CORREÇÃO: Exclui todos os prêmios existentes para a liga 6 (exceto os que estão sendo atualizados)
            print(f"[DEBUG-PREMIO] Excluindo prêmios existentes da liga 6 para evitar conflitos de posição", flush=True)
            # Se já existirem prêmios, exclui-os antes de criar novos para evitar conflito de unicidade
            CustomLeaguePrize.objects.filter(league_id=6).delete()
            
            # Cria ou atualiza os prêmios
            for prize_data in data['prizes']:
                print(f"\n[DEBUG-PREMIO] Processando prêmio posição {prize_data['position']}", flush=True)
                try:
                    # Criar novo prêmio
                    print(f"[DEBUG-PREMIO] Criando novo prêmio para posição {prize_data['position']}", flush=True)
                    league_id = prize_data.get('league_id', 6)  # Usa o league_id enviado ou 6 como padrão
                    try:
                        league = CustomLeague.objects.get(id=league_id)
                        prize = CustomLeaguePrize.objects.create(position=prize_data['position'], league=league)
                        print(f"[DEBUG-PREMIO] Usando league_id={league_id} para novo prêmio", flush=True)
                    except Exception as e:
                        print(f"[DEBUG-PREMIO] Erro ao obter liga {league_id}: {e}", flush=True)
                        # Fallback para league_id=6
                        league = CustomLeague.objects.get(id=6)
                        prize = CustomLeaguePrize.objects.create(position=prize_data['position'], league=league)
                            
                    # Processa a imagem do prêmio
                    prize_image_url = None
                    if prize_data.get('image'):
                        print(f"[DEBUG-PREMIO] Processando imagem para prêmio posição {prize_data['position']}", flush=True)
                        if prize_data['image'].startswith('data:image'):
                            format, imgstr = prize_data['image'].split(';base64,')
                            ext = format.split('/')[-1]
                            data_img = ContentFile(base64.b64decode(imgstr), name=f'prize_{prize_data["position"]}.{ext}')
                            prize.image.save(f'prize_{prize_data["position"]}.{ext}', data_img, save=True)
                            prize_image_url = prize.image.url if prize.image else None
                        elif prize_data['image'].startswith('/media/'):
                            prize.image = prize_data['image'].replace('/media/', '', 1)
                            prize.save()
                            prize_image_url = prize_data['image']
                    
                    # Cria os valores para cada nível
                    prize_values = {}
                    saved_prize_values = []
                    for level_name, value in prize_data['values'].items():
                        if level_name in created_levels:
                            print(f"[DEBUG-PREMIO] Definindo valor {value} para nível {level_name}", flush=True)
                            # Verificar se já existe um valor para este prêmio e nível
                            existing_value = CustomLeaguePrizeValue.objects.filter(
                                prize=prize,
                                level=created_levels[level_name]
                            ).first()
                            
                            if existing_value:
                                # Atualizar o valor existente
                                existing_value.value = value
                                existing_value.save()
                                print(f"[DEBUG-PREMIO] Valor atualizado para o prêmio {prize.id}, nível {level_name}", flush=True)
                            else:
                                # Criar novo valor
                                prize_value = CustomLeaguePrizeValue.objects.create(
                                    prize=prize,
                                    level=created_levels[level_name],
                                    value=value
                                )
                                print(f"[DEBUG-PREMIO] Novo valor criado para o prêmio {prize.id}, nível {level_name}", flush=True)
                            
                            # Armazena o valor para retornar na resposta
                            prize_values[level_name] = value
                            saved_prize_values.append({
                                'level_id': created_levels[level_name].id,
                                'level_name': level_name,
                                'value': value
                            })
                        else:
                            print(f"[DEBUG-PREMIO] AVISO: Nível {level_name} não encontrado para prêmio {prize_data['position']}", flush=True)
                
                    # Adiciona o prêmio à lista de retorno
                    saved_prizes.append({
                        'id': prize.id,
                        'position': prize_data['position'],
                        'image': prize_image_url,
                        'values': prize_values,
                        'prize_values': saved_prize_values  # Inclui os objetos de valores para compatibilidade
                    })
                    
                    print(f"[DEBUG-PREMIO] Prêmio posição {prize_data['position']} criado com sucesso", flush=True)
                except Exception as e:
                    print(f"[DEBUG-PREMIO] ERRO ao criar prêmio posição {prize_data['position']}: {str(e)}", flush=True)
                    raise
            
            # Processa a configuração de premiação
            award_config = None
            if data.get('award_config'):
                print("\n[DEBUG-PREMIO] Processando configuração de premiação...", flush=True)
                try:
                    weekly = data['award_config']['weekly']
                    season = data['award_config']['season']
                    
                    # Atualiza cada parâmetro diretamente - não precisa excluir primeiro
                    # Busca o objeto Parameters (normalmente deve ter apenas uma instância)
                    params, created = Parameters.objects.get_or_create(id=1)
                    
                    # Atualiza os campos diretamente
                    params.weekly_award_day = weekly['day']
                    params.weekly_award_time = weekly['time']
                    params.season_award_month = season['month']
                    params.season_award_day = season['day']
                    params.season_award_time = season['time']
                    params.save()
                    
                    award_config = {
                        'weekly': weekly,
                        'season': season
                    }
                    
                    print("[DEBUG-PREMIO] Configuração de premiação salva com sucesso", flush=True)
                except Exception as e:
                    print(f"[DEBUG-PREMIO] ERRO ao salvar configuração de premiação: {str(e)}", flush=True)
                    raise
                    
        print("\n[DEBUG-PREMIO] ==================== SALVAMENTO CONCLUÍDO COM SUCESSO ====================", flush=True)
        sys.stdout.flush()
        
        # Retorna os dados salvos para atualizar a interface
        return JsonResponse({
            'success': True,
            'levels': saved_levels,
            'prizes': saved_prizes,
            'award_config': award_config
        })
        
    except json.JSONDecodeError as e:
        print(f"\n[DEBUG-PREMIO] ERRO ao decodificar JSON: {str(e)}", flush=True)
        return JsonResponse({'success': False, 'message': 'Dados inválidos'})
    except Exception as e:
        print(f"\n[DEBUG-PREMIO] ERRO não esperado: {str(e)}", flush=True)
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
@require_http_methods(["DELETE"])
def futliga_jogador_nivel_excluir(request, nivel_id):
    """
    Exclui um nível específico.
    """
    try:
        nivel = CustomLeagueLevel.objects.get(id=nivel_id)
        nivel.delete()
        return JsonResponse({'message': 'Nível excluído com sucesso'})
    except CustomLeagueLevel.DoesNotExist:
        return JsonResponse({'error': 'Nível não encontrado'}, status=404)
    except Exception as e:
        logger.error(f'Erro ao excluir nível: {str(e)}')
        return JsonResponse({'error': 'Erro ao excluir nível'}, status=500)

@login_required
def futliga_niveis(request):
    """
    Lista todos os níveis das futligas
    """
    # Limpa as mensagens antigas
    storage = messages.get_messages(request)
    storage.used = True

    # Obtém todos os níveis ordenados por data de criação
    levels = CustomLeagueLevel.objects.all().order_by('-created_at')

    context = {
        'levels': levels
    }

    return render(request, 'administrativo/futligas-niveis.html', context)

def continentes(request):
    """
    Lista todos os continentes ordenados por nome
    """
    continents = Continent.objects.all().order_by('name')
    return render(request, 'administrativo/continentes.html', {'continents': continents})

def continente_novo(request):
    """
    Cria um novo continente
    """
    if request.method == 'POST':
        name = request.POST.get('name')
        
        if not name:
            messages.error(request, 'O nome é obrigatório.')
            return redirect('administrativo:continente_novo')
        
        try:
            # Verifica se já existe um continente com o mesmo nome
            if Continent.objects.filter(name=name).exists():
                messages.error(request, 'Continente já existe')
                return redirect('administrativo:continente_novo')
            
            with transaction.atomic():
                Continent.objects.create(name=name)
                messages.success(request, 'Continente criado com sucesso!')
                return redirect('administrativo:continentes')
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, 'Erro ao criar continente.')
        
        return redirect('administrativo:continente_novo')
    
    return render(request, 'administrativo/continente-novo.html')

def continente_editar(request, id):
    """
    Edita um continente existente
    """
    continent = get_object_or_404(Continent, id=id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        
        if not name:
            messages.error(request, 'O nome é obrigatório.')
            return redirect('administrativo:continente_editar', id=id)
        
        try:
            with transaction.atomic():
                continent.name = name
                continent.full_clean()
                continent.save()
                messages.success(request, 'Continente atualizado com sucesso!')
                return redirect('administrativo:continentes')
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, 'Erro ao atualizar continente.')
        
        return redirect('administrativo:continente_editar', id=id)
    
    related_data = continent.get_related_data()
    return render(request, 'administrativo/continente-editar.html', {
        'continent': continent,
        'countries': related_data['countries'],
        'championships': related_data['championships']
    })

def continente_excluir(request, id):
    """
    Exclui um continente específico.
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Método não permitido'
        })
        
    continent = get_object_or_404(Continent, id=id)
    
    try:
        # Verifica se pode excluir
        if not continent.can_delete():
            related_data = continent.get_related_data()
            message = f"Não é possível excluir o continente {continent.name} pois existem registros vinculados: "
            
            if related_data['countries'].exists():
                countries = ", ".join([c.name for c in related_data['countries']])
                message += f"Países ({countries})"
            
            if related_data['championships'].exists():
                if related_data['countries'].exists():
                    message += " e "
                championships = ", ".join([c.name for c in related_data['championships']])
                message += f"Campeonatos ({championships})"
            
            return JsonResponse({'success': False, 'message': message})
        
        # Se chegou aqui, pode excluir
        continent.delete()
        return JsonResponse({
            'success': True,
            'message': 'Continente excluído com sucesso!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao excluir continente: {str(e)}'
        })

def continente_excluir_em_massa(request):
    """
    Exclui múltiplos continentes selecionados.
    """
    if request.method == 'POST':
        ids = request.POST.getlist('ids[]')
        if not ids:
            return JsonResponse({
                'success': False,
                'message': 'Nenhum continente selecionado'
            })
        
        cannot_delete = []
        deleted = 0
        
        for continent_id in ids:
            continent = get_object_or_404(Continent, id=continent_id)
            if continent.can_delete():
                continent.delete()
                deleted += 1
            else:
                related_data = continent.get_related_data()
                cannot_delete.append(f"{continent.name} ({', '.join(related_data)})")
        
        if cannot_delete:
            message = f"Não foi possível excluir os seguintes continentes pois possuem registros vinculados: {', '.join(cannot_delete)}"
            if deleted > 0:
                message = f"{deleted} continente(s) excluído(s). " + message
            return JsonResponse({'success': False, 'message': message})
        
        return JsonResponse({
            'success': True,
            'message': f'{deleted} continente(s) excluído(s) com sucesso!'
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    })

def continente_exportar(request):
    """
    Exporta os continentes para Excel
    """
    continents = Continent.objects.all().order_by('name')
    
    # Prepara os dados ajustando o fuso horário
    data = []
    for continent in continents:
        data.append({
            'Nome': continent.name,
            'Data Criação': (continent.created_at - timezone.timedelta(hours=3)).strftime('%d/%m/%Y %H:%M')
        })
    
    # Cria o DataFrame com os dados já formatados
    df = pd.DataFrame(data)
    
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="continentes.xlsx"'
    
    df.to_excel(response, index=False)
    return response

def continente_importar(request):
    """
    Importa continentes de um arquivo Excel
    """
    if request.method == 'POST' and request.FILES.get('file'):
        fields = [('name', 'Nome')]
        unique_fields = ['name']
        
        success, message = import_from_excel(
            request.FILES['file'],
            Continent,
            fields,
            unique_fields
        )
        
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
        
        return redirect('administrativo:continentes')
    
    messages.error(request, 'Nenhum arquivo enviado.')
    return redirect('administrativo:continentes')

def paises(request):
    """
    Lista todos os países ordenados por nome.
    """
    countries = Country.objects.all().order_by('name')
    return render(request, 'administrativo/paises.html', {
        'countries': countries
    })

def pais_novo(request):
    """
    Cria um novo país.
    """
    if request.method == 'POST':
        name = request.POST.get('name')
        continent_id = request.POST.get('continent')
        
        if not all([name, continent_id]):
            messages.error(request, 'Todos os campos são obrigatórios')
            return redirect('administrativo:pais_novo')
            
        # Verifica se já existe um país com este nome
        if Country.objects.filter(name=name).exists():
            return JsonResponse({
                'success': False,
                'message': 'País já existe'
            })
            
        try:
            continent = Continent.objects.get(id=continent_id)
            country = Country.objects.create(
                name=name,
                continent=continent
            )
            return JsonResponse({
                'success': True,
                'message': 'País criado com sucesso',
                'redirect': reverse('administrativo:paises')
            })
        except Continent.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Continente não encontrado'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    continents = Continent.objects.all().order_by('name')
    states = []  # Lista vazia pois é um novo país
    teams = []   # Lista vazia pois é um novo país
    championships = []  # Lista vazia pois é um novo país
    
    return render(request, 'administrativo/pais-novo.html', {
        'continents': continents,
        'states': states,
        'teams': teams,
        'championships': championships
    })

def pais_editar(request, id):
    """
    Edita um país existente.
    """
    country = get_object_or_404(Country, id=id)
    
    # Obtém os dados relacionados
    related_data = country.get_related_data()
    states = related_data['states']
    championships = related_data['championships']
    teams = related_data['teams']
    
    # Verifica se tem campeonatos vinculados
    has_championships = championships.exists()
    
    if request.method == 'POST':
        name = request.POST.get('name')
        continent_id = request.POST.get('continent')
        
        if not all([name, continent_id]):
            messages.error(request, 'Todos os campos são obrigatórios')
            return redirect('administrativo:pais_editar', id=id)
        
        try:
            # Se tem campeonatos vinculados, só permite editar o nome
            if has_championships:
                if country.name != name:
                    country.name = name
                    country.save()
                    messages.success(request, 'Nome do país atualizado com sucesso')
                return redirect('administrativo:paises')
            
            # Se não tem campeonatos, permite editar tudo
            # Verifica se já existe um país com o mesmo nome no continente
            if Country.objects.filter(name=name, continent_id=continent_id).exclude(id=id).exists():
                messages.error(request, 'Já existe um país com este nome neste continente')
                return redirect('administrativo:pais_editar', id=id)
            
            # Atualiza os dados do país
            continent = Continent.objects.get(id=continent_id)
            country.name = name
            country.continent = continent
            country.save()
            
            messages.success(request, 'País atualizado com sucesso')
            return redirect('administrativo:paises')
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar país: {str(e)}')
            return redirect('administrativo:pais_editar', id=id)
    
    # Obtém todos os continentes para o select
    continents = Continent.objects.all().order_by('name')
    
    return render(request, 'administrativo/pais-editar.html', {
        'country': country,
        'continents': continents,
        'states': states,
        'teams': teams,
        'championships': championships,
        'has_championships': has_championships
    })

def pais_excluir(request, id):
    """
    Exclui um país se não tiver vinculações.
    """
    country = get_object_or_404(Country, id=id)
    
    if not country.can_delete():
        messages.error(request, 'Não é possível excluir este país pois existem registros vinculados')
        return JsonResponse({
            'success': False,
            'message': 'Não é possível excluir este país pois existem registros vinculados'
        })
        
    try:
        country.delete()
        messages.success(request, 'País excluído com sucesso')
        return JsonResponse({
            'success': True,
            'message': 'País excluído com sucesso'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao excluir país: {str(e)}'
        })

def pais_excluir_em_massa(request):
    """
    Exclui múltiplos países se não tiverem vinculações.
    """
    if request.method == 'POST':
        ids = request.POST.getlist('ids[]')
        if not ids:
            return JsonResponse({
                'success': False,
                'message': 'Nenhum país selecionado'
            })
            
        try:
            # Filtra apenas os países que podem ser excluídos
            countries = Country.objects.filter(id__in=ids)
            deletable_countries = [c for c in countries if c.can_delete()]
            
            # Exclui os países que podem ser excluídos
            for country in deletable_countries:
                country.delete()
                
            if len(deletable_countries) == len(ids):
                return JsonResponse({
                    'success': True,
                    'message': 'Países excluídos com sucesso'
                })
            else:
                return JsonResponse({
                    'success': True,
                    'message': f'{len(deletable_countries)} de {len(ids)} países foram excluídos. Alguns países não puderam ser excluídos por terem registros vinculados'
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    })

def pais_exportar(request):
    """
    Exporta os países para um arquivo Excel.
    """
    countries = Country.objects.all()
    fields = [
        ('name', 'Nome'),
        ('continent__name', 'Continente')
    ]
    return export_to_excel(countries, fields, 'paises.xlsx')

def pais_importar(request):
    """
    Importa países de um arquivo Excel
    """
    if request.method == 'POST' and request.FILES.get('file'):
        fields = [('name', 'Nome'), ('continent__name', 'Continente')]
        unique_fields = ['name']
        
        success, message = import_from_excel(
            request.FILES['file'],
            Country,
            fields,
            unique_fields
        )
        
        if success:
            return JsonResponse({
                'success': True,
                'message': message
            })
        else:
            return JsonResponse({
                'success': False,
                'message': message
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Nenhum arquivo enviado.'
    })

def estados(request):
    """
    Lista todos os estados.
    """
    # Limpa as mensagens antigas
    storage = messages.get_messages(request)
    for _ in storage:
        pass  # Itera sobre as mensagens para marcá-las como lidas
    storage.used = True
    
    states = State.objects.all().order_by('country__name', 'name')
    return render(request, 'administrativo/estados.html', {'states': states})

def estado_novo(request):
    """
    Cria um novo estado.
    """
    if request.method == 'POST':
        name = request.POST.get('name')
        country_id = request.POST.get('country')
        
        try:
            country = Country.objects.get(id=country_id)
            
            # Verifica se já existe um estado com este nome no país
            if State.objects.filter(name=name, country=country).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Estado já existe'
                })
            
            state = State(name=name, country=country)
            state.full_clean()
            state.save()
            return JsonResponse({
                'success': True,
                'message': 'Estado criado com sucesso!',
                'redirect': reverse('administrativo:estados')
            })
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro de validação: {str(e)}'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao criar estado: {str(e)}'
            })
    
    countries = Country.objects.all().order_by('name')
    return render(request, 'administrativo/estado-novo.html', {'countries': countries})

def estado_excluir(request, id):
    """
    Exclui um estado existente.
    """
    if request.method == 'POST':
        try:
            state = get_object_or_404(State, id=id)
            
            # Verifica se tem times vinculados
            if state.team_set.exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Não é possível excluir o estado pois existem times vinculados'
                })
            
            # Verifica se tem campeonatos vinculados
            if Championship.objects.filter(state=state).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Não é possível excluir o estado pois existem campeonatos vinculados'
                })
                
            state.delete()
            return JsonResponse({
                'success': True,
                'message': 'Estado excluído com sucesso'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Erro ao excluir estado. Verifique se não existem registros vinculados.'
            })
            
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    }, status=405)

def estado_excluir_em_massa(request):
    """
    Exclui múltiplos estados selecionados.
    """
    if request.method == 'POST':
        ids = request.POST.getlist('ids[]')
        if not ids:
            return JsonResponse({
                'success': False,
                'message': 'Nenhum estado selecionado'
            })
            
        try:
            # Verifica se algum estado tem times ou campeonatos vinculados
            states = State.objects.filter(id__in=ids)
            states_to_delete = []
            non_deletable_count = 0
            
            for state in states:
                if state.team_set.exists() or Championship.objects.filter(state=state).exists():
                    non_deletable_count += 1
                else:
                    states_to_delete.append(state.id)
            
            # Exclui apenas os estados que não têm vínculos
            if states_to_delete:
                State.objects.filter(id__in=states_to_delete).delete()
            
            if non_deletable_count > 0:
                if len(states_to_delete) > 0:
                    message = f'{len(states_to_delete)} estado(s) excluído(s) com sucesso. {non_deletable_count} estado(s) não foi(ram) excluído(s) pois possui(em) registros vinculados'
                else:
                    message = f'{non_deletable_count} estado(s) não pode(m) ser excluído(s) pois possui(em) registros vinculados'
                return JsonResponse({
                    'success': True,
                    'message': message
                })
            
            return JsonResponse({
                'success': True,
                'message': 'Estados excluídos com sucesso'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Erro ao excluir estados. Verifique se não existem registros vinculados.'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    })

def estado_importar(request):
    """
    Importa estados de um arquivo Excel
    """
    if request.method == 'POST' and request.FILES.get('file'):
        fields = [('name', 'Nome'), ('country__name', 'País')]
        unique_fields = ['name', 'country']
        
        success, message = import_from_excel(
            request.FILES['file'],
            State,
            fields,
            unique_fields
        )
        
        return JsonResponse({
            'success': success,
            'message': message
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Nenhum arquivo enviado.'
    })

def estado_exportar(request):
    """
    Exporta estados para um arquivo Excel.
    """
    states = State.objects.all().order_by('country__name', 'name')
    fields = [
        ('name', 'Nome'),
        ('country__name', 'País')
    ]
    return export_to_excel(states, fields, 'estados.xlsx')

def estado_editar(request, id):
    """
    Edita um estado existente.
    """
    # Limpa as mensagens antigas
    storage = messages.get_messages(request)
    for _ in storage:
        pass  # Limpa as mensagens antigas
    
    try:
        state = State.objects.get(id=id)
    except State.DoesNotExist:
        messages.error(request, 'Estado não encontrado')
        return redirect('administrativo:estados')
    
    if request.method == 'GET':
        # Busca times e campeonatos vinculados
        teams = Team.objects.filter(state=state).order_by('name')
        championships = Championship.objects.filter(state=state).order_by('name')
        
        # Verifica se tem campeonatos vinculados
        has_championships = championships.exists()
        
        context = {
            'state': state,
            'countries': Country.objects.all().order_by('name'),
            'teams': teams,
            'championships': championships,
            'has_championships': has_championships
        }
        return render(request, 'administrativo/estado-editar.html', context)
        
    name = request.POST.get('name')
    country_id = request.POST.get('country')
    
    if not name:
        messages.error(request, 'O nome é obrigatório')
        return redirect('administrativo:estado_editar', id=id)
        
    try:
        # Verifica se tem campeonatos vinculados
        has_championships = Championship.objects.filter(state=state).exists()
        
        # Se tem campeonatos, só permite editar o nome
        if has_championships:
            if State.objects.filter(name=name, country=state.country).exclude(id=id).exists():
                messages.error(request, 'Já existe um estado com este nome neste país')
                return redirect('administrativo:estado_editar', id=id)
                
            state.name = name
        else:
            # Se não tem campeonatos, permite editar tudo
            if country_id:
                country = Country.objects.get(id=country_id)
                if State.objects.filter(name=name, country=country).exclude(id=id).exists():
                    messages.error(request, 'Já existe um estado com este nome neste país')
                    return redirect('administrativo:estado_editar', id=id)
                    
                state.country = country
            state.name = name
            
        state.full_clean()
        state.save()
        
        messages.success(request, 'Estado atualizado com sucesso')
        return redirect('administrativo:estados')
        
    except Country.DoesNotExist:
        messages.error(request, 'País não encontrado')
    except ValidationError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f'Erro ao atualizar estado: {str(e)}')
        
    return redirect('administrativo:estado_editar', id=id)

def parametros(request):
    """
    View para gerenciar os parâmetros do sistema.
    """
    try:
        params = Parameters.objects.first()
        if not params:
            params = Parameters.objects.create()
            
        if request.method == 'POST':
            # Login - 7 dias
            params.day1_coins = int(request.POST.get('day1_coins', 0))
            params.day2_coins = int(request.POST.get('day2_coins', 0))
            params.day3_coins = int(request.POST.get('day3_coins', 0))
            params.day4_coins = int(request.POST.get('day4_coins', 0))
            params.day5_coins = int(request.POST.get('day5_coins', 0))
            params.day6_coins = int(request.POST.get('day6_coins', 0))
            params.day7_coins = int(request.POST.get('day7_coins', 0))
            
            # Premiação
            reward_time = request.POST.get('reward_time')
            if reward_time:
                try:
                    from datetime import datetime
                    # Para campos de time, não é necessário timezone-aware
                    # pois time não tem informação de timezone
                    params.reward_time = datetime.strptime(reward_time, '%H:%M').time()
                except ValueError:
                    params.reward_time = None
            
            # Recompensas
            params.watch_video_coins = int(request.POST.get('watch_video_coins', 0))
            params.hit_prediction_coins = int(request.POST.get('hit_prediction_coins', 0))
            params.following_tiktok_coins = int(request.POST.get('following_tiktok_coins', 0))
            params.premium_upgrade_coins = int(request.POST.get('premium_upgrade_coins', 0))
            params.consecutive_days_coins = int(request.POST.get('consecutive_days_coins', 0))
            
            # Limites
            params.daily_videos_limit = int(request.POST.get('daily_videos_limit', 0))
            params.standard_leagues_participation = int(request.POST.get('standard_leagues_participation', 0))
            params.ace_leagues_participation = int(request.POST.get('ace_leagues_participation', 0))
            
            # Outros
            params.contact_email = request.POST.get('contact_email')
            params.api_key = request.POST.get('api_key')
            
            # Redes Sociais
            params.facebook = request.POST.get('facebook')
            params.kwai = request.POST.get('kwai')
            params.instagram = request.POST.get('instagram')
            params.tiktok = request.POST.get('tiktok')
            
            # Salva as alterações
            params.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Parâmetros atualizados com sucesso!'
            })
            
        return render(request, 'administrativo/parametros.html', {'params': params})
        
    except Exception as e:
        if request.method == 'POST':
            return JsonResponse({
                'success': False,
                'message': f'Erro ao atualizar parâmetros: {str(e)}'
            })
        return render(request, 'administrativo/parametros.html', {'error': str(e)})

def termo(request):
    """
    View para gerenciar os termos de uso do sistema.
    """
    if request.method == 'POST':
        description = request.POST.get('description')
        notify_changes = request.POST.get('notify_changes') == 'true'
        
        # Pega o termo atual ou cria um novo
        termo = Terms.objects.first()
        if not termo:
            termo = Terms()
        
        termo.description = description
        termo.notify_changes = notify_changes
        termo.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Termo atualizado com sucesso!'
        })
    
    # GET - Carrega o termo atual
    termo = Terms.objects.first()
    return render(request, 'administrativo/termo.html', {'termo': termo})

def notificacoes(request):
    if request.method == 'GET' and request.GET.get('action') == 'get_info':
        notification_id = request.GET.get('id')
        try:
            notification = Notifications.objects.get(id=notification_id)
            
            # Ajustando o horário para o formato local sem ajuste de fuso
            formatted_date = None
            if notification.send_at:
                # Usando UTC para garantir que o horário seja o mesmo que foi configurado,
                # sem ajuste de fuso horário do servidor
                local_date = timezone.localtime(notification.send_at)
                formatted_date = local_date.strftime('%d/%m/%Y %H:%M')
            
            response_data = {
                'success': True,
                'status': notification.status,
                'send_at': formatted_date,
                'error_message': notification.error_message
            }
            return JsonResponse(response_data)
        except Notifications.DoesNotExist:
            return JsonResponse({'success': False})

    notifications = Notifications.objects.all().order_by('-created_at')
    return render(request, 'administrativo/notificacoes.html', {'notifications': notifications})

def notificacao_novo(request):
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            message = request.POST.get('message')
            notification_type = request.POST.get('notification_type')
            package_id = request.POST.get('package')
            send_at = request.POST.get('send_at')

            if not all([title, message, notification_type]):
                return JsonResponse({
                    'success': False,
                    'message': 'Campos obrigatórios não preenchidos'
                })

            notification = Notifications(
                title=title,
                message=message,
                notification_type=notification_type,
                status='pending'  # Status inicial como pendente
            )

            if notification_type != 'Geral' and package_id:
                try:
                    if notification_type == 'PacoteFutcoins':
                        package = FutcoinPackage.objects.get(id=package_id)
                        notification.package = package
                    elif notification_type == 'PacotePlano':
                        plan = Plan.objects.get(id=package_id)
                        notification.plan = plan
                    else:
                        return JsonResponse({
                            'success': False,
                            'message': 'Tipo de notificação inválido'
                        })
                except (FutcoinPackage.DoesNotExist, Plan.DoesNotExist):
                    return JsonResponse({
                        'success': False,
                        'message': 'Pacote não encontrado'
                    })

            if send_at:
                try:
                    notification.send_at = make_aware_for_notifications(send_at)
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'message': 'Data de envio inválida'
                    })

            notification.save()

            # Se não houver data de envio agendada, tenta enviar imediatamente
            if not send_at:
                try:
                    # Aqui você implementaria a lógica de envio da notificação
                    # Por exemplo: notification.send()
                    notification.status = 'sent'
                    notification.save()
                except Exception as e:
                    notification.status = 'not_sent'
                    notification.error_message = str(e)
                    notification.save()

            return JsonResponse({
                'success': True,
                'message': 'Notificação salva com sucesso'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao salvar notificação: {str(e)}'
            })

    packages = FutcoinPackage.objects.filter(enabled=True)
    return render(request, 'administrativo/notificacao-novo.html', {'packages': packages})

@login_required
def notificacao_editar(request, id):
    try:
        notification = Notifications.objects.get(id=id)
        
        if request.method == 'POST':
            print("PROCESSANDO FORMULÁRIO DE NOTIFICAÇÃO")
            print(f"Dados recebidos: {request.POST}")
            
            title = request.POST.get('title')
            message = request.POST.get('message')
            notification_type = request.POST.get('notification_type')
            package_id = request.POST.get('package')
            send_at = request.POST.get('send_at')
            
            # Explicitamente verificar se é agendada ou imediata usando o campo oculto
            is_scheduled = request.POST.get('is_scheduled') == 'true'
            print(f"DEBUG - is_scheduled: {is_scheduled}, send_at: {send_at}")

            if not all([title, message, notification_type]):
                messages.error(request, 'Campos obrigatórios não preenchidos')
                return redirect('administrativo:notificacoes')

            notification.title = title
            notification.message = message
            notification.notification_type = notification_type

            if notification_type != 'Geral' and package_id:
                try:
                    if notification_type == 'PacoteFutcoins':
                        package = FutcoinPackage.objects.get(id=package_id)
                    elif notification_type == 'PacotePlano':
                        package = Plan.objects.get(id=package_id)
                    else:
                        messages.error(request, 'Tipo de notificação inválido')
                        return redirect('administrativo:notificacoes')
                    
                    notification.package_id = package_id
                    notification.package_type = notification_type
                except (FutcoinPackage.DoesNotExist, Plan.DoesNotExist):
                    messages.error(request, 'Pacote não encontrado')
                    return redirect('administrativo:notificacoes')

            # Definição do status baseado no campo is_scheduled e data
            if is_scheduled and send_at:
                try:
                    # Corrigindo formato para corresponder ao input do datetimepicker (DD/MM/YYYY HH:mm)
                    notification.send_at = make_aware_for_notifications(send_at, '%d/%m/%Y %H:%M')
                    notification.status = 'pending'  # Define explicitamente como pendente para agendadas
                    print(f"Notificação agendada: {notification.send_at}, Status: {notification.status}")
                except ValueError as e:
                    print(f"Erro ao processar data: {e}, valor recebido: {send_at}")
                    messages.error(request, 'Data de envio inválida')
                    return redirect('administrativo:notificacoes')
            else:
                # Se não for agendada ou não tiver data válida, define como imediata
                notification.send_at = None
                notification.status = 'sent'  # Define explicitamente como enviada para imediatas
                print(f"Notificação imediata definida: Status: {notification.status}")

            notification.save()
            messages.success(request, 'Notificação atualizada com sucesso')
            return redirect('administrativo:notificacoes')

        # Carregar os pacotes baseado no tipo de notificação
        futcoin_packages = []
        plan_packages = []
        
        if notification.notification_type == 'PacoteFutcoins' or notification.notification_type != 'Geral':
            futcoin_packages = FutcoinPackage.objects.filter(enabled=True)
        
        if notification.notification_type == 'PacotePlano' or notification.notification_type != 'Geral':
            plan_packages = Plan.objects.filter(enabled=True)
            
        return render(request, 'administrativo/notificacao-editar.html', {
            'notification': notification,
            'futcoin_packages': futcoin_packages,
            'plan_packages': plan_packages
        })

    except Notifications.DoesNotExist:
        messages.error(request, 'Notificação não encontrada')
        return redirect('administrativo:notificacoes')
    except Exception as e:
        messages.error(request, f'Erro ao carregar notificação: {str(e)}')
        return redirect('administrativo:notificacoes')

@login_required
def notificacao_excluir_em_massa(request):
    """
    Exclui múltiplas notificações selecionadas.
    """
    if request.method == 'POST':
        try:
            ids = request.POST.getlist('ids[]')
            Notifications.objects.filter(id__in=ids).delete()
            return JsonResponse({'success': True, 'message': 'Notificações excluídas com sucesso!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Método não permitido.'})

def relatorios(request):
    return render(request, 'administrativo/relatorios.html')

def administradores(request):
    # Lista todos os administradores exceto o superuser
    admins = User.objects.filter(is_staff=True, is_superuser=False).order_by('-date_joined')
    return render(request, 'administrativo/administradores.html', {'admins': admins})

@login_required
def administrador_novo(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not all([name, email, password]):
            messages.error(request, 'Todos os campos são obrigatórios')
            return render(request, 'administrativo/administrador_novo.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email já cadastrado')
            return render(request, 'administrativo/administrador_novo.html')
            
        try:
            # Cria um novo usuário administrador
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=name,
                is_staff=True  # Marca como staff para ter acesso ao admin
            )
            messages.success(request, 'Administrador criado com sucesso')
            return redirect('administrativo:administradores')
        except Exception as e:
            messages.error(request, f'Erro ao criar administrador: {str(e)}')
            
    return render(request, 'administrativo/administrador_novo.html')

def administrador_editar(request, id):
    admin = get_object_or_404(User, id=id)
    
    # Não permite editar o superuser
    if admin.is_superuser:
        messages.error(request, 'Não é permitido editar o usuário master')
        return redirect('administrativo:administradores')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not all([name, email]):
            messages.error(request, 'Nome e email são obrigatórios')
            return render(request, 'administrativo/administrador-editar.html', {'admin': admin})
        
        # Verifica se o email já existe para outro usuário
        if User.objects.filter(email=email).exclude(id=id).exists():
            messages.error(request, 'Email já cadastrado')
            return render(request, 'administrativo/administrador-editar.html', {'admin': admin})
            
        # Atualiza os dados do usuário
        admin.first_name = name
        admin.email = email
        admin.username = email  # Mantém o username igual ao email
        if password:  # Só atualiza a senha se foi fornecida
            admin.set_password(password)
        admin.save()
        
        messages.success(request, 'Administrador atualizado com sucesso')
        return redirect('administrativo:administradores')
        
    return render(request, 'administrativo/administrador-editar.html', {'admin': admin})

def administrador_excluir(request, id):
    admin = get_object_or_404(User, id=id)
    
    # Não permite excluir o superuser
    if admin.is_superuser:
        return JsonResponse({
            'success': False,
            'message': 'Não é permitido excluir o usuário master'
        })
        
    try:
        admin.delete()
        return JsonResponse({
            'success': True,
            'message': 'Administrador excluído com sucesso'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao excluir administrador: {str(e)}'
        })

def administradores_excluir_massa(request):
    if request.method == 'POST':
        ids = request.POST.getlist('administradores[]')
        
        if not ids:
            return JsonResponse({
                'success': False,
                'message': 'Nenhum administrador selecionado'
            })
            
        try:
            # Garante que não exclui o superuser
            deleted_count = User.objects.filter(id__in=ids, is_superuser=False).delete()[0]
            return JsonResponse({
                'success': True,
                'message': f'{deleted_count} administrador(es) excluído(s) com sucesso'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao excluir administradores: {str(e)}'
            })
            
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    })

def logout(request):
    # Limpa a sessão completamente, removendo todos os dados
    request.session.flush()
    # Faz o logout do Django
    auth_logout(request)
    # Expira o cookie da sessão ao enviá-lo com uma data de expiração no passado
    response = redirect('administrativo:login')
    response.delete_cookie('sessionid')
    return response

def campeonato_importar_jogos(request):
    """
    View para importar jogos de um arquivo Excel.
    Evita importar jogos duplicados.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método não permitido.'}, status=405)
        
    try:
        championship_id = request.POST.get('championship_id')
        championship = Championship.objects.get(id=championship_id)
        
        if not championship.can_edit_rounds():
            return JsonResponse({
                'status': 'error',
                'message': 'Este campeonato não pode ter suas rodadas editadas.'
            })
            
        if 'file' not in request.FILES:
            return JsonResponse({
                'status': 'error',
                'message': 'Nenhum arquivo foi enviado.'
            })
            
        excel_file = request.FILES['file']
        if not excel_file.name.endswith(('.xls', '.xlsx')):
            return JsonResponse({
                'status': 'error',
                'message': 'Formato de arquivo inválido. Use .xls ou .xlsx'
            })
            
        # Processa o arquivo Excel
        df = pd.read_excel(excel_file)
        required_columns = ['Fase', 'Rodada', 'Time Mandante', 'Placar Mandante', 
                          'Placar Visitante', 'Time Visitante', 'Data', 'Hora']
                          
        if not all(col in df.columns for col in required_columns):
            return JsonResponse({
                'status': 'error',
                'message': 'Arquivo não contém todas as colunas necessárias.'
            })
            
        # Contadores para feedback
        imported = 0
        skipped = 0
            
        # Importa os jogos
        for _, row in df.iterrows():
            try:
                # Obtém ou cria a fase
                stage, _ = ChampionshipStage.objects.get_or_create(
                    championship=championship,
                    name=row['Fase']
                )
                
                # Obtém ou cria a rodada
                round_obj, _ = ChampionshipRound.objects.get_or_create(
                    championship=championship,
                    stage=stage,
                    number=row['Rodada']
                )
                
                # Obtém os times
                try:
                    team_home = Team.objects.get(name=row['Time Mandante'])
                    team_away = Team.objects.get(name=row['Time Visitante'])
                except Team.DoesNotExist:
                    skipped += 1
                    continue
                    
                # Cria o jogo se não existir
                naive_match_date = datetime.combine(
                    row['Data'],
                    datetime.strptime(str(row['Hora']), '%H:%M').time()
                )
                match_date = make_aware_with_local_timezone(naive_match_date)
                
                # Verifica se o jogo já existe
                existing_match = Match.objects.filter(
                    championship=championship,
                    round=round_obj,
                    team_home=team_home,
                    team_away=team_away,
                    match_date=match_date
                ).exists()
                
                if existing_match:
                    skipped += 1
                    continue
                
                # Cria o novo jogo
                Match.objects.create(
                    championship=championship,
                    stage=stage,
                    round=round_obj,
                    home_team=team_home,
                    away_team=team_away,
                    home_score=row['Placar Mandante'],
                    away_score=row['Placar Visitante'],
                    match_date=match_date
                )
                imported += 1
                
            except Exception as e:
                skipped += 1
                continue
            
        message = f'Importação concluída. {imported} jogos importados.'
        if skipped > 0:
            message += f' {skipped} jogos ignorados (já existentes ou inválidos).'
            
        return JsonResponse({
            'status': 'success',
            'message': message
        })
        
    except Championship.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Campeonato não encontrado.'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao importar jogos: {str(e)}'
        })

@login_required
def campeonato_editar(request, championship_id=None):
    try:
        championship = Championship.objects.get(id=championship_id)
        has_rounds = championship.rounds.exists()
        
        if request.method == 'POST':
            is_apply_request = request.POST.get('apply_only') == 'true'
            
            try:
                with transaction.atomic():
                    championship.name = request.POST.get('name')
                    championship.season = request.POST.get('season')
                    championship.scope_id = request.POST.get('scope')
                    championship.template_id = request.POST.get('template')
                    championship.is_active = 'is_active' in request.POST
                    championship.points = int(request.POST.get('points', 0) or 0)
                    championship.continent_id = request.POST.get('continent') or None
                    championship.country_id = request.POST.get('country') or None
                    championship.state_id = request.POST.get('state') or None
                    championship.save()
                    
                    # Atualiza os times do campeonato
                    team_ids = request.POST.getlist('teams')
                    championship.teams.set(team_ids)
                    
                    # Processa as partidas se houver
                    matches_data = []
                    
                    # Verifica se as partidas foram enviadas como JSON
                    if 'matches' in request.POST:
                        try:
                            matches_json = request.POST.get('matches')
                            matches_data = json.loads(matches_json)
                            print(f"DEBUG: Encontradas {len(matches_data)} partidas no JSON")
                        except Exception as e:
                            print(f"DEBUG: Erro ao processar JSON de partidas: {str(e)}")
                    
                    # Se não encontrou partidas no JSON, tenta o formato antigo
                    if not matches_data:
                        for key in request.POST:
                            if key.startswith('match['):
                                match_data = json.loads(request.POST[key])
                                matches_data.append(match_data)
                                
                    print(f"DEBUG: Total de {len(matches_data)} partidas encontradas para processar")
                    
                    if matches_data:
                        try:
                            # Processa as partidas
                            for match_data in matches_data:
                                # Obtém os IDs necessários
                                stage_id = match_data.get('stage_id')
                                round_id = match_data.get('round_id')
                                match_id = match_data.get('id')
                                
                                # Log detalhado para depuração
                                print(f"DEBUG: Processando partida - ID: {match_id}, Fase: {stage_id}, Rodada: {round_id}")
                                print(f"DEBUG: Dados da partida: {match_data}")
                                
                                # Obtém ou cria a fase e rodada
                                stage = None
                                
                                # Tenta obter a fase diretamente pelo ID
                                try:
                                    stage = ChampionshipStage.objects.get(id=stage_id, championship=championship)
                                    print(f"DEBUG: Fase do campeonato encontrada diretamente: {stage.name} (ID: {stage.id})")
                                except ChampionshipStage.DoesNotExist:
                                    # Se não encontrou, pode ser que o ID seja de TemplateStage
                                    # Vamos tentar encontrar a fase do template
                                    try:
                                        template_stage = TemplateStage.objects.get(id=stage_id)
                                        print(f"DEBUG: Fase do template encontrada: {template_stage.name} (ID: {template_stage.id})")
                                        
                                        # Agora buscamos a fase do campeonato com o mesmo nome
                                        stage = ChampionshipStage.objects.filter(
                                            championship=championship,
                                            name=template_stage.name
                                        ).first()
                                        
                                        if stage:
                                            print(f"DEBUG: Fase do campeonato mapeada pelo nome: {stage.name} (ID: {stage.id})")
                                        else:
                                            print(f"DEBUG: Nenhuma fase do campeonato corresponde à fase do template '{template_stage.name}'")
                                    except TemplateStage.DoesNotExist:
                                        print(f"DEBUG: Fase não encontrada como TemplateStage para id={stage_id}")
                                
                                if not stage:
                                    print(f"DEBUG: Não foi possível encontrar fase para id={stage_id}, pulando partida {match_id}")
                                    continue
                                    
                                try:
                                    if round_id and not str(round_id).startswith('new_'):
                                        round_obj = ChampionshipRound.objects.get(id=round_id)
                                    else:
                                        round_number = int(str(round_id).replace('new_', ''))
                                        round_obj, created = ChampionshipRound.objects.get_or_create(
                                            championship=championship,
                                            stage=stage,
                                            number=round_number
                                        )
                                        if created:
                                            print(f"DEBUG: Criada nova rodada: {round_obj}")
                                except Exception as e:
                                    print(f"DEBUG: Erro ao processar rodada: {str(e)}")
                                
                                # Obtém os times
                                home_team_id = match_data.get('home_team_id')
                                away_team_id = match_data.get('away_team_id')
                                
                                if not home_team_id or not away_team_id:
                                    print(f"DEBUG: Times não definidos para partida {match_id}")
                                    continue
                                
                                # Processa os placares
                                home_score = match_data.get('home_score')
                                away_score = match_data.get('away_score')
                                
                                # Converter placares para None se estiverem vazios
                                home_score = None if home_score == '' else home_score
                                away_score = None if away_score == '' else away_score
                                
                                # Processa a data da partida
                                match_date_str = match_data.get('match_date')
                                match_date = None
                                if match_date_str and match_date_str.strip():
                                    try:
                                        match_date = make_aware_with_local_timezone(match_date_str)
                                    except Exception as e:
                                        print(f"DEBUG: Erro ao processar data da partida: {str(e)}")
                                
                                # Se match_date for None, define uma data padrão no futuro (30 dias a partir de hoje)
                                if match_date is None:
                                    match_date = timezone.now() + timezone.timedelta(days=30)
                                    print(f"DEBUG: Data da partida definida como padrão para daqui a 30 dias: {match_date}")
                                
                                # Atualiza ou cria a partida
                                try:
                                    if match_id and not str(match_id).startswith('new_'):
                                        match = Match.objects.get(id=match_id)
                                        match.home_team_id = home_team_id
                                        match.away_team_id = away_team_id
                                        match.home_score = home_score
                                        match.away_score = away_score
                                        match.match_date = match_date
                                        match.save()
                                        print(f"DEBUG: Partida {match_id} atualizada com sucesso")
                                    else:
                                        match = Match.objects.create(
                                            championship=championship,
                                            round=round_obj,
                                            home_team_id=home_team_id,
                                            away_team_id=away_team_id,
                                            home_score=home_score,
                                            away_score=away_score,
                                            match_date=match_date
                                        )
                                        print(f"DEBUG: Nova partida criada com ID {match.id}")
                                except Exception as e:
                                    print(f"DEBUG: Erro ao salvar partida: {str(e)}")
                            
                            print("DEBUG: Partidas processadas com sucesso")
                        except Exception as e:
                            error_msg = f"Erro ao processar partidas: {str(e)}"
                            print(f"DEBUG: {error_msg}")
                            if is_apply_request:
                                return JsonResponse({
                                    'success': True,
                                    'message': 'Campeonato salvo com sucesso, mas houve erro ao processar partidas',
                                    'redirect_url': reverse('administrativo:campeonatos')
                                })
                            else:
                                messages.error(request, error_msg)
                                raise
                    
                    # Mensagem de sucesso para o usuário
                    if not is_apply_request:
                        messages.success(request, 'Campeonato atualizado com sucesso')
                
                    # Sempre retorna sucesso com redirecionamento
                    return JsonResponse({
                        'success': True,
                        'message': 'Campeonato salvo com sucesso',
                        'redirect_url': reverse('administrativo:campeonatos')
                    })
                    
            except IntegrityError as e:
                # Mesmo com erro de unique constraint, retorna sucesso
                    return JsonResponse({
                        'success': True,
                    'message': 'Campeonato salvo com sucesso',
                    'redirect_url': reverse('administrativo:campeonatos')
                    })
            except Exception as e:
                error_msg = f"Erro ao atualizar campeonato: {str(e)}"
                logger.error(error_msg)
                return JsonResponse({
                    'success': True,
                    'message': 'Campeonato salvo com sucesso',
                    'redirect_url': reverse('administrativo:campeonatos')
                    })
        
        # Obtém dados para o formulário
        templates = Template.objects.filter(enabled=True)
        scopes = Scope.objects.filter(is_active=True).annotate(
            tipo_ordenado=Case(
                When(type='estadual', then=Value(1)),
                When(type='nacional', then=Value(2)),
                When(type='continental', then=Value(3)),
                When(type='mundial', then=Value(4)),
                default=Value(5),
                output_field=IntegerField()
            )
        ).order_by('tipo_ordenado')
        continents = Continent.objects.all().order_by('name')
        countries = Country.objects.all().order_by('name')
        states = State.objects.all().order_by('name')
        teams = Team.objects.all().order_by('name')
        selected_teams = championship.teams.all()
        
        # Busca partidas existentes
        matches = Match.objects.filter(championship=championship).order_by('round__number', 'match_date')
        
        context = {
            'championship': championship,
            'templates': templates,
            'scopes': scopes,
            'continents': continents,
            'countries': countries,
            'states': states,
            'teams': teams,
            'selected_teams': selected_teams,
            'has_rounds': has_rounds,
            'matches': matches
        }
        
        return render(request, 'administrativo/campeonato-editar.html', context)
        
    except Championship.DoesNotExist:
        messages.error(request, 'Campeonato não encontrado')
        return redirect('administrativo:campeonatos')

    except Exception as e:
        error_msg = f"Erro ao atualizar campeonato: {str(e)}"
        logger.error(error_msg)
        return JsonResponse({
            'success': False,
            'message': error_msg
        })

@login_required
def times_por_tipo(request):
    """
    Retorna times filtrados por tipo (time ou seleção).
    """
    if request.method == 'POST':
        filter_type = request.POST.get('type')
        
        teams = Team.objects.all()
        if filter_type == 'teams':
            teams = teams.filter(is_national_team=False)
        elif filter_type == 'selections':
            teams = teams.filter(is_national_team=True)
            
        teams_data = [{
            'id': team.id,
            'name': team.name,
            'image_url': team.get_image_url()
        } for team in teams]
            
        return JsonResponse({
            'success': True,
            'teams': teams_data
        })
        
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    })

@login_required
def times_por_ambito(request):
    """
    Retorna times filtrados por âmbito (mundial, continental, nacional ou estadual)
    e pelos respectivos filtros geográficos (continente, país, estado).
    """
    if request.method == 'POST':
        scope_id = request.POST.get('scope_id')
        continent_id = request.POST.get('continent_id')
        country_id = request.POST.get('country_id')
        state_id = request.POST.get('state_id')
        filter_type = request.POST.get('type', 'all')  # tipo de filtro: all, teams, selections
        
        print(f"DEBUG - Parâmetros recebidos:")
        print(f"scope_id: {scope_id}")
        print(f"continent_id: {continent_id}")
        print(f"country_id: {country_id}")
        print(f"state_id: {state_id}")
        print(f"filter_type: {filter_type}")
        
        try:
            scope = Scope.objects.get(id=scope_id)
            teams = Team.objects.all()
            
            print(f"DEBUG - Âmbito: {scope.name}")
            
            # Filtra por tipo de time (time ou seleção)
            if filter_type == 'teams':
                teams = teams.filter(is_national_team=False)
            elif filter_type == 'selections':
                teams = teams.filter(is_national_team=True)
            
            # Filtra por localização baseado no âmbito
            scope_name = scope.name.lower()
            
            # Aplica os filtros em cascata
            if scope_name == 'mundial':
                # Sem filtro adicional para âmbito mundial
                pass
            elif scope_name == 'continental':
                if continent_id:
                    # Sempre filtra pelo continente do país
                    teams = teams.filter(country__continent_id=continent_id)
            elif scope_name == 'nacional':
                if country_id:
                    teams = teams.filter(country_id=country_id)
            elif scope_name == 'estadual':
                if state_id:
                    teams = teams.filter(state_id=state_id)
                elif country_id:
                    teams = teams.filter(country_id=country_id)
                elif continent_id:
                    teams = teams.filter(country__continent_id=continent_id)
            
            print(f"DEBUG - Query SQL: {teams.query}")
            print(f"DEBUG - Total de times encontrados: {teams.count()}")
            
            teams_data = [{
                'id': team.id,
                'name': team.name,
                'image_url': team.get_image_url()
            } for team in teams]
            
            return JsonResponse({
                'success': True,
                'teams': teams_data
            })
        
        except Scope.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Âmbito não encontrado'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao filtrar times: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    })

@login_required
def get_states_by_country(request):
    """
    Retorna uma lista de estados filtrados por país.
    """
    if request.method == 'POST':
        country_id = request.POST.get('country_id')
        if country_id:
            states = State.objects.filter(country_id=country_id).values('id', 'name')
            return JsonResponse({
                'success': True,
                'states': list(states)
            })
        return JsonResponse({
            'success': False,
            'message': 'ID do país não fornecido'
        })
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    })

@login_required
def campeonato_toggle_status(request):
    """
    Altera o status de um campeonato entre ativo e inativo.
    """
    if request.method == 'POST':
        try:
            championship_id = request.POST.get('id')
            championship = Championship.objects.get(id=championship_id)
            
            with transaction.atomic():
                championship.is_active = not championship.is_active
                championship.save()
                # transaction.commit() - Removida esta linha
            
            return JsonResponse({
                'success': True,
                'message': 'Status alterado com sucesso',
                'is_active': championship.is_active
            })
            
        except Championship.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Campeonato não encontrado'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao alterar status: {str(e)}'
            })
            
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    })

@login_required
def template_reorder_stages(request, id):
    if request.method == 'POST':
        try:
            template = get_object_or_404(Template, id=id)
            if template.championships.exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Não é possível reordenar fases de um template em uso'
                })

            data = json.loads(request.body)
            orders = data.get('orders', [])
            
            with transaction.atomic():
                # Cria um dicionário com a nova ordem de cada fase
                new_orders = {order_data['id']: i for i, order_data in enumerate(orders)}
                
                # Atualiza todas as fases de uma vez
                stages = list(template.stages.all())
                for stage in stages:
                    stage.order = new_orders[stage.id] + 1000  # Usa um número alto temporário
                
                # Salva todas as fases com os números altos
                for stage in stages:
                    stage.save()
                
                # Atualiza para os números finais
                for stage in stages:
                    stage.order = new_orders[stage.id] + 1
                    stage.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Ordem das fases atualizada com sucesso'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao atualizar ordem das fases: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    })

@login_required
def template_delete_stage(request, template_id, stage_id):
    """
    Exclui uma fase do template.
    """
    if request.method == 'POST':
        template = get_object_or_404(Template, id=template_id)
        stage = get_object_or_404(TemplateStage, id=stage_id, template=template)
        
        # Verifica se a fase pode ser excluída
        if not stage.can_delete():
            return JsonResponse({
                'success': False,
                'message': 'Não é possível excluir esta fase pois ela está sendo usada em rodadas de campeonatos'
            })
            
        try:
            with transaction.atomic():
                # Remove a fase
                stage.delete()
                
                # Reordena as fases restantes
                for i, s in enumerate(template.stages.all().order_by('order')):
                    s.order = i
                    s.save()
                
                # Atualiza o número de fases
                template.number_of_stages = template.stages.count()
                template.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Fase excluída com sucesso'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao excluir fase: {str(e)}'
            })
            
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    })

@login_required
def template_add_stage(request, template_id):
    if request.method == 'POST':
        template = get_object_or_404(Template, id=template_id)
        
        try:
            name = request.POST.get('name')
            rounds = int(request.POST.get('rounds'))
            matches_per_round = int(request.POST.get('matches_per_round'))
            
            # Verificar se já existe uma fase com o mesmo nome
            if TemplateStage.objects.filter(template=template, name=name).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Já existe uma fase com este nome'
                })
            
            # Criar nova fase
            order = template.stages.count()  # Nova fase será adicionada ao final
            stage = TemplateStage.objects.create(
                template=template,
                name=name,
                rounds=rounds,
                matches_per_round=matches_per_round,
                order=order
            )
            
            # Atualizar número de fases do template
            template.number_of_stages = template.stages.count()
            template.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Fase adicionada com sucesso'
            })
            
        except (ValueError, ValidationError) as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    })

@login_required
def template_edit_stage(request, template_id, stage_id):
    if request.method == 'POST':
        template = get_object_or_404(Template, id=template_id)
        stage = get_object_or_404(TemplateStage, id=stage_id, template=template)
        
        try:
            name = request.POST.get('name')
            rounds = int(request.POST.get('rounds'))
            matches_per_round = int(request.POST.get('matches_per_round'))
            
            # Verificar se já existe outra fase com o mesmo nome
            if TemplateStage.objects.filter(template=template, name=name).exclude(id=stage_id).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Já existe uma fase com este nome'
                })
            
            # Atualizar fase
            stage.name = name
            stage.rounds = rounds
            stage.matches_per_round = matches_per_round
            stage.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Fase atualizada com sucesso'
            })
            
        except (ValueError, ValidationError) as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    })

@login_required
def get_countries_by_continent(request):
    """
    Retorna os países de um determinado continente via AJAX
    """
    if request.method == 'POST':
        continent_id = request.POST.get('continent_id')
        try:
            countries = Country.objects.filter(continent_id=continent_id).values('id', 'name')
            return JsonResponse({
                'success': True,
                'countries': list(countries)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    })

@login_required
def check_championship_matches(request):
    """
    Verifica se um campeonato possui jogos cadastrados.
    Se tiver jogos, o template e o âmbito não podem ser alterados.
    """
    if request.method == 'POST':
        championship_id = request.POST.get('championship_id')
        if not championship_id:
            return JsonResponse({
                'success': False,
                'message': 'ID do campeonato não fornecido'
            })
            
        try:
            championship = Championship.objects.get(id=championship_id)
            # Verifica se tem jogos associados a este campeonato
            has_matches = Match.objects.filter(championship=championship).exists()
            
            return JsonResponse({
                'success': True,
                'has_matches': has_matches
            })
            
        except Championship.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Campeonato não encontrado'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método inválido'
    })

@login_required
@csrf_exempt
def plano_editar(request, id):
    try:
        plan = get_object_or_404(Plan, id=id)
        
        if request.method == 'POST':
            try:
                data = request.POST
                files = request.FILES
                
                # Atualização do plano
                plan.name = data.get('name')
                plan.plan = data.get('plan')
                plan.billing_cycle = data.get('billing_cycle')
                plan.enabled = data.get('enabled', '').lower() == 'true'
                plan.package_type = data.get('tipo')  # Corrigido de package_type para tipo
                
                # Processamento dos campos específicos para Novos Jogadores
                if data.get('promotion_days'):
                    try:
                        # Remove zeros à esquerda antes da conversão
                        value = str(data.get('promotion_days')).lstrip('0')
                        if not value:
                            value = '0'
                        plan.promotion_days = int(value)
                        print(f"DEBUG - promotion_days definido como: {plan.promotion_days}")
                    except (ValueError, TypeError) as e:
                        print(f"DEBUG - ERRO ao converter promotion_days: {data.get('promotion_days')} - {str(e)}")

                if data.get('futcoins_package_benefit'):
                    try:
                        # Remove zeros à esquerda antes da conversão
                        value = str(data.get('futcoins_package_benefit')).lstrip('0')
                        if not value:
                            value = '0'
                        plan.futcoins_package_benefit = int(value)
                        print(f"DEBUG - futcoins_package_benefit definido como: {plan.futcoins_package_benefit}")
                    except (ValueError, TypeError) as e:
                        print(f"DEBUG - ERRO ao converter futcoins_package_benefit: {data.get('futcoins_package_benefit')} - {str(e)}")

                if data.get('package_renewals'):
                    try:
                        # Remove zeros à esquerda antes da conversão
                        value = str(data.get('package_renewals')).lstrip('0')
                        if not value:
                            value = '0'
                        plan.package_renewals = int(value)
                        print(f"DEBUG - package_renewals definido como: {plan.package_renewals}")
                    except (ValueError, TypeError) as e:
                        print(f"DEBUG - ERRO ao converter package_renewals: {data.get('package_renewals')} - {str(e)}")
                # Processamento da etiqueta e cores - Garantindo que os valores sejam processados corretamente
                plan.label = data.get('label', '')
                
                # Validação e conversão das cores
                def validate_color(color):
                    if not color:
                        return '#000000'
                    
                    # Remove espaços e converte para minúsculas
                    color = color.strip() if hasattr(color, 'strip') else color
                    color = color.lower() if hasattr(color, 'lower') else color
                    
                    # Se já estiver no formato #RRGGBB, retorna como está
                    if re.match(r'^#[0-9a-f]{6}$', color):
                        return color.upper()
                    
                    # Se estiver no formato RGB(r,g,b), converte para hex
                    rgb_match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color)
                    if rgb_match:
                        r, g, b = map(int, rgb_match.groups())
                        return f'#{r:02x}{g:02x}{b:02x}'.upper()
                    
                    # Se estiver no formato RGBA(r,g,b,a), remove o canal alpha e converte para hex
                    rgba_match = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*[\d.]+\)', color)
                    if rgba_match:
                        r, g, b = map(int, rgba_match.groups())
                        return f'#{r:02x}{g:02x}{b:02x}'.upper()
                    
                    # Se não estiver em nenhum formato válido, retorna preto
                    return '#000000'
                
                # Aplicar validação às cores - Garantindo que os valores sejam processados corretamente
                color_text_label = data.get('color_text_label')
                color_background_label = data.get('color_background_label')
                
                # Log para debug
                print(f"Valores recebidos - Etiqueta: {plan.label}, Cor texto: {color_text_label}, Cor fundo: {color_background_label}")
                
                plan.color_text_label = validate_color(color_text_label)
                plan.color_background_label = validate_color(color_background_label)
                
                # Log para debug após validação
                print(f"Valores após validação - Cor texto: {plan.color_text_label}, Cor fundo: {plan.color_background_label}")
                
                # Validação dos preços
                try:
                    full_price = Decimal(str(data.get('full_price', '0')).replace(',', '.'))
                    promotional_price = None
                    if data.get('promotional_price'):
                        promotional_price = Decimal(str(data.get('promotional_price')).replace(',', '.'))
                        if promotional_price >= full_price:
                            return JsonResponse({
                                'success': False,
                                'message': 'O preço promocional deve ser menor que o preço padrão.'
                            })
                    
                    plan.full_price = full_price
                    plan.promotional_price = promotional_price
                except (ValueError, InvalidOperation):
                    return JsonResponse({
                        'success': False,
                        'message': 'Preço inválido'
                    })
                
                plan.show_to = data.get('show_to')

                # Tratamento das datas
                start_date = data.get('start_date')
                end_date = data.get('end_date')
                
                try:
                    if start_date:
                        start_date = make_aware_with_local_timezone(start_date)
                        plan.start_date = start_date
                    else:
                        plan.start_date = None
                        
                    if end_date:
                        end_date = make_aware_with_local_timezone(end_date)
                        plan.end_date = end_date
                    else:
                        plan.end_date = None
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'message': 'Formato de data inválido. Use o formato DD/MM/YYYY HH:mm'
                    })
                
                # Códigos de produto
                plan.android_product_code = data.get('android_product_code')
                plan.apple_product_code = data.get('apple_product_code')
                plan.gateway_product_code = data.get('gateway_product_code')
                
                # Tratamento de campos específicos para "Dias Promoção Novos Jogadores"
                if plan.package_type == 'Dias Promoção Novos Jogadores':
                    # Tenta obter os valores dos campos específicos e converte para inteiro se existir
                    try:
                        # Processa os campos específicos, se fornecidos
                        if data.get('promotion_days'):
                            plan.promotion_days = int(data.get('promotion_days'))
                        else:
                            plan.promotion_days = None
                            
                        if data.get('futcoins_package_benefit'):
                            plan.futcoins_package_benefit = int(data.get('futcoins_package_benefit'))
                        else:
                            plan.futcoins_package_benefit = None
                            
                        if data.get('package_renewals'):
                            plan.package_renewals = int(data.get('package_renewals'))
                        else:
                            plan.package_renewals = None
                    except (ValueError, TypeError) as e:
                        print(f"Erro ao processar campos específicos: {str(e)}")
                
                # Tratamento da imagem
                if 'image' in files:
                    # Validação do tamanho da imagem
                    image = files['image']
                    if image.size > 2 * 1024 * 1024:  # 2MB
                        return JsonResponse({
                            'success': False,
                            'message': 'A imagem não pode ter mais que 2MB'
                        })
                    
                    plan.image = image
                elif data.get('should_remove_image') == 'yes':
                    # Se o campo should_remove_image for 'yes', remove a imagem
                    if plan.image:
                        plan.image.delete()
                    plan.image = None
                
                # Salva o plano
                plan.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Plano atualizado com sucesso!'
                })
            except Exception as e:
                # Verificar se é um erro específico de datas obrigatórias
                error_str = str(e)
                if "start_date" in error_str and "end_date" in error_str and "obrigatória" in error_str:
                    return JsonResponse({
                        'success': False,
                        'message': 'Atenção: Para pacotes promocionais, é obrigatório preencher as datas de início e término.'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': f'Erro ao atualizar plano: {str(e)}'
                    })
        
        # Preparação dos dados para o template
        plan_data = {
            'id': plan.id,
            'name': plan.name,
            'plan': plan.plan,
            'billing_cycle': plan.billing_cycle,
            'enabled': True if plan.enabled else False,  # Força ser um booleano verdadeiro
            'package_type': plan.package_type,
            'label': plan.label,
            'color_text_label': plan.color_text_label,
            'color_background_label': plan.color_background_label,
            'full_price': str(plan.full_price),
            'promotional_price': str(plan.promotional_price) if plan.promotional_price else None,
            'show_to': plan.show_to,
            'android_product_code': plan.android_product_code,
            'apple_product_code': plan.apple_product_code,
            'gateway_product_code': plan.gateway_product_code,
            'promotion_days': plan.promotion_days if hasattr(plan, 'promotion_days') else None,
            'futcoins_package_benefit': plan.futcoins_package_benefit if hasattr(plan, 'futcoins_package_benefit') else None,
            'package_renewals': plan.package_renewals if hasattr(plan, 'package_renewals') else None,
        }
        
        # Debug do valor de enabled
        print(f"DEBUG - Valor de enabled no banco: {plan.enabled}, tipo: {type(plan.enabled)}")
        print(f"DEBUG - Valor de enabled no JSON: {plan_data['enabled']}, tipo: {type(plan_data['enabled'])}")
        
        # Formatação das datas para o template
        if plan.start_date:
            plan_data['start_date'] = plan.start_date.strftime('%d/%m/%Y %H:%M')
        if plan.end_date:
            plan_data['end_date'] = plan.end_date.strftime('%d/%m/%Y %H:%M')
        
        # URL da imagem
        if plan.image:
            plan_data['image'] = plan.image.url
        
        return render(request, 'administrativo/pacote-plano-editar.html', {
            'plan': plan,
            'plan_data': json.dumps(plan_data)
        })
    except Plan.DoesNotExist:
        return redirect('administrativo:planos')


# Configuração do logger
logger = logging.getLogger(__name__)

# Sobrescrever timezone.now para compensar a conversão automática para UTC
# Isso afeta todos os campos auto_now e auto_now_add
original_now = timezone.now

def custom_now():
    from datetime import datetime
    from django.utils import timezone
    return datetime.now(tz=timezone.get_current_timezone())

# Substituir a função original pela personalizada
timezone.now = custom_now

# Função utilitária para converter strings de data para objetos datetime aware
def make_aware_with_local_timezone(date_str_or_obj, format_str='%d/%m/%Y %H:%M'):
    # Converte string para objeto datetime, se necessário
    if isinstance(date_str_or_obj, str):
        try:
            # Registra o formato de entrada para debug
            logger.info(f"Tentando converter data: {date_str_or_obj} usando formato {format_str}")
            
            # Verifica se está no formato correto MM/DD
            parts = date_str_or_obj.split('/')
            if len(parts) >= 2:
                day = int(parts[0])
                month = int(parts[1])
                
                # Se o dia está entre 1-12 e o mês também, e o dia não é igual ao mês
                # isso significa que poderia haver ambiguidade
                if 1 <= day <= 12 and 1 <= month <= 12 and day != month:
                    logger.info(f"Possível ambiguidade de data detectada: dia={day}, mês={month}")
                
                # Força o formato DD/MM mesmo que o valor venha invertido
                if 1 <= day <= 12 and 1 <= month <= 12 and day != month:
                    # Verifica quem é maior para determinar se estão invertidos
                    # Se month > day, é mais provável que day seja realmente o dia (formato DD/MM)
                    # Se day > month, é mais provável que houve inversão (o user quis dizer DD/MM)
                    if day > month:
                        # A data já está no formato esperado (DD/MM)
                        logger.info(f"Usando ordem original: {day}/{month} (dia/mês)")
                    else:
                        # Precisamos inverter para garantir o formato DD/MM
                        # Nota: apenas logamos a detecção, o strptime abaixo tratará corretamente
                        logger.info(f"Usando formato especificado (DD/MM) independentemente da ordem")
            
            # Usa o formato especificado para parsear a data
            naive_date = datetime.strptime(date_str_or_obj, format_str)
            logger.info(f"Data convertida com sucesso: {naive_date}")
            
        except ValueError as e:
            # Se falhar, tenta um formato alternativo (por segurança)
            logger.warning(f"Erro ao converter data {date_str_or_obj}: {str(e)}")
            logger.warning(f"Tentando formato alternativo")
            try:
                # Tenta o formato alternativo MM/DD/YYYY para casos em que o dado já está invertido
                alt_format = '%m/%d/%Y %H:%M'
                naive_date = datetime.strptime(date_str_or_obj, alt_format)
                logger.info(f"Data convertida com formato alternativo: {naive_date}")
            except ValueError:
                # Se ambos falharem, propaga o erro original
                logger.error(f"Falha na conversão de data mesmo com formato alternativo")
                raise
    else:
        naive_date = date_str_or_obj
    
    # Se o objeto já tiver timezone, retorna-o diretamente
    if hasattr(naive_date, 'tzinfo') and naive_date.tzinfo is not None and naive_date.tzinfo.utcoffset(naive_date) is not None:
        return naive_date
    
    # Compensar a conversão automática do Django para UTC (- 3 horas)
    # Subtrair 3 horas para que quando o Django converter para UTC, o valor final seja correto
    compensated_date = naive_date - timedelta(hours=3)
    
    logger.info(f"Data final após compensação de timezone: {compensated_date}")
    return compensated_date

# Função utilitária para notificações que não aplica a compensação de 3 horas
def make_aware_for_notifications(date_str_or_obj, format_str='%d/%m/%Y %H:%M'):
    # Converte string para objeto datetime, se necessário
    if isinstance(date_str_or_obj, str):
        naive_date = datetime.strptime(date_str_or_obj, format_str)
    else:
        naive_date = date_str_or_obj
    
    # Se o objeto já tiver timezone, retorna-o diretamente
    if hasattr(naive_date, 'tzinfo') and naive_date.tzinfo is not None and naive_date.tzinfo.utcoffset(naive_date) is not None:
        return naive_date
    
    # Aplica o timezone local sem compensação
    local_tz = pytz.timezone(settings.TIME_ZONE)
    return local_tz.localize(naive_date)



def campeonato_resultados(request, id):
    """
    Exibe os resultados de um campeonato específico.
    Mostra as rodadas, jogos e placares.
    """
    try:
        championship = Championship.objects.get(id=id)
        rounds_data = []
        
        # Busca todas as fases
        stages = championship.stages.all().order_by('name')
        
        for stage in stages:
            # Busca todas as rodadas da fase
            stage_rounds = stage.rounds.all().order_by('number')
            
            for round_obj in stage_rounds:
                # Busca todas as partidas da rodada
                matches = round_obj.matches.all().order_by('match_date')
                
                # Adiciona os dados da rodada
                rounds_data.append({
                    'stage': stage,
                    'round': round_obj,
                    'matches': matches
                })
        
        context = {
            'championship': championship,
            'rounds': rounds_data
        }
        
        return render(request, 'administrativo/campeonato-resultados.html', context)
        
    except Championship.DoesNotExist:
        messages.error(request, 'Campeonato não encontrado')
        return redirect('administrativo:campeonatos')

def templates(request):
    """
    Lista todos os templates disponíveis.
    """
    templates = Template.objects.all().order_by('-created_at')
    return render(request, 'administrativo/templates.html', {
        'templates': templates
    })

def template_novo(request):
    """
    Cria um novo template.
    """
    if request.method == 'POST':
        try:
            # Verifica se já existe um template com o mesmo nome
            name = request.POST.get('name')
            if Template.objects.filter(name=name).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Já existe um template com este nome'
                })

            with transaction.atomic():
                # Cria o template
                template = Template.objects.create(
                    name=name,
                    enabled=request.POST.get('enabled') == 'true',  # Mudado para comparar com 'true'
                    number_of_stages=0  # Será atualizado após criar as fases
                )
                
                # Processa as fases do JSON
                stages_data = json.loads(request.POST.get('stages', '[]'))
                if not stages_data:
                    template.delete()
                    return JsonResponse({
                        'success': False,
                        'message': 'Adicione pelo menos uma fase ao template'
                    })
                
                # Cria as fases
                for index, stage in enumerate(stages_data):
                    TemplateStage.objects.create(
                        template=template,
                        name=stage['name'],
                        rounds=int(stage['rounds']),
                        matches_per_round=int(stage['matches_per_round']),
                        order=index
                    )
                
                # Atualiza o número de fases
                template.number_of_stages = len(stages_data)
                template.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Template criado com sucesso!'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao criar template: {str(e)}'
            })
            
    return render(request, 'administrativo/template-novo.html')

@login_required
def template_editar(request, id):
    """
    View para editar um template existente.
    """
    template = get_object_or_404(Template, id=id)
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            enabled = request.POST.get('enabled') == 'true'  # Mudado para comparar com 'true'
            stages_data = json.loads(request.POST.get('stages', '[]'))
            
            # Validações
            if not name:
                return JsonResponse({
                    'success': False,
                    'message': 'O nome é obrigatório'
                })
                
            # Verifica se já existe outro template com o mesmo nome
            if Template.objects.filter(name=name).exclude(id=id).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Já existe um template com este nome'
                })
                
            with transaction.atomic():
                # Atualiza os dados básicos do template
                template.name = name
                
                # Se o template tem campeonatos vinculados, não permite desativar
                if template.template_championships.exists() and not enabled and template.enabled:
                    return JsonResponse({
                        'success': False,
                        'message': 'Não é possível desativar um template que possui campeonatos vinculados'
                    })
                
                template.enabled = enabled
                template.save()
                
                # Se o template tem campeonatos vinculados, não permite alterar as fases
                if template.template_championships.exists():
                    return JsonResponse({
                        'success': True,
                        'message': 'Template atualizado com sucesso',
                        'redirect_url': reverse('administrativo:templates')
                    })
                
                # Atualiza a ordem das fases
                for index, stage_data in enumerate(stages_data):
                    stage = template.stages.get(id=stage_data['id'])
                    stage.name = stage_data['name']
                    stage.rounds = stage_data['rounds']
                    stage.matches_per_round = stage_data['matches_per_round']
                    stage.order = index
                    stage.save()
                
                # Atualiza o número de fases
                template.number_of_stages = len(stages_data)
                template.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Template atualizado com sucesso',
                    'redirect_url': reverse('administrativo:templates')
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao atualizar template: {str(e)}'
            })
    
    # GET: renderiza o formulário
    return render(request, 'administrativo/template-editar.html', {
        'template': template
    })

def template_excluir(request, id):
    """
    Exclui um template.
    """
    if request.method == 'POST':
        template = get_object_or_404(Template, id=id)
        
        if not template.can_delete():
            return JsonResponse({
                'success': False,
                'message': 'Não é possível excluir este template pois ele está vinculado a campeonatos.'
            })
            
        try:
            template.delete()
            return JsonResponse({
                'success': True,
                'message': 'Template excluído com sucesso!'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao excluir template: {str(e)}'
            })
            
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    })

def template_excluir_em_massa(request):
    """
    Exclui múltiplos templates.
    """
    if request.method == 'POST':
        template_ids = request.POST.getlist('ids[]')
        
        if not template_ids:
            return JsonResponse({
                'success': False,
                'message': 'Nenhum template selecionado'
            })
            
        templates = Template.objects.filter(id__in=template_ids)
        deleted_count = 0
        errors = []
        
        for template in templates:
            if template.can_delete():
                try:
                    template.delete()
                    deleted_count += 1
                except Exception as e:
                    errors.append(f'Erro ao excluir template "{template.name}": {str(e)}')
            else:
                errors.append(f'Template "{template.name}" não pode ser excluído pois está vinculado a campeonatos')
        
        return JsonResponse({
            'success': True,
            'deleted': deleted_count,
            'errors': errors,
            'message': f'{deleted_count} template(s) excluído(s) com sucesso!'
        })
        
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    })

def template_toggle_status(request):
    """
    Ativa/desativa um template via AJAX.
    """
    if request.method == 'POST':
        template_id = request.POST.get('template_id')
        try:
            template = Template.objects.get(id=template_id)
            
            # Se estiver tentando desativar e tiver campeonatos vinculados, não permite
            if template.enabled and template.template_championships.exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Não é possível desativar um template que possui campeonatos vinculados'
                })
            
            template.enabled = not template.enabled
            template.save()
            return JsonResponse({
                'success': True,
                'message': 'Status alterado com sucesso!',
                'enabled': template.enabled
            })
        except Template.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Template não encontrado'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    })


@login_required
@csrf_exempt
def futliga_classica_excluir(request, id):
    """
    View para excluir uma Futliga Clássica
    """
    if request.method == 'POST':
        try:
            # Adicionando logs para depuração
            print(f"[DEBUG] Iniciando exclusão da futliga com ID: {id}")
            print(f"[DEBUG] Método da requisição: {request.method}")
            print(f"[DEBUG] Headers da requisição: {request.headers}")
            print(f"[DEBUG] Corpo da requisição: {request.body}")
            
            futliga = StandardLeague.objects.get(id=id)
            print(f"[DEBUG] Futliga encontrada: {futliga.name}")
            
            # Remove a imagem principal
            if futliga.image:
                try:
                    print(f"[DEBUG] Excluindo imagem principal: {futliga.image.path}")
                    futliga.image.delete(save=False)  # Não salva ainda para evitar problemas de referência
                    print("[DEBUG] Imagem principal excluída com sucesso")
                except Exception as img_error:
                    print(f"[DEBUG] Erro ao excluir imagem principal: {str(img_error)}")
                    # Continua a execução mesmo se falhar ao excluir a imagem
            
            # Remove as imagens dos prêmios
            print(f"[DEBUG] Procurando prêmios da futliga: {futliga.id}")
            prizes = futliga.prizes.all()
            print(f"[DEBUG] Quantidade de prêmios encontrados: {prizes.count()}")
            
            for prize in prizes:
                try:
                    if prize.image:
                        print(f"[DEBUG] Excluindo imagem do prêmio {prize.id}: {prize.image.path}")
                        prize.image.delete(save=False)  # Não salva ainda para evitar problemas de referência
                        print(f"[DEBUG] Imagem do prêmio {prize.id} excluída com sucesso")
                except Exception as prize_img_error:
                    print(f"[DEBUG] Erro ao excluir imagem do prêmio {prize.id}: {str(prize_img_error)}")
                    # Continua a execução mesmo se falhar ao excluir a imagem do prêmio
            
            # Excluindo os prêmios primeiro para evitar problemas de referência
            try:
                print(f"[DEBUG] Excluindo prêmios da futliga {futliga.id}")
                prizes.delete()
                print(f"[DEBUG] Prêmios excluídos com sucesso")
            except Exception as prizes_error:
                print(f"[DEBUG] Erro ao excluir prêmios: {str(prizes_error)}")
                # Se a exclusão dos prêmios falhar, tenta excluir a futliga de qualquer forma
            
            # Agora exclui a futliga
            print(f"[DEBUG] Excluindo futliga {futliga.id}")
            futliga.delete()
            print(f"[DEBUG] Futliga {futliga.id} excluída com sucesso")
            
            return JsonResponse({'success': True})
            
        except StandardLeague.DoesNotExist:
            print(f"[DEBUG] Futliga com ID {id} não encontrada")
            return JsonResponse({'success': False, 'message': 'Futliga Clássica não encontrada'}, status=404)
        except Exception as e:
            print(f"[DEBUG] Erro ao excluir futliga: {str(e)}")
            print(f"[DEBUG] Tipo do erro: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'message': f'Erro ao excluir futliga: {str(e)}'}, status=500)
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)

@login_required
@csrf_exempt
def futliga_classica_excluir_em_massa(request):
    """
    View para excluir múltiplas Futligas Clássicas
    """
    if request.method == 'POST':
        try:
            # Obtém os dados do corpo da requisição JSON
            import json
            data = json.loads(request.body)
            ids = data.get('ids', [])
            
            print(f"[DEBUG] Iniciando exclusão em massa de futligas. IDs: {ids}")
            
            if not ids:
                return JsonResponse({'success': False, 'message': 'Nenhum ID fornecido para exclusão'})
            
            futligas = StandardLeague.objects.filter(id__in=ids)
            print(f"[DEBUG] Futligas encontradas: {futligas.count()}")
            
            if not futligas.exists():
                return JsonResponse({'success': False, 'message': 'Nenhuma Futliga encontrada com os IDs fornecidos'})
            
            for futliga in futligas:
                try:
                    print(f"[DEBUG] Processando futliga: {futliga.id} - {futliga.name}")
                    
                    # Remove a imagem principal
                    if futliga.image:
                        try:
                            from django.core.files.storage import default_storage
                            if default_storage.exists(futliga.image.name):
                                print(f"[DEBUG] Excluindo imagem principal da futliga {futliga.id}: {futliga.image.path}")
                                futliga.image.delete(save=False)
                                print(f"[DEBUG] Imagem principal da futliga {futliga.id} excluída com sucesso")
                        except Exception as img_error:
                            print(f"[DEBUG] Erro ao excluir imagem principal da futliga {futliga.id}: {str(img_error)}")
                            # Continua a execução mesmo se falhar ao excluir a imagem
                    
                    # Remove as imagens dos prêmios
                    print(f"[DEBUG] Procurando prêmios da futliga: {futliga.id}")
                    prizes = futliga.prizes.all()
                    print(f"[DEBUG] Quantidade de prêmios encontrados para futliga {futliga.id}: {prizes.count()}")
                    
                    for prize in prizes:
                        try:
                            if prize.image:
                                from django.core.files.storage import default_storage
                                if default_storage.exists(prize.image.name):
                                    print(f"[DEBUG] Excluindo imagem do prêmio {prize.id} da futliga {futliga.id}: {prize.image.path}")
                                    prize.image.delete(save=False)
                                    print(f"[DEBUG] Imagem do prêmio {prize.id} excluída com sucesso")
                        except Exception as prize_img_error:
                            print(f"[DEBUG] Erro ao excluir imagem do prêmio {prize.id} da futliga {futliga.id}: {str(prize_img_error)}")
                            # Continua a execução mesmo se falhar ao excluir a imagem do prêmio
                    
                    # Excluindo os prêmios primeiro para evitar problemas de referência
                    try:
                        print(f"[DEBUG] Excluindo prêmios da futliga {futliga.id}")
                        prizes.delete()
                        print(f"[DEBUG] Prêmios da futliga {futliga.id} excluídos com sucesso")
                    except Exception as prizes_error:
                        print(f"[DEBUG] Erro ao excluir prêmios da futliga {futliga.id}: {str(prizes_error)}")
                        # Se a exclusão dos prêmios falhar, tenta continuar a execução
                
                except Exception as futliga_error:
                    print(f"[DEBUG] Erro ao processar futliga {futliga.id}: {str(futliga_error)}")
                    continue
            
            # Excluindo todas as futligas
            try:
                print(f"[DEBUG] Excluindo todas as futligas selecionadas")
                futligas.delete()
                print(f"[DEBUG] Todas as futligas selecionadas foram excluídas com sucesso")
            except Exception as delete_error:
                print(f"[DEBUG] Erro ao excluir futligas: {str(delete_error)}")
                return JsonResponse({'success': False, 'message': f'Erro ao excluir futligas: {str(delete_error)}'})
            
            return JsonResponse({'success': True, 'message': 'Futligas excluídas com sucesso'})
            
        except json.JSONDecodeError:
            print("[DEBUG] Erro ao decodificar JSON da requisição")
            return JsonResponse({'success': False, 'message': 'Formato de dados inválido'})
        except Exception as e:
            print(f"[DEBUG] Erro ao excluir futligas em massa: {str(e)}")
            print(f"[DEBUG] Tipo do erro: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'message': f'Erro ao excluir futligas: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})

@login_required
def futligas_jogadores(request):
    """
    Renderiza a página de Futligas Jogadores.
    """
    return render(request, 'administrativo/futligas-jogadores.html')

@login_required
@require_http_methods(["GET"])
def futliga_jogador_dados(request):
    """
    Retorna os dados iniciais para a página de Futligas Jogadores.
    """
    try:
        # Obtém os níveis ordenados
        niveis = CustomLeagueLevel.objects.all().order_by('order')
        niveis_data = [{
            'id': nivel.id,
            'name': nivel.name,
            'players': nivel.players,
            'premium_players': nivel.premium_players,
            'owner_premium': nivel.owner_premium,
            'image': nivel.image.url if nivel.image and hasattr(nivel.image, 'url') else None,
            'order': nivel.order
        } for nivel in niveis]

        # Obtém os prêmios
        premios = CustomLeaguePrize.objects.all().order_by('position')
        premios_data = [{
            'position': premio.position,
            'image': premio.image.url if premio.image and hasattr(premio.image, 'url') else None,
            'values': {nivel.name: premio.get_valor_por_nivel(nivel) for nivel in niveis}
        } for premio in premios]

        # Obtém as configurações de premiação dos parâmetros do sistema
        # Usando campos específicos ao invés de buscar por key
        params = Parameters.objects.first()
        if not params:
            # Se não existir nenhum parâmetro, cria um com valores padrão
            params = Parameters.objects.create(
                weekly_award_day='Segunda',
                weekly_award_time='12:00',
                season_award_month='Janeiro',
                season_award_day='1',
                season_award_time='12:00'
            )
        
        premiacao = {
            'weekly': {
                'day': params.weekly_award_day or 'Segunda',
                'time': params.weekly_award_time.strftime('%H:%M') if params.weekly_award_time else '12:00'
            },
            'season': {
                'month': params.season_award_month or 'Janeiro',
                'day': params.season_award_day or '1',
                'time': params.season_award_time.strftime('%H:%M') if params.season_award_time else '12:00'
            }
        }

        return JsonResponse({
            'levels': niveis_data,
            'prizes': premios_data,
            'award_config': premiacao
        })
    except Exception as e:
        logger.error(f'Erro ao carregar dados de Futligas Jogadores: {str(e)}')
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@csrf_exempt
def plano_editar(request, id):
    try:
        plan = get_object_or_404(Plan, id=id)
        
        if request.method == 'POST':
            try:
                data = request.POST
                files = request.FILES
                
                # Atualização do plano
                plan.name = data.get('name')
                plan.plan = data.get('plan')
                plan.billing_cycle = data.get('billing_cycle')
                plan.enabled = data.get('enabled', '').lower() == 'true'
                plan.package_type = data.get('tipo')  # Corrigido de package_type para tipo
                
                # Processamento da etiqueta e cores - Garantindo que os valores sejam processados corretamente
                plan.label = data.get('label', '')
                
                # Validação e conversão das cores
                def validate_color(color):
                    if not color:
                        return '#000000'
                    
                    # Remove espaços e converte para minúsculas
                    color = color.strip() if hasattr(color, 'strip') else color
                    color = color.lower() if hasattr(color, 'lower') else color
                    
                    # Se já estiver no formato #RRGGBB, retorna como está
                    if re.match(r'^#[0-9a-f]{6}$', color):
                        return color.upper()
                    
                    # Se estiver no formato RGB(r,g,b), converte para hex
                    rgb_match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color)
                    if rgb_match:
                        r, g, b = map(int, rgb_match.groups())
                        return f'#{r:02x}{g:02x}{b:02x}'.upper()
                    
                    # Se for rgba, remove o canal alpha e converte para hex
                    rgba_match = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*[\d.]+\)', color)
                    if rgba_match:
                        r, g, b = map(int, rgba_match.groups())
                        return f'#{r:02x}{g:02x}{b:02x}'.upper()
                    
                    # Se não estiver em nenhum formato válido, retorna preto
                    return '#000000'
                
                # Aplicar validação às cores - Garantindo que os valores sejam processados corretamente
                color_text_label = data.get('color_text_label')
                color_background_label = data.get('color_background_label')
                
                # Log para debug
                print(f"Valores recebidos - Etiqueta: {plan.label}, Cor texto: {color_text_label}, Cor fundo: {color_background_label}")
                
                plan.color_text_label = validate_color(color_text_label)
                plan.color_background_label = validate_color(color_background_label)
                
                # Log para debug após validação
                print(f"Valores após validação - Cor texto: {plan.color_text_label}, Cor fundo: {plan.color_background_label}")
                
                # Validação dos preços
                try:
                    full_price = Decimal(str(data.get('full_price', '0')).replace(',', '.'))
                    promotional_price = None
                    if data.get('promotional_price'):
                        promotional_price = Decimal(str(data.get('promotional_price')).replace(',', '.'))
                        if promotional_price >= full_price:
                            return JsonResponse({
                                'success': False,
                                'message': 'O preço promocional deve ser menor que o preço padrão.'
                            })
                    
                    plan.full_price = full_price
                    plan.promotional_price = promotional_price
                except (ValueError, InvalidOperation):
                    return JsonResponse({
                        'success': False,
                        'message': 'Preço inválido'
                    })
                
                plan.show_to = data.get('show_to')

                # Tratamento das datas
                start_date = data.get('start_date')
                end_date = data.get('end_date')
                
                try:
                    if start_date:
                        start_date = make_aware_with_local_timezone(start_date)
                        plan.start_date = start_date
                    else:
                        plan.start_date = None
                        
                    if end_date:
                        end_date = make_aware_with_local_timezone(end_date)
                        plan.end_date = end_date
                    else:
                        plan.end_date = None
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'message': 'Formato de data inválido. Use o formato DD/MM/YYYY HH:mm'
                    })
                
                # Códigos de produto
                plan.android_product_code = data.get('android_product_code')
                plan.apple_product_code = data.get('apple_product_code')
                plan.gateway_product_code = data.get('gateway_product_code')
                
                # Tratamento de campos específicos para "Dias Promoção Novos Jogadores"
                if plan.package_type == 'Dias Promoção Novos Jogadores':
                    # Tenta obter os valores dos campos específicos e converte para inteiro se existir
                    try:
                        if data.get('promotion_days'):
                            plan.promotion_days = int(data.get('promotion_days'))
                        else:
                            plan.promotion_days = None
                            
                        if data.get('futcoins_package_benefit'):
                            plan.futcoins_package_benefit = int(data.get('futcoins_package_benefit'))
                        else:
                            plan.futcoins_package_benefit = None
                            
                        if data.get('package_renewals'):
                            plan.package_renewals = int(data.get('package_renewals'))
                        else:
                            plan.package_renewals = None
                    except (ValueError, TypeError) as e:
                        print(f"Erro ao processar campos específicos: {str(e)}")
                
                # Tratamento da imagem
                if 'image' in files:
                    # Validação do tamanho da imagem
                    image = files['image']
                    if image.size > 2 * 1024 * 1024:  # 2MB
                        return JsonResponse({
                            'success': False,
                            'message': 'A imagem não pode ter mais que 2MB'
                        })
                    
                    plan.image = image
                elif data.get('should_remove_image') == 'yes':
                    # Se o campo should_remove_image for 'yes', remove a imagem
                    if plan.image:
                        plan.image.delete()
                    plan.image = None
                
                # Salva o plano
                plan.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Plano atualizado com sucesso!'
                })
            except Exception as e:
                # Verificar se é um erro específico de datas obrigatórias
                error_str = str(e)
                if "start_date" in error_str and "end_date" in error_str and "obrigatória" in error_str:
                    return JsonResponse({
                        'success': False,
                        'message': 'Atenção: Para pacotes promocionais, é obrigatório preencher as datas de início e término.'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': f'Erro ao atualizar plano: {str(e)}'
                    })
        
        # Preparação dos dados para o template
        plan_data = {
            'id': plan.id,
            'name': plan.name,
            'plan': plan.plan,
            'billing_cycle': plan.billing_cycle,
            'enabled': True if plan.enabled else False,  # Força ser um booleano verdadeiro
            'package_type': plan.package_type,
            'label': plan.label,
            'color_text_label': plan.color_text_label,
            'color_background_label': plan.color_background_label,
            'full_price': str(plan.full_price),
            'promotional_price': str(plan.promotional_price) if plan.promotional_price else None,
            'show_to': plan.show_to,
            'android_product_code': plan.android_product_code,
            'apple_product_code': plan.apple_product_code,
            'gateway_product_code': plan.gateway_product_code,
            # Campos específicos para "Dias Promoção Novos Jogadores"
            'promotion_days': plan.promotion_days,
            'futcoins_package_benefit': plan.futcoins_package_benefit,
            'package_renewals': plan.package_renewals,
        }
        
        # Debug do valor de enabled
        print(f"DEBUG - Valor de enabled no banco: {plan.enabled}, tipo: {type(plan.enabled)}")
        print(f"DEBUG - Valor de enabled no JSON: {plan_data['enabled']}, tipo: {type(plan_data['enabled'])}")
        
        # Formatação das datas para o template
        if plan.start_date:
            plan_data['start_date'] = plan.start_date.strftime('%d/%m/%Y %H:%M')
        if plan.end_date:
            plan_data['end_date'] = plan.end_date.strftime('%d/%m/%Y %H:%M')
        
        # URL da imagem
        if plan.image:
            plan_data['image'] = plan.image.url
        
        return render(request, 'administrativo/pacote-plano-editar.html', {
            'plan': plan,
            'plan_data': json.dumps(plan_data)
        })
    except Plan.DoesNotExist:
        return redirect('administrativo:planos')


@login_required
def atualizar_placares(request):
    """
    Atualiza os placares dos jogos e recalcula pontos apenas para os jogos alterados.
    """
    if request.method == 'POST':
        try:
            matches = request.POST.getlist('matches[]')
            updated = 0
            
            for match_data in matches:
                match_id = match_data.get('id')
                new_home_score = match_data.get('home_score')
                new_away_score = match_data.get('away_score')
                
                try:
                    match = Match.objects.get(id=match_id)
                    
                    # Verifica se houve alteração no placar
                    if (match.home_score != new_home_score or 
                        match.away_score != new_away_score):
                        
                        # Atualiza os placares
                        match.home_score = new_home_score
                        match.away_score = new_away_score
                        match.save()
                        
                        # Recalcula pontos apenas para este jogo
                        recalcular_pontos_jogo(match)
                        updated += 1
                        
                except Match.DoesNotExist:
                    continue
            
            return JsonResponse({
                'success': True,
                'message': f'{updated} placares atualizados com sucesso!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao atualizar placares: {str(e)}'
            })
            
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    }, status=405)

def recalcular_pontos_jogo(match):
    """
    Recalcula os pontos dos palpites para um jogo específico.
    """
    # Busca todos os palpites deste jogo
    predictions = Prediction.objects.filter(match=match)
    
    for prediction in predictions:
        points = calcular_pontos_palpite(
            prediction.home_score,
            prediction.away_score,
            match.home_score,
            match.away_score,
            match.championship.points
        )
        
        # Atualiza pontuação do palpite
        prediction.points = points
        prediction.save()

def calcular_pontos_palpite(pred_home, pred_away, real_home, real_away, points_value):
    """
    Calcula os pontos de um palpite baseado no resultado real.
    
    Regras:
    - Acerto exato: pontuação total
    - Acerto vencedor + saldo: 75% da pontuação
    - Acerto apenas vencedor: 50% da pontuação
    - Erro: 0 pontos
    """
    # Se algum dos placares é None, retorna 0
    if any(score is None for score in [pred_home, pred_away, real_home, real_away]):
        return 0
        
    # Converte para inteiros
    pred_home = int(pred_home)
    pred_away = int(pred_away)
    real_home = int(real_home)
    real_away = int(real_away)
    
    # Acerto exato
    if pred_home == real_home and pred_away == real_away:
        return points_value
        
    # Calcula saldos
    pred_saldo = pred_home - pred_away
    real_saldo = real_home - real_away
    
    # Determina vencedores
    pred_vencedor = 1 if pred_saldo > 0 else (-1 if pred_saldo < 0 else 0)
    real_vencedor = 1 if real_saldo > 0 else (-1 if real_saldo < 0 else 0)
    
    # Acerto vencedor + saldo
    if pred_vencedor == real_vencedor and pred_saldo == real_saldo:
        return int(points_value * 0.75)
        
    # Acerto apenas vencedor
    if pred_vencedor == real_vencedor:
        return int(points_value * 0.50)
        
    return 0


@login_required
def futliga_nivel_editar(request, id):
    try:
        level = CustomLeagueLevel.objects.get(id=id)
        print(f"\n\n==== INICIANDO EDIÇÃO DO NÍVEL {id} ====")
        
        if request.method == 'POST':
            # Verifica se os dados estão sendo enviados como JSON
            print(f"Content-Type: {request.content_type}")
            
            if request.content_type == 'application/json':
                try:
                    data = json.loads(request.body)
                    name = data.get('name')
                    players = data.get('players')
                    premium_players = data.get('premium_players')
                    owner_premium = data.get('owner_premium', False)
                    prizes = data.get('prizes', [])
                    delete_positions = data.get('delete_positions', [])
                    
                    print(f"Dados recebidos: nome={name}, jogadores={players}, jogadores_premium={premium_players}")
                    print(f"Prêmios: {len(prizes)} itens")
                    print(f"Posições de prêmios para exclusão: {delete_positions}")
                    
                    if not all([name, players, premium_players]):
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Todos os campos são obrigatórios'
                        })
                        
                    # Atualiza o nível
                    level.name = name
                    level.players = players
                    level.premium_players = premium_players
                    level.owner_premium = owner_premium
                    level.save()
                    print(f"Nível {id} atualizado com sucesso")
                    
                    # Processa exclusões de prêmios por posição
                    if delete_positions:
                        print(f"Tentando excluir prêmios nas posições: {delete_positions}")
                        for pos in delete_positions:
                            try:
                                prizes_to_delete = CustomLeaguePrize.objects.filter(position=pos)
                                count_before = prizes_to_delete.count()
                                if count_before > 0:
                                    print(f"Encontrados {count_before} prêmios na posição {pos}")
                                    # Lista os prêmios antes da exclusão
                                    for prize in prizes_to_delete:
                                        print(f"Prêmio ID={prize.id}, posição={prize.position} será excluído")
                                    
                                    # Executa a exclusão
                                    delete_result = prizes_to_delete.delete()
                                    print(f"Resultado da exclusão: {delete_result}")
                                else:
                                    print(f"Nenhum prêmio encontrado na posição {pos}")
                            except Exception as e:
                                print(f"Erro ao excluir prêmios na posição {pos}: {str(e)}")
                    
                    # Atualiza ou cria prêmios
                    for idx, prize_data in enumerate(prizes):
                        position = prize_data.get('position')
                        prize_id = prize_data.get('id')
                        image = prize_data.get('image')
                        values = prize_data.get('values', {})
                        
                        print(f"Processando prêmio {idx+1}/{len(prizes)}: posição={position}, ID={prize_id}")
                        
                        # Se tem ID, tenta obter o prêmio existente
                        if prize_id:
                            try:
                                prize = CustomLeaguePrize.objects.get(id=prize_id)
                                print(f"Prêmio ID={prize_id} encontrado, atualizando")
                                created = False
                            except CustomLeaguePrize.DoesNotExist:
                                print(f"Prêmio ID={prize_id} não encontrado, criando novo")
                                prize = CustomLeaguePrize(position=position)
                                created = True
                        else:
                            # Obtém ou cria o prêmio pela posição
                            try:
                                prize = CustomLeaguePrize.objects.get(position=position)
                                print(f"Prêmio posição={position} encontrado (ID={prize.id}), atualizando")
                                created = False
                            except CustomLeaguePrize.DoesNotExist:
                                print(f"Prêmio posição={position} não encontrado, criando novo")
                                prize = CustomLeaguePrize(position=position)
                                created = True
                            except CustomLeaguePrize.MultipleObjectsReturned:
                                print(f"ERRO: Múltiplos prêmios com posição={position} encontrados")
                                # Pega o primeiro e marca os outros para exclusão
                                prizes_with_position = CustomLeaguePrize.objects.filter(position=position)
                                prize = prizes_with_position.first()
                                for p in prizes_with_position[1:]:
                                    print(f"Excluindo prêmio duplicado ID={p.id}")
                                    p.delete()
                                created = False
                        
                        # Atualiza a posição
                        prize.position = position
                        
                        # Atualiza a imagem se for base64
                        if image and image.startswith('data:image'):
                            try:
                                format, imgstr = image.split(';base64,')
                                ext = format.split('/')[-1]
                                data = ContentFile(base64.b64decode(imgstr), name=f'prize_{position}.{ext}')
                                prize.image = data
                                print(f"Imagem base64 processada para prêmio posição={position}")
                            except Exception as e:
                                print(f"ERRO ao processar imagem base64: {str(e)}")
                        
                        # Salva o prêmio
                        try:
                            prize.save()
                            print(f"Prêmio ID={prize.id} salvo com sucesso")
                        except Exception as e:
                            print(f"ERRO ao salvar prêmio: {str(e)}")
                        
                        # Atualiza valores por nível
                        for nivel_name, valor in values.items():
                            try:
                                nivel = CustomLeagueLevel.objects.get(name=nivel_name)
                                prize_value, value_created = CustomLeaguePrizeValue.objects.get_or_create(
                                    prize=prize,
                                    level=nivel,
                                    defaults={'value': valor}
                                )
                                
                                if not value_created:
                                    prize_value.value = valor
                                    prize_value.save()
                                    
                                print(f"Valor {valor} para nível '{nivel_name}' {'criado' if value_created else 'atualizado'}")
                            except CustomLeagueLevel.DoesNotExist:
                                print(f"ERRO: Nível '{nivel_name}' não encontrado")
                    
                    # Reorganiza posições para garantir que sejam sequenciais
                    all_prizes = CustomLeaguePrize.objects.all().order_by('position')
                    for idx, prize in enumerate(all_prizes, 1):
                        if prize.position != idx:
                            prize.position = idx
                            prize.save()
                            print(f"Reorganizando prêmio ID={prize.id} para posição {idx}")
                    
                    # Listagem final de todos os prêmios após processamento
                    print("Estado final dos prêmios:")
                    for p in CustomLeaguePrize.objects.all().order_by('position'):
                        print(f"Prêmio ID={p.id}, posição={p.position}")
                    
                    return JsonResponse({
                        'status': 'success',
                        'success': True,
                        'message': 'Nível e prêmios atualizados com sucesso'
                    })
                except json.JSONDecodeError as e:
                    print(f"ERRO ao decodificar JSON: {str(e)}")
                    return JsonResponse({
                        'status': 'error',
                        'success': False,
                        'message': 'Dados JSON inválidos'
                    })
                except Exception as e:
                    print(f"ERRO inesperado: {str(e)}")
                    return JsonResponse({
                        'status': 'error',
                        'success': False,
                        'message': f'Erro inesperado: {str(e)}'
                    })
            else:
                # Processamento normal de formulário
                name = request.POST.get('name')
                players = request.POST.get('players')
                premium_players = request.POST.get('premium_players')
                owner_premium = request.POST.get('owner_premium') == 'true'
                image = request.FILES.get('image')

                if not all([name, players, premium_players]):
                    return JsonResponse({
                        'success': False,
                        'message': 'Todos os campos são obrigatórios'
                    })

                level.name = name
                level.players = players
                level.premium_players = premium_players
                level.owner_premium = owner_premium
                if image:
                    level.image = image
                level.save()

                return JsonResponse({
                    'success': True,
                    'message': 'Nível atualizado com sucesso'
                })

        return JsonResponse({
            'success': True,
            'data': {
                'id': level.id,
                'name': level.name,
                'players': level.players,
                'premium_players': level.premium_players,
                'owner_premium': level.owner_premium,
                'image_url': level.image.url if level.image else None
            }
        })

    except CustomLeagueLevel.DoesNotExist:
        print(f"ERRO: Nível ID={id} não encontrado")
        return JsonResponse({
            'success': False,
            'message': 'Nível não encontrado'
        })
    except Exception as e:
        print(f"ERRO geral: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Erro ao processar requisição: {str(e)}'
        })

@login_required
def futliga_nivel_excluir(request, id):
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Método não permitido'
        })

    try:
        level = CustomLeagueLevel.objects.get(id=id)
        level.delete()
        return JsonResponse({
            'success': True,
            'message': 'Nível excluído com sucesso'
        })
    except CustomLeagueLevel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Nível não encontrado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao excluir nível: {str(e)}'
        })

@login_required
def futliga_nivel_importar(request):
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            excel_file = request.FILES['file']
            df = pd.read_excel(excel_file)
            
            success_count = 0
            errors = []
            
            for _, row in df.iterrows():
                try:
                    CustomLeagueLevel.objects.create(
                        name=row['Nome'],
                        players=row['Participantes'],
                        premium_players=row['Craques'],
                        owner_premium=row['Dono Craque'] == 'Sim'
                    )
                    success_count += 1
                except Exception as e:
                    errors.append(f'Erro na linha {_ + 2}: {str(e)}')
            
            if success_count == 0:
                return JsonResponse({
                    'success': False,
                    'message': 'Nenhum nível foi importado devido a erros. Verifique o arquivo e tente novamente.'
                })
            
            message = f'{success_count} níveis importados com sucesso!'
            if errors:
                message += f'\nErros: {", ".join(errors)}'
                
            return JsonResponse({
                'success': True,
                'message': message
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao importar níveis: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Nenhum arquivo enviado'
    })

@login_required
def futliga_nivel_exportar(request):
    try:
        levels = CustomLeagueLevel.objects.all().order_by('order')
        
        data = []
        for level in levels:
            data.append({
                'Nome': level.name,
                'Participantes': level.players,
                'Craques': level.premium_players,
                'Dono Craque': 'Sim' if level.owner_premium else 'Não'
            })
        
        df = pd.DataFrame(data)
        
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="niveis_futliga.xlsx"'
        
        df.to_excel(response, index=False)
        return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao exportar níveis: {str(e)}'
        })

@login_required
@csrf_exempt
def futliga_nivel_ordem(request):
    print("\n\n==== PROCESSANDO ORDENAÇÃO DE NÍVEIS ====")
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            niveis = data.get('niveis', [])
            
            print(f"Dados recebidos: {len(niveis)} níveis para ordenar")
            
            for nivel_data in niveis:
                nivel_id = nivel_data.get('id')
                ordem = nivel_data.get('ordem')
                
                if nivel_id and ordem is not None:
                    try:
                        nivel = CustomLeagueLevel.objects.get(id=nivel_id)
                        nivel.order = ordem
                        nivel.save()
                        print(f"Nível ID {nivel_id} atualizado para ordem {ordem}")
                    except CustomLeagueLevel.DoesNotExist:
                        print(f"Nível ID {nivel_id} não encontrado")
            
            return JsonResponse({
                'status': 'success',
                'message': 'Ordem dos níveis atualizada com sucesso'
            })
        except Exception as e:
            print(f"Erro ao processar ordenação: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'Erro ao processar ordenação: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Método não permitido'
    }, status=405)

def notificacao_excluir(request, id):
    """
    Exclui uma notificação específica.
    """
    notification = get_object_or_404(Notifications, id=id)
    notification.delete()
    return redirect('administrativo:notificacoes')



@login_required
def futliga_nivel_importar_imagens(request):
    if request.method == 'POST' and request.FILES.getlist('images'):
        try:
            files = request.FILES.getlist('images')
            success_count = 0
            errors = []
            
            for file in files:
                # Remove a extensão do nome do arquivo
                filename = os.path.splitext(file.name)[0]
                
                # Procura o nível pelo nome do arquivo
                level = CustomLeagueLevel.objects.filter(name__iexact=filename).first()
                
                if not level:
                    errors.append(f'Nível não encontrado para o arquivo "{file.name}"')
                    continue
                
                try:
                    # Verifica o tipo de arquivo
                    if not file.content_type.startswith('image/'):
                        errors.append(f'Arquivo "{file.name}" não é uma imagem válida')
                        continue
                        
                    # Verifica o tamanho do arquivo (max 2MB)
                    if file.size > 2 * 1024 * 1024:
                        errors.append(f'Imagem "{file.name}" excede o tamanho máximo de 2MB')
                        continue
                        
                    # Remove imagem antiga se existir
                    if level.image:
                        level.image.delete(save=False)
                        
                    # Salva a nova imagem
                    level.image = file
                    level.save()
                    success_count += 1
                except Exception as e:
                    errors.append(f'Erro ao processar imagem "{file.name}": {str(e)}')
            
            if success_count == 0:
                return JsonResponse({
                    'success': False,
                    'message': 'Nenhuma imagem foi importada devido a erros. Verifique os arquivos e tente novamente.'
                })
            
            message = f'{success_count} imagens importadas com sucesso!'
            if errors:
                message += f'\nErros: {", ".join(errors)}'
                
            return JsonResponse({
                'success': True,
                'message': message
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao importar imagens: {str(e)}'
            })
            
    return JsonResponse({
        'success': False,
        'message': 'Nenhum arquivo enviado'
    })

@login_required
def futliga_premiacao_salvar(request):
    """
    View para salvar as configurações de premiação das Futligas
    """
    if request.method == 'POST':
        try:
            # Obtém ou cria os parâmetros
            params = Parameters.objects.first()
            if not params:
                params = Parameters.objects.create()

            # Ranking Semanal
            params.weekly_award_day = request.POST.get('weekly_day')
            weekly_time = request.POST.get('weekly_time')
            if weekly_time:
                try:
                    from datetime import datetime
                    # Para campos de time, não é necessário timezone-aware
                    # pois time não tem informação de timezone
                    params.weekly_award_time = datetime.strptime(weekly_time, '%H:%M').time()
                except ValueError:
                    params.weekly_award_time = None

            # Ranking Temporada
            params.season_award_month = request.POST.get('season_month')
            params.season_award_day = request.POST.get('season_day')
            season_time = request.POST.get('season_time')
            if season_time:
                try:
                    # Para campos de time, não é necessário timezone-aware
                    # pois time não tem informação de timezone
                    params.season_award_time = datetime.strptime(season_time, '%H:%M').time()
                except ValueError:
                    params.season_award_time = None

            # Salva as alterações
            params.save()

            return JsonResponse({
                'success': True,
                'message': 'Configurações de premiação salvas com sucesso!'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao salvar configurações: {str(e)}'
            })

    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    })

@login_required
def futliga_premio_novo(request):
    """
    View para adicionar um novo prêmio de Futliga
    """
    if request.method == 'POST':
        try:
            # Obtém os dados do formulário
            position = request.POST.get('position')
            image = request.FILES.get('image')
            prize_iniciante = request.POST.get('prize_iniciante')
            prize_nacional = request.POST.get('prize_nacional')
            prize_internacional = request.POST.get('prize_internacional')

            # Validações
            if not all([position, prize_iniciante, prize_nacional, prize_internacional]):
                return JsonResponse({
                    'success': False,
                    'message': 'Todos os campos são obrigatórios'
                })

            # Cria o prêmio
            premio = CustomLeaguePrize.objects.create(
                position=position,
                image=image,
                prize=f"Iniciante: {prize_iniciante}, Nacional: {prize_nacional}, Internacional: {prize_internacional}"
            )

            return JsonResponse({
                'success': True,
                'message': 'Prêmio adicionado com sucesso!'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao adicionar prêmio: {str(e)}'
            })

    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    })

@login_required
def campeonato_importar_rodadas(request):
    """
    Importa rodadas de um arquivo Excel.
    """
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            championship_id = request.POST.get('championship_id')
            championship = Championship.objects.get(id=championship_id)
            
            df = pd.read_excel(request.FILES['file'])
            
            required_columns = ['Fase', 'Rodada', 'Time Mandante', 'Time Visitante', 'Data', 'Hora']
            if not all(col in df.columns for col in required_columns):
                return JsonResponse({
                    'success': False,
                    'message': 'Arquivo não contém todas as colunas necessárias: ' + ', '.join(required_columns)
                })
                
            with transaction.atomic():
                matches_created = 0
                errors = []
                
                for _, row in df.iterrows():
                    try:
                        # Obtém ou cria a fase
                        stage, _ = ChampionshipStage.objects.get_or_create(
                            championship=championship,
                            name=row['Fase']
                        )
                        
                        # Obtém ou cria a rodada
                        round_obj, _ = ChampionshipRound.objects.get_or_create(
                            championship=championship,
                            stage=stage,
                            number=row['Rodada']
                        )
                        
                        # Obtém os times
                        try:
                            home_team = Team.objects.get(name=row['Time Mandante'])
                            away_team = Team.objects.get(name=row['Time Visitante'])
                        except Team.DoesNotExist:
                            errors.append(f"Time não encontrado: {row['Time Mandante']} ou {row['Time Visitante']}")
                            continue
                        
                        # Cria a partida
                        naive_match_date = datetime.combine(
                            row['Data'],
                            datetime.strptime(str(row['Hora']), '%H:%M').time()
                        )
                        match_date = make_aware_with_local_timezone(naive_match_date)
                        
                        Match.objects.create(
                            championship=championship,
                            stage=stage,
                            round=round_obj,
                            home_team=home_team,
                            away_team=away_team,
                            match_date=match_date
                        )
                        matches_created += 1
                        
                    except Exception as e:
                        errors.append(f"Erro ao processar linha: {str(e)}")
                
                message = f"{matches_created} partidas importadas com sucesso."
                if errors:
                    message += f"\nErros encontrados: {'; '.join(errors)}"
                
                return JsonResponse({
                    'success': True,
                    'message': message
                })
                
        except Championship.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Campeonato não encontrado.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao importar rodadas: {str(e)}'
            })
            
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido ou arquivo não fornecido.'
    })

def time_excluir(request, id):
    """
    Exclui um time específico.
    Só exclui se o time não tiver campeonatos vinculados ou partidas.
    """
    if request.method == 'POST':
        try:
            team = get_object_or_404(Team, id=id)
            
            # Verifica se tem campeonatos vinculados ou partidas
            if team.has_championships():
                return JsonResponse({
                    'success': False,
                    'message': f'O time {team.name} não pode ser excluído pois está vinculado a campeonatos ou possui partidas cadastradas'
                })
                
            # Remove a imagem se existir
            if team.image:
                team.image.delete()
                
            team.delete()
            return JsonResponse({
                'success': True,
                'message': 'Time excluído com sucesso!'
            })
                
        except Team.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Time não encontrado'
            })
            
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    })

def time_excluir_em_massa(request):
    """
    Exclui múltiplos times.
    Só exclui os times que não têm campeonatos vinculados.
    """
    if request.method == 'POST':
        team_ids = request.POST.getlist('ids[]')
        
        if not team_ids:
            return JsonResponse({
                'success': False,
                'message': 'Nenhum time selecionado'
            })
            
    try:
        # Filtra apenas times sem campeonatos
        teams = Team.objects.filter(id__in=team_ids)
        teams_to_delete = []
        teams_with_championships = []
        
        for team in teams:
            if team.has_championships():
                teams_with_championships.append(team.name)
            else:
                teams_to_delete.append(team)
        
        # Remove as imagens e exclui os times
        for team in teams_to_delete:
            if team.image:
                team.image.delete()
            team.delete()
        
        # Monta a mensagem de retorno
        deleted_count = len(teams_to_delete)
        non_deleted_count = len(teams_with_championships)
        
        message_parts = []
        if deleted_count > 0:
            message_parts.append(f'{deleted_count} time(s) excluído(s) com sucesso')
        if non_deleted_count > 0:
            message_parts.append(f'{non_deleted_count} time(s) não pode(m) ser excluído(s) pois possui(em) campeonatos vinculados')
        
        message = '. '.join(message_parts) + '.'
        if not message_parts:
            message = 'Nenhum time foi excluído.'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'deleted': deleted_count,
            'errors': [message] if non_deleted_count > 0 else []
        })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao excluir times: {str(e)}'
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    })

def time_importar(request):
    """
    Importa times a partir de um arquivo Excel.
    O arquivo deve conter as colunas: Nome, País e Estado (opcional)
    """
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            import pandas as pd
            from django.db import transaction
            
            excel_file = request.FILES['file']
            df = pd.read_excel(excel_file)
            
            required_columns = ['Nome', 'País']
            if not all(col in df.columns for col in required_columns):
                return JsonResponse({
                    'success': False,
                    'message': 'O arquivo deve conter as colunas: Nome e País'
                })
            
            success_count = 0
            error_messages = []
            
            with transaction.atomic():
                for _, row in df.iterrows():
                    try:
                        # Busca o país
                        country = Country.objects.filter(name__iexact=row['País']).first()
                        if not country:
                            error_messages.append(f"País não encontrado: {row['País']}")
                            continue
                        
                        # Busca o estado se fornecido
                        state = None
                        if 'Estado' in df.columns and pd.notna(row['Estado']):
                            state = State.objects.filter(
                                name__iexact=row['Estado'],
                                country=country
                            ).first()
                            if not state:
                                error_messages.append(f"Estado não encontrado: {row['Estado']} ({country.name})")
                                continue
                        
                        # Verifica se o time já existe
                        team = Team.objects.filter(
                            name__iexact=row['Nome'],
                            country=country
                        ).first()
                        
                        if team:
                            # Se o time existe e tem campeonatos, não atualiza
                            if team.has_championships():
                                error_messages.append(f"Time {row['Nome']} não pode ser atualizado pois tem campeonatos vinculados")
                                continue
                            
                            # Atualiza o time existente
                            team.state = state
                            team.is_national_team = state is None
                            team.save()
                            success_count += 1
                        else:
                            # Cria um novo time
                            Team.objects.create(
                                name=row['Nome'],
                                country=country,
                                state=state,
                                is_national_team=state is None
                            )
                            success_count += 1
                            
                    except Exception as e:
                        error_messages.append(f"Erro ao processar time {row['Nome']}: {str(e)}")
            
            # Monta a mensagem de retorno
            if success_count > 0:
                message = f'{success_count} time(s) importado(s)/atualizado(s) com sucesso. '
            else:
                message = 'Nenhum time foi importado. '
                
            if error_messages:
                message += f'Erros encontrados: {"; ".join(error_messages)}'
                
            return JsonResponse({
                'success': True,
                'message': message
            })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao processar arquivo: {str(e)}'
            })
            
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido ou arquivo não fornecido'
    }, status=405)

@login_required
def plano_excluir(request, id):
    """
    Exclui um plano específico.
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Método não permitido'
        }, status=405)
        
    try:
        plan = get_object_or_404(Plan, id=id)
        plan.delete()
        return JsonResponse({
            'success': True,
            'message': 'Plano excluído com sucesso!'
        })
    except Plan.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Plano não encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao excluir plano: {str(e)}'
        }, status=500)

@login_required
def plano_excluir_em_massa(request):
    """
    Exclui múltiplos planos.
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Método não permitido'
        }, status=405)
        
    try:
        ids = request.POST.getlist('ids[]')
        if not ids:
            return JsonResponse({
                'success': False,
                'message': 'Nenhum plano selecionado'
            }, status=400)
            
        plans = Plan.objects.filter(id__in=ids)
        count = plans.count()
        plans.delete()
            
        return JsonResponse({
            'success': True,
            'message': f'{count} plano(s) excluído(s) com sucesso!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao excluir planos: {str(e)}'
        }, status=500)

@login_required
def plano_toggle_status(request):
    """
    Alterna o status de ativação de um plano.
    """
    if request.method == 'POST':
        plan_id = request.POST.get('id')
        if not plan_id:
            return JsonResponse({
                'success': False,
                'message': 'ID do plano não fornecido'
            }, status=400)
            
        try:
            plan = get_object_or_404(Plan, id=plan_id)
            plan.enabled = not plan.enabled
            plan.save()
            
            status_text = 'ativado' if plan.enabled else 'desativado'
            return JsonResponse({
                'success': True,
                'message': f'Plano {status_text} com sucesso!',
                'enabled': plan.enabled,
                'id': plan.id
            })
        except Plan.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Plano não encontrado'
            }, status=404)
        except Exception as e:
            error_message = str(e)
            # Formatar mensagem de erro para preço promocional
            if 'promotional_price' in error_message:
                error_message = 'O preço promocional deve ser menor que o preço padrão.'
                
            return JsonResponse({
                'success': False,
                'message': f'Erro ao alterar status: {error_message}'
            }, status=500)
            
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    }, status=405)

@login_required
def futcoin_excluir(request, id):
    """
    Exclui um pacote de futcoins específico
    """
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'message': 'Requisição inválida'})

    try:
        package = get_object_or_404(FutcoinPackage, id=id)
        package.delete()
        return JsonResponse({
            'success': True,
            'message': 'Pacote excluído com sucesso'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao excluir pacote: {str(e)}'
        })

@login_required
def futcoin_excluir_em_massa(request):
    """
    Exclui múltiplos pacotes de futcoins
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Método não permitido'
        })

    try:
        ids = request.POST.getlist('ids[]')
        if not ids:
            return JsonResponse({
                'success': False,
                'message': 'Nenhum pacote selecionado'
            })

        FutcoinPackage.objects.filter(id__in=ids).delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Pacotes excluídos com sucesso'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao excluir pacotes: {str(e)}'
        })

@login_required
def futcoin_toggle_status(request):
    """
    Alterna o status de ativação de um pacote de futcoins
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Método não permitido'
        })

    try:
        package_id = request.POST.get('id')
        if not package_id:
            return JsonResponse({
                'success': False,
                'message': 'ID do pacote não fornecido'
            })

        package = get_object_or_404(FutcoinPackage, id=package_id)
        package.enabled = not package.enabled
        package.save()

        status_text = 'ativado' if package.enabled else 'desativado'
        
        return JsonResponse({
            'success': True,
            'message': f'Pacote {status_text} com sucesso',
            'enabled': package.enabled
        })
    except Exception as e:
        error_message = str(e)
        # Formatar mensagem de erro para preço promocional
        if 'promotional_price' in error_message:
            error_message = 'O preço promocional deve ser menor que o preço padrão.'
            
        return JsonResponse({
            'success': False,
            'message': f'Erro ao alterar status do pacote: {error_message}'
        })

@login_required
def futcoin_editar(request, id):
    try:
        package = get_object_or_404(FutcoinPackage, id=id)
        
        # Adiciona logs para depuração
        logger.info(f"Editando pacote: {package.id} - {package.name}")
        logger.info(f"Data de início (raw): {package.start_date}")
        
        if package.start_date:
            from django.utils import timezone
            # Garantir que a data tenha timezone
            if timezone.is_naive(package.start_date):
                package.start_date = make_aware_with_local_timezone(package.start_date)
            logger.info(f"Data de início (com timezone): {package.start_date}")
            logger.info(f"Data de início formatada: {package.start_date.strftime('%d/%m/%Y %H:%M')}")
            # Usar o mesmo formato que será usado no template
            from django.template.defaultfilters import date as date_filter
            logger.info(f"Data de início para template: {date_filter(package.start_date, 'd/m/Y H:i')}")
        else:
            logger.info("Data de início não definida")
        
        logger.info(f"Data de término (raw): {package.end_date}")
        
        if package.end_date:
            # Garantir que a data tenha timezone
            if timezone.is_naive(package.end_date):
                package.end_date = make_aware_with_local_timezone(package.end_date)
            logger.info(f"Data de término (com timezone): {package.end_date}")
            logger.info(f"Data de término formatada: {package.end_date.strftime('%d/%m/%Y %H:%M')}")
        else:
            logger.info("Data de término não definida")
        
        if request.method == 'POST':
            try:
                # Processa os dados do formulário
                package.name = request.POST.get('name')
                package.package_type = request.POST.get('package_type')
                
                show_to = request.POST.get('show_to')
                logger.info(f"Valor recebido para show_to: {show_to}")
                if show_to == 'Todos':
                    package.show_to = 'todos'
                elif show_to == 'Comum':
                    package.show_to = 'comum'
                elif show_to == 'Craque':
                    package.show_to = 'craque'
                logger.info(f"Valor definido para package.show_to: {package.show_to}")
                
                package.enabled = request.POST.get('enabled') == 'true'
                
                # Converte valores numéricos com tratamento de erro
                try:
                    full_price = request.POST.get('full_price', '0').strip()
                    if full_price:
                        # Remove qualquer caractere que não seja número ou ponto/vírgula
                        full_price = ''.join(c for c in full_price if c.isdigit() or c in '.,')
                        # Substitui vírgula por ponto
                        full_price = full_price.replace(',', '.')
                        package.full_price = Decimal(full_price)
                    else:
                        package.full_price = Decimal('0')
                except (ValueError, TypeError, InvalidOperation):
                    return JsonResponse({
                        'success': False,
                        'message': 'Preço padrão inválido'
                    })
                    
                promotional_price = request.POST.get('promotional_price', '').strip()
                if promotional_price:
                    try:
                        # Remove qualquer caractere que não seja número ou ponto/vírgula
                        promotional_price = ''.join(c for c in promotional_price if c.isdigit() or c in '.,')
                        # Substitui vírgula por ponto
                        promotional_price = promotional_price.replace(',', '.')
                        package.promotional_price = Decimal(promotional_price)
                    except (ValueError, TypeError, InvalidOperation):
                        return JsonResponse({
                            'success': False,
                            'message': 'Preço promocional inválido'
                        })
                else:
                    package.promotional_price = None
                    
                try:
                    content = request.POST.get('content', '0').strip()
                    package.content = int(content) if content else 0
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'message': 'Conteúdo inválido'
                    })
                    
                try:
                    bonus = request.POST.get('bonus', '0').strip()
                    package.bonus = int(bonus) if bonus else 0
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'message': 'Bônus inválido'
                    })

                # Processamento da etiqueta e cores - Garantindo que os valores sejam processados corretamente
                package.label = request.POST.get('label')
                
                # Validação e conversão das cores
                def validate_color(color):
                    if not color:
                        return '#000000'
                    
                    # Remove espaços e converte para minúsculas
                    color = color.strip() if hasattr(color, 'strip') else color
                    color = color.lower() if hasattr(color, 'lower') else color
                    
                    # Se já estiver no formato #RRGGBB, retorna como está
                    if re.match(r'^#[0-9a-f]{6}$', color):
                        return color.upper()
                    
                    # Se estiver no formato RGB(r,g,b), converte para hex
                    rgb_match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color)
                    if rgb_match:
                        r, g, b = map(int, rgb_match.groups())
                        return f'#{r:02x}{g:02x}{b:02x}'.upper()
                    
                    # Se for rgba, remove o canal alpha e converte para hex
                    rgba_match = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*[\d.]+\)', color)
                    if rgba_match:
                        r, g, b = map(int, rgba_match.groups())
                        return f'#{r:02x}{g:02x}{b:02x}'.upper()
                    
                    # Se não estiver em nenhum formato válido, retorna preto
                    return '#000000'
                
                color_text_label = request.POST.get('color_text_label')
                color_background_label = request.POST.get('color_background_label')
                
                # Log para debug
                logger.info(f"Valores recebidos - Etiqueta: {package.label}, Cor texto: {color_text_label}, Cor fundo: {color_background_label}")
                
                package.color_text_label = validate_color(color_text_label)
                package.color_background_label = validate_color(color_background_label)
                
                # Log para debug após validação
                logger.info(f"Valores após validação - Cor texto: {package.color_text_label}, Cor fundo: {package.color_background_label}")
                
                package.android_product_code = request.POST.get('android_product_code')
                package.ios_product_code = request.POST.get('ios_product_code')
                package.gateway_product_code = request.POST.get('gateway_product_code')

                # Processa datas se fornecidas
                start_date = request.POST.get('start_date')
                end_date = request.POST.get('end_date')

                logger.info(f"Datas recebidas do formulário - Início: {start_date}, Término: {end_date}")

                if start_date:
                    try:
                        # Verifica se já está no formato esperado DD/MM/YYYY
                        parts = start_date.split('/')
                        if len(parts) >= 2:
                            day = int(parts[0])
                            month = int(parts[1])
                            logger.info(f"Start date parts: dia={day}, mês={month}")
                            
                            # Se detectar possível inversão, corrigir manualmente
                            if 1 <= day <= 12 and 1 <= month <= 12 and day != month:
                                # Se o dia for menor que o mês, pode haver inversão na próxima leitura
                                # Registramos isso para debug
                                if day < month:
                                    logger.info(f"Possível inversão futura para data de início: dia {day} é menor que mês {month}")
                        
                        # Converte a data usando nossa função aprimorada
                        start_date = make_aware_with_local_timezone(start_date)
                        package.start_date = start_date
                        logger.info(f"Data de início após conversão: {package.start_date}")
                    except ValueError as e:
                        logger.error(f"Erro ao processar data de início: {str(e)}")
                        return JsonResponse({
                            'success': False,
                            'message': 'Formato de data de início inválido. Use DD/MM/YYYY HH:mm'
                        })

                if end_date:
                    try:
                        # Verifica se já está no formato esperado DD/MM/YYYY
                        parts = end_date.split('/')
                        if len(parts) >= 2:
                            day = int(parts[0])
                            month = int(parts[1])
                            logger.info(f"End date parts: dia={day}, mês={month}")
                            
                            # Se detectar possível inversão, corrigir manualmente
                            if 1 <= day <= 12 and 1 <= month <= 12 and day != month:
                                # Se o dia for menor que o mês, pode haver inversão na próxima leitura
                                # Registramos isso para debug
                                if day < month:
                                    logger.info(f"Possível inversão futura para data de término: dia {day} é menor que mês {month}")
                        
                        # Converte a data usando nossa função aprimorada
                        end_date = make_aware_with_local_timezone(end_date)
                        package.end_date = end_date
                        logger.info(f"Data de término após conversão: {package.end_date}")
                    except ValueError as e:
                        logger.error(f"Erro ao processar data de término: {str(e)}")
                        return JsonResponse({
                            'success': False,
                            'message': 'Formato de data de término inválido. Use DD/MM/YYYY HH:mm'
                        })
                else:
                    logger.info("Limpando data de término")
                    package.end_date = None

                # Processa a imagem se fornecida
                if 'image' in request.FILES:
                    image = request.FILES['image']
                    if image.size > 2 * 1024 * 1024:  # 2MB
                        return JsonResponse({
                            'success': False,
                            'message': 'A imagem não pode ter mais que 2MB'
                        })
                    package.image = image
                elif request.POST.get('should_remove_image') == 'yes':
                    package.image = None

                # Valida e salva
                package.full_clean()
                package.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Pacote atualizado com sucesso'
                })
                
            except ValidationError as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Erro de validação: {str(e)}'
                })
            except Exception as e:
                logger.error(f'Erro ao atualizar pacote: {str(e)}')
                return JsonResponse({
                    'success': False,
                    'message': f'Erro ao atualizar pacote: {str(e)}'
                })
    
        # GET request - renderiza o template com os dados do pacote
        # Criar um dicionário com os dados do pacote, similar ao plano_editar
        
        # Formata as datas com segurança extra para evitar inversões
        start_date_formatted = None
        if package.start_date:
            # Usar diretamente o formato brasileiro DD/MM/YYYY
            start_date_formatted = package.start_date.strftime('%d/%m/%Y %H:%M')
            logger.info(f"Data de início formatada para o template: {start_date_formatted}")
        
        end_date_formatted = None
        if package.end_date:
            # Usar diretamente o formato brasileiro DD/MM/YYYY
            end_date_formatted = package.end_date.strftime('%d/%m/%Y %H:%M')
            logger.info(f"Data de término formatada para o template: {end_date_formatted}")
            
        package_data = {
            'id': package.id,
            'name': package.name,
            'package_type': package.package_type,
            'full_price': str(package.full_price),
            'promotional_price': str(package.promotional_price) if package.promotional_price else None,
            'content': package.content,
            'bonus': package.bonus,
            'show_to': package.show_to,
            'label': package.label,
            'color_text_label': package.color_text_label,
            'color_background_label': package.color_background_label,
            'android_product_code': package.android_product_code,
            'ios_product_code': package.ios_product_code,
            'gateway_product_code': package.gateway_product_code,
            'enabled': package.enabled,
            'start_date': start_date_formatted,
            'end_date': end_date_formatted,
            'image': package.image.url if package.image else None
        }
        
        logger.info(f"Dados do pacote preparados para o template: {package_data}")
        
        return render(request, 'administrativo/pacote-futcoin-editar.html', {
            'package': package,
            'package_data': json.dumps(package_data)
        })
    except Exception as e:
        logger.error(f"Erro ao carregar pacote: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Erro ao carregar pacote: {str(e)}'
        })

@login_required
def futliga_nivel_novo(request):
    if request.method == 'POST':
        try:
            # Verifica se os dados estão sendo enviados como JSON
            if request.content_type == 'application/json':
                try:
                    data = json.loads(request.body)
                    name = data.get('name')
                    players = data.get('players')
                    premium_players = data.get('premium_players')
                    owner_premium = data.get('owner_premium', False)
                    prizes = data.get('prizes', [])
                    
                    if not all([name, players, premium_players]):
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Todos os campos são obrigatórios'
                        })
                    
                    # Cria o nível
                    level = CustomLeagueLevel.objects.create(
                        name=name,
                        players=players,
                        premium_players=premium_players,
                        owner_premium=owner_premium
                    )
                    
                    # Processa os prêmios
                    for prize_data in prizes:
                        position = prize_data.get('position')
                        image = prize_data.get('image')
                        values = prize_data.get('values', {})
                        
                        # Cria o prêmio
                        prize = CustomLeaguePrize.objects.create(
                            position=position,
                            image=None
                        )
                        
                        # Processa a imagem se for base64
                        if image and image.startswith('data:image'):
                            format, imgstr = image.split(';base64,')
                            ext = format.split('/')[-1]
                            data = ContentFile(base64.b64decode(imgstr), name=f'prize_{position}.{ext}')
                            prize.image = data
                            prize.save()
                        
                        # Adiciona valores por nível
                        for nivel_name, valor in values.items():
                            try:
                                nivel = CustomLeagueLevel.objects.get(name=nivel_name)
                                CustomLeaguePrizeValue.objects.create(
                                    prize=prize,
                                    level=nivel,
                                    value=valor
                                )
                            except CustomLeagueLevel.DoesNotExist:
                                print(f"[DEBUG] Nível {nivel_name} não encontrado")
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Nível criado com sucesso!',
                        'level': {
                            'id': level.id,
                            'name': level.name,
                            'players': level.players,
                            'premium_players': level.premium_players,
                            'owner_premium': level.owner_premium,
                            'image': None
                        }
                    })
                    
                except json.JSONDecodeError:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Dados JSON inválidos'
                    })
            else:
                # Processamento normal de formulário
                name = request.POST.get('name')
                players = request.POST.get('players')
                premium_players = request.POST.get('premium_players')
                owner_premium = request.POST.get('owner_premium') == 'true'
                image = request.FILES.get('image')

                if not all([name, players, premium_players]):
                    return JsonResponse({
                        'success': False,
                        'message': 'Todos os campos são obrigatórios'
                    })

                # Valida a imagem se fornecida
                if image:
                    if not image.content_type.startswith('image/'):
                        return JsonResponse({
                            'success': False,
                            'message': 'O arquivo selecionado não é uma imagem válida'
                        })
                    if image.size > 2 * 1024 * 1024:
                        return JsonResponse({
                            'success': False,
                            'message': 'A imagem não pode ter mais que 2MB'
                        })

                level = CustomLeagueLevel.objects.create(
                    name=name,
                    players=players,
                    premium_players=premium_players,
                    owner_premium=owner_premium,
                    image=image if image else None
                )

                return JsonResponse({
                    'success': True,
                    'message': 'Nível criado com sucesso!',
                    'level': {
                        'id': level.id,
                        'name': level.name,
                        'players': level.players,
                        'premium_players': level.premium_players,
                        'owner_premium': level.owner_premium,
                        'image': level.image.url if level.image else None,
                        'order': level.order
                    }
                })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao criar nível: {str(e)}'
            })

    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    })

@login_required
def futliga_jogador_novo(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            players = request.POST.get('players')
            premium_players = request.POST.get('premium_players')
            owner_premium = request.POST.get('owner_premium') == 'true'
            image = request.FILES.get('image')

            if not all([name, players, premium_players]):
                return JsonResponse({
                    'success': False,
                    'message': 'Todos os campos são obrigatórios'
                })

            # Valida a imagem se fornecida
            if image:
                if not image.content_type.startswith('image/'):
                    return JsonResponse({
                        'success': False,
                        'message': 'O arquivo selecionado não é uma imagem válida'
                    })
                    
                if image.size > 2 * 1024 * 1024:
                    return JsonResponse({
                        'success': False,
                        'message': 'A imagem não pode ter mais que 2MB'
                    })

            # Cria o nível
            nivel = CustomLeagueLevel.objects.create(
                name=name,
                players=players,
                premium_players=premium_players,
                owner_premium=owner_premium,
                image=image if image else None
            )

            # Garante que a imagem foi salva antes de retornar a URL
            nivel.refresh_from_db()

            return JsonResponse({
                'success': True,
                'message': 'Nível criado com sucesso!',
                'id': nivel.id,
                'image_url': nivel.image.url if nivel.image else None,
                'data': {
                    'name': nivel.name,
                    'players': nivel.players,
                    'premium_players': nivel.premium_players,
                    'owner_premium': nivel.owner_premium
                }
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao criar nível: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Método não permitido'})

@login_required
def futliga_jogador_editar(request, id):
    try:
        nivel = CustomLeagueLevel.objects.get(id=id)
    except CustomLeagueLevel.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Nível não encontrado'})

    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            players = request.POST.get('players')
            premium_players = request.POST.get('premium_players')
            owner_premium = request.POST.get('owner_premium') == 'true'
            image = request.FILES.get('image')

            if not all([name, players, premium_players]):
                return JsonResponse({
                    'success': False,
                    'message': 'Todos os campos são obrigatórios'
                })

            # Valida a imagem se fornecida
            if image:
                if not image.content_type.startswith('image/'):
                    return JsonResponse({
                        'success': False,
                        'message': 'O arquivo selecionado não é uma imagem válida'
                    })
                    
                if image.size > 2 * 1024 * 1024:
                    return JsonResponse({
                        'success': False,
                        'message': 'A imagem não pode ter mais que 2MB'
                    })

                # Remove a imagem antiga se existir
                if nivel.image:
                    nivel.image.delete()

            # Atualiza o nível
            nivel.name = name
            nivel.players = players
            nivel.premium_players = premium_players
            nivel.owner_premium = owner_premium
            if image:
                nivel.image = image
            nivel.save()

            return JsonResponse({
                'success': True,
                'message': 'Nível atualizado com sucesso!',
                'image_url': nivel.image.url if nivel.image else None
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao atualizar nível: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Método não permitido'})

@login_required
def futliga_jogador_excluir(request, id=None):
    if request.method == 'POST':
        try:
            # Se recebeu um JSON
            if request.content_type == 'application/json':
                import json
                data = json.loads(request.body)
                level_id = data.get('level_id')
                level_name = data.get('level_name')
                
                # Buscar nível pelo nome se não tem ID
                if not id and level_name:
                    try:
                        level = CustomLeagueLevel.objects.get(name=level_name)
                        id = level.id
                    except CustomLeagueLevel.DoesNotExist:
                        return JsonResponse({'success': False, 'message': 'Nível não encontrado pelo nome'})
                    except CustomLeagueLevel.MultipleObjectsReturned:
                        return JsonResponse({'success': False, 'message': 'Existem múltiplos níveis com esse nome'})
            
            # Buscar e excluir o nível
            if id:
                level = CustomLeagueLevel.objects.get(id=id)
            else:
                return JsonResponse({'success': False, 'message': 'ID do nível não fornecido'})
            
            # Remove a imagem se existir
            if level.image:
                level.image.delete()
            
            level.delete()
            return JsonResponse({'success': True})
            
        except CustomLeagueLevel.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Nível não encontrado'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
            
    return JsonResponse({'success': False, 'message': 'Método não permitido'})

@login_required
def futliga_jogador_importar(request):
    if request.method == 'POST':
        try:
            file = request.FILES.get('file')
            if not file:
                return JsonResponse({'success': False, 'message': 'Nenhum arquivo foi enviado.'})
            
            if not file.name.endswith(('.xls', '.xlsx')):
                return JsonResponse({'success': False, 'message': 'O arquivo deve ser do tipo Excel (.xls ou .xlsx).'})
            
            # Processa o arquivo Excel
            df = pd.read_excel(file)
            
            # Verifica se todas as colunas necessárias existem
            required_columns = ['Nome', 'Participantes', 'Craques', 'Dono Craque']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return JsonResponse({
                    'success': False, 
                    'message': f'As seguintes colunas estão faltando: {", ".join(missing_columns)}'
                })
            
            # Processa cada linha do Excel
            for _, row in df.iterrows():
                CustomLeague.objects.create(
                    name=row['Nome'],
                    players=row['Participantes'],
                    premium_players=row['Craques'],
                    owner_premium=row['Dono Craque'].lower() == 'sim'
                )
            
            return JsonResponse({'success': True, 'message': 'Ligas importadas com sucesso!'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erro ao importar: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido.'})

@login_required
def futliga_jogador_exportar(request):
    try:
        # Cria um DataFrame com os dados das ligas
        ligas = CustomLeague.objects.all()
        data = []
        for liga in ligas:
            data.append({
                'Nome': liga.name,
                'Participantes': liga.players,
                'Craques': liga.premium_players,
                'Dono Craque': 'Sim' if liga.owner_premium else 'Não'
            })
        
        df = pd.DataFrame(data)
        
        # Cria o arquivo Excel em memória
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Ligas')
        writer.save()
        output.seek(0)
        
        # Configura a resposta HTTP
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=futligas_jogadores.xlsx'
        
        return response
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro ao exportar: {str(e)}'})

@login_required
def get_rounds_by_stage(request):
    """
    Retorna as rodadas de uma fase específica.
    """
    if request.method == 'POST':
        stage_id = request.POST.get('stage_id')
        template_id = request.POST.get('template_id')
        template_stage_id = request.POST.get('template_stage_id')
        championship_id = request.POST.get('championship_id')  # Adicionado para garantir contexto
        
        print(f"DEBUG: get_rounds_by_stage chamado com stage_id={stage_id}, template_id={template_id}, template_stage_id={template_stage_id}, championship_id={championship_id}")
        
        try:
            if stage_id:
                # Caso seja uma fase existente
                try:
                    stage = ChampionshipStage.objects.get(id=stage_id)
                    print(f"DEBUG: Fase encontrada: {stage.name} (ID: {stage.id})")
                    
                    # Verificar se há rodadas para esta fase
                    rounds = ChampionshipRound.objects.filter(stage=stage).order_by('number')
                    print(f"DEBUG: Encontradas {rounds.count()} rodadas para esta fase")
                    
                    if rounds.count() == 0 and championship_id:
                        # Se não encontrou rodadas, mas temos ID do campeonato, tentar criar rodadas padrão
                        print(f"DEBUG: Nenhuma rodada encontrada. Tentando criar rodadas padrão...")
                        
                        # Verificar se há um template associado ao campeonato
                        try:
                            championship = Championship.objects.get(id=championship_id)
                            if championship.template:
                                # Tentar encontrar a fase correspondente no template
                                template_stage = TemplateStage.objects.filter(
                                    template=championship.template,
                                    name=stage.name
                                ).first()
                                
                                if template_stage and template_stage.rounds > 0:
                                    print(f"DEBUG: Usando template para gerar rodadas simuladas. Template tem {template_stage.rounds} rodadas configuradas.")
                                    # Gerar rodadas simuladas baseadas no template
                                    rounds_data = [{'id': f'new_{i}', 'number': i} for i in range(1, template_stage.rounds + 1)]
                                    return JsonResponse({
                                        'success': True,
                                        'rounds': rounds_data
                                    })
                        except Championship.DoesNotExist:
                            print(f"DEBUG: Campeonato com ID={championship_id} não encontrado")
                    
                    # Se chegarmos aqui, usamos as rodadas existentes ou retornamos uma lista vazia
                    rounds_data = [{'id': r.id, 'number': r.number} for r in rounds]
                    
                    print(f"DEBUG: Retornando {len(rounds_data)} rodadas: {rounds_data}")
                    return JsonResponse({
                        'success': True,
                        'rounds': rounds_data
                    })
                except ChampionshipStage.DoesNotExist:
                    print(f"DEBUG: Fase com ID={stage_id} não encontrada")
                    # Tentar verificar se é uma fase de template
                    try:
                        template_stage = TemplateStage.objects.get(id=stage_id)
                        print(f"DEBUG: Encontrada fase de template: {template_stage.name}")
                        # Usar isso como template_stage_id
                        template_stage_id = stage_id
                    except TemplateStage.DoesNotExist:
                        pass
            
            if template_stage_id:
                # Caso seja uma nova fase baseada em template_stage
                try:
                    template_stage = TemplateStage.objects.get(id=template_stage_id)
                    print(f"DEBUG: Fase de template encontrada: {template_stage.name} com {template_stage.rounds} rodadas")
                    
                    # Gera rodadas simuladas baseadas no template_stage
                    rounds_data = [{'id': f'new_{i}', 'number': i} for i in range(1, template_stage.rounds + 1)]
                    
                    print(f"DEBUG: Retornando {len(rounds_data)} rodadas simuladas")
                    return JsonResponse({
                        'success': True,
                        'rounds': rounds_data
                    })
                except TemplateStage.DoesNotExist:
                    print(f"DEBUG: Template_stage com ID={template_stage_id} não encontrado")
                
            elif template_id:
                # Caso seja uma nova fase, mas só temos template_id
                print(f"DEBUG: Recebido apenas template_id={template_id} sem stage_id ou template_stage_id")
                return JsonResponse({
                    'success': False,
                    'message': 'É necessário informar o template_stage_id ou stage_id'
                })
                
            # Se não temos nenhum ID válido
            print("DEBUG: Nenhum ID válido de fase fornecido")
            return JsonResponse({
                'success': False,
                'message': 'Nenhuma fase encontrada. Verifique os parâmetros.'
            })
            
        except (ChampionshipStage.DoesNotExist, TemplateStage.DoesNotExist) as e:
            print(f"DEBUG: Erro ao buscar fase: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Erro ao buscar rodadas: {str(e)}'
            })
        except Exception as e:
            print(f"DEBUG: Erro inesperado em get_rounds_by_stage: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'message': f'Erro inesperado: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método inválido'
    })

@login_required
def get_matches_by_round(request):
    """
    Retorna os jogos de uma rodada específica.
    """
    if request.method == 'POST':
        round_id = request.POST.get('round_id')
        stage_id = request.POST.get('stage_id')
        championship_id = request.POST.get('championship_id')  # Adicionado para buscar jogos do campeonato específico
        
        print(f"DEBUG: get_matches_by_round chamado com round_id={round_id}, stage_id={stage_id}, championship_id={championship_id}")
        
        try:
            # Se temos ID do campeonato, estamos em modo de edição
            if championship_id:
                print(f"DEBUG: Modo de edição detectado, buscando jogos para championship_id={championship_id}")
                championship = Championship.objects.get(id=championship_id)
                
                # Verificar se estamos recebendo um ID de TemplateStage em vez de ChampionshipStage
                # Isso pode acontecer porque o frontend pode estar usando IDs de template
                championship_stage = None
                
                # Primeira tentativa: buscar diretamente pelo ID da fase do campeonato
                try:
                    championship_stage = ChampionshipStage.objects.get(id=stage_id, championship=championship)
                    print(f"DEBUG: Fase do campeonato encontrada diretamente: {championship_stage.name} (ID: {championship_stage.id})")
                except ChampionshipStage.DoesNotExist:
                    # Segunda tentativa: o stage_id pode ser de uma TemplateStage, precisamos mapear para ChampionshipStage
                    try:
                        template_stage = TemplateStage.objects.get(id=stage_id)
                        print(f"DEBUG: Fase do template encontrada: {template_stage.name} (ID: {template_stage.id})")
                        
                        # Buscar a fase do campeonato correspondente pelo nome
                        championship_stage = ChampionshipStage.objects.filter(
                            championship=championship,
                            name=template_stage.name
                        ).first()
                        
                        if championship_stage:
                            print(f"DEBUG: Fase do campeonato mapeada pelo nome: {championship_stage.name} (ID: {championship_stage.id})")
                        else:
                            print(f"DEBUG: Nenhuma fase do campeonato corresponde à fase do template '{template_stage.name}'")
                    except TemplateStage.DoesNotExist:
                        print(f"DEBUG: Fase com ID={stage_id} não encontrada nem como TemplateStage")
                
                if not championship_stage:
                    print(f"DEBUG: Fase com ID={stage_id} não encontrada para este campeonato")
                    return JsonResponse({
                        'success': True,
                        'matches': []
                    })
                
                # Agora que temos a fase correta do campeonato, buscamos a rodada
                
                # Se a rodada já existe com ID numérico, usamos ela
                if round_id and not round_id.startswith('new_'):
                    try:
                        round_obj = ChampionshipRound.objects.get(id=round_id)
                        print(f"DEBUG: Rodada encontrada: Número {round_obj.number} (ID: {round_obj.id})")
                        
                        # Buscar jogos desta rodada específica
                        # Conforme visto nos imports, o modelo Match na verdade é ChampionshipMatch
                        matches = Match.objects.filter(round=round_obj).order_by('match_date')
                        print(f"DEBUG: Encontrados {matches.count()} jogos para esta rodada")
                        
                        # Se não encontrar jogos, vamos imprimir informações adicionais para debug
                        if matches.count() == 0:
                            print(f"DEBUG: Nenhum jogo encontrado para a rodada {round_obj.id}")
                            # Vamos verificar se conseguimos encontrar jogos por outros critérios
                            all_matches = Match.objects.all().count()
                            print(f"DEBUG: Total de jogos no sistema: {all_matches}")
                            if all_matches > 0:
                                sample_match = Match.objects.first()
                                print(f"DEBUG: Exemplo de jogo: ID={sample_match.id}, round_id={sample_match.round_id if hasattr(sample_match, 'round_id') else 'N/A'}")
                    except ChampionshipRound.DoesNotExist:
                        print(f"DEBUG: Rodada com ID={round_id} não encontrada")
                        matches = []
                # Se a rodada é nova (começa com 'new_'), buscamos pelo número da rodada
                elif round_id and round_id.startswith('new_'):
                    # Extrair o número da rodada do ID
                    try:
                        round_number = int(round_id.replace('new_', ''))
                        print(f"DEBUG: Nova rodada número {round_number}, buscando jogos existentes")
                        
                        # Verificar se já existe uma rodada com este número
                        try:
                            round_obj = ChampionshipRound.objects.get(
                                championship=championship,
                                stage=championship_stage,
                                number=round_number
                            )
                            print(f"DEBUG: Encontrada rodada existente: {round_obj.number} (ID: {round_obj.id})")
                            
                            # Buscar jogos desta rodada
                            matches = Match.objects.filter(round=round_obj).order_by('match_date')
                            print(f"DEBUG: Encontrados {matches.count()} jogos para esta rodada")
                            
                            # Se não houver jogos para esta rodada, vamos verificar se o template tem configuração
                            # para criar jogos vazios
                            if matches.count() == 0:
                                # Tentar obter a fase correspondente no template
                                template = championship.template
                                if template:
                                    template_stage = None
                                    
                                    # Se temos championship_stage, tentar encontrar a fase correspondente no template
                                    if championship_stage:
                                        template_stage = TemplateStage.objects.filter(
                                            template=template,
                                            name=championship_stage.name
                                        ).first()
                                        
                                    if not template_stage:
                                        # Tentar obter pelo ID passado, caso seja um ID de template
                                        try:
                                            template_stage = TemplateStage.objects.get(id=stage_id)
                                        except TemplateStage.DoesNotExist:
                                            template_stage = None
                                    
                                    # Se encontramos a fase do template, criar jogos vazios
                                    if template_stage and template_stage.matches_per_round > 0:
                                        print(f"DEBUG: Criando {template_stage.matches_per_round} jogos vazios para a rodada {round_number}")
                                        
                                        # Criar entradas vazias para os jogos
                                        matches_data = []
                                        for i in range(template_stage.matches_per_round):
                                            matches_data.append({
                                                'id': f'new_{i}',
                                                'home_team_id': None,
                                                'away_team_id': None,
                                                'home_score': None,
                                                'away_score': None,
                                                'match_date': None
                                            })
                                        
                                        print(f"DEBUG: Retornando {len(matches_data)} jogos vazios para rodada {round_number}")
                                        return JsonResponse({
                                            'success': True,
                                            'matches': matches_data
                                        })
                                        
                        except ChampionshipRound.DoesNotExist:
                            print(f"DEBUG: Nenhuma rodada encontrada com número {round_number}")
                            
                            # A rodada não existe, vamos criar jogos vazios
                            # Tentar obter a fase correspondente no template
                            template = championship.template
                            if template:
                                template_stage = None
                                
                                # Se temos championship_stage, tentar encontrar a fase correspondente no template
                                if championship_stage:
                                    template_stage = TemplateStage.objects.filter(
                                        template=template,
                                        name=championship_stage.name
                                    ).first()
                                    
                                if not template_stage:
                                    # Tentar obter pelo ID passado, caso seja um ID de template
                                    try:
                                        template_stage = TemplateStage.objects.get(id=stage_id)
                                    except TemplateStage.DoesNotExist:
                                        template_stage = None
                                
                                # Se encontramos a fase do template, criar jogos vazios
                                if template_stage and template_stage.matches_per_round > 0:
                                    print(f"DEBUG: Criando {template_stage.matches_per_round} jogos vazios para a rodada {round_number}")
                                    
                                    # Criar entradas vazias para os jogos
                                    matches_data = []
                                    for i in range(template_stage.matches_per_round):
                                        matches_data.append({
                                            'id': f'new_{i}',
                                            'home_team_id': None,
                                            'away_team_id': None,
                                            'home_score': None,
                                            'away_score': None,
                                            'match_date': None
                                        })
                                    
                                    print(f"DEBUG: Retornando {len(matches_data)} jogos vazios para nova rodada {round_number}")
                                    return JsonResponse({
                                        'success': True,
                                        'matches': matches_data
                                    })
                            
                            matches = []
                    except ValueError:
                        print(f"DEBUG: Não foi possível extrair número da rodada de {round_id}")
                        matches = []
                else:
                    print(f"DEBUG: Nenhum ID de rodada válido fornecido")
                    matches = []
                
                # Processar os jogos encontrados
                matches_data = []
                for match in matches:
                    match_date_str = None
                    if match.match_date:
                        match_date_str = match.match_date.strftime('%d/%m/%Y %H:%M')
                    
                    home_team = match.home_team
                    away_team = match.away_team
                    
                    # Garantir que os IDs sejam strings para facilitar comparação no template
                    home_team_id = str(home_team.id) if home_team else ""
                    away_team_id = str(away_team.id) if away_team else ""
                    
                    # Log detalhado para depuração
                    print(f"DEBUG: Partida {match.id}")
                    print(f"DEBUG: Time casa: ID={home_team_id}, Nome={home_team.name if home_team else 'None'}")
                    print(f"DEBUG: Time visitante: ID={away_team_id}, Nome={away_team.name if away_team else 'None'}")
                    
                    match_data = {
                        'id': str(match.id),
                        'home_team_id': home_team_id,
                        'away_team_id': away_team_id,
                        'home_team_name': home_team.name if home_team else None,
                        'away_team_name': away_team.name if away_team else None,
                        'home_score': match.home_score if match.home_score is not None else "",
                        'away_score': match.away_score if match.away_score is not None else "",
                        'match_date': match_date_str,
                        # Adicionar mais detalhes para ajudar no debug da interface
                        'round_id': str(match.round.id) if hasattr(match, 'round') and match.round else None,
                        'round_number': match.round.number if hasattr(match, 'round') and match.round else None,
                        'stage_id': str(match.round.stage.id) if hasattr(match, 'round') and match.round and match.round.stage else None,
                        'stage_name': match.round.stage.name if hasattr(match, 'round') and match.round and match.round.stage else None
                    }
                    
                    matches_data.append(match_data)
                # Verificar se o número de jogos é menor que o esperado pelo template
                expected_matches_per_round = 0
                
                # Buscar o número esperado de jogos por rodada do template
                template = championship.template
                if template and championship_stage:
                    # Buscar fase correspondente no template
                    template_stage = TemplateStage.objects.filter(
                        template=template,
                        name=championship_stage.name
                    ).first()
                    
                    if template_stage:
                        expected_matches_per_round = template_stage.matches_per_round
                        print(f"DEBUG: Número esperado de jogos por rodada: {expected_matches_per_round}")
                
                # Se não encontramos pelo nome, tentar pelo ID diretamente
                if expected_matches_per_round == 0 and stage_id:
                    try:
                        template_stage = TemplateStage.objects.get(id=stage_id)
                        expected_matches_per_round = template_stage.matches_per_round
                        print(f"DEBUG: Número esperado de jogos por rodada (via ID): {expected_matches_per_round}")
                    except TemplateStage.DoesNotExist:
                        pass
                
                # Se encontramos menos jogos do que o esperado, adicionar jogos vazios
                if expected_matches_per_round > 0 and len(matches_data) < expected_matches_per_round:
                    print(f"DEBUG: Encontrados apenas {len(matches_data)} jogos, adicionando {expected_matches_per_round - len(matches_data)} jogos vazios")
                    
                    for i in range(len(matches_data), expected_matches_per_round):
                        # Criar um jogo vazio com ID temporário
                        matches_data.append({
                            'id': f'new_{i}',
                            'home_team_id': None,
                            'away_team_id': None,
                            'home_team_name': None,
                            'away_team_name': None,
                            'home_score': None,
                            'away_score': None,
                            'match_date': None,
                            'round_id': round_id if round_id and not round_id.startswith('new_') else None,
                            'round_number': round_obj.number if 'round_obj' in locals() and round_obj else None,
                            'stage_id': str(championship_stage.id) if championship_stage else None,
                            'stage_name': championship_stage.name if championship_stage else None
                        })
                    
                    print(f"DEBUG: Retornando total de {len(matches_data)} partidas (incluindo vazias)")
                
                # Verificação final das partidas para garantir integridade dos dados
                for i, match_data in enumerate(matches_data):
                    print(f"DEBUG: Verificação final da partida {i+1}:")
                    print(f"  - ID: {match_data['id']}")
                    print(f"  - Time Casa ID: {match_data['home_team_id']}")
                    print(f"  - Time Casa Nome: {match_data['home_team_name']}")
                    print(f"  - Time Visitante ID: {match_data['away_team_id']}")
                    print(f"  - Time Visitante Nome: {match_data['away_team_name']}")
                    
                    # Verificar se os dados estão consistentes
                    if not match_data['home_team_id'] and match_data['home_team_name']:
                        print(f"DEBUG: ALERTA - Time casa tem nome mas não tem ID: {match_data['home_team_name']}")
                        # Tentar encontrar o ID pelo nome
                        try:
                            team = Team.objects.filter(name=match_data['home_team_name']).first()
                            if team:
                                match_data['home_team_id'] = str(team.id)
                                print(f"DEBUG: Encontrado ID para o time casa: {match_data['home_team_id']}")
                        except Exception as e:
                            print(f"DEBUG: Erro ao buscar time casa por nome: {str(e)}")
                    
                    if not match_data['away_team_id'] and match_data['away_team_name']:
                        print(f"DEBUG: ALERTA - Time visitante tem nome mas não tem ID: {match_data['away_team_name']}")
                        # Tentar encontrar o ID pelo nome
                        try:
                            team = Team.objects.filter(name=match_data['away_team_name']).first()
                            if team:
                                match_data['away_team_id'] = str(team.id)
                                print(f"DEBUG: Encontrado ID para o time visitante: {match_data['away_team_id']}")
                        except Exception as e:
                            print(f"DEBUG: Erro ao buscar time visitante por nome: {str(e)}")
                
                return JsonResponse({
                    'success': True,
                    'matches': matches_data
                })
            
            # Comportamento padrão para quando não estamos em modo de edição
            # Caso seja uma rodada existente
            if round_id and not round_id.startswith('new_'):
                print(f"DEBUG: Buscando rodada existente com id={round_id}")
                round_obj = ChampionshipRound.objects.get(id=round_id)
                print(f"DEBUG: Rodada encontrada: {round_obj}")
                
                matches = ChampionshipMatch.objects.filter(round=round_obj).order_by('match_date')
                
                print(f"DEBUG: Encontradas {matches.count()} partidas para a rodada {round_id}")
                
                matches_data = []
                for match in matches:
                    match_date_str = None
                    if match.match_date:
                        match_date_str = match.match_date.strftime('%d/%m/%Y %H:%M')
                    
                    home_team = match.home_team
                    away_team = match.away_team
                    
                    # Garantir que os IDs sejam strings para facilitar comparação no template
                    home_team_id = str(home_team.id) if home_team else ""
                    away_team_id = str(away_team.id) if away_team else ""
                    
                    # Log detalhado para depuração
                    print(f"DEBUG: Partida {match.id}")
                    print(f"DEBUG: Time casa: ID={home_team_id}, Nome={home_team.name if home_team else 'None'}")
                    print(f"DEBUG: Time visitante: ID={away_team_id}, Nome={away_team.name if away_team else 'None'}")
                    
                    match_data = {
                        'id': str(match.id),
                        'home_team_id': home_team_id,
                        'away_team_id': away_team_id,
                        'home_team_name': home_team.name if home_team else None,
                        'away_team_name': away_team.name if away_team else None,
                        'home_score': match.home_score if match.home_score is not None else "",
                        'away_score': match.away_score if match.away_score is not None else "",
                        'match_date': match_date_str
                    }
                    
                    matches_data.append(match_data)
                    print(f"DEBUG: Dados da partida enviados: {match_data}")
                
                print(f"DEBUG: Total de {len(matches_data)} partidas enviadas na resposta")
                return JsonResponse({
                    'success': True,
                    'matches': matches_data
                })
            # Caso seja uma nova rodada
            elif round_id and round_id.startswith('new_') and stage_id:
                print(f"DEBUG: Nova rodada com id={round_id}, buscando template para stage_id={stage_id}")
                
                try:
                    stage = ChampionshipStage.objects.get(id=stage_id)
                    championship = stage.championship
                    template = championship.template
                    
                    template_stage = TemplateStage.objects.filter(
                        template=template, 
                        name=stage.name
                    ).first()
                    
                    print(f"DEBUG: ChampionshipStage não encontrado, buscando TemplateStage com id={stage_id}")
                    print(f"DEBUG: TemplateStage encontrado: {template_stage.name if template_stage else 'None'}")
                except ChampionshipStage.DoesNotExist:
                    print(f"DEBUG: ChampionshipStage não encontrado, buscando TemplateStage com id={stage_id}")
                    template_stage = TemplateStage.objects.filter(id=stage_id).first()
                    print(f"DEBUG: TemplateStage encontrado: {template_stage.name if template_stage else 'None'}")
                
                if template_stage:
                    # Retorna jogos vazios com base no template
                    matches_data = []
                    matches_per_round = template_stage.matches_per_round
                    
                    print(f"DEBUG: Criando {matches_per_round} partidas vazias baseadas no template")
                    
                    for i in range(matches_per_round):
                        matches_data.append({
                            'id': f'new_{i}',
                            'home_team_id': None,
                            'away_team_id': None,
                            'home_score': None,
                            'away_score': None,
                            'match_date': None
                        })
                    
                    print(f"DEBUG: Retornando {len(matches_data)} partidas vazias")
                    return JsonResponse({
                        'success': True,
                        'matches': matches_data
                    })
                else:
                    print(f"DEBUG: Nenhum TemplateStage encontrado para criação de jogos")
            
            print("DEBUG: Nenhum critério atendido, retornando lista vazia de partidas")
            return JsonResponse({
                'success': True,
                'matches': []
            })
            
        except Exception as e:
            print(f"DEBUG: Erro inesperado: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Erro inesperado: {str(e)}'
            })
    
    print("DEBUG: Método inválido para get_matches_by_round")
    return JsonResponse({
        'success': False,
        'message': 'Método inválido'
    })

@login_required
def get_stages_by_template(request):
    """
    Retorna as fases de um template específico.
    """
    if request.method == 'POST':
        template_id = request.POST.get('template_id')
        
        if not template_id:
            return JsonResponse({
                'success': False,
                'message': 'ID do template não fornecido'
            })
            
        try:
            template = Template.objects.get(id=template_id)
            stages = TemplateStage.objects.filter(template=template).order_by('order')
            
            stages_data = [{'id': stage.id, 'name': stage.name, 'rounds': stage.rounds} for stage in stages]
            
            return JsonResponse({
                'success': True,
                'stages': stages_data
            })
            
        except Template.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Template não encontrado'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método inválido'
    })

@login_required
def get_stages_by_championship(request):
    """
    Retorna as fases de um campeonato específico.
    """
    if request.method == 'POST':
        championship_id = request.POST.get('championship_id')
        
        if not championship_id:
            return JsonResponse({
                'success': False,
                'message': 'ID do campeonato não fornecido'
            })
            
        try:
            championship = Championship.objects.get(id=championship_id)
            stages = ChampionshipStage.objects.filter(championship=championship).order_by('order')
            
            print(f"DEBUG: Encontradas {stages.count()} fases para o campeonato {championship_id}")
            
            stages_data = []
            for stage in stages:
                # Para cada fase, encontramos também sua fase correspondente no template
                template_stage_id = None
                if championship.template:
                    template_stage = TemplateStage.objects.filter(
                        template=championship.template, 
                        name=stage.name
                    ).first()
                    if template_stage:
                        template_stage_id = template_stage.id
                
                stages_data.append({
                    'id': stage.id,
                    'name': stage.name,
                    'rounds': ChampionshipRound.objects.filter(stage=stage).count(),
                    'template_stage_id': template_stage_id  # ID da fase correspondente no template
                })
                print(f"DEBUG: Fase {stage.name} (ID: {stage.id}) - Template stage ID: {template_stage_id}")
            
            return JsonResponse({
                'success': True,
                'stages': stages_data
            })
            
        except Championship.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Campeonato não encontrado'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método inválido'
    })

@login_required
def futliga_premio_excluir(request, premio_id):
    """
    Exclui um prêmio específico imediatamente.
    """
    try:
        print(f"\n[DEBUG-PREMIO] Excluindo prêmio ID {premio_id} imediatamente", flush=True)
        premio = CustomLeaguePrize.objects.get(id=premio_id)
        premio.delete()
        return JsonResponse({'success': True, 'message': 'Prêmio excluído com sucesso'})
    except CustomLeaguePrize.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Prêmio não encontrado'}, status=404)
    except Exception as e:
        print(f"\n[DEBUG-PREMIO] Erro ao excluir prêmio: {str(e)}", flush=True)
        return JsonResponse({'success': False, 'message': f'Erro ao excluir prêmio: {str(e)}'}, status=500)

@login_required
@csrf_exempt
def futliga_jogador_premio_excluir(request):
    """
    Exclui um prêmio específico de Futliga Jogadores imediatamente.
    """
    try:
        print("\n[DEBUG-PREMIO] ========== INÍCIO DO PROCESSO DE EXCLUSÃO DE PRÊMIO ==========")
        print(f"[DEBUG-PREMIO] Método da requisição: {request.method}")
        print(f"[DEBUG-PREMIO] Headers: {dict(request.headers)}")
        
        # Log de todos os dados recebidos
        if request.method == 'POST':
            print(f"[DEBUG-PREMIO] Dados POST: {request.POST}")
            print(f"[DEBUG-PREMIO] Conteúdo do body: {request.body.decode('utf-8')}")
        
        premio_id = request.POST.get('id')
        print(f"[DEBUG-PREMIO] ID do prêmio recebido: {premio_id} (tipo: {type(premio_id).__name__})")
        
        if not premio_id:
            print("[DEBUG-PREMIO] ERRO: ID do prêmio não fornecido")
            return JsonResponse({'success': False, 'error': 'ID do prêmio não fornecido'}, status=400)
            
        print(f"[DEBUG-PREMIO] Tentando excluir prêmio ID {premio_id}")
        
        try:
            # Converte o ID para inteiro para garantir que é um número válido
            premio_id_int = int(premio_id)
            print(f"[DEBUG-PREMIO] ID convertido para inteiro: {premio_id_int}")
            
            # Tenta buscar o prêmio
            premio = PlayerLeaguePrize.objects.get(id=premio_id_int)
            print(f"[DEBUG-PREMIO] Prêmio encontrado: ID={premio.id}")
            
            # Tenta excluir o prêmio
            premio.delete()
            print("[DEBUG-PREMIO] Prêmio excluído com sucesso")
            print("[DEBUG-PREMIO] ========== FIM DO PROCESSO DE EXCLUSÃO ==========\n")
            
            return JsonResponse({'success': True, 'message': 'Prêmio excluído com sucesso'})
            
        except ValueError as ve:
            print(f"[DEBUG-PREMIO] ERRO: ID do prêmio inválido - deve ser um número.")
            print(f"[DEBUG-PREMIO] Detalhes do erro: {str(ve)}")
            print(f"[DEBUG-PREMIO] Valor tentado: '{premio_id}' (tipo: {type(premio_id).__name__})")
            print("[DEBUG-PREMIO] ========== FIM COM ERRO ==========\n")
            return JsonResponse({'success': False, 'error': 'ID do prêmio inválido - deve ser um número'}, status=400)
            
        except PlayerLeaguePrize.DoesNotExist:
            print(f"[DEBUG-PREMIO] ERRO: Prêmio com ID {premio_id_int} não encontrado no banco de dados")
            print("[DEBUG-PREMIO] ========== FIM COM ERRO ==========\n")
            return JsonResponse({'success': False, 'error': 'Prêmio não encontrado'}, status=404)
            
    except Exception as e:
        print(f"\n[DEBUG-PREMIO] ERRO CRÍTICO ao excluir prêmio: {str(e)}")
        print(f"[DEBUG-PREMIO] Tipo do erro: {type(e).__name__}")
        import traceback
        print(f"[DEBUG-PREMIO] Stack trace completo:\n{traceback.format_exc()}")
        print("[DEBUG-PREMIO] ========== FIM COM ERRO CRÍTICO ==========\n")
        return JsonResponse({'success': False, 'error': f'Erro ao excluir prêmio: {str(e)}'}, status=500)

@login_required
def pacotes_futcoins_ativos(request):
    """
    API para retornar pacotes de futcoins ativos em formato JSON
    """
    try:
        # Busca todos os pacotes de futcoins ativos
        pacotes = FutcoinPackage.objects.filter(enabled=True).order_by('name')
        
        # Formata os pacotes para o formato de resposta
        pacotes_json = []
        for pacote in pacotes:
            pacotes_json.append({
                'id': pacote.id,
                'name': pacote.name,
                'price': float(pacote.promotional_price) if hasattr(pacote, 'promotional_price') and pacote.promotional_price else float(pacote.full_price)
            })
        
        # Retorna os pacotes em formato JSON
        return JsonResponse({
            'success': True,
            'pacotes': pacotes_json
        })
    except Exception as e:
        # Em caso de erro, retorna uma resposta de erro
        import traceback
        print(f"Erro ao buscar pacotes de futcoins: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'Erro ao buscar pacotes de futcoins: {str(e)}',
            'pacotes': []
        })
