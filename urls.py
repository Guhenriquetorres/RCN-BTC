from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PrevisaoBTCViewSet
from django.contrib import admin
from django.urls import path, include

router = DefaultRouter()
router.register(r'previsoes', PrevisaoBTCViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api_btc.urls')),
]

