from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render
from django.http import JsonResponse
from .models import PrevisaoBTC
from .serializers import PrevisaoBTCSerializer
from .modelos.modelo_lstm import prever_btc, prever_btc_dias_a_frente
from datetime import datetime, timedelta
import yfinance as yf

# -------------------------------
# ViewSet da API (DRF)
# -------------------------------
class PrevisaoBTCViewSet(viewsets.ModelViewSet):
    queryset = PrevisaoBTC.objects.all()
    serializer_class = PrevisaoBTCSerializer

    @action(detail=False, methods=['get'], url_path='buscar_por_data')
    def buscar_por_data(self, request):
        data_str = request.query_params.get('data')
        if not data_str:
            return Response({'erro': 'Data não enviada'}, status=400)

        data_solicitada = datetime.strptime(data_str, "%Y-%m-%d").date()
        preco_real = None

        # Se a data for anterior a hoje, tenta buscar o valor real
        if data_solicitada < datetime.today().date():
            try:
                historico = yf.download(
                    "BTC-USD",
                    start=data_str,
                    end=(data_solicitada + timedelta(days=1)).strftime("%Y-%m-%d")
                )
                if not historico.empty:
                    preco_real = round(float(historico['Close'].iloc[0]), 2)
            except Exception as e:
                print("Erro ao buscar valor real:", e)

        try:
            previsao = PrevisaoBTC.objects.get(data=data_solicitada)
            serializer = self.get_serializer(previsao)
            data = serializer.data
            data['preco_real'] = preco_real
            return Response(data)
        except PrevisaoBTC.DoesNotExist:
            pass  # segue para prever

        try:
            ultima_data_disponivel = PrevisaoBTC.objects.order_by('-data').first()
            base = ultima_data_disponivel.data if ultima_data_disponivel else datetime(2024, 1, 1).date()
            dias_para_prever = (data_solicitada - base).days

            if dias_para_prever <= 0:
                return Response({'erro': 'Data inválida ou já prevista'}, status=400)

            previsoes = prever_btc_dias_a_frente(dias=dias_para_prever)
            for i, valor in enumerate(previsoes):
                data_prevista = base + timedelta(days=i + 1)
                PrevisaoBTC.objects.create(
                    data=data_prevista,
                    preco_previsto=float(valor),
                    modelo='LSTM',
                    paridade='BTC-USD'
                )

            previsao = PrevisaoBTC.objects.get(data=data_solicitada)
            serializer = self.get_serializer(previsao)
            data = serializer.data
            data['preco_real'] = preco_real
            return Response(data)

        except Exception as e:
            return Response({'erro': str(e)}, status=500)

# -------------------------------
# Página de visualização HTML
# -------------------------------
def pagina_previsao(request):
    return render(request, 'previsao.html')


def buscar_previsao_html(request):
    if request.method == 'GET':
        return render(request, 'buscar_previsao.html')

    elif request.method == 'POST':
        dias = int(request.POST.get('dias', 1))
        previsoes = prever_btc_dias_a_frente(dias)
        return render(request, 'buscar_previsao.html', {'previsoes': previsoes})


# -------------------------------
# API JSON usada pelo Frontend
# -------------------------------
def buscar_por_data_json(request):
    data_str = request.GET.get('data')
    if not data_str:
        return JsonResponse({'erro': 'Data não fornecida.'})

    try:
        data_escolhida = datetime.strptime(data_str, "%Y-%m-%d").date()
        data_base = datetime(2024, 1, 1).date()
        dias_a_frente = (data_escolhida - data_base).days
        preco_real = None

        if data_escolhida < datetime.today().date():
            try:
                historico = yf.download(
                    "BTC-USD",
                    start=data_str,
                    end=(data_escolhida + timedelta(days=1)).strftime("%Y-%m-%d")
                )
                if not historico.empty:
                    preco_real = round(float(historico['Close'].iloc[0]), 2)
            except Exception as e:
                print("Erro ao buscar valor real:", e)

        previsao = PrevisaoBTC.objects.filter(data=data_escolhida).first()
        if previsao:
            return JsonResponse({
                'data': previsao.data.strftime('%Y-%m-%d'),
                'preco_previsto': round(previsao.preco_previsto, 2),
                'modelo': previsao.modelo,
                'paridade': previsao.paridade,
                'preco_real': preco_real
            })

        previsoes = prever_btc_dias_a_frente(dias=dias_a_frente)
        valor_previsto = float(previsoes[-1])

        nova_previsao = PrevisaoBTC.objects.create(
            data=data_escolhida,
            preco_previsto=valor_previsto,
            modelo='LSTM',
            paridade='BTC-USD'
        )

        return JsonResponse({
            'data': data_str,
            'preco_previsto': round(valor_previsto, 2),
            'modelo': 'LSTM',
            'paridade': 'BTC-USD',
            'preco_real': preco_real
        })

    except Exception as e:
        return JsonResponse({'erro': f'Erro ao prever: {str(e)}'})
