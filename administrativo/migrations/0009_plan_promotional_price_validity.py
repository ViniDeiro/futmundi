# Generated by Django 4.2.17 on 2025-02-24 04:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrativo', '0008_delete_plano_alter_plan_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='promotional_price_validity',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
