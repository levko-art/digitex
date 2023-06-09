# Generated by Django 2.2.20 on 2021-05-21 18:22

import django.core.validators
from django.db import migrations, models
import exchange.fields


class Migration(migrations.Migration):

    dependencies = [
        ('blockfunder', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProgramLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('hyperlink', models.CharField(max_length=512)),
            ],
        ),
        migrations.AddField(
            model_name='program',
            name='description',
            field=models.CharField(blank=True, max_length=2048),
        ),
        migrations.AddField(
            model_name='program',
            name='phase',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='program',
            name='phase_description',
            field=models.CharField(blank=True, max_length=2048),
        ),
        migrations.AddField(
            model_name='program',
            name='phase_info',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='transaction',
            name='buy_out',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='wallet',
            name='total_rewarded',
            field=exchange.fields.FixedDecimalField(default=0, validators=[django.core.validators.MinValueValidator(limit_value=0)]),
        ),
        migrations.AddField(
            model_name='program',
            name='links',
            field=models.ManyToManyField(blank=True, to='blockfunder.ProgramLink'),
        ),
    ]
