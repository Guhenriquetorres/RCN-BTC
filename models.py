from django.db import models

class PrevisaoBTC(models.Model):
    data = models.DateField()
    preco_previsto = models.FloatField()
    modelo = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.data} - {self.modelo}"
