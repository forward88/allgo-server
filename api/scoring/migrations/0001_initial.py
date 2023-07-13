# Generated by Django 3.2.8 on 2022-01-18 09:30

import api.scoring.models.achievement
from django.db import migrations, models
import pathlib


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Achievement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('color_image', api.scoring.models.achievement.RelativeFilePathModelField(match='.*.png', max_length=1024, path=api.scoring.models.achievement.color_asset_path)),
                ('grey_image', api.scoring.models.achievement.RelativeFilePathModelField(match='.*.png', max_length=1024, path=api.scoring.models.achievement.grey_asset_path)),
                ('order_rank', models.PositiveSmallIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='UserXPLevel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.PositiveIntegerField()),
                ('xp_threshold', models.PositiveIntegerField(verbose_name='XP Threshold')),
            ],
            options={
                'verbose_name': 'User XP Level',
            },
        ),
    ]
