# Generated by Django 4.2.17 on 2025-02-24 03:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrativo', '0007_update_plan_model'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Plano',
        ),
        migrations.AlterModelOptions(
            name='plan',
            options={'verbose_name': 'Plan', 'verbose_name_plural': 'Plans'},
        ),
        migrations.AddField(
            model_name='plan',
            name='android_product_code',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='plan',
            name='apple_product_code',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
