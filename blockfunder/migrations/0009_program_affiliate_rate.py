# Generated by Django 2.2.23 on 2021-06-01 10:44

from django.db import migrations
import exchange.fields


class Migration(migrations.Migration):

    dependencies = [
        ('blockfunder', '0008_program_buy_enable'),
    ]

    operations = [
        migrations.AddField(
            model_name='program',
            name='affiliate_rate',
            field=exchange.fields.FixedDecimalField(default=0.0),
        ),
    ]
