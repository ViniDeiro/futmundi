from django.db import models
from django.utils import timezone

class User(models.Model):
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
    
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
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
    is_active = models.BooleanField(default=True)
    is_star = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.name

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
        if not kwargs.get('update_fields'):
            self.update_points()

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
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictions')
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
        unique_together = ['user', 'match']  # Um palpite por usuário por partida

    def __str__(self):
        return f"{self.user.name} - {self.match}"

    def save(self, *args, **kwargs):
        # Calcula o total de gastos
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
    image = models.CharField(max_length=255, null=True, blank=True)  # Caminho da imagem no storage
    is_national_team = models.BooleanField(default=False)
    continent = models.ForeignKey('Continent', on_delete=models.PROTECT, null=True, blank=True)
    country = models.ForeignKey('Country', on_delete=models.PROTECT, null=True, blank=True)
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
        return not Championship.objects.filter(teams=self).exists()

    def get_related_data(self):
        """
        Retorna dados relacionados ao time.
        """
        return {
            'championships': list(Championship.objects.filter(teams=self).values('id', 'name')),
            'players': list(self.player_set.values('id', 'name'))
        }

    def get_image_url(self):
        """
        Retorna a URL da imagem do time ou a URL do escudo genérico.
        """
        if self.image:
            return self.image
        return 'static/administrativo/img/generic-shield.png'

    def save(self, *args, **kwargs):
        # Se o país não tem estados, garante que state seja None
        if not self.country.state_set.exists():
            self.state = None
        super().save(*args, **kwargs)

# Pacotes
class FutcoinPackage(models.Model):
    name = models.CharField(max_length=255)
    amount = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'futcoin_packages'

class Plan(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'plans'

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
        ordering = ['name']  # Ordenação padrão por nome

    def __str__(self):
        return self.name

    def can_delete(self):
        # Verifica apenas se existem países relacionados
        return not self.country_set.exists()

    def get_related_data(self):
        related_data = []
        countries = self.country_set.all()
        if countries:
            related_data.append(f'Países: {", ".join([country.name for country in countries])}')
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
        return not self.state_set.exists()

    def get_related_data(self):
        """
        Retorna dados relacionados ao país
        """
        return {
            'states': self.state_set.order_by('name').all()
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
class Parameter(models.Model):
    key = models.CharField(max_length=255, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'parameters'

class Term(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    version = models.CharField(max_length=10)
    active_from = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'terms'

class Notification(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = 'notifications'

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
