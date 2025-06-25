from django.db import models

class PrevisaoBTC(models.Model):
    data = models.DateField(unique=True)
    preco_previsto = models.FloatField()
    modelo = models.CharField(max_length=50, default='LSTM')  # NOVO
    paridade = models.CharField(max_length=10, default='BTC-USD')  # NOVO

    def __str__(self):
        return f"{self.data} - ${self.preco_previsto:,.2f}"
