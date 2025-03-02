import os
import django
import sys

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'futmundi.settings')
django.setup()

from administrativo.models import Parameters
from django.db.models import Q

def create_or_update_parameters():
    # Parâmetros necessários para futligas jogadores
    futliga_parameters = {
        'futliga_jogador_dia_semanal': 'Segunda',
        'futliga_jogador_horario_semanal': '12:00',
        'futliga_jogador_mes_temporada': 'Janeiro',
        'futliga_jogador_dia_temporada': '1',
        'futliga_jogador_horario_temporada': '12:00'
    }
    
    for key, default_value in futliga_parameters.items():
        param, created = Parameters.objects.get_or_create(
            key=key,
            defaults={'value': default_value}
        )
        
        if created:
            print(f"Parâmetro '{key}' criado com valor '{default_value}'")
        else:
            print(f"Parâmetro '{key}' já existe com valor '{param.value}'")

def check_parameters():
    # Verifica se os parâmetros existem
    print("\nParâmetros existentes:")
    params = Parameters.objects.filter(
        Q(key__startswith='futliga_jogador')
    )
    
    if not params.exists():
        print("Nenhum parâmetro de futliga_jogador encontrado!")
    else:
        for param in params:
            print(f"- {param.key}: {param.value}")

def main():
    print("Verificando e criando parâmetros para futligas jogadores...\n")
    create_or_update_parameters()
    check_parameters()
    print("\nOperação concluída!")

if __name__ == "__main__":
    main() 