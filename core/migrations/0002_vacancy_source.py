# Generated by Django 4.2.19 on 2025-02-22 18:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='vacancy',
            name='source',
            field=models.TextField(blank=True, null=True, verbose_name='Vacancy Source'),
        ),
    ]
