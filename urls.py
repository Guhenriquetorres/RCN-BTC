from django.urls import path 
from .views import buscar_previsao_html
from rest_framework.routers import DefaultRouter
from .views import PrevisaoBTCViewSet
from api_btc import views

router = DefaultRouter()
router.register(r'previsoes', PrevisaoBTCViewSet)

urlpatterns = [
    path('previsao/', views.pagina_previsao, name='pagina_previsao'), 
    path('buscar_previsao/', views.buscar_previsao_html, name='buscar_previsao_html'),
    path('api/previsoes/buscar_por_data/', views.buscar_por_data_json, name='buscar_por_data_json'),
]

urlpatterns += router.urls
