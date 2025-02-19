from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.urls import reverse
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import (
    User, Scope, Championship, Template, Team,
    FutcoinPackage, Plan, ClassicLeague, Player,
    Continent, Country, State, Parameter, Term, 
    Notification, Administrator, ScopeLevel
)
from .utils import export_to_excel, import_from_excel
import pandas as pd
import csv

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
    return render(request, 'administrativo/campeonatos.html')

def campeonato_novo(request):
    return render(request, 'administrativo/campeonato-novo.html')

def templates(request):
    return render(request, 'administrativo/templates.html')

def template_novo(request):
    return render(request, 'administrativo/template-novo.html')

def times(request):
    return render(request, 'administrativo/times.html')

def time_novo(request):
    return render(request, 'administrativo/time-novo.html')

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
        try:
            ids = request.POST.get('ids', '').split(',')
            if not ids:
                messages.error(request, 'Nenhum estado selecionado')
                return redirect('administrativo:estados')
                
            # Verifica se algum estado tem campeonatos vinculados
            states_with_championships = State.objects.filter(
                id__in=ids,
                country__championship__isnull=False
            ).distinct()
            
            if states_with_championships.exists():
                messages.error(request, 'Não é possível excluir estados que possuem campeonatos vinculados')
                return redirect('administrativo:estados')
                
            # Exclui os estados selecionados
            State.objects.filter(id__in=ids).delete()
            messages.success(request, 'Estados excluídos com sucesso')
            
        except Exception as e:
            messages.error(request, f'Erro ao excluir estados: {str(e)}')
            
    return redirect('administrativo:estados')

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