import requests

# Suponha que `df_future` tem as previsões
# df_future deve ter um índice de data e uma coluna "BTC_Previsto"
url = "http://127.0.0.1:8000/api/previsoes/"  # ou endpoint da sua API em produção

for data, row in df_future.iterrows():
    payload = {
        "data": data.strftime('%Y-%m-%d'),
        "preco_previsto": row['BTC_Previsto']
    }
    response = requests.post(url, json=payload)
    print(data.date(), response.status_code, response.text)
# Certifique-se de que o servidor da API esteja rodando antes de executar este script
# Você pode precisar instalar a biblioteca requests se ainda não estiver instalada:     