from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('administrativo', '0004_auto_20250225_0132'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notifications',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Título')),
                ('message', models.TextField(verbose_name='Mensagem')),
                ('notification_type', models.CharField(
                    choices=[
                        ('generic', 'Geral'),
                        ('package_plan', 'Pacote Plano'),
                        ('package_coins', 'Pacote Futcoin'),
                    ],
                    default='generic',
                    max_length=20,
                    verbose_name='Tipo'
                )),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pendente'),
                        ('sent', 'Enviado'),
                        ('not_sent', 'Não Enviado'),
                    ],
                    default='pending',
                    max_length=20,
                    verbose_name='Status'
                )),
                ('send_at', models.DateTimeField(blank=True, null=True, verbose_name='Data de Envio')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Data de Criação')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Data de Atualização')),
            ],
            options={
                'verbose_name': 'Notificação',
                'verbose_name_plural': 'Notificações',
                'db_table': 'notifications',
                'ordering': ['-created_at'],
            },
        ),
    ] 