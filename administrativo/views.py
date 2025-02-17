from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.urls import reverse
from .models import (
    User, Scope, Championship, Template, Team,
    FutcoinPackage, Plan, ClassicLeague, Player,
    Continent, Country, State, Parameter, Term, 
    Notification, Administrator
)

def login(request):
    # Se já estiver logado, redireciona para a página inicial
    if request.session.get('admin_id'):
        return redirect('administrativo:usuarios')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            admin = Administrator.objects.get(email=email)
            if check_password(password, admin.password):
                # Salva os dados do admin na sessão
                request.session['admin_id'] = admin.id
                request.session['admin_name'] = admin.name
                request.session['is_root'] = admin.is_root
                messages.success(request, 'Login realizado com sucesso!')
                return redirect('administrativo:usuarios')
            else:
                messages.error(request, 'Senha incorreta')
        except Administrator.DoesNotExist:
            messages.error(request, 'Email não encontrado')
        
    return render(request, 'administrativo/login.html')

def usuarios(request):
    return render(request, 'administrativo/usuarios.html')

def usuario_editar(request):
    return render(request, 'administrativo/usuario-editar.html')

def ambitos(request):
    return render(request, 'administrativo/ambitos.html')

def ambito_editar(request):
    return render(request, 'administrativo/ambito-editar.html')

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
    return render(request, 'administrativo/continentes.html')

def continente_novo(request):
    return render(request, 'administrativo/continente-novo.html')

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
    messages.success(request, 'Logout realizado com sucesso!')
    return redirect('administrativo:login') 