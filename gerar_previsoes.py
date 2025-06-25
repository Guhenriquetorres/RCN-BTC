import os
import sys
import django
import pandas as pd
import numpy as np
from datetime import timedelta
from keras.models import load_model
from joblib import load

# ====== Configuração do Django ======
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # RNC-BTC/
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# ====== Agora podemos importar o modelo do app ======
from api_btc.models import PrevisaoBTC
from django.conf import settings

# ====== Carregamento do modelo e scaler ======
model_path = os.path.join(settings.BASE_DIR, 'api_btc', 'modelos', 'modelo_lstm')
scaler_path = os.path.join(settings.BASE_DIR, 'modelos', 'scaler_y.pkl')

model = load_model(model_path)
scaler_y = load(scaler_path)

# ====== Carregando dados reais ======
import yfinance as yf
from fredapi import Fred
from sklearn.preprocessing import StandardScaler

btc = yf.download('BTC-USD', start='2015-01-01', end='2024-01-01')
sp500 = yf.download('^GSPC', start='2015-01-01', end='2024-01-01')
fed = Fred(api_key='f2aeb0f0a807498a62d1b0d4311a431c')
fed_funds = fed.get_series('FEDFUNDS', start='2015-01-01', end='2024-01-01')

btc = btc[['Close', 'Volume']].rename(columns={'Close': 'BTC_Close_BTC-USD', 'Volume': 'BTC_Volume_BTC-USD'})
sp500 = sp500[['Close', 'Volume']].rename(columns={'Close': 'SP500_Close_^GSPC', 'Volume': 'SP500_Volume_^GSPC'})
fed_funds = pd.DataFrame(fed_funds, columns=['FedFundsRate'])

all_dates = pd.date_range(start=btc.index.min(), end=btc.index.max(), freq='D')
btc = btc.reindex(all_dates)
sp500 = sp500.reindex(all_dates)
fed_funds = fed_funds.reindex(all_dates).interpolate().ffill().bfill()

merged = btc.merge(sp500, left_index=True, right_index=True)
merged = merged.merge(fed_funds, left_index=True, right_index=True)
merged = merged.dropna()

# ====== Escalamento e criação da sequência ======
numerical_cols = [
    'BTC_Close_BTC-USD',
    'SP500_Close_^GSPC',
    'FedFundsRate',
    'BTC_Volume_BTC-USD',
    'SP500_Volume_^GSPC'
]

scaler_X = StandardScaler()
merged_scaled = merged.copy()
merged_scaled[numerical_cols] = scaler_X.fit_transform(merged[numerical_cols])

# Última sequência de 60 timesteps
lookback = 60
last_sequence = merged_scaled[numerical_cols].values[-lookback:]

# Repetir a última sequência para 30 dias (mantendo os mesmos dados)
X_future = np.array([last_sequence for _ in range(30)])

# ====== Previsões ======
y_pred_scaled = model.predict(X_future)
y_pred = scaler_y.inverse_transform(y_pred_scaled)

# ====== Geração das datas futuras ======
ultima_data = merged.index[-1]
datas_futuras = pd.date_range(start=ultima_data + timedelta(days=1), periods=30)

# ====== Criação de DataFrame ======
df_future = pd.DataFrame({
    'data': datas_futuras,
    'preco_previsto': y_pred.flatten(),
    'modelo': 'LSTM',
    'paridade': 'BTC-USD'
})

# ====== Inserção ou atualização no banco ======
for _, row in df_future.iterrows():
    PrevisaoBTC.objects.update_or_create(
        data=row['data'],
        defaults={
            'preco_previsto': row['preco_previsto'],
            'modelo': row['modelo'],
            'paridade': row['paridade']
        }
    )

# ====== Log final ======
print(df_future)
print("✅ Previsões salvas com sucesso no banco!")