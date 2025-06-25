from rest_framework import serializers
from .models import PrevisaoBTC

class PrevisaoBTCSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrevisaoBTC
        fields = ['data', 'preco_previsto']  # Sem 'modelo' se ele não existir no model
         