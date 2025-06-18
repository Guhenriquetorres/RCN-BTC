from rest_framework import serializers
from .models import PrevisaoBTC

class PrevisaoBTCSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrevisaoBTC
        fields = '__all__'
