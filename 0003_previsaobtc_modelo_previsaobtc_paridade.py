# Generated by Django 5.2.2 on 2025-06-25 16:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_btc', '0002_remove_previsaobtc_modelo_alter_previsaobtc_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='previsaobtc',
            name='modelo',
            field=models.CharField(default='LSTM', max_length=50),
        ),
        migrations.AddField(
            model_name='previsaobtc',
            name='paridade',
            field=models.CharField(default='BTC-USD', max_length=10),
        ),
    ]
