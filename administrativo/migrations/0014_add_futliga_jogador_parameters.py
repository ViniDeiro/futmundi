from django.db import migrations, models

def create_futliga_parameters(apps, schema_editor):
    Parameters = apps.get_model('administrativo', 'Parameters')
    
    # Cria os parâmetros se não existirem
    Parameters.objects.get_or_create(
        key='futliga_jogador_dia_semanal',
        defaults={'value': 'Segunda'}
    )
    Parameters.objects.get_or_create(
        key='futliga_jogador_horario_semanal',
        defaults={'value': '12:00'}
    )
    Parameters.objects.get_or_create(
        key='futliga_jogador_mes_temporada',
        defaults={'value': 'Janeiro'}
    )
    Parameters.objects.get_or_create(
        key='futliga_jogador_dia_temporada',
        defaults={'value': '1'}
    )
    Parameters.objects.get_or_create(
        key='futliga_jogador_horario_temporada',
        defaults={'value': '12:00'}
    )

def remove_futliga_parameters(apps, schema_editor):
    Parameters = apps.get_model('administrativo', 'Parameters')
    Parameters.objects.filter(
        key__in=[
            'futliga_jogador_dia_semanal',
            'futliga_jogador_horario_semanal',
            'futliga_jogador_mes_temporada',
            'futliga_jogador_dia_temporada',
            'futliga_jogador_horario_temporada'
        ]
    ).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('administrativo', '0013_alter_customleague_image'),  # Ajuste para a última migração existente
    ]

    operations = [
        migrations.AddField(
            model_name='parameters',
            name='key',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='parameters',
            name='value',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.RunPython(create_futliga_parameters, remove_futliga_parameters),
    ] 