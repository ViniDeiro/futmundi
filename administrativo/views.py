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
from .models import (
    User, Scope, Championship, Template, Team,
    FutcoinPackage, Plan, ClassicLeague, Player,
    Continent, Country, State, Parameter, Term, 
    Notification, Administrator, ScopeLevel, TemplateStage,
    ChampionshipStage, ChampionshipRound, ChampionshipMatch
)
from .utils import export_to_excel, import_from_excel
import pandas as pd
import csv
import os
from datetime import datetime

def login(request):
    # Limpa as mensagens antigas
    storage = messages.get_messages(request)
    storage.used = True
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not all([email, password]):
            messages.error(request, 'Todos os campos são obrigatórios')
            return render(request, 'administrativo/login.html')
            
        administrator = Administrator.objects.filter(email=email).first()
        
        if not administrator or not check_password(password, administrator.password):
            messages.error(request, 'Email ou senha inválidos')
            return render(request, 'administrativo/login.html')
            
        # Salva os dados do admin na sessão com os nomes corretos das variáveis
        request.session['admin_id'] = administrator.id
        request.session['admin_name'] = administrator.name
        request.session['is_root'] = administrator.is_root
        
        return redirect('administrativo:usuarios')
        
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
    
    # Obtém todos os âmbitos ordenados por tipo
    scopes = Scope.objects.all().order_by(
        'type'
    ).extra(
        select={'type_order': """CASE 
            WHEN type = 'estadual' THEN 1
            WHEN type = 'nacional' THEN 2
            WHEN type = 'continental' THEN 3
            WHEN type = 'mundial' THEN 4
            ELSE 5
        END"""},
        order_by=['type_order']
    )
    
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
    Cria os 4 âmbitos padrão se eles não existirem.
    """
    default_scopes = [
        {
            'name': 'Estadual',
            'type': 'estadual',
            'boost': 100,
            'futcoins': 1000,
            'is_default': True
        },
        {
            'name': 'Nacional',
            'type': 'nacional',
            'boost': 200,
            'futcoins': 2000,
            'is_default': True
        },
        {
            'name': 'Continental',
            'type': 'continental',
            'boost': 300,
            'futcoins': 3000,
            'is_default': True
        },
        {
            'name': 'Mundial',
            'type': 'mundial',
            'boost': 400,
            'futcoins': 4000,
            'is_default': True
        }
    ]
    
    for scope_data in default_scopes:
        scope, created = Scope.objects.get_or_create(
            type=scope_data['type'],
            defaults=scope_data
        )
        
        if created:
            # Cria níveis de alavancagem
            for level in range(1, 4):
                ScopeLevel.objects.create(
                    scope=scope,
                    type='leverage',
                    level=level,
                    points=level * 100,
                    futcoins=level * 1000
                )
            
            # Cria níveis de seguro
            for level in range(1, 4):
                ScopeLevel.objects.create(
                    scope=scope,
                    type='insurance',
                    level=level,
                    points=level * 50,
                    futcoins=level * 500
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

def campeonato_novo(request):
    """
    View para criar um novo campeonato em 3 etapas:
    1. Informações gerais
    2. Seleção de times
    3. Configuração de rodadas
    """
    # Limpa mensagens antigas
    storage = messages.get_messages(request)
    storage.used = True
    
    if request.method == 'POST':
        step = request.POST.get('step')
        
        if step == '1':
            # Etapa 1: Informações gerais
            try:
                # Valida se já existe campeonato com mesmo nome e temporada
                name = request.POST.get('name')
                season = request.POST.get('season')
                if Championship.objects.filter(name=name, season=season).exists():
                    return JsonResponse({
                        'success': False,
                        'message': 'Já existe um campeonato com este nome e temporada.'
                    })
                
                # Cria o campeonato
                championship = Championship.objects.create(
                    name=name,
                    season=season,
                    template_id=request.POST.get('template'),
                    scope_id=request.POST.get('scope'),
                    continent_id=request.POST.get('continent'),
                    country_id=request.POST.get('country'),
                    state_id=request.POST.get('state'),
                    points=request.POST.get('points', 0),
                    is_active=request.POST.get('enabled') == 'on'
                )
                
                request.session['championship_id'] = championship.id
                
                return JsonResponse({
                    'success': True,
                    'next_step': True,
                    'message': 'Informações gerais salvas com sucesso.'
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Erro ao salvar informações gerais: {str(e)}'
                })
                
        elif step == '2':
            # Etapa 2: Seleção de times
            try:
                championship_id = request.session.get('championship_id')
                if not championship_id:
                    return JsonResponse({
                        'success': False,
                        'message': 'Campeonato não encontrado. Inicie o processo novamente.'
                    })
                
                championship = Championship.objects.get(id=championship_id)
                
                if not championship.can_edit_teams():
                    return JsonResponse({
                        'success': False,
                        'message': 'Este campeonato não pode ter seus times editados.'
                    })
                
                # Adiciona os times selecionados
                team_ids = request.POST.getlist('teams')
                championship.teams.clear()
                championship.teams.add(*team_ids)
                
                return JsonResponse({
                    'success': True,
                    'next_step': True,
                    'message': 'Times adicionados com sucesso.'
                })
                
            except Championship.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Campeonato não encontrado.'
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Erro ao adicionar times: {str(e)}'
                })
                
        elif step == '3':
            # Etapa 3: Configuração de rodadas
            try:
                championship_id = request.session.get('championship_id')
                if not championship_id:
                    return JsonResponse({
                        'success': False,
                        'message': 'Campeonato não encontrado. Inicie o processo novamente.'
                    })
                
                championship = Championship.objects.get(id=championship_id)
                
                if not championship.can_edit_rounds():
                    return JsonResponse({
                        'success': False,
                        'message': 'Este campeonato não pode ter suas rodadas editadas.'
                    })
                
                # Processa os jogos
                matches_data = []
                for key, value in request.POST.items():
                    if key.startswith('matches['):
                        match_index = key.split('[')[1].split(']')[0]
                        field = key.split('][')[1].rstrip(']')
                        
                        while len(matches_data) <= int(match_index):
                            matches_data.append({})
                            
                        matches_data[int(match_index)][field] = value
                
                # Cria os jogos
                stage = ChampionshipStage.objects.get(id=request.POST.get('stage'))
                round_obj = ChampionshipRound.objects.get(id=request.POST.get('round'))
                
                for match_data in matches_data:
                    if all(k in match_data for k in ['team_home', 'team_away', 'match_date']):
                        ChampionshipMatch.objects.create(
                            championship=championship,
                            stage=stage,
                            round=round_obj,
                            team_home_id=match_data['team_home'],
                            team_away_id=match_data['team_away'],
                            score_home=match_data.get('score_home'),
                            score_away=match_data.get('score_away'),
                            match_date=datetime.strptime(match_data['match_date'], '%d/%m/%Y %H:%M')
                        )
                
                # Limpa o ID do campeonato da sessão
                del request.session['championship_id']
                
                return JsonResponse({
                    'success': True,
                    'next_step': False,
                    'message': 'Campeonato criado com sucesso!'
                })
                
            except Championship.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Campeonato não encontrado.'
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Erro ao configurar rodadas: {str(e)}'
                })
    
    # GET: Exibe o formulário inicial
    return render(request, 'administrativo/campeonato-novo.html', {
        'templates': Template.objects.filter(enabled=True).order_by('name'),
        'scopes': Scope.objects.filter(is_active=True).order_by('name'),
        'continents': Continent.objects.all().order_by('name'),
        'countries': Country.objects.all().order_by('name'),
        'states': State.objects.all().order_by('name'),
        'teams': Team.objects.all().order_by('name')
    })

def campeonato_excluir(request, id):
    """
    Exclui um campeonato específico.
    Só exclui se o campeonato estiver inativo.
    """
    if request.method == 'POST':
        try:
            championship = Championship.objects.get(id=id)
            
            if not championship.is_active:
                championship.delete()
                return JsonResponse({
                    'success': True,
                    'message': 'Campeonato excluído com sucesso!'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Este campeonato não pode ser excluído pois está ativo'
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
    Exclui múltiplos campeonatos selecionados.
    Só exclui campeonatos inativos e sem palpites.
    """
    if request.method == 'POST':
        championship_ids = request.POST.getlist('ids[]')
        
        if not championship_ids:
            return JsonResponse({
                'success': False,
                'message': 'Nenhum campeonato selecionado'
            })
            
        deleted_count = 0
        errors = []
        
        for championship_id in championship_ids:
            try:
                championship = Championship.objects.get(id=championship_id)
                if championship.can_delete():
                    championship.delete()
                    deleted_count += 1
                else:
                    errors.append(f'Campeonato "{championship.name}" não pode ser excluído pois está ativo ou tem palpites vinculados')
            except Championship.DoesNotExist:
                errors.append(f'Campeonato {championship_id} não encontrado')
        
        if deleted_count > 0:
            message = f'{deleted_count} campeonato(s) excluído(s) com sucesso!'
            if errors:
                message += f' Erros: {", ".join(errors)}'
            return JsonResponse({
                'success': True,
                'message': message
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Nenhum campeonato pôde ser excluído. ' + ', '.join(errors)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    }, status=405)

def campeonato_resultados(request, id):
    """
    Exibe os resultados de um campeonato específico.
    Mostra as rodadas, jogos e placares.
    """
    try:
        championship = Championship.objects.get(id=id)
        stages = championship.stages.all().order_by('order')
        rounds = []
        
        for stage in stages:
            stage_rounds = stage.rounds.all().order_by('number')
            for round in stage_rounds:
                matches = round.matches.all().order_by('match_date')
                rounds.append({
                    'stage': stage,
                    'round': round,
                    'matches': matches
                })
        
        context = {
            'championship': championship,
            'rounds': rounds
        }
        
        return render(request, 'administrativo/campeonato-resultados.html', context)
        
    except Championship.DoesNotExist:
        messages.error(request, 'Campeonato não encontrado')
        return redirect('administrativo:campeonatos')

def templates(request):
    """
    Lista todos os templates disponíveis.
    """
    templates = Template.objects.all()
    return render(request, 'administrativo/templates.html', {
        'templates': templates
    })

def template_novo(request):
    """
    Cria um novo template.
    """
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Cria o template
                template = Template.objects.create(
                    name=request.POST.get('name'),
                    enabled=True,
                    number_of_stages=int(request.POST.get('number_of_stages', 1))
                )
                
                # Cria as fases
                stages_data = []
                for i in range(template.number_of_stages):
                    stage_name = request.POST.get(f'stage_name_{i}')
                    rounds = int(request.POST.get(f'stage_rounds_{i}', 0))
                    matches_per_round = int(request.POST.get(f'stage_matches_per_round_{i}', 0))
                    
                    if stage_name and rounds > 0 and matches_per_round > 0:
                        stages_data.append({
                            'template': template,
                            'name': stage_name,
                            'rounds': rounds,
                            'matches_per_round': matches_per_round,
                            'order': i
                        })
                
                # Cria todas as fases de uma vez
                TemplateStage.objects.bulk_create([
                    TemplateStage(**data) for data in stages_data
                ])
                
                messages.success(request, 'Template criado com sucesso!')
                return redirect('administrativo:templates')
                
        except Exception as e:
            messages.error(request, f'Erro ao criar template: {str(e)}')
    return render(request, 'administrativo/template-novo.html')
            
    return render(request, 'administrativo/template-novo.html')

def template_editar(request, id):
    """
    Edita um template existente.
    """
    template = get_object_or_404(Template, id=id)
    
    if request.method == 'POST':
        try:
            # Verifica se o nome foi alterado e se já existe
            new_name = request.POST.get('name')
            if new_name != template.name and Template.objects.filter(name=new_name).exists():
                messages.error(request, 'Já existe um template com este nome')
                return redirect('administrativo:template_editar', id=id)

            # Verifica se o template está em uso
            template_in_use = template.championships.exists()
            
            with transaction.atomic():
                # Atualiza dados básicos do template
                template.name = new_name
                template.enabled = request.POST.get('enabled') == 'on'
                template.save()
                
                # Atualiza as fases existentes e cria novas se necessário
                existing_stages = {stage.order: stage for stage in template.stages.all()}
                new_stages_data = []
                stages_to_delete = set(existing_stages.keys())
                
                for i in range(int(request.POST.get('number_of_stages', 1))):
                    stage_name = request.POST.get(f'stage_name_{i}')
                    rounds = int(request.POST.get(f'stage_rounds_{i}', 0))
                    matches_per_round = int(request.POST.get(f'stage_matches_per_round_{i}', 0))
                    
                    if not stage_name or rounds <= 0 or matches_per_round <= 0:
                        messages.error(request, f'Dados inválidos para a fase {i+1}')
                        return redirect('administrativo:template_editar', id=id)
                    
                    if i in existing_stages:
                        stage = existing_stages[i]
                        
                        # Se o template está em uso, verifica alterações críticas
                        if template_in_use:
                            if stage.rounds != rounds or stage.matches_per_round != matches_per_round:
                                messages.error(request, 'Não é possível alterar o número de rodadas ou jogos por rodada em templates em uso')
                                return redirect('administrativo:template_editar', id=id)
                        
                        # Atualiza fase existente
                        stage.name = stage_name
                        stage.rounds = rounds
                        stage.matches_per_round = matches_per_round
                        stage.save()
                        stages_to_delete.remove(i)
                    else:
                        # Cria nova fase
                        new_stages_data.append(TemplateStage(
                            template=template,
                            name=stage_name,
                            rounds=rounds,
                            matches_per_round=matches_per_round,
                            order=i
                        ))
                
                # Remove fases que não existem mais
                if not template_in_use and stages_to_delete:
                    TemplateStage.objects.filter(
                        template=template,
                        order__in=stages_to_delete
                    ).delete()
                
                # Cria novas fases
                if new_stages_data:
                    TemplateStage.objects.bulk_create(new_stages_data)
                
                # Atualiza número de fases
                template.number_of_stages = template.stages.count()
                template.save()
                
                messages.success(request, 'Template atualizado com sucesso!')
                return redirect('administrativo:templates')
                
        except ValueError as e:
            messages.error(request, f'Dados inválidos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar template: {str(e)}')
            
    return render(request, 'administrativo/template-editar.html', {'template': template})

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
        # Verifica se já existe um template com o nome "Cópia de {nome}"
        new_name = f"Cópia de {template.name}"
        if Template.objects.filter(name=new_name).exists():
            messages.error(request, f'Já existe um template com o nome "{new_name}"')
            return redirect('administrativo:templates')
            
        new_template = template.duplicate()
        messages.success(request, 'Template duplicado com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao duplicar template: {str(e)}')
        
    return redirect('administrativo:templates')

def template_importar(request):
    """
    Importa templates de um arquivo Excel.
    """
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            df = pd.read_excel(request.FILES['file'])
            
            required_columns = ['nome', 'fase', 'rodadas', 'jogos_por_rodada']
            if not all(col in df.columns for col in required_columns):
                messages.error(request, 'Arquivo não contém todas as colunas necessárias: ' + ', '.join(required_columns))
                return redirect('administrativo:templates')
                
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
                            templates_created -= 1
                            errors.append(f'Template {template_name}: Nenhuma fase válida encontrada')
                            
                    except Exception as e:
                        errors.append(f'Erro ao processar template {template_name}: {str(e)}')
                
                # Mensagens de resultado
                if templates_created > 0:
                    messages.success(request, f'{templates_created} template(s) criado(s) com sucesso')
                if templates_updated > 0:
                    messages.info(request, f'{templates_updated} template(s) atualizado(s)')
                if errors:
                    messages.warning(request, 'Alguns erros ocorreram durante a importação:')
                    for error in errors:
                        messages.warning(request, error)
                        
        except Exception as e:
            messages.error(request, f'Erro ao processar arquivo: {str(e)}')
            
    return redirect('administrativo:templates')

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
                messages.error(request, 'O nome do time é obrigatório')
                return redirect('administrativo:time_novo')

            if not country_id:
                messages.error(request, 'O país é obrigatório')
                return redirect('administrativo:time_novo')

            if not image:
                messages.error(request, 'A imagem é obrigatória')
                return redirect('administrativo:time_novo')

            if not is_national_team and not state_id:
                messages.error(request, 'O estado é obrigatório para times que não são seleções')
                return redirect('administrativo:time_novo')

            # Busca país e estado
            country = Country.objects.get(id=country_id)
            state = None
            if not is_national_team and state_id:
                state = State.objects.get(id=state_id)

            # Verifica se já existe um time com o mesmo nome no país
            if Team.objects.filter(name=name, country=country).exists():
                messages.error(request, 'Já existe um time com este nome neste país')
                return redirect('administrativo:time_novo')

            # Cria o time
            team = Team.objects.create(
                name=name,
                country=country,
                state=state,
                is_national_team=is_national_team,
                image=image
            )

            messages.success(request, 'Time criado com sucesso!')
            return redirect('administrativo:times')

        except Country.DoesNotExist:
            messages.error(request, 'País não encontrado')
        except State.DoesNotExist:
            messages.error(request, 'Estado não encontrado')
        except Exception as e:
            messages.error(request, f'Erro ao criar time: {str(e)}')
        
        return redirect('administrativo:time_novo')

    # GET: Carrega o formulário
    countries = Country.objects.all().order_by('name')
    states = State.objects.all().order_by('name')
    return render(request, 'administrativo/time-novo.html', {
        'countries': countries,
        'states': states
    })

def time_editar(request, id):
    """
    View para editar um time existente.
    """
    team = get_object_or_404(Team, id=id)
    
    if request.method == 'POST':
        try:
            # Valida se o time pode ser editado
            if Championship.objects.filter(teams=team).exists():
                messages.error(request, 'Este time não pode ser editado pois está vinculado a campeonatos.')
                return redirect('administrativo:times')
            
            # Atualiza os dados do time
            team.name = request.POST.get('name')
            team.continent_id = request.POST.get('continent')
            team.country_id = request.POST.get('country')
            team.state_id = request.POST.get('state')
            team.is_national_team = request.POST.get('is_national_team') == 'on'
            
            # Salva a imagem se fornecida
            if 'image' in request.FILES:
                team.image = request.FILES['image']
            
            team.save()
            messages.success(request, 'Time atualizado com sucesso.')
            return redirect('administrativo:times')
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar time: {str(e)}')
            return redirect('administrativo:time_editar', id=id)
    
    # GET: Carrega o formulário
    continents = Continent.objects.all().order_by('name')
    countries = Country.objects.all().order_by('name')
    states = State.objects.all().order_by('name')
    championships = Championship.objects.filter(teams=team).order_by('name')
    
    return render(request, 'administrativo/time-editar.html', {
        'team': team,
        'continents': continents,
        'countries': countries,
        'states': states,
        'championships': championships,
        'has_championships': championships.exists()
    })

def time_excluir(request, id):
    """
    Exclui um time.
    """
    team = get_object_or_404(Team, id=id)
    
    if not team.can_delete():
        messages.error(request, 'Não é possível excluir este time pois ele está vinculado a campeonatos')
        return redirect('administrativo:times')
        
    try:
        # TODO: Remover a imagem do storage se existir
        team.delete()
        messages.success(request, 'Time excluído com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir time: {str(e)}')
        
    return redirect('administrativo:times')

def time_excluir_em_massa(request):
    """
    Exclui múltiplos times.
    """
    if request.method == 'POST':
        team_ids = request.POST.getlist('teams[]')
        
        if not team_ids:
            return JsonResponse({
                'status': 'error',
                'message': 'Nenhum time selecionado'
            })
            
        teams = Team.objects.filter(id__in=team_ids)
        deleted_count = 0
        errors = []
        
        for team in teams:
            if team.can_delete():
                # TODO: Remover a imagem do storage se existir
                team.delete()
                deleted_count += 1
            else:
                errors.append(f'Time "{team.name}" não pode ser excluído pois está vinculado a campeonatos')
        
        return JsonResponse({
            'status': 'success',
            'deleted': deleted_count,
            'errors': errors
        })
        
    return JsonResponse({
        'status': 'error',
        'message': 'Método não permitido'
    })

def time_importar(request):
    """
    Importa times de um arquivo Excel.
    """
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            df = pd.read_excel(request.FILES['file'])
            
            required_columns = ['nome', 'continente', 'pais', 'estado', 'selecao']
            if not all(col in df.columns for col in required_columns):
                raise ValueError('Arquivo não contém todas as colunas necessárias')
                
            with transaction.atomic():
                teams_created = 0
                teams_updated = 0
                errors = []
                
                for _, row in df.iterrows():
                    try:
                        # Obtém ou cria o time
                        continent = Continent.objects.get(name=row['continente'])
                        country = Country.objects.get(name=row['pais'])
                        state = None
                        if pd.notna(row['estado']):
                            state = State.objects.filter(name=row['estado'], country=country).first()
                        
                        team, created = Team.objects.get_or_create(
                            name=row['nome'],
                            country=country,
                            defaults={
                                'continent': continent,
                                'state': state,
                                'is_national_team': row['selecao'] == 'Sim'
                            }
                        )
                        
                        if created:
                            teams_created += 1
                        else:
                            # Só atualiza se não tiver campeonatos vinculados
                            if not team.championships.exists():
                                team.continent = continent
                                team.state = state
                                team.is_national_team = row['selecao'] == 'Sim'
                                team.save()
                                teams_updated += 1
                            else:
                                errors.append(f'Time "{team.name}" não foi atualizado pois tem campeonatos vinculados')
                            
                    except (Continent.DoesNotExist, Country.DoesNotExist) as e:
                        errors.append(f'Erro ao processar time "{row["nome"]}": {str(e)}')
                
                message = f'{teams_created} times criados e {teams_updated} atualizados com sucesso!'
                if errors:
                    message += f'\nErros: {", ".join(errors)}'
                    
                messages.success(request, message)
                
        except Exception as e:
            messages.error(request, f'Erro ao importar times: {str(e)}')
            
    return redirect('administrativo:times')

def time_exportar(request):
    """
    Exporta times para um arquivo Excel.
    """
    teams = Team.objects.all().select_related('continent', 'country', 'state')
    
    data = []
    for team in teams:
        data.append({
            'nome': team.name,
            'continente': team.continent.name,
            'pais': team.country.name,
            'estado': team.state.name if team.state else '',
            'selecao': 'Sim' if team.is_national_team else 'Não',
            'campeonatos': ', '.join(team.championships.values_list('name', flat=True))
        })
    
    df = pd.DataFrame(data)
    
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="times.xlsx"'
    
    df.to_excel(response, index=False)
    return response

def time_importar_imagens(request):
    """
    Importa imagens para os times.
    """
    if request.method == 'POST':
        try:
            files = request.FILES.getlist('images')
            if not files:
                messages.error(request, 'Nenhuma imagem selecionada')
                return redirect('administrativo:times')
            
            success_count = 0
            errors = []
            
            for file in files:
                # Remove a extensão do nome do arquivo
                filename = os.path.splitext(file.name)[0]
                
                # Procura o time pelo nome do arquivo
                team = Team.objects.filter(name__iexact=filename).first()
                
                if team:
                    try:
                        # TODO: Implementar o upload da imagem para o storage
                        # team.image = caminho_da_imagem
                        team.save()
                        success_count += 1
                    except Exception as e:
                        errors.append(f'Erro ao processar imagem "{file.name}": {str(e)}')
                else:
                    errors.append(f'Time não encontrado para a imagem "{file.name}"')
            
            message = f'{success_count} imagens importadas com sucesso!'
            if errors:
                message += f'\nErros: {", ".join(errors)}'
                
            messages.success(request, message)
            
        except Exception as e:
            messages.error(request, f'Erro ao importar imagens: {str(e)}')
            
    return redirect('administrativo:times')

def futcoins(request):
    return render(request, 'administrativo/futcoins.html')

def pacote_futcoin_novo(request):
    return render(request, 'administrativo/pacote-futcoin-novo.html')

def planos(request):
    return render(request, 'administrativo/planos.html')

def pacote_plano_novo(request):
    return render(request, 'administrativo/pacote-plano-novo.html')

def futligas_classicas(request):
    return render(request, 'administrativo/futligas-classicas.html')

def futliga_classica_novo(request):
    return render(request, 'administrativo/futliga-classica-novo.html')

def futligas_jogadores(request):
    return render(request, 'administrativo/futligas-jogadores.html')

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
    
    if not continent.can_delete():
        related_data = continent.get_related_data()
        message = f"Não é possível excluir o continente {continent.name} pois existem registros vinculados: "
        message += ", ".join(related_data)
        return JsonResponse({'success': False, 'message': message})
    
    try:
        continent.delete()
        return JsonResponse({'success': True, 'message': 'Continente excluído com sucesso!'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro ao excluir continente: {str(e)}'})

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
    fields = [
        ('name', 'Nome'),
        ('created_at', 'Data Criação')
    ]
    return export_to_excel(continents, fields, 'continentes.xlsx')

def continente_importar(request):
    """
    Importa continentes de um arquivo Excel
    """
    if request.method == 'POST' and request.FILES.get('file'):
        fields = [('name', 'name')]
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
            
        # Verifica se já existe um país com este nome no continente
        if Country.objects.filter(name=name, continent_id=continent_id).exists():
            messages.error(request, 'Já existe um país com este nome neste continente')
            return redirect('administrativo:pais_novo')
            
        try:
            continent = Continent.objects.get(id=continent_id)
            country = Country.objects.create(
                name=name,
                continent=continent
            )
            messages.success(request, 'País criado com sucesso')
            return redirect('administrativo:paises')
        except Exception as e:
            messages.error(request, f'Erro ao criar país: {str(e)}')
            return redirect('administrativo:pais_novo')
    
    continents = Continent.objects.all().order_by('name')
    return render(request, 'administrativo/pais-novo.html', {
        'continents': continents
    })

def pais_editar(request, id):
    """
    Edita um país existente.
    """
    country = get_object_or_404(Country, id=id)
    
    # Obtém os dados relacionados
    states = State.objects.filter(country=country).order_by('name')
    championships = country.championships.all()  # Usa a relação reversa
    teams = Team.objects.filter(championship__in=championships).order_by('name')
    
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
        return redirect('administrativo:paises')
        
    try:
        country.delete()
        messages.success(request, 'País excluído com sucesso')
    except Exception as e:
        messages.error(request, f'Erro ao excluir país: {str(e)}')
        
    return redirect('administrativo:paises')

def pais_excluir_em_massa(request):
    """
    Exclui múltiplos países se não tiverem vinculações.
    """
    if request.method == 'POST':
        ids = request.POST.getlist('ids[]')
        if not ids:
            return JsonResponse({'error': 'Nenhum país selecionado'}, status=400)
            
        try:
            # Filtra apenas os países que podem ser excluídos
            countries = Country.objects.filter(id__in=ids)
            deletable_countries = [c for c in countries if c.can_delete()]
            
            # Exclui os países que podem ser excluídos
            for country in deletable_countries:
                country.delete()
                
            if len(deletable_countries) == len(ids):
                message = 'Países excluídos com sucesso'
            else:
                message = f'{len(deletable_countries)} de {len(ids)} países foram excluídos. Alguns países não puderam ser excluídos por terem registros vinculados'
                
            return JsonResponse({'message': message})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)

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
    Importa países de um arquivo Excel.
    """
    if request.method != 'POST' or 'file' not in request.FILES:
        messages.error(request, 'Nenhum arquivo foi enviado')
        return redirect('administrativo:paises')
    
    file = request.FILES['file']
    fields = [
        ('name', 'name'),
        ('continent__name', 'continent')
    ]
    
    success, message = import_from_excel(file, Country, fields, ['name'])
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return redirect('administrativo:paises')

def estados(request):
    """
    Lista todos os estados.
    """
    # Limpa as mensagens antigas
    storage = messages.get_messages(request)
    for _ in storage:
        pass  # Limpa as mensagens antigas
    
    states = State.objects.all().order_by('country__name', 'name')
    return render(request, 'administrativo/estados.html', {'states': states})

def estado_novo(request):
    """
    Cria um novo estado.
    """
    # Limpa as mensagens antigas
    storage = messages.get_messages(request)
    for _ in storage:
        pass  # Limpa as mensagens antigas
    
    if request.method == 'POST':
        name = request.POST.get('name')
        country_id = request.POST.get('country')
        
        try:
            country = Country.objects.get(id=country_id)
            state = State(name=name, country=country)
            state.full_clean()
            state.save()
            messages.success(request, 'Estado criado com sucesso!')
            return redirect('administrativo:estados')
        except ValidationError as e:
            messages.error(request, f'Erro de validação: {str(e)}')
        except Exception as e:
            messages.error(request, f'Erro ao criar estado: {str(e)}')
    
    countries = Country.objects.all().order_by('name')
    return render(request, 'administrativo/estado-novo.html', {'countries': countries})

def estado_excluir(request, id):
    """
    Exclui um estado existente.
    """
    if request.method == 'POST':
        try:
            state = get_object_or_404(State, id=id)
            
            # Verifica se tem campeonatos vinculados
            if Championship.objects.filter(country=state.country).exists():
                messages.error(request, 'Não é possível excluir o estado pois existem campeonatos vinculados')
                return redirect('administrativo:estados')
                
            state.delete()
            messages.success(request, 'Estado excluído com sucesso')
            
        except Exception as e:
            messages.error(request, f'Erro ao excluir estado: {str(e)}')
            
    return redirect('administrativo:estados')

def estado_excluir_em_massa(request):
    """
    Exclui múltiplos estados selecionados.
    """
    if request.method == 'POST':
        ids = request.POST.getlist('ids[]')
        if not ids:
            return JsonResponse({'error': 'Nenhum estado selecionado'}, status=400)
            
        try:
            # Verifica se algum estado tem times ou campeonatos vinculados
            states = State.objects.filter(id__in=ids)
            non_deletable_states = []
            
            for state in states:
                if state.team_set.exists() or Championship.objects.filter(state=state).exists():
                    non_deletable_states.append(state.name)
            
            if non_deletable_states:
                return JsonResponse({
                    'error': f'Os seguintes estados não podem ser excluídos pois possuem registros vinculados: {", ".join(non_deletable_states)}'
                }, status=400)
                
            # Exclui os estados que podem ser excluídos
            states.delete()
            return JsonResponse({'message': 'Estados excluídos com sucesso'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)

def estado_importar(request):
    """
    Importa estados a partir de um arquivo Excel.
    """
    if request.method != 'POST' or 'file' not in request.FILES:
        messages.error(request, 'Nenhum arquivo foi enviado')
        return redirect('administrativo:estados')
    
    file = request.FILES['file']
    fields = [
        ('name', 'name'),
        ('country__name', 'country')
    ]
    
    success, message = import_from_excel(file, State, fields, ['name', 'country'])
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return redirect('administrativo:estados')

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
        teams = Team.objects.filter(championship__country=state.country).order_by('name')
        championships = Championship.objects.filter(country=state.country).order_by('name')
        
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
        has_championships = Championship.objects.filter(country=state.country).exists()
        
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
    return render(request, 'administrativo/parametros.html')

def termo(request):
    return render(request, 'administrativo/termo.html')

def notificacoes(request):
    return render(request, 'administrativo/notificacoes.html')

def notificacao_novo(request):
    return render(request, 'administrativo/notificacao-novo.html')

def relatorios(request):
    return render(request, 'administrativo/relatorios.html')

def administradores(request):
    # Lista todos os administradores exceto o root
    admins = Administrator.objects.filter(is_root=False).order_by('-created_at')
    return render(request, 'administrativo/administradores.html', {'admins': admins})

def administrador_novo(request):
    # Limpa as mensagens antigas
    storage = messages.get_messages(request)
    storage.used = True
    
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not all([name, email, password]):
            messages.error(request, 'Todos os campos são obrigatórios')
            return render(request, 'administrativo/administrador_novo.html')
        
        if Administrator.objects.filter(email=email).exists():
            messages.error(request, 'Email já cadastrado')
            return render(request, 'administrativo/administrador_novo.html')
            
        Administrator.objects.create(
            name=name,
            email=email,
            password=make_password(password),
            is_root=False
        )
        messages.success(request, 'Administrador criado com sucesso')
        return redirect('administrativo:administradores')
        
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
        messages.error(request, 'Não é permitido excluir o usuário root')
        return redirect('administrativo:administradores')
        
    admin.delete()
    messages.success(request, 'Administrador excluído com sucesso')
    return redirect('administrativo:administradores')

def administradores_excluir_massa(request):
    if request.method == 'POST':
        ids = request.POST.getlist('administradores[]')
        # Garante que não exclui o usuário root
        Administrator.objects.filter(id__in=ids, is_root=False).delete()
        messages.success(request, 'Administradores excluídos com sucesso')
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

def logout(request):
    # Limpa a sessão
    request.session.flush()
    return redirect('administrativo:login') 

def campeonato_importar_jogos(request):
    """
    View para importar jogos de um arquivo Excel.
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
            
        # Importa os jogos
        for _, row in df.iterrows():
            # Obtém ou cria a fase
            stage, _ = ChampionshipStage.objects.get_or_create(
                championship=championship,
                name=row['Fase']
            )
            
            # Obtém ou cria a rodada
            round_obj, _ = ChampionshipRound.objects.get_or_create(
                championship=championship,
                name=str(row['Rodada'])
            )
            
            # Obtém os times
            try:
                team_home = Team.objects.get(name=row['Time Mandante'])
                team_away = Team.objects.get(name=row['Time Visitante'])
            except Team.DoesNotExist:
                continue
                
            # Cria o jogo
            match_date = datetime.combine(
                row['Data'],
                datetime.strptime(str(row['Hora']), '%H:%M').time()
            )
            
            ChampionshipMatch.objects.create(
                championship=championship,
                stage=stage,
                round=round_obj,
                team_home=team_home,
                team_away=team_away,
                score_home=row['Placar Mandante'],
                score_away=row['Placar Visitante'],
                match_date=match_date
            )
            
        return JsonResponse({'status': 'success'})
        
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
    """
    Edita um campeonato existente.
    Permite editar informações gerais e times se o campeonato não tiver rodadas.
    """
    try:
        championship = Championship.objects.get(id=id)
        
        if request.method == 'POST':
            try:
                with transaction.atomic():
                    # Obtém os dados do formulário
                    name = request.POST.get('name')
                    season = request.POST.get('season')
                    template_id = request.POST.get('template')
                    scope_id = request.POST.get('scope')
                    continent_id = request.POST.get('continent')
                    country_id = request.POST.get('country')
                    state_id = request.POST.get('state')
                    is_active = request.POST.get('is_active') == 'on'
                    
                    # Valida campos obrigatórios
                    if not all([name, season, template_id, scope_id, country_id]):
                        messages.error(request, 'Todos os campos obrigatórios devem ser preenchidos')
                        return redirect('administrativo:campeonato_editar', id=id)
                    
                    # Verifica se já existe um campeonato com o mesmo nome e temporada
                    if Championship.objects.filter(name=name, season=season).exclude(id=id).exists():
                        messages.error(request, 'Já existe um campeonato com este nome e temporada')
                        return redirect('administrativo:campeonato_editar', id=id)
                    
                    # Atualiza os dados do campeonato
                    championship.name = name
                    championship.season = season
                    championship.template_id = template_id
                    championship.scope_id = scope_id
                    championship.continent_id = continent_id
                    championship.country_id = country_id
                    championship.state_id = state_id
                    championship.is_active = is_active
                    championship.save()
                    
                    # Atualiza os times se permitido
                    if championship.can_edit_teams():
                        teams = request.POST.getlist('teams[]')
                        championship.teams.clear()
                        championship.teams.add(*teams)
                    
                    messages.success(request, 'Campeonato atualizado com sucesso')
                    return redirect('administrativo:campeonatos')
                    
            except Exception as e:
                messages.error(request, f'Erro ao atualizar campeonato: {str(e)}')
                return redirect('administrativo:campeonato_editar', id=id)
        
        # Obtém dados para o formulário
        templates = Template.objects.filter(enabled=True)
        scopes = Scope.objects.filter(is_active=True)
        continents = Continent.objects.all()
        countries = Country.objects.all()
        states = State.objects.all()
        teams = Team.objects.all()
        selected_teams = championship.teams.all()
        
        return render(request, 'administrativo/campeonato-editar.html', {
            'championship': championship,
            'templates': templates,
            'scopes': scopes,
            'continents': continents,
            'countries': countries,
            'states': states,
            'teams': teams,
            'selected_teams': selected_teams
        })
        
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
            teams = teams.filter(is_selection=False)
        elif filter_type == 'selections':
            teams = teams.filter(is_selection=True)
            
        return JsonResponse({
            'success': True,
            'teams': list(teams.values('id', 'name'))
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
    if request.method == 'POST':
        championship_id = request.POST.get('id')
        try:
            championship = Championship.objects.get(id=championship_id)
            championship.is_active = not championship.is_active
            championship.save()
            
            status = 'ativado' if championship.is_active else 'desativado'
            return JsonResponse({
                'success': True,
                'message': f'Campeonato {status} com sucesso!',
                'is_active': championship.is_active
            })
        except Championship.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Campeonato não encontrado.'
            })
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido.'
    }) 