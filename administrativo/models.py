from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.templatetags.static import static
from django.db.models import Q
from django.core.exceptions import ValidationError
import os

class User(AbstractUser):
    # NOTA: Este modelo herda AbstractUser, mas a migração inicial não incluiu todos os campos
    # necessários da classe base (como password, username, etc). O erro "Unknown column 'users.password'"
    # ocorre porque o Django espera que esses campos existam na tabela.
    # As opções para resolver são:
    # 1. Refazer todas as migrações (recomendado para ambiente de desenvolvimento)
    # 2. Criar uma migração manual para adicionar os campos faltantes (opção de emergência para produção)
    
    PLAN_CHOICES = [
        ('common', 'Common'),
        ('star', 'Star'),
    ]
    
    PERIOD_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semiannual', 'Semiannual'),
        ('annual', 'Annual'),
    ]
    
    futcoins = models.IntegerField(default=0)
    current_plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='common')
    registration_date = models.DateTimeField(default=timezone.now)
    star_date = models.DateTimeField(null=True, blank=True)
    current_period = models.CharField(max_length=20, choices=PERIOD_CHOICES, default='monthly')
    period_start = models.DateTimeField(null=True, blank=True)
    period_end = models.DateTimeField(null=True, blank=True)
    period_renewals = models.IntegerField(default=0)
    facebook_linked = models.BooleanField(default=False)
    google_linked = models.BooleanField(default=False)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    plan_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    packages_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_star = models.BooleanField(default=False)
    
    # Sobrescrevendo os campos ManyToMany do AbstractUser para adicionar related_name
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='administrativo_users',  # Adicionando related_name personalizado
        related_query_name='administrativo_user'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='administrativo_users',  # Adicionando related_name personalizado
        related_query_name='administrativo_user'
    )
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        swappable = 'AUTH_USER_MODEL'
    
    def __str__(self):
        return self.get_full_name() or self.username

# Campeonatos
class ScopeLevel(models.Model):
    """
    Entity that represents a level configuration for leverage or insurance in a scope.
    
    Properties:
    - scope: Reference to the parent Scope
    - type: Type of level (leverage or insurance)
    - level: Level number (1, 2 or 3)
    - points: Points awarded at this level
    - futcoins: Price in Futcoins for this level
    - is_active: Whether this level is active
    - created_at: Creation timestamp
    - updated_at: Last update timestamp
    """
    
    LEVEL_TYPES = [
        ('leverage', 'Alavancagem'),
        ('insurance', 'Seguro'),
    ]
    
    scope = models.ForeignKey('Scope', on_delete=models.CASCADE, related_name='levels')
    type = models.CharField(max_length=20, choices=LEVEL_TYPES)
    level = models.IntegerField()  # 1, 2 ou 3
    points = models.IntegerField(default=0)
    futcoins = models.IntegerField(default=0)  # Preço em Futcoins
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'scope_levels'
        verbose_name = 'Nível de Âmbito'
        verbose_name_plural = 'Níveis de Âmbito'
        unique_together = ['scope', 'type', 'level']  # Garante que não haja duplicidade

    def __str__(self):
        return f"{self.get_type_display()} Nível {self.level} - {self.scope.name}"

    def save(self, *args, **kwargs):
        # Garante que valores não sejam negativos
        self.points = max(0, self.points)
        self.futcoins = max(0, self.futcoins)
        super().save(*args, **kwargs)

class Scope(models.Model):
    """
    Entity that represents a competition scope in the system.
    
    Properties:
    - name: Scope name
    - type: Scope type (state, national, continental, worldwide)
    - boost: Boost points for this scope
    - futcoins: Base price in Futcoins
    - is_active: Whether this scope is active
    - is_default: Whether this is a default scope that cannot be deleted
    - created_at: Creation timestamp
    - updated_at: Last update timestamp
    
    Default Scopes:
    - State: Basic regional scope
    - National: Country-wide scope
    - Continental: Continent-wide scope
    - Worldwide: Global scope
    
    Each scope has:
    - 3 leverage levels with specific points and prices
    - 3 insurance levels with specific points and prices
    """
    
    SCOPE_TYPES = [
        ('estadual', 'Estadual'),
        ('nacional', 'Nacional'),
        ('continental', 'Continental'),
        ('mundial', 'Mundial'),
    ]

    SCOPE_TYPE_ORDER = {
        'estadual': 1,
        'nacional': 2,
        'continental': 3,
        'mundial': 4
    }
    
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=SCOPE_TYPES, default='estadual')
    boost = models.IntegerField(default=0)
    futcoins = models.IntegerField(default=0)  # Preço base em Futcoins
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'scopes'
        verbose_name = 'Âmbito'
        verbose_name_plural = 'Âmbitos'
        ordering = ['type']  # Ordenação padrão por tipo

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Garante que valores não sejam negativos
        self.boost = max(0, self.boost)
        self.futcoins = max(0, self.futcoins)
        super().save(*args, **kwargs)

class Championship(models.Model):
    """
    Entidade que representa um campeonato no sistema.
    
    Propriedades:
    - name: Nome do campeonato
    - season: Temporada
    - template: Template que define a estrutura de fases e rodadas
    - scope: Âmbito do campeonato (estadual, nacional, etc.)
    - continent: Continente (opcional)
    - country: País
    - state: Estado (opcional)
    - points: Método de pontuação
    - current_stage: Fase atual
    - current_round: Rodada atual
    - is_active: Se o campeonato está ativo
    - created_at: Data de criação
    - updated_at: Data de atualização
    """
    
    name = models.CharField(max_length=255)
    season = models.CharField(max_length=50, null=True, blank=True)
    template = models.ForeignKey('Template', on_delete=models.PROTECT, related_name='template_championships', null=True, blank=True)
    scope = models.ForeignKey('Scope', on_delete=models.PROTECT, related_name='championships', null=True, blank=True)
    continent = models.ForeignKey('Continent', on_delete=models.PROTECT, null=True, blank=True)
    country = models.ForeignKey('Country', on_delete=models.PROTECT, null=True, blank=True)
    state = models.ForeignKey('State', on_delete=models.PROTECT, null=True, blank=True)
    points = models.IntegerField(default=0)
    current_stage = models.ForeignKey('ChampionshipStage', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    current_round = models.ForeignKey('ChampionshipRound', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    teams = models.ManyToManyField('Team', related_name='team_championships', blank=True)

    class Meta:
        db_table = 'championships'
        verbose_name = 'Campeonato'
        verbose_name_plural = 'Campeonatos'
        ordering = ['-created_at']
        unique_together = ['name', 'season']  # Nome + Temporada devem ser únicos

    def __str__(self):
        return f"{self.name} - {self.season}"

    def can_delete(self):
        """
        Verifica se o campeonato pode ser excluído.
        Só pode excluir se estiver inativo e não tiver palpites.
        """
        return not self.is_active and not self.predictions.exists()

    def can_edit_teams(self):
        """
        Verifica se os times do campeonato podem ser editados.
        Só pode editar se não houver rodadas cadastradas.
        """
        return not self.rounds.exists()

    def can_edit_rounds(self):
        """
        Verifica se as rodadas podem ser editadas.
        Depende do status do campeonato e se já há palpites.
        """
        if not self.is_active:
            return True
        return not self.predictions.exists()

    def get_related_data(self):
        """
        Retorna dados relacionados ao campeonato.
        """
        return {
            'teams': list(self.teams.values('id', 'name')),
            'stages': list(self.stages.values('id', 'name')),
            'rounds': list(self.rounds.values('id', 'number')),
            'predictions': self.predictions.count()
        }

    def update_points(self):
        """
        Atualiza a pontuação do campeonato baseado nos resultados das partidas.
        Cada vitória vale 3 pontos, empate 1 ponto.
        """
        total_points = 0
        for match in self.matches.all():
            if match.home_score is not None and match.away_score is not None:
                if match.home_score > match.away_score:
                    total_points += 3
                elif match.home_score == match.away_score:
                    total_points += 1
        self.points = total_points
        self.save(update_fields=['points'])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class ChampionshipStage(models.Model):
    """
    Entidade que representa uma fase de um campeonato.
    """
    championship = models.ForeignKey(Championship, on_delete=models.CASCADE, related_name='stages')
    template_stage = models.ForeignKey('TemplateStage', on_delete=models.PROTECT)
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField()
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'championship_stages'
        verbose_name = 'Fase do Campeonato'
        verbose_name_plural = 'Fases do Campeonato'
        ordering = ['order']
        unique_together = ['championship', 'order']

    def __str__(self):
        return f"{self.championship.name} - {self.name}"

class ChampionshipRound(models.Model):
    """
    Entidade que representa uma rodada de um campeonato.
    """
    championship = models.ForeignKey(Championship, on_delete=models.CASCADE, related_name='rounds')
    stage = models.ForeignKey(ChampionshipStage, on_delete=models.CASCADE, related_name='rounds')
    number = models.PositiveIntegerField()
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'championship_rounds'
        verbose_name = 'Rodada do Campeonato'
        verbose_name_plural = 'Rodadas do Campeonato'
        ordering = ['number']
        unique_together = ['championship', 'stage', 'number']

    def __str__(self):
        return f"{self.championship.name} - Rodada {self.number}"

    def can_edit(self):
        """
        Verifica se a rodada pode ser editada.
        Não pode editar se:
        1. Algum jogo já aconteceu
        2. Existem palpites para jogos desta rodada
        """
        now = timezone.now()
        
        # Verifica se algum jogo já aconteceu
        if self.matches.filter(match_date__lt=now).exists():
            return False
            
        # Verifica se existem palpites
        if self.matches.filter(predictions__isnull=False).exists():
            return False
            
        return True

class ChampionshipMatch(models.Model):
    """
    Entidade que representa uma partida de uma rodada.
    """
    championship = models.ForeignKey(Championship, on_delete=models.CASCADE, related_name='matches')
    round = models.ForeignKey(ChampionshipRound, on_delete=models.CASCADE, related_name='matches')
    home_team = models.ForeignKey('Team', on_delete=models.PROTECT, related_name='+')
    away_team = models.ForeignKey('Team', on_delete=models.PROTECT, related_name='+')
    home_score = models.IntegerField(null=True, blank=True)
    away_score = models.IntegerField(null=True, blank=True)
    match_date = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'championship_matches'
        verbose_name = 'Partida do Campeonato'
        verbose_name_plural = 'Partidas do Campeonato'
        ordering = ['match_date']

    def __str__(self):
        return f"{self.home_team.name} vs {self.away_team.name}"

    def clean(self):
        """
        Validações adicionais:
        - Times diferentes
        - Times participantes do campeonato
        - Data válida
        """
        if self.home_team == self.away_team:
            raise ValidationError('O time mandante e o visitante devem ser diferentes')
        
        if not self.championship.teams.filter(id=self.home_team.id).exists():
            raise ValidationError('O time mandante não participa deste campeonato')
            
        if not self.championship.teams.filter(id=self.away_team.id).exists():
            raise ValidationError('O time visitante não participa deste campeonato')
            
        if self.match_date and self.match_date < timezone.now():
            raise ValidationError('A data do jogo não pode ser no passado')

class Prediction(models.Model):
    """
    Entidade que representa um palpite em uma partida.
    """
    RESULT_CHOICES = [
        ('victory', 'Vitória'),
        ('draw', 'Empate'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('hit', 'Acerto'),
        ('miss', 'Erro'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='predictions'
    )
    match = models.ForeignKey(ChampionshipMatch, on_delete=models.CASCADE, related_name='predictions')
    result = models.CharField(max_length=20, choices=RESULT_CHOICES)
    boost_bonus = models.IntegerField(default=0)
    leverage_expenses = models.IntegerField(default=0)
    insurance_expenses = models.IntegerField(default=0)
    total_expenses = models.IntegerField(default=0)
    remaining_credits = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    hits = models.IntegerField(default=0)
    leverage = models.IntegerField(default=0)
    insurance = models.IntegerField(default=0)
    bonus = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'predictions'
        verbose_name = 'Palpite'
        verbose_name_plural = 'Palpites'
        ordering = ['-created_at']
        unique_together = ['user', 'match']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.match}"

    def save(self, *args, **kwargs):
        self.total_expenses = self.leverage_expenses + self.insurance_expenses
        super().save(*args, **kwargs)

class Template(models.Model):
    name = models.CharField(max_length=255, unique=True)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    number_of_stages = models.PositiveIntegerField(default=1)
    championships = models.ManyToManyField(Championship, related_name='templates', blank=True)

    class Meta:
        db_table = 'templates'
        verbose_name = 'Template'
        verbose_name_plural = 'Templates'

    def __str__(self):
        return self.name

    def can_delete(self):
        return not Championship.objects.filter(template=self).exists()

    def get_related_data(self):
        data = {
            'championships': list(self.championships.values_list('name', flat=True)),
            'stages': list(self.stages.values_list('name', flat=True))
        }
        return data

    def duplicate(self):
        new_template = Template.objects.create(
            name=f"Cópia de {self.name}",
            enabled=self.enabled,
            number_of_stages=self.number_of_stages
        )
        
        for stage in self.stages.all():
            stage.duplicate(new_template)
            
        return new_template

class TemplateStage(models.Model):
    template = models.ForeignKey(Template, on_delete=models.CASCADE, related_name='stages')
    name = models.CharField(max_length=255)
    rounds = models.PositiveIntegerField()
    matches_per_round = models.PositiveIntegerField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'template_stages'
        verbose_name = 'Fase do Template'
        verbose_name_plural = 'Fases do Template'
        ordering = ['order']
        unique_together = ['template', 'order']

    def __str__(self):
        return f"{self.template.name} - {self.name}"

    def can_delete(self):
        """
        Verifica se a fase pode ser excluída.
        Uma fase pode ser excluída se não estiver sendo usada em nenhuma rodada de campeonato.
        """
        # Verifica se há alguma fase de campeonato usando este template_stage que tenha rodadas
        championship_stages = ChampionshipStage.objects.filter(template_stage=self)
        for stage in championship_stages:
            if stage.rounds.exists():
                return False
        return True

    def duplicate(self, new_template):
        return TemplateStage.objects.create(
            template=new_template,
            name=self.name,
            rounds=self.rounds,
            matches_per_round=self.matches_per_round,
            order=self.order
        )

class Team(models.Model):
    """
    Entity that represents a team in the system.
    
    Properties:
    - name: Team name
    - image: Team shield/logo image path
    - is_national_team: Whether this is a national team
    - continent: Reference to the Continent
    - country: Reference to the Country
    - state: Reference to the State (optional)
    - created_at: Creation timestamp
    - updated_at: Last update timestamp
    """
    
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='teams/shields/', null=True, blank=True)
    is_national_team = models.BooleanField(default=False)
    continent = models.ForeignKey('Continent', on_delete=models.PROTECT, null=True, blank=True)
    country = models.ForeignKey('Country', on_delete=models.PROTECT)
    state = models.ForeignKey('State', on_delete=models.PROTECT, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'teams'
        verbose_name = 'Time'
        verbose_name_plural = 'Times'
        ordering = ['name']
        unique_together = ['name', 'country']  # Nome único por país

    def __str__(self):
        return f"{self.name} - {self.country.name}"

    def can_delete(self):
        """
        Verifica se o time pode ser excluído.
        """
        return not self.team_championships.exists()

    def get_related_data(self):
        """
        Retorna dados relacionados ao time.
        """
        return {
            'championships': list(self.team_championships.values('id', 'name')),
            'players': list(self.player_set.values('id', 'name'))
        }

    def get_image_url(self):
        """
        Retorna a URL da imagem do time ou a URL do escudo genérico.
        """
        if self.image:
            return self.image.url
        return '/static/administrativo/img/Generico.png'

    def has_championships(self):
        """
        Verifica se o time tem campeonatos vinculados ou está em partidas.
        """
        return (
            self.team_championships.exists() or
            ChampionshipMatch.objects.filter(Q(home_team=self) | Q(away_team=self)).exists()
        )

    def save(self, *args, **kwargs):
        # Se for seleção, garante que o estado seja None
        if self.is_national_team:
            self.state = None
        # Se o país não tem estados, garante que state seja None
        elif self.country and not self.country.state_set.exists():
            self.state = None
            
        # Garante que o continente seja o mesmo do país
        if self.country and self.country.continent:
            self.continent = self.country.continent
            
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Remove a imagem do storage antes de excluir o time
        """
        if self.image:
            self.image.delete(save=False)
        super().delete(*args, **kwargs)

# Pacotes
class FutcoinPackage(models.Model):
    """
    Entidade que representa um pacote de Futcoins no sistema.
    
    Propriedades:
    - name: Nome do pacote
    - image: Imagem do pacote
    - enabled: Se o pacote está ativo
    - package_type: Tipo do pacote (Padrão ou Promocional)
    - label: Etiqueta do pacote
    - color_text_label: Cor do texto da etiqueta
    - color_background_label: Cor de fundo da etiqueta
    - full_price: Preço padrão
    - promotional_price: Preço promocional
    - content: Conteúdo do pacote (quantidade de Futcoins)
    - bonus: Bônus adicional
    - show_to: Para quem mostrar (Todos, Comum ou Craque)
    - start_date: Data de início
    - end_date: Data de término
    """
    
    PACKAGE_TYPE_CHOICES = [
        ('padrao', 'Padrão'),
        ('promocional', 'Promocional'),
    ]
    
    SHOW_TO_CHOICES = [
        ('todos', 'Todos'),
        ('comum', 'Comum'),
        ('craque', 'Craque'),
    ]
    
    name = models.CharField(max_length=255, verbose_name='Nome')
    image = models.ImageField(upload_to='futcoins/packages/', null=True, blank=True, verbose_name='Imagem')
    enabled = models.BooleanField(default=True, verbose_name='Ativo')
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPE_CHOICES, default='padrao', verbose_name='Tipo')
    label = models.CharField(max_length=50, null=True, blank=True, verbose_name='Etiqueta')
    color_text_label = models.CharField(max_length=7, default='#000000', verbose_name='Cor do Texto da Etiqueta')
    color_background_label = models.CharField(max_length=7, default='#FFFFFF', verbose_name='Cor de Fundo da Etiqueta')
    full_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Preço Padrão')
    promotional_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Preço Promocional')
    content = models.IntegerField(default=0, verbose_name='Conteúdo')
    bonus = models.IntegerField(default=0, verbose_name='Bônus')
    show_to = models.CharField(max_length=20, choices=SHOW_TO_CHOICES, default='todos', verbose_name='Exibir Para')
    start_date = models.DateTimeField(null=True, blank=True, verbose_name='Data de Início')
    end_date = models.DateTimeField(null=True, blank=True, verbose_name='Data de Término')
    android_product_code = models.CharField(max_length=100, null=True, blank=True, verbose_name='Código do Produto (Android)')
    ios_product_code = models.CharField(max_length=100, null=True, blank=True, verbose_name='Código do Produto (iOS)')
    gateway_product_code = models.CharField(max_length=100, null=True, blank=True, verbose_name='Código do Produto (Gateway)')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'futcoin_packages'
        verbose_name = 'Pacote Futcoin'
        verbose_name_plural = 'Pacotes Futcoins'
        ordering = ['name']

    def __str__(self):
        return self.name

    def clean(self):
        # Validações personalizadas
        errors = {}
        
        # Validação do tipo de pacote e etiqueta
        if self.package_type == 'promocional' and not self.label:
            errors['label'] = 'A etiqueta é obrigatória para pacotes promocionais.'
        
        # Validação do preço promocional
        if self.promotional_price is not None:
            if self.promotional_price <= 0:
                errors['promotional_price'] = 'O preço promocional deve ser maior que zero.'
            if self.promotional_price >= self.full_price:
                errors['promotional_price'] = 'O preço promocional deve ser menor que o preço padrão. Por favor, verifique os valores informados.'
        
        # Validação das datas para pacotes promocionais
        if self.package_type == 'promocional':
            if not self.start_date:
                errors['start_date'] = 'A data de início é obrigatória para pacotes promocionais.'
            if not self.end_date:
                errors['end_date'] = 'A data de término é obrigatória para pacotes promocionais.'
        
        # Validação geral das datas
        if self.start_date and self.end_date and self.start_date > self.end_date:
            errors['start_date'] = 'A data de início não pode ser posterior à data de término.'
            errors['end_date'] = 'A data de término não pode ser anterior à data de início.'
        
        # Validação das cores
        for field in ['color_text_label', 'color_background_label']:
            color = getattr(self, field)
            # Verifica se é uma cor no formato rgba
            if color and len(color) > 7:
                # Tenta converter para o formato hexadecimal
                try:
                    # Extrai os valores RGB do formato rgba
                    import re
                    rgba_match = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*[\d.]+)?\)', color)
                    if rgba_match:
                        r, g, b = map(int, rgba_match.groups())
                        # Converte para hexadecimal
                        hex_color = f'#{r:02x}{g:02x}{b:02x}'.upper()
                        # Atualiza o valor do campo
                        setattr(self, field, hex_color)
                    else:
                        errors[field] = 'Cor inválida. Use o formato hexadecimal (#RRGGBB).'
                except Exception:
                    errors[field] = 'Cor inválida. Use o formato hexadecimal (#RRGGBB).'
            elif not color.startswith('#') or len(color) != 7 or not all(c in '0123456789ABCDEFabcdef' for c in color[1:]):
                errors[field] = 'Cor inválida. Use o formato hexadecimal (#RRGGBB).'
        
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def is_valid_period(self):
        """
        Verifica se o pacote está dentro do período válido de exibição
        """
        now = timezone.now()
        if self.start_date and self.end_date:
            return self.start_date <= now <= self.end_date
        elif self.start_date:
            return self.start_date <= now
        elif self.end_date:
            return now <= self.end_date
        return True

    def get_final_price(self):
        """
        Retorna o preço final do pacote (promocional se disponível, senão o preço padrão)
        """
        if self.promotional_price and self.is_valid_period():
            return self.promotional_price
        return self.full_price

    def get_total_coins(self):
        """
        Retorna o total de moedas (conteúdo + bônus)
        """
        return self.content + self.bonus

class Plan(models.Model):
    BILLING_CYCLE_CHOICES = [
        ('Mensal', 'Mensal'),
        ('Semestral', 'Semestral'),
        ('Anual', 'Anual')
    ]
    
    PACKAGE_TYPE_CHOICES = [
        ('Padrão', 'Padrão'),
        ('Promocional', 'Promocional')
    ]
    
    SHOW_TO_CHOICES = [
        ('Todos', 'Todos'),
        ('Comum', 'Comum'),
        ('Craque', 'Craque')
    ]

    name = models.CharField(max_length=255, verbose_name='Nome')
    plan = models.CharField(max_length=50, verbose_name='Plano')
    billing_cycle = models.CharField(
        max_length=20,
        choices=BILLING_CYCLE_CHOICES,
        verbose_name='Ciclo de Cobrança'
    )
    image = models.ImageField(upload_to='plans/', null=True, blank=True, verbose_name='Imagem')
    enabled = models.BooleanField(default=True, verbose_name='Ativo')
    package_type = models.CharField(
        max_length=20,
        choices=PACKAGE_TYPE_CHOICES,
        verbose_name='Tipo do Pacote'
    )
    label = models.CharField(max_length=50, null=True, blank=True, verbose_name='Etiqueta')
    color_text_label = models.CharField(max_length=7, default='#FFFFFF', verbose_name='Cor do Texto da Etiqueta')
    color_background_label = models.CharField(max_length=7, default='#CC000C', verbose_name='Cor de Fundo da Etiqueta')
    full_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço Padrão')
    promotional_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Preço Promocional')
    color_text_billing_cycle = models.CharField(max_length=7, default='#192639', verbose_name='Cor do Texto do Ciclo')
    show_to = models.CharField(
        max_length=20,
        choices=SHOW_TO_CHOICES,
        default='Todos',
        verbose_name='Exibir Para'
    )
    start_date = models.DateTimeField(null=True, blank=True, verbose_name='Data de Início')
    end_date = models.DateTimeField(null=True, blank=True, verbose_name='Data de Término')
    android_product_code = models.CharField(max_length=100, null=True, blank=True, verbose_name='Código do Produto (Android)')
    apple_product_code = models.CharField(max_length=100, null=True, blank=True, verbose_name='Código do Produto (Apple)')
    gateway_product_code = models.CharField(max_length=100, null=True, blank=True, verbose_name='Código do Produto (Gateway)')
    promotional_price_validity = models.IntegerField(null=True, blank=True, verbose_name='Validade do Preço Promocional')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        db_table = 'plans'
        verbose_name = 'Plano'
        verbose_name_plural = 'Planos'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def clean(self):
        # Validações personalizadas
        errors = {}
        
        # Validação do tipo de pacote e etiqueta
        if self.package_type == 'Promocional' and not self.label:
            errors['label'] = 'A etiqueta é obrigatória para pacotes promocionais.'
        
        # Validação do preço promocional
        if self.promotional_price is not None:
            if self.promotional_price <= 0:
                errors['promotional_price'] = 'O preço promocional deve ser maior que zero.'
            if self.promotional_price >= self.full_price:
                errors['promotional_price'] = 'O preço promocional deve ser menor que o preço padrão. Por favor, verifique os valores informados.'
        
        # Validação das datas para pacotes promocionais
        if self.package_type == 'Promocional':
            if not self.start_date:
                errors['start_date'] = 'A data de início é obrigatória para pacotes promocionais.'
            if not self.end_date:
                errors['end_date'] = 'A data de término é obrigatória para pacotes promocionais.'
        
        # Validação geral das datas
        if self.start_date and self.end_date and self.start_date > self.end_date:
            errors['start_date'] = 'A data de início não pode ser posterior à data de término.'
            errors['end_date'] = 'A data de término não pode ser anterior à data de início.'
        
        # Validação das cores
        for field in ['color_text_label', 'color_background_label', 'color_text_billing_cycle']:
            color = getattr(self, field)
            # Verifica se é uma cor no formato rgba
            if color and len(color) > 7:
                # Tenta converter para o formato hexadecimal
                try:
                    # Extrai os valores RGB do formato rgba
                    import re
                    rgba_match = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*[\d.]+)?\)', color)
                    if rgba_match:
                        r, g, b = map(int, rgba_match.groups())
                        # Converte para hexadecimal
                        hex_color = f'#{r:02x}{g:02x}{b:02x}'.upper()
                        # Atualiza o valor do campo
                        setattr(self, field, hex_color)
                    else:
                        errors[field] = 'Cor inválida. Use o formato hexadecimal (#RRGGBB).'
                except Exception:
                    errors[field] = 'Cor inválida. Use o formato hexadecimal (#RRGGBB).'
            elif not color.startswith('#') or len(color) != 7 or not all(c in '0123456789ABCDEFabcdef' for c in color[1:]):
                errors[field] = 'Cor inválida. Use o formato hexadecimal (#RRGGBB).'
        
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Garante que as cores estejam em maiúsculas
        self.color_text_label = self.color_text_label.upper()
        self.color_background_label = self.color_background_label.upper()
        self.color_text_billing_cycle = self.color_text_billing_cycle.upper()
        
        # Chama a validação
        self.full_clean()
        
        super().save(*args, **kwargs)

    def is_valid_period(self):
        """
        Verifica se o plano está dentro do período válido de exibição
        """
        now = timezone.now()
        if self.start_date and self.end_date:
            return self.start_date <= now <= self.end_date
        elif self.start_date:
            return self.start_date <= now
        elif self.end_date:
            return now <= self.end_date
        return True

    def get_final_price(self):
        """
        Retorna o preço final do plano (promocional se disponível, senão o preço padrão)
        """
        if self.promotional_price and self.is_valid_period():
            return self.promotional_price
        return self.full_price

# Futligas
class ClassicLeague(models.Model):
    name = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'classic_leagues'

class Player(models.Model):
    name = models.CharField(max_length=255)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'players'

# Locais
class Continent(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Continente'
        verbose_name_plural = 'Continentes'
        ordering = ['name']

    def __str__(self):
        return self.name

    def can_delete(self):
        """
        Verifica se o continente pode ser excluído.
        Retorna False se houver países ou campeonatos vinculados.
        """
        return not (self.country_set.exists() or Championship.objects.filter(continent=self).exists())

    def get_related_data(self):
        """
        Retorna dados relacionados ao continente
        """
        related_data = {
            'countries': self.country_set.order_by('name').all(),
            'championships': Championship.objects.filter(continent=self).order_by('name')
        }
        return related_data

class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    continent = models.ForeignKey(Continent, on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'País'
        verbose_name_plural = 'Países'
        ordering = ['name']

    def __str__(self):
        return self.name

    def can_delete(self):
        """
        Verifica se o país pode ser excluído checando suas vinculações
        """
        return not (self.state_set.exists() or Championship.objects.filter(country=self).exists())

    def get_related_data(self):
        """
        Retorna dados relacionados ao país
        """
        return {
            'states': self.state_set.order_by('name').all(),
            'championships': Championship.objects.filter(country=self).order_by('name'),
            'teams': self.team_set.order_by('name').all()
        }

class State(models.Model):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'
        ordering = ['name']
        unique_together = ['name', 'country']  # Nome único por país

    def __str__(self):
        return f"{self.name} - {self.country.name}"

# Configurações
class Administrator(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_root = models.BooleanField(default=False)

    class Meta:
        db_table = 'administrators'
        verbose_name = 'Administrador'
        verbose_name_plural = 'Administradores'

    def __str__(self):
        return self.name

class StandardLeague(models.Model):
    """
    Entidade que representa uma Futliga Clássica (Padrão).
    """
    name = models.CharField(max_length=255, verbose_name='Nome')
    image = models.ImageField(upload_to='futligas/standard/', null=True, blank=True, verbose_name='Imagem')
    award_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Diária'),
            ('weekly', 'Semanal'),
            ('monthly', 'Mensal')
        ],
        verbose_name='Frequência de Premiação'
    )
    weekday = models.IntegerField(
        choices=[
            (0, 'Segunda'),
            (1, 'Terça'),
            (2, 'Quarta'),
            (3, 'Quinta'),
            (4, 'Sexta'),
            (5, 'Sábado'),
            (6, 'Domingo')
        ],
        verbose_name='Dia da Semana'
    )
    plans = models.ManyToManyField('Plan', verbose_name='Planos')
    players = models.IntegerField(verbose_name='Quantidade de Participantes')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        db_table = 'standard_leagues'
        verbose_name = 'Futliga Padrão'
        verbose_name_plural = 'Futligas Padrão'
        ordering = ['name']

    def __str__(self):
        return self.name

class StandardLeaguePrize(models.Model):
    """
    Entidade que representa os prêmios de uma Futliga Padrão.
    """
    league = models.ForeignKey(StandardLeague, on_delete=models.CASCADE, related_name='prizes', verbose_name='Futliga')
    position = models.IntegerField(verbose_name='Posição')
    image = models.ImageField(upload_to='futligas/prizes/', null=True, blank=True, verbose_name='Imagem')
    prize = models.CharField(max_length=255, verbose_name='Prêmio')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'standard_league_prizes'
        verbose_name = 'Prêmio de Futliga Padrão'
        verbose_name_plural = 'Prêmios de Futliga Padrão'
        ordering = ['position']
        unique_together = ['league', 'position']

    def __str__(self):
        return f"{self.league.name} - {self.position}º Lugar"

def custom_league_image_path(instance, filename):
    # Cria o diretório se não existir
    upload_path = 'futligas/custom'
    full_path = os.path.join(settings.MEDIA_ROOT, upload_path)
    os.makedirs(full_path, exist_ok=True)
    # Retorna o caminho do arquivo
    return os.path.join(upload_path, filename)

class CustomLeague(models.Model):
    """
    Entidade que representa uma Futliga de Jogadores (Personalizada).
    """
    name = models.CharField(max_length=255, verbose_name='Nome')
    image = models.ImageField(upload_to=custom_league_image_path, null=True, blank=True, verbose_name='Imagem')
    privacy = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Pública'),
            ('private', 'Privada')
        ],
        default='public',
        verbose_name='Privacidade'
    )
    players = models.IntegerField(verbose_name='Quantidade de Participantes')
    premium_players = models.IntegerField(verbose_name='Quantidade de Craques')
    owner_premium = models.BooleanField(default=False, verbose_name='Dono Craque')
    league_link = models.URLField(null=True, blank=True, verbose_name='Link do Grupo')
    level = models.IntegerField(
        choices=[
            (1, 'Nível 1'),
            (2, 'Nível 2'),
            (3, 'Nível 3')
        ],
        default=1,
        verbose_name='Nível'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        db_table = 'custom_leagues'
        verbose_name = 'Futliga Personalizada'
        verbose_name_plural = 'Futligas Personalizadas'
        ordering = ['name']

    def __str__(self):
        return self.name

class CustomLeagueLevel(models.Model):
    """
    Entidade que representa um nível de configuração para Futligas Personalizadas.
    """
    name = models.CharField(max_length=255, verbose_name='Nome')
    image = models.ImageField(upload_to='futligas/levels/', null=True, blank=True, verbose_name='Imagem')
    players = models.IntegerField(verbose_name='Quantidade de Participantes')
    premium_players = models.IntegerField(verbose_name='Quantidade de Craques')
    owner_premium = models.BooleanField(default=False, verbose_name='Dono Craque')
    order = models.IntegerField(default=0, verbose_name='Ordem')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        db_table = 'custom_league_levels'
        verbose_name = 'Nível de Futliga'
        verbose_name_plural = 'Níveis de Futliga'
        ordering = ['order']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Se não houver ordem definida, coloca como último
        if not self.order:
            last_order = CustomLeagueLevel.objects.aggregate(models.Max('order'))['order__max']
            self.order = (last_order or 0) + 1
        super().save(*args, **kwargs)

class CustomLeaguePrizeValue(models.Model):
    """
    Entidade que representa o valor de um prêmio para um nível específico.
    """
    prize = models.ForeignKey('CustomLeaguePrize', on_delete=models.CASCADE, related_name='values', verbose_name='Prêmio')
    level = models.ForeignKey('CustomLeagueLevel', on_delete=models.CASCADE, related_name='prize_values', verbose_name='Nível')
    value = models.IntegerField(verbose_name='Valor')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'custom_league_prize_values'
        verbose_name = 'Valor de Prêmio por Nível'
        verbose_name_plural = 'Valores de Prêmios por Nível'
        unique_together = ['prize', 'level']

    def __str__(self):
        return f'{self.prize} - {self.level}: {self.value}'

class CustomLeaguePrize(models.Model):
    """
    Entidade que representa os prêmios de uma Futliga Personalizada.
    """
    league = models.ForeignKey(CustomLeague, on_delete=models.CASCADE, related_name='prizes', verbose_name='Futliga')
    position = models.IntegerField(verbose_name='Posição')
    image = models.ImageField(upload_to='futligas/prizes/', null=True, blank=True, verbose_name='Imagem')
    prize = models.CharField(max_length=255, verbose_name='Prêmio')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'custom_league_prizes'
        verbose_name = 'Prêmio de Futliga Personalizada'
        verbose_name_plural = 'Prêmios de Futliga Personalizada'
        ordering = ['position']
        unique_together = ['league', 'position']

    def __str__(self):
        return f'{self.league.name} - {self.position}º Lugar'

    def set_valor_por_nivel(self, nivel, valor):
        """
        Define o valor do prêmio para um nível específico.
        """
        CustomLeaguePrizeValue.objects.update_or_create(
            prize=self,
            level=nivel,
            defaults={'value': valor}
        )

    def get_valor_por_nivel(self, nivel):
        """
        Retorna o valor do prêmio para um nível específico.
        """
        try:
            return self.values.get(level=nivel).value
        except CustomLeaguePrizeValue.DoesNotExist:
            return 0

class LeagueInvitation(models.Model):
    """
    Entidade que representa os convites para Futligas.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='league_invitations',
        verbose_name='Usuário'
    )
    invitations = models.IntegerField(default=0, verbose_name='Quantidade de Convites')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'league_invitations'
        verbose_name = 'Convite de Futliga'
        verbose_name_plural = 'Convites de Futliga'

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} - {self.invitations} convites'

class Parameters(models.Model):
    """
    Entidade que representa os parâmetros do sistema.
    """
    # Login - 7 dias
    day1_coins = models.IntegerField(verbose_name='Dia 1', default=0)
    day2_coins = models.IntegerField(verbose_name='Dia 2', default=0)
    day3_coins = models.IntegerField(verbose_name='Dia 3', default=0)
    day4_coins = models.IntegerField(verbose_name='Dia 4', default=0)
    day5_coins = models.IntegerField(verbose_name='Dia 5', default=0)
    day6_coins = models.IntegerField(verbose_name='Dia 6', default=0)
    day7_coins = models.IntegerField(verbose_name='Dia 7', default=0)
    
    # Premiação
    reward_time = models.TimeField(verbose_name='Horário Premiação', null=True, blank=True)
    
    # Premiação Semanal
    weekly_award_day = models.CharField(verbose_name='Dia da Premiação Semanal', max_length=20, null=True, blank=True)
    weekly_award_time = models.TimeField(verbose_name='Horário da Premiação Semanal', null=True, blank=True)
    
    # Premiação por Temporada
    season_award_month = models.CharField(verbose_name='Mês da Premiação por Temporada', max_length=20, null=True, blank=True)
    season_award_day = models.CharField(verbose_name='Dia da Premiação por Temporada', max_length=20, null=True, blank=True)
    season_award_time = models.TimeField(verbose_name='Horário da Premiação por Temporada', null=True, blank=True)
    
    # Recompensas
    watch_video_coins = models.IntegerField(verbose_name='Futcoins por Vídeo', default=0)
    hit_prediction_coins = models.IntegerField(verbose_name='Futcoins por Acerto', default=0)
    following_tiktok_coins = models.IntegerField(verbose_name='Futcoins por Seguir TikTok', default=0)
    premium_upgrade_coins = models.IntegerField(verbose_name='Futcoins por Upgrade Premium', default=0)
    consecutive_days_coins = models.IntegerField(verbose_name='Futcoins por Dias Seguidos', default=0)
    
    # Limites
    daily_videos_limit = models.IntegerField(verbose_name='Limite de Vídeos Diários', default=0)
    standard_leagues_participation = models.IntegerField(verbose_name='Participação em Futligas (Comum)', default=0)
    ace_leagues_participation = models.IntegerField(verbose_name='Participação em Futligas (Craque)', default=0)
    
    # Outros
    contact_email = models.EmailField(verbose_name='Email de Contato', null=True, blank=True)
    api_key = models.CharField(verbose_name='Chave de API (Tiny)', max_length=255, null=True, blank=True)
    
    # Redes Sociais
    facebook = models.URLField(verbose_name='Facebook', null=True, blank=True)
    kwai = models.URLField(verbose_name='Kwai', null=True, blank=True)
    instagram = models.URLField(verbose_name='Instagram', null=True, blank=True)
    tiktok = models.URLField(verbose_name='TikTok', null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'parameters'
        verbose_name = 'Parâmetro'
        verbose_name_plural = 'Parâmetros'

    def __str__(self):
        return 'Parâmetros do Sistema'

class Terms(models.Model):
    """
    Entidade que representa os termos de uso do sistema.
    """
    description = models.TextField(verbose_name='Descrição')
    notify_changes = models.BooleanField(default=False, verbose_name='Notificar Mudanças')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'terms'
        verbose_name = 'Termo'
        verbose_name_plural = 'Termos'

    def __str__(self):
        return f'Termos de Uso - {self.created_at.strftime("%d/%m/%Y")}'

class Notifications(models.Model):
    """
    Entidade que representa as notificações do sistema.
    """
    NOTIFICATION_TYPE_CHOICES = (
        ('generic', 'Geral'),
        ('package_coins', 'Pacote Futcoins'),
        ('package_plan', 'Pacote Plano'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pendente'),
        ('sent', 'Enviado'),
        ('not_sent', 'Não Enviado'),
    )

    title = models.CharField(max_length=100, verbose_name='Título')
    message = models.TextField(verbose_name='Mensagem')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES, verbose_name='Tipo')
    package = models.ForeignKey(FutcoinPackage, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Pacote')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Plano')
    send_at = models.DateTimeField(null=True, blank=True, verbose_name='Data de Envio')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name='Status')
    error_message = models.TextField(null=True, blank=True, verbose_name='Mensagem de Erro')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Data de Atualização')

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-created_at']
