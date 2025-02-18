from rest_framework import serializers
from .models import Scope, ScopeLevel

class ScopeLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScopeLevel
        fields = ['id', 'type', 'level', 'points', 'futcoins', 'is_active']

class ScopeSerializer(serializers.ModelSerializer):
    levels = ScopeLevelSerializer(many=True, read_only=True)
    
    class Meta:
        model = Scope
        fields = ['id', 'name', 'type', 'boost', 'futcoins', 'is_active', 'is_default', 'levels'] 