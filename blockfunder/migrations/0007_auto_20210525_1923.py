# Generated by Django 2.2.20 on 2021-05-25 19:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blockfunder', '0006_auto_20210524_1243'),
    ]

    operations = [
        migrations.AddField(
            model_name='program',
            name='finish_type',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='program',
            name='lock_type',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
