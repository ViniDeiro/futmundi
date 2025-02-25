from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrativo', '0005_notifications'),
    ]

    operations = [
        migrations.AddField(
            model_name='notifications',
            name='package',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name='notifications',
                to='administrativo.futcoinpackage',
                verbose_name='Pacote'
            ),
        ),
    ] 