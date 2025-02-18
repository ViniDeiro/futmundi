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

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Garante que valores não sejam negativos
        self.boost = max(0, self.boost)
        self.futcoins = max(0, self.futcoins)
        super().save(*args, **kwargs)

class Championship(models.Model):
    name = models.CharField(max_length=255)
    scope = models.ForeignKey(Scope, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'championships'

class Template(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'templates'

class Team(models.Model):
    name = models.CharField(max_length=255)
    championship = models.ForeignKey(Championship, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'teams'

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
    nome = models.CharField(max_length=100, null=True, blank=True)
    data_criacao = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Continente'
        verbose_name_plural = 'Continentes'

    def __str__(self):
        return self.nome or ''

class Country(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=2)
    continent = models.ForeignKey(Continent, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'countries'

class State(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=2)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'states'

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
