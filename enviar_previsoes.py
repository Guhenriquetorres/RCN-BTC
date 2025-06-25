import requests
import pandas as pd
from datetime import datetime, timedelta

# Exemplo fictício de DataFrame (substitua pelo seu)
start_date = datetime.today()
dates = [start_date + timedelta(days=i) for i in range(30)]
precos = [75000 + i * 100 for i in range(30)]

df_future = pd.DataFrame({
    'data': dates,
    'BTC_Previsto': precos
})
df_future.set_index('data', inplace=True)

url = "http://127.0.0.1:8000/api/previsoes/"

for data, row in df_future.iterrows():
    payload = {
        "data": data.strftime('%Y-%m-%d'),
        "preco_previsto": row['BTC_Previsto']
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"{data.date()} → {response.status_code}: OK")
    except requests.exceptions.HTTPError as e:
        print(f"Erro HTTP em {data.date()}: {e} - {response.text}")
    except Exception as e:
        print(f"Erro geral em {data.date()}: {e}")
