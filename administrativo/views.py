from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.urls import reverse
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.db.models import Case, When, Value, IntegerField
from django.core.files.storage import default_storage
from django.views.decorators.http import require_http_methods
from .models import (
    User, Scope, Championship, Template, Team,
    FutcoinPackage, Plan, ClassicLeague, Player,
    Continent, Country, State, Parameters, Terms, 
    Notifications, Administrator, ScopeLevel, TemplateStage,
    ChampionshipStage, ChampionshipRound, ChampionshipMatch,
    Prediction, StandardLeague, StandardLeaguePrize,
    CustomLeague, CustomLeagueLevel, CustomLeaguePrize
)
from .utils import export_to_excel, import_from_excel
import pandas as pd
import csv
import os
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

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

def usuarios(request):
    return render(request, 'administrativo/usuarios.html')

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

    # Obtém todos os campeonatos ordenados por data de criação
    championships = Championship.objects.all().order_by('-created_at')

    context = {
        'championships': championships
    }

    return render(request, 'administrativo/campeonatos.html', context)

@login_required
def campeonato_novo(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Cria o campeonato com os dados básicos
                championship = Championship.objects.create(
                    name=request.POST.get('name'),
                    season=request.POST.get('season'),
                    points=request.POST.get('points', 0),
                    template_id=request.POST.get('template'),
                    scope_id=request.POST.get('scope'),
                    continent_id=request.POST.get('continent'),
                    country_id=request.POST.get('country'),
                    state_id=request.POST.get('state'),
                    is_active=request.POST.get('is_active') == 'on'
                )

                # Adiciona os times selecionados
                teams = request.POST.getlist('teams[]')
                if teams:
                    championship.teams.add(*teams)

                # Processa as rodadas se houver
                matches_data = json.loads(request.POST.get('matches', '[]'))
                if matches_data:
                    # Agrupa partidas por fase e rodada
                    stages = {}
                    for match in matches_data:
                        stage_name = match['stage']
                        round_number = match['round']
                        
                        if stage_name not in stages:
                            stages[stage_name] = {}
                        
                        if round_number not in stages[stage_name]:
                            stages[stage_name][round_number] = []
                            
                        stages[stage_name][round_number].append(match)
                    
                    # Cria as fases, rodadas e partidas
                    for stage_name, rounds in stages.items():
                        stage = ChampionshipStage.objects.create(
                            championship=championship,
                            name=stage_name
                        )
                        
                        for round_number, matches in rounds.items():
                            round_obj = ChampionshipRound.objects.create(
                                championship=championship,
                                stage=stage,
                                number=round_number
                            )
                            
                            for match in matches:
                                match_date = datetime.strptime(match['match_date'], '%d/%m/%Y %H:%M')
                                ChampionshipMatch.objects.create(
                                    championship=championship,
                                    stage=stage,
                                    round=round_obj,
                                    home_team_id=match['home_team'],
                                    away_team_id=match['away_team'],
                                    home_score=match['home_score'],
                                    away_score=match['away_score'],
                                    match_date=match_date
                                )

                return JsonResponse({
                    'success': True,
                    'message': 'Campeonato criado com sucesso!'
                })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao criar campeonato: {str(e)}'
            })

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

            if not is_national_team and not state_id:
                return JsonResponse({
                    'success': False,
                    'message': 'O estado é obrigatório para times que não são seleções'
                })

            # Busca país e estado
            country = Country.objects.get(id=country_id)
            state = None
            if not is_national_team and state_id:
                state = State.objects.get(id=state_id)

            # Verifica se o país tem estados cadastrados e se é necessário um estado
            if not is_national_team and country.state_set.exists() and not state_id:
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
    View para editar um time existente.
    """
    team = get_object_or_404(Team, id=id)
    has_championships = team.has_championships()
    
    if request.method == 'POST':
        try:
            # Se tem campeonatos vinculados, só permite editar a imagem
            if has_championships:
                if 'image' in request.FILES:
                    # Remove imagem antiga se existir
                    if team.image:
                        team.image.delete(save=False)
                    team.image = request.FILES['image']
                elif request.POST.get('remove_image') == 'on':
                    # Remove a imagem se solicitado
                    if team.image:
                        team.image.delete(save=False)
                    team.image = None
                team.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Imagem do time atualizada com sucesso.',
                    'redirect_url': reverse('administrativo:times')
                })
            
            # Se não tem campeonatos, permite editar tudo
            name = request.POST.get('name')
            country_id = request.POST.get('country')
            state_id = request.POST.get('state')
            is_national_team = request.POST.get('is_national_team') == 'on'
            
            # Validações básicas
            if not name or not country_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Nome e país são obrigatórios'
                })
                
            # Busca o país
            country = Country.objects.get(id=country_id)
            
            # Verifica se já existe outro time com o mesmo nome no país
            if Team.objects.filter(name=name, country_id=country_id).exclude(id=id).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Já existe um time com este nome neste país'
                })
                
            # Atualiza os dados do time
            team.name = name
            team.country = country
            team.is_national_team = is_national_team
            
            # Atualiza a imagem se fornecida
            if 'image' in request.FILES:
                if team.image:
                    team.image.delete(save=False)
                team.image = request.FILES['image']
            elif request.POST.get('remove_image') == 'on':
                if team.image:
                    team.image.delete(save=False)
                team.image = None
            
            # Se não for seleção nacional, verifica o estado
            if not is_national_team:
                # Se o país tem estados cadastrados, o estado é obrigatório
                if country.state_set.exists():
                    if not state_id:
                        return JsonResponse({
                            'success': False,
                            'message': 'Estado é obrigatório para times deste país'
                        })
                    team.state = State.objects.get(id=state_id)
                else:
                    # Se o país não tem estados, remove qualquer estado que possa estar associado
                    team.state = None
            else:
                # Se for seleção nacional, remove o estado
                team.state = None
            
            team.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Time atualizado com sucesso.',
                'redirect_url': reverse('administrativo:times')
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao atualizar time: {str(e)}'
            })
    
    # GET: Carrega o formulário
    countries = Country.objects.all().order_by('name')
    states = State.objects.filter(country=team.country).order_by('name') if team.country else []
    championships = Championship.objects.filter(teams=team).order_by('name')
    
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
            files = request.FILES.getlist('images')
            if not files:
                return JsonResponse({
                    'success': False,
                    'message': 'Nenhuma imagem selecionada'
                })
            
            # Primeiro, verifica se todos os times existem
            times_not_found = []
            for file in files:
                filename = os.path.splitext(file.name)[0]
                if not Team.objects.filter(name__iexact=filename).exists():
                    times_not_found.append(filename)
            
            if times_not_found:
                if len(times_not_found) > 4:
                    message = f'{len(times_not_found)} times não estão cadastrados. Por favor, cadastre-os primeiro.'
                else:
                    message = f'Os seguintes times não foram encontrados: {", ".join(times_not_found)}. Por favor, cadastre-os primeiro.'
                return JsonResponse({
                    'success': False,
                    'message': message
                })
            
            success_count = 0
            errors = []
            
            for file in files:
                # Remove a extensão do nome do arquivo
                filename = os.path.splitext(file.name)[0]
                
                # Procura o time pelo nome do arquivo
                team = Team.objects.filter(name__iexact=filename).first()
                
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
        'message': 'Método não permitido'
    })

def futcoins(request):
    packages = FutcoinPackage.objects.all().order_by('-created_at')
    return render(request, 'administrativo/futcoins.html', {'packages': packages})

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
                    start_date = datetime.strptime(start_date, '%d/%m/%Y %H:%M')
                if end_date:
                    end_date = datetime.strptime(end_date, '%d/%m/%Y %H:%M')
            except ValueError as e:
                return JsonResponse({
                    'success': False,
                    'message': 'Formato de data inválido. Use o formato DD/MM/YYYY HH:mm'
                })
            
            # Criação do pacote
            package = FutcoinPackage(
                name=data.get('name'),
                enabled=data.get('enabled', 'true') == 'true',
                package_type=data.get('package_type'),
                label=data.get('label'),
                color_text_label=data.get('color_text_label', '#000000'),
                color_background_label=data.get('color_background_label', '#FFFFFF'),
                full_price=data.get('full_price'),
                promotional_price=data.get('promotional_price') if data.get('promotional_price') else None,
                content=data.get('content'),
                bonus=data.get('bonus', 0),
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

def pacote_plano_novo(request):
    if request.method == 'POST':
        try:
            data = request.POST
            files = request.FILES
            
            # Validação dos campos obrigatórios
            required_fields = ['name', 'full_price', 'promotional_price']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({
                        'success': False,
                        'message': f'O campo {field} é obrigatório.'
                    })
            
            # Criação do plano
            plan = Plan(
                name=data.get('name'),
                plan=data.get('plan'),
                billing_cycle=data.get('billing_cycle'),
                enabled=data.get('enabled', 'true') == 'true',
                package_type=data.get('package_type'),
                label=data.get('label'),
                color_text_label=data.get('color_text_label', '#000000'),
                color_background_label=data.get('color_background_label', '#FFFFFF'),
                full_price=data.get('full_price'),
                promotional_price=data.get('promotional_price'),
                promotional_price_validity=data.get('promotional_price_validity'),
                android_product_code=data.get('android_product_code'),
                apple_product_code=data.get('apple_product_code'),
                color_text_billing_cycle=data.get('color_text_billing_cycle', '#192639'),
                show_to=data.get('show_to'),
                start_date=data.get('start_date') if data.get('start_date') else None,
                end_date=data.get('end_date') if data.get('end_date') else None
            )
            
            # Tratamento da imagem
            if 'image' in files:
                plan.image = files['image']
            
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

@login_required
def futliga_classica_novo(request):
    """
    Cria uma nova futliga clássica.
    """
    if request.method == 'POST':
        try:
            # Dados básicos
            name = request.POST.get('name')
            players = request.POST.get('players')
            award_frequency = request.POST.get('award_frequency')
            
            # Validações
            if not name:
                return JsonResponse({'success': False, 'message': 'O nome é obrigatório'})
            
            if not award_frequency:
                return JsonResponse({'success': False, 'message': 'A frequência de premiação é obrigatória'})
            
            # Cria a Futliga
            futliga = StandardLeague(
                name=name,
                players=players,
                award_frequency=award_frequency
            )
            
            # Imagem principal
            if request.FILES.get('image'):
                futliga.image = request.FILES['image']
            
            # Dia/horário de premiação
            if award_frequency == 'Semanal':
                weekday = request.POST.get('weekday')
                if not weekday:
                    return JsonResponse({'success': False, 'message': 'O dia da semana é obrigatório para premiação semanal'})
                futliga.weekday = weekday
            elif award_frequency == 'Mensal':
                monthday = request.POST.get('monthday')
                if not monthday:
                    return JsonResponse({'success': False, 'message': 'O dia do mês é obrigatório para premiação mensal'})
                futliga.monthday = monthday
            
            award_time = request.POST.get('award_time')
            if award_time:
                futliga.award_time = award_time
            
            futliga.save()
            
            # Processa os prêmios
            positions = request.POST.getlist('prize_positions[]')
            descriptions = request.POST.getlist('prize_descriptions[]')
            images = request.FILES.getlist('prize_images[]')
            
            for i in range(len(positions)):
                prize = StandardLeaguePrize(
                    league=futliga,
                    position=positions[i],
                    prize=descriptions[i]
                )
                if i < len(images):
                    prize.image = images[i]
                prize.save()
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return render(request, 'administrativo/futliga-classica-novo.html')

@login_required
def futliga_classica_editar(request, id):
    """
    View para editar uma Futliga Clássica existente
    """
    try:
        futliga = StandardLeague.objects.get(id=id)
    except StandardLeague.DoesNotExist:
        messages.error(request, 'Futliga Clássica não encontrada')
        return redirect('administrativo:futligas_classicas')
    
    if request.method == 'POST':
        try:
            # Dados básicos
            name = request.POST.get('name')
            players = request.POST.get('players')
            award_frequency = request.POST.get('award_frequency')
            
            # Validações
            if not name:
                return JsonResponse({'success': False, 'message': 'O nome é obrigatório'})
            
            if not award_frequency:
                return JsonResponse({'success': False, 'message': 'A frequência de premiação é obrigatória'})
            
            # Atualiza a Futliga
            futliga.name = name
            futliga.players = players
            futliga.award_frequency = award_frequency
            
            # Imagem principal
            if request.FILES.get('image'):
                if futliga.image:
                    futliga.image.delete()
                futliga.image = request.FILES['image']
            
            # Dia/horário de premiação
            if award_frequency == 'weekly':
                weekday = request.POST.get('weekday')
                if not weekday:
                    return JsonResponse({'success': False, 'message': 'O dia da semana é obrigatório para premiação semanal'})
                try:
                    weekday = int(weekday)
                    if weekday < 0 or weekday > 6:
                        return JsonResponse({'success': False, 'message': 'Dia da semana inválido'})
                    futliga.weekday = weekday
                except ValueError:
                    return JsonResponse({'success': False, 'message': 'Dia da semana inválido'})
            elif award_frequency == 'monthly':
                monthday = request.POST.get('monthday')
                if not monthday:
                    return JsonResponse({'success': False, 'message': 'O dia do mês é obrigatório para premiação mensal'})
                try:
                    monthday = int(monthday)
                    if monthday < 1 or monthday > 31:
                        return JsonResponse({'success': False, 'message': 'Dia do mês inválido'})
                    futliga.monthday = monthday
                except ValueError:
                    return JsonResponse({'success': False, 'message': 'Dia do mês inválido'})
            
            award_time = request.POST.get('award_time')
            if award_time:
                futliga.award_time = award_time
            
            futliga.save()
            
            # Remove prêmios existentes
            futliga.prizes.all().delete()
            
            # Processa os novos prêmios
            positions = request.POST.getlist('prize_positions[]')
            descriptions = request.POST.getlist('prize_descriptions[]')
            images = request.FILES.getlist('prize_images[]')
            
            for i in range(len(positions)):
                try:
                    position = int(positions[i])
                    if position < 1:
                        return JsonResponse({'success': False, 'message': f'Posição {position} inválida'})
                        
                    prize = StandardLeaguePrize(
                        league=futliga,
                        position=position,
                        prize=descriptions[i]
                    )
                    if i < len(images):
                        prize.image = images[i]
                    prize.save()
                except ValueError:
                    return JsonResponse({'success': False, 'message': f'Posição {positions[i]} inválida'})
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return render(request, 'administrativo/futliga-classica-editar.html', {
        'futliga': futliga
    })

@login_required
def futliga_classica_excluir(request, id):
    """
    View para excluir uma Futliga Clássica
    """
    if request.method == 'POST':
        try:
            futliga = StandardLeague.objects.get(id=id)
            
            # Remove a imagem principal
            if futliga.image:
                futliga.image.delete()
            
            # Remove as imagens dos prêmios
            for prize in futliga.prizes.all():
                if prize.image:
                    prize.image.delete()
            
            futliga.delete()
            return JsonResponse({'success': True})
            
        except StandardLeague.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Futliga Clássica não encontrada'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})

@login_required
def futliga_classica_excluir_em_massa(request):
    """
    View para excluir múltiplas Futligas Clássicas
    """
    if request.method == 'POST':
        try:
            ids = request.POST.getlist('ids[]')
            futligas = StandardLeague.objects.filter(id__in=ids)
            
            for futliga in futligas:
                # Remove a imagem principal
                if futliga.image:
                    futliga.image.delete()
                
                # Remove as imagens dos prêmios
                for prize in futliga.prizes.all():
                    if prize.image:
                        prize.image.delete()
            
            futligas.delete()
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})

@login_required
def futligas_jogadores(request):
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

            # Cria o nível
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
                'redirect_url': reverse('administrativo:futligas_jogadores')
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao criar nível: {str(e)}'
            })

    # GET - renderiza o template com os níveis existentes
    levels = CustomLeagueLevel.objects.all().order_by('order')
    return render(request, 'administrativo/futligas_jogadores.html', {
        'levels': levels
    })

@login_required
def futligas_niveis(request):
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
            response_data = {
                'success': True,
                'status': notification.status,
                'send_at': notification.send_at.strftime('%d/%m/%Y %H:%M') if notification.send_at else None,
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

            if notification_type != 'generic' and package_id:
                try:
                    package = FutcoinPackage.objects.get(id=package_id)
                    notification.package = package
                except FutcoinPackage.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'Pacote não encontrado'
                    })

            if send_at:
                try:
                    notification.send_at = datetime.strptime(send_at, '%d/%m/%Y %H:%M')
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
            title = request.POST.get('title')
            message = request.POST.get('message')
            notification_type = request.POST.get('notification_type')
            package_id = request.POST.get('package')
            send_at = request.POST.get('send_at')

            if not all([title, message, notification_type]):
                messages.error(request, 'Campos obrigatórios não preenchidos')
                return redirect('administrativo:notificacao_editar', id=id)

            notification.title = title
            notification.message = message
            notification.notification_type = notification_type

            if notification_type != 'generic' and package_id:
                try:
                    package = FutcoinPackage.objects.get(id=package_id)
                    notification.package = package
                except FutcoinPackage.DoesNotExist:
                    messages.error(request, 'Pacote não encontrado')
                    return redirect('administrativo:notificacao_editar', id=id)
            else:
                notification.package = None

            if send_at:
                try:
                    notification.send_at = datetime.strptime(send_at, '%Y-%m-%d %H:%M')
                    notification.status = 'pending'
                except ValueError:
                    messages.error(request, 'Data de envio inválida')
                    return redirect('administrativo:notificacao_editar', id=id)
            else:
                notification.send_at = None
                try:
                    # Aqui você implementaria a lógica de envio da notificação
                    # Por exemplo: notification.send()
                    notification.status = 'sent'
                except Exception as e:
                    notification.status = 'not_sent'
                    notification.error_message = str(e)

            notification.save()
            messages.success(request, 'Notificação atualizada com sucesso')
            return redirect('administrativo:notificacoes')

        packages = FutcoinPackage.objects.filter(enabled=True)
        return render(request, 'administrativo/notificacao-editar.html', {
            'notification': notification,
            'packages': packages
        })

    except Notifications.DoesNotExist:
        messages.error(request, 'Notificação não encontrada')
        return redirect('administrativo:notificacoes')
    except Exception as e:
        messages.error(request, f'Erro ao carregar notificação: {str(e)}')
        return redirect('administrativo:notificacoes')

def relatorios(request):
    return render(request, 'administrativo/relatorios.html')

def administradores(request):
    # Lista todos os administradores exceto o root
    admins = Administrator.objects.filter(is_root=False).order_by('-created_at')
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
    admin = get_object_or_404(Administrator, id=id)
    
    # Não permite editar o usuário root
    if admin.is_root:
        messages.error(request, 'Não é permitido editar o usuário root')
        return redirect('administrativo:administradores')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not all([name, email]):
            messages.error(request, 'Nome e email são obrigatórios')
            return render(request, 'administrativo/administrador-editar.html', {'admin': admin})
        
        # Verifica se o email já existe para outro administrador
        if Administrator.objects.filter(email=email).exclude(id=id).exists():
            messages.error(request, 'Email já cadastrado')
            return render(request, 'administrativo/administrador-editar.html', {'admin': admin})
            
        admin.name = name
        admin.email = email
        if password:  # Só atualiza a senha se foi fornecida
            admin.password = make_password(password)
        admin.save()
        
        messages.success(request, 'Administrador atualizado com sucesso')
        return redirect('administrativo:administradores')
        
    return render(request, 'administrativo/administrador-editar.html', {'admin': admin})

def administrador_excluir(request, id):
    admin = get_object_or_404(Administrator, id=id)
    
    # Não permite excluir o usuário root
    if admin.is_root:
        return JsonResponse({
            'success': False,
            'message': 'Não é permitido excluir o usuário root'
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
            # Garante que não exclui o usuário root
            deleted_count = Administrator.objects.filter(id__in=ids, is_root=False).delete()[0]
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
    # Limpa a sessão
    request.session.flush()
    # Faz o logout do Django
    auth_logout(request)
    return redirect('administrativo:login')

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
                match_date = datetime.combine(
                    row['Data'],
                    datetime.strptime(str(row['Hora']), '%H:%M').time()
                )
                
                # Verifica se o jogo já existe
                existing_match = ChampionshipMatch.objects.filter(
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
                ChampionshipMatch.objects.create(
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
def campeonato_editar(request, id):
    try:
        championship = Championship.objects.get(id=id)
        has_rounds = championship.rounds.exists()
        
        if request.method == 'POST':
            try:
                with transaction.atomic():
                    # Atualiza dados básicos do campeonato
                    championship.name = request.POST.get('name')
                    championship.season = request.POST.get('season')
                    championship.points = request.POST.get('points', 0)
                    championship.template_id = request.POST.get('template')
                    championship.scope_id = request.POST.get('scope')
                    championship.continent_id = request.POST.get('continent')
                    championship.country_id = request.POST.get('country')
                    championship.state_id = request.POST.get('state')
                    championship.is_active = request.POST.get('is_active') == 'on'
                    championship.save()
                    
                    # Atualiza os times
                    teams = request.POST.getlist('teams[]')
                    championship.teams.clear()
                    championship.teams.add(*teams)
                    
                    # Processa as rodadas se houver
                    matches_data = json.loads(request.POST.get('matches', '[]'))
                    if matches_data:
                        # Limpa rodadas existentes
                        championship.matches.all().delete()
                        championship.rounds.all().delete()
                        championship.stages.all().delete()
                        
                        # Agrupa partidas por fase e rodada
                        stages = {}
                        for match in matches_data:
                            template_stage_id = match['stage_id']  # ID da fase do template
                            round_number = match['round']
                            
                            if template_stage_id not in stages:
                                stages[template_stage_id] = {}
                            
                            if round_number not in stages[template_stage_id]:
                                stages[template_stage_id][round_number] = []
                                
                            stages[template_stage_id][round_number].append(match)
                        
                        # Cria as fases, rodadas e partidas
                        for template_stage_id, rounds in stages.items():
                            # Busca a fase do template para obter o nome
                            template_stage = championship.template.stages.get(id=template_stage_id)
                            
                            # Cria a fase do campeonato
                            stage = ChampionshipStage.objects.create(
                                championship=championship,
                                name=template_stage.name,
                                template_stage_id=template_stage_id,  # Adiciona o ID da fase do template
                                order=template_stage.order  # Adiciona a ordem da fase do template
                            )
                            
                            for round_number, matches in rounds.items():
                                round_obj = ChampionshipRound.objects.create(
                                    championship=championship,
                                    stage=stage,
                                    number=round_number
                                )
                                
                                for match in matches:
                                    match_date = datetime.strptime(match['match_date'], '%d/%m/%Y %H:%M')
                                    ChampionshipMatch.objects.create(
                                        championship=championship,
                                        round=round_obj,
                                        home_team_id=match['home_team'],
                                        away_team_id=match['away_team'],
                                        home_score=match['home_score'] if match['home_score'] != '' else None,
                                        away_score=match['away_score'] if match['away_score'] != '' else None,
                                        match_date=match_date
                                    )
                    
                    messages.success(request, 'Campeonato atualizado com sucesso')
                    return JsonResponse({
                        'success': True,
                        'message': 'Campeonato atualizado com sucesso',
                        'redirect_url': reverse('administrativo:campeonatos')
                    })
                    
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Erro ao atualizar campeonato: {str(e)}'
                })
        
        # Obtém dados para o formulário
        templates = Template.objects.filter(enabled=True)
        scopes = Scope.objects.filter(is_active=True)
        continents = Continent.objects.all().order_by('name')
        countries = Country.objects.all().order_by('name')
        states = State.objects.all().order_by('name')
        teams = Team.objects.all().order_by('name')
        selected_teams = championship.teams.all()
        
        context = {
            'championship': championship,
            'templates': templates,
            'scopes': scopes,
            'continents': continents,
            'countries': countries,
            'states': states,
            'teams': teams,
            'selected_teams': selected_teams,
            'has_rounds': has_rounds
        }
        
        return render(request, 'administrativo/campeonato-editar.html', context)
        
    except Championship.DoesNotExist:
        messages.error(request, 'Campeonato não encontrado')
        return redirect('administrativo:campeonatos')

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
            championship_id = request.POST.get('championship_id')
            championship = Championship.objects.get(id=championship_id)
            
            with transaction.atomic():
                championship.is_active = not championship.is_active
                championship.save()
                transaction.commit()
            
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
                    match = ChampionshipMatch.objects.get(id=match_id)
                    
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
                        
                except ChampionshipMatch.DoesNotExist:
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
                plan.label = data.get('label')
                plan.color_text_label = data.get('color_text_label')
                plan.color_background_label = data.get('color_background_label')
                plan.full_price = data.get('full_price')
                plan.promotional_price = data.get('promotional_price')
                plan.color_text_billing_cycle = data.get('color_text_billing_cycle')
                plan.show_to = data.get('show_to')
                plan.promotional_price_validity = data.get('promotional_price_validity')
                
                # Tratamento das datas
                start_date = data.get('start_date')
                end_date = data.get('end_date')
                
                try:
                    if start_date:
                        plan.start_date = datetime.strptime(start_date, '%d/%m/%Y %H:%M')
                    else:
                        plan.start_date = None
                        
                    if end_date:
                        plan.end_date = datetime.strptime(end_date, '%d/%m/%Y %H:%M')
                    else:
                        plan.end_date = None
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'message': 'Data inválida. Use o formato DD/MM/YYYY HH:mm'
                    })
                
                # Tratamento da imagem
                if 'image' in files:
                    if plan.image:
                        plan.image.delete()
                    plan.image = files['image']
                
                plan.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Plano atualizado com sucesso!'
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Erro ao atualizar plano: {str(e)}'
                })
        
        # Se não for POST, renderiza o template com os dados do plano
        plan_data = {
            'id': plan.id,
            'name': plan.name,
            'plan': plan.plan,
            'billing_cycle': plan.billing_cycle,
            'enabled': plan.enabled,
            'package_type': plan.package_type,
            'label': plan.label,
            'color_text_label': plan.color_text_label,
            'color_background_label': plan.color_background_label,
            'full_price': str(plan.full_price),
            'promotional_price': str(plan.promotional_price) if plan.promotional_price else None,
            'color_text_billing_cycle': plan.color_text_billing_cycle,
            'show_to': plan.show_to,
            'promotional_price_validity': plan.promotional_price_validity,
            'start_date': plan.start_date.strftime('%d/%m/%Y %H:%M') if plan.start_date else None,
            'end_date': plan.end_date.strftime('%d/%m/%Y %H:%M') if plan.end_date else None,
            'image': plan.image.url if plan.image else None
        }
        
        return render(request, 'administrativo/pacote-plano-editar.html', {
            'plan': plan,
            'plan_data': json.dumps(plan_data)
        })
        
    except Plan.DoesNotExist:
        messages.error(request, 'Plano não encontrado')
        return redirect('administrativo:planos')
    except Exception as e:
        messages.error(request, f'Erro ao carregar plano: {str(e)}')
        return redirect('administrativo:planos')

@login_required
def futliga_nivel_editar(request, id):
    try:
        level = CustomLeagueLevel.objects.get(id=id)
        
        if request.method == 'POST':
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
        return JsonResponse({
            'success': False,
            'message': 'Nível não encontrado'
        })
    except Exception as e:
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
def notificacao_excluir(request, id):
    """
    Exclui uma notificação específica.
    """
    try:
        notification = Notifications.objects.get(id=id)
        notification.delete()
        return JsonResponse({'success': True, 'message': 'Notificação excluída com sucesso!'})
    except Notifications.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Notificação não encontrada.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

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

@login_required
def notificacao_editar(request, id):
    try:
        notification = Notifications.objects.get(id=id)
        
        if request.method == 'POST':
            title = request.POST.get('title')
            message = request.POST.get('message')
            notification_type = request.POST.get('notification_type')
            package_id = request.POST.get('package')
            send_at = request.POST.get('send_at')

            if not all([title, message, notification_type]):
                messages.error(request, 'Campos obrigatórios não preenchidos')
                return redirect('administrativo:notificacao_editar', id=id)

            notification.title = title
            notification.message = message
            notification.notification_type = notification_type

            if notification_type != 'generic' and package_id:
                try:
                    package = FutcoinPackage.objects.get(id=package_id)
                    notification.package = package
                except FutcoinPackage.DoesNotExist:
                    messages.error(request, 'Pacote não encontrado')
                    return redirect('administrativo:notificacao_editar', id=id)
            else:
                notification.package = None

            if send_at:
                try:
                    notification.send_at = datetime.strptime(send_at, '%Y-%m-%d %H:%M')
                    notification.status = 'pending'
                except ValueError:
                    messages.error(request, 'Data de envio inválida')
                    return redirect('administrativo:notificacao_editar', id=id)
            else:
                notification.send_at = None
                try:
                    # Aqui você implementaria a lógica de envio da notificação
                    # Por exemplo: notification.send()
                    notification.status = 'sent'
                except Exception as e:
                    notification.status = 'not_sent'
                    notification.error_message = str(e)

            notification.save()
            messages.success(request, 'Notificação atualizada com sucesso')
            return redirect('administrativo:notificacoes')

        packages = FutcoinPackage.objects.filter(enabled=True)
        return render(request, 'administrativo/notificacao-editar.html', {
            'notification': notification,
            'packages': packages
        })

    except Notifications.DoesNotExist:
        messages.error(request, 'Notificação não encontrada')
        return redirect('administrativo:notificacoes')
    except Exception as e:
        messages.error(request, f'Erro ao carregar notificação: {str(e)}')
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
                    params.weekly_award_time = datetime.strptime(weekly_time, '%H:%M').time()
                except ValueError:
                    params.weekly_award_time = None

            # Ranking Temporada
            params.season_award_month = request.POST.get('season_month')
            params.season_award_day = request.POST.get('season_day')
            season_time = request.POST.get('season_time')
            if season_time:
                try:
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
                        match_date = datetime.combine(
                            row['Data'],
                            datetime.strptime(str(row['Hora']), '%H:%M').time()
                        )
                        
                        ChampionshipMatch.objects.create(
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
        if len(teams_with_championships) == 0:
            message = 'Times excluídos com sucesso!'
        else:
            deleted_count = len(teams_to_delete)

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

def plano_excluir(request, id):
    """
    Exclui um plano específico.
    """
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'message': 'Requisição inválida'})
        
    try:
        plan = get_object_or_404(Plan, id=id)
        plan.delete()
        return JsonResponse({
            'success': True,
            'message': 'Plano excluído com sucesso!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao excluir plano: {str(e)}'
        })

def plano_excluir_em_massa(request):
    """
    Exclui múltiplos planos.
    """
    try:
        ids = request.POST.getlist('ids[]')
        Plan.objects.filter(id__in=ids).delete()
        return JsonResponse({
            'success': True,
            'message': 'Planos excluídos com sucesso!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao excluir planos: {str(e)}'
        })

def plano_toggle_status(request):
    """
    Alterna o status de ativação de um plano.
    """
    if request.method == 'POST':
        plan_id = request.POST.get('id')
        try:
            plan = get_object_or_404(Plan, id=plan_id)
            plan.enabled = not plan.enabled
            plan.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Status alterado com sucesso!',
                'enabled': plan.enabled
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
        return JsonResponse({
            'success': False,
            'message': f'Erro ao alterar status do pacote: {str(e)}'
        })

@login_required
def futcoin_editar(request, id):
    """
    Edita um pacote de futcoins existente
    """
    package = get_object_or_404(FutcoinPackage, id=id)
    
    if request.method == 'POST':
        try:
            # Atualiza os dados básicos
            package.name = request.POST.get('name')
            package.package_type = request.POST.get('package_type')
            package.enabled = request.POST.get('enabled') == 'true'
            package.full_price = request.POST.get('full_price')
            package.promotional_price = request.POST.get('promotional_price')
            package.label = request.POST.get('label')
            package.color_text_label = request.POST.get('color_text_label')
            package.color_background_label = request.POST.get('color_background_label')
            package.show_to = request.POST.get('show_to')

            # Processa datas se fornecidas
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')

            if start_date:
                try:
                    package.start_date = datetime.strptime(start_date, '%d/%m/%Y %H:%M')
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'message': 'Formato de data de início inválido. Use DD/MM/YYYY HH:mm'
                    })

            if end_date:
                try:
                    package.end_date = datetime.strptime(end_date, '%d/%m/%Y %H:%M')
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'message': 'Formato de data de término inválido. Use DD/MM/YYYY HH:mm'
                    })

            # Processa a imagem se fornecida
            if 'image' in request.FILES:
                image = request.FILES['image']
                if image.size > 2 * 1024 * 1024:  # 2MB
                    return JsonResponse({
                        'success': False,
                        'message': 'A imagem não pode ter mais que 2MB'
                    })
                package.image = image

            package.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Pacote atualizado com sucesso'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao atualizar pacote: {str(e)}'
            })
    
    # GET request - renderiza o template com os dados do pacote
    context = {
        'package': package,
        'package_data': {
            'id': package.id,
            'name': package.name,
            'package_type': package.package_type,
            'enabled': package.enabled,
            'full_price': package.full_price,
            'promotional_price': package.promotional_price,
            'label': package.label,
            'color_text_label': package.color_text_label,
            'color_background_label': package.color_background_label,
            'show_to': package.show_to,
            'start_date': package.start_date.strftime('%d/%m/%Y %H:%M') if package.start_date else '',
            'end_date': package.end_date.strftime('%d/%m/%Y %H:%M') if package.end_date else '',
            'image': package.image.url if package.image else None
        }
    }
    
    return render(request, 'administrativo/pacote-futcoin-editar.html', context)

@login_required
def futliga_nivel_novo(request):
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
def jogador_importar(request):
    if request.method == 'POST':
        try:
            file = request.FILES.get('file')
            if not file:
                return JsonResponse({'success': False, 'message': 'Nenhum arquivo foi enviado.'})
            
            # Verifica a extensão do arquivo
            if not file.name.endswith('.xlsx'):
                return JsonResponse({'success': False, 'message': 'O arquivo deve estar no formato .xlsx'})
            
            # TODO: Implementar a lógica de importação dos jogadores
            # Por enquanto retorna sucesso
            return JsonResponse({'success': True, 'message': 'Jogadores importados com sucesso!'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erro ao importar jogadores: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido.'})

@login_required
def importar_rodadas(request):
    if request.method == 'POST' and request.FILES.get('arquivo'):
        try:
            import pandas as pd
            from datetime import datetime
            
            # Lê o arquivo Excel
            df = pd.read_excel(request.FILES['arquivo'])
            
            # Lista para armazenar as rodadas processadas
            rodadas_processadas = []
            
            # Processa cada linha do Excel
            for _, row in df.iterrows():
                rodada = {
                    'fase': str(row['Fase']),
                    'rodada': int(row['Rodada']),
                    'mandante': str(row['Mandante']),
                    'placar_mandante': int(row['Placar M.']) if pd.notna(row['Placar M.']) else None,
                    'placar_visitante': int(row['Placar V.']) if pd.notna(row['Placar V.']) else None,
                    'visitante': str(row['Visitante']),
                    'data': row['Data'],
                    'hora': row['Hora']
                }
                rodadas_processadas.append(rodada)
            
            return JsonResponse({
                'success': True,
                'message': 'Rodadas importadas com sucesso',
                'rodadas': rodadas_processadas
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao processar arquivo: {str(e)}'
            }, status=400)
            
    return JsonResponse({
        'success': False,
        'message': 'Requisição inválida'
    }, status=400)

@login_required
def futliga_importar(request):
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
                FutligaJogadores.objects.create(
                    name=row['Nome'],
                    players=row['Participantes'],
                    premium_players=row['Craques'],
                    owner_premium=row['Dono Craque'].lower() == 'sim'
                )
            
            return JsonResponse({'success': True, 'message': 'Futligas importadas com sucesso!'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erro ao importar: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido.'})