from rest_framework import viewsets
from .models import PrevisaoBTC
from .serializers import PrevisaoBTCSerializer

class PrevisaoBTCViewSet(viewsets.ModelViewSet):
    queryset = PrevisaoBTC.objects.all()
    serializer_class = PrevisaoBTCSerializer
