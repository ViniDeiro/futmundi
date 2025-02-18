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
    Exclui um continente
    """
    continent = get_object_or_404(Continent, id=id)
    
    if not continent.can_delete():
        messages.error(request, 'Não é possível excluir o continente pois existem registros vinculados.')
        return redirect('administrativo:continentes')
    
    try:
        continent.delete()
        messages.success(request, 'Continente excluído com sucesso!')
    except Exception as e:
        messages.error(request, 'Erro ao excluir continente.')
    
    return redirect('administrativo:continentes')

def continente_excluir_em_massa(request):
    """
    Exclui múltiplos continentes
    """
    if request.method == 'POST':
        ids = request.POST.getlist('ids[]')
        
        if not ids:
            return JsonResponse({'success': False, 'message': 'Nenhum continente selecionado.'})
        
        try:
            with transaction.atomic():
                continents = Continent.objects.filter(id__in=ids)
                # Filtra apenas os que podem ser excluídos
                deletable = [c for c in continents if c.can_delete()]
                
                if not deletable:
                    return JsonResponse({
                        'success': False,
                        'message': 'Nenhum dos continentes selecionados pode ser excluído pois possuem registros vinculados.'
                    })
                
                # Exclui os continentes que podem ser excluídos
                for continent in deletable:
                    continent.delete()
                
                return JsonResponse({
                    'success': True,
                    'message': f'{len(deletable)} continente(s) excluído(s) com sucesso!'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Erro ao excluir continentes.'
            })
    
    return JsonResponse({'success': False, 'message': 'Método não permitido.'})

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
    return render(request, 'administrativo/paises.html')

def pais_novo(request):
    return render(request, 'administrativo/pais-novo.html')

def estados(request):
    return render(request, 'administrativo/estados.html')

def estado_novo(request):
    return render(request, 'administrativo/estado-novo.html')

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