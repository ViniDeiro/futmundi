# Generated by Django 4.2.17 on 2025-02-26 08:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('administrativo', '0009_classicleague_created_at'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='classicleague',
            name='created_at',
        ),
    ]
