# Generated by Django 2.2.23 on 2021-05-26 13:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blockfunder', '0007_auto_20210525_1923'),
    ]

    operations = [
        migrations.AddField(
            model_name='program',
            name='buy_enable',
            field=models.BooleanField(default=True),
        ),
    ]
