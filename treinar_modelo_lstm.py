import numpy as np
import pandas as pd
import os
import joblib
from keras.models import Sequential
from keras.layers import LSTM, Dense
from sklearn.preprocessing import StandardScaler
import yfinance as yf
from fredapi import Fred
from sklearn.metrics import mean_squared_error
from fredapi import Fred
from sklearn.metrics import r2_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ========== 1. Baixar e preparar dados ==========
# Fetch historical data
btc = yf.download('BTC-USD', start='2015-01-01', end='2024-01-01')
sp500 = yf.download('^GSPC', start='2015-01-01', end='2024-01-01')

# Extract closing prices and ensure indices are dates
btc_close = btc['Close']
sp500_close = sp500['Close']

btc_close.index = pd.to_datetime(btc_close.index)
sp500_close.index = pd.to_datetime(sp500_close.index)

"""**FEDERAL RESERVE**"""

# Fetch Federal Funds Rate data from FRED
fred = Fred(api_key='f2aeb0f0a807498a62d1b0d4311a431c')  # Replace with your valid FRED API key
fed_funds_rate = fred.get_series('FEDFUNDS', start='2015-01-01', end='2024-01-01')

# Ensure consistent datetime format
btc.index = btc.index.tz_localize(None)  # Remove timezone information
sp500.index = sp500.index.tz_localize(None)  # Remove timezone information
fed_funds_rate.index = fed_funds_rate.index.tz_localize(None)  # Remove timezone information

"""# **ETL DA COLUNA**"""

# Certifique-se de que cada conjunto de dados seja um DataFrame com 'Close' e 'Volume'
btc_close_volume = btc[['Close', 'Volume']].copy()  # Criar DataFrame com apenas as colunas necessárias
sp500_close_volume = sp500[['Close', 'Volume']].copy()  # Criar DataFrame com apenas as colunas necessárias
fed_funds_rate = pd.DataFrame(fed_funds_rate, columns=['FedFundsRate'])  # Garantir um DataFrame

# Renomear para evitar conflitos
btc_close_volume = btc_close_volume.rename(columns={'Close': 'BTC_Close', 'Volume': 'BTC_Volume'})
sp500_close_volume = sp500_close_volume.rename(columns={'Close': 'SP500_Close', 'Volume': 'SP500_Volume'})

# Garantir que os índices sejam datetime
btc_close_volume.index = pd.to_datetime(btc_close_volume.index).tz_localize(None)
sp500_close_volume.index = pd.to_datetime(sp500_close_volume.index).tz_localize(None)
fed_funds_rate.index = pd.to_datetime(fed_funds_rate.index)

# Remover informações de fuso horário dos índices
btc_close_volume.index = btc_close.index.tz_localize(None)
sp500_close_volume.index = sp500_close.index.tz_localize(None)
fed_funds_rate.index = fed_funds_rate.index.tz_localize(None)

# Todas no mesmo tipo
btc_close_volume.index = pd.to_datetime(btc_close.index)
sp500_close_volume.index = pd.to_datetime(sp500_close.index)
fed_funds_rate.index = pd.to_datetime(fed_funds_rate.index)

print(btc_close_volume.index.tz)        # Check timezone info for btc_close
print(sp500_close_volume.index.tz)      # Check timezone info for sp500_close
print(fed_funds_rate.index.tz)   # Check timezone info for fed_funds_rate

# Garantir datetime e remover timezone
btc_close_volume.index = pd.to_datetime(btc_close_volume.index).tz_localize(None)
sp500_close_volume.index = pd.to_datetime(sp500_close_volume.index).tz_localize(None)
fed_funds_rate.index = pd.to_datetime(fed_funds_rate.index).tz_localize(None)

# Criar intervalo de datas com base no BTC
start_date = btc_close_volume.index.min()
end_date = btc_close_volume.index.max()
all_dates = pd.date_range(start=start_date, end=end_date, freq='D')

# Reindexar todos os DataFrames na base de BTC
btc_close_volume = btc_close_volume.reindex(all_dates)
sp500_close_volume = sp500_close_volume.reindex(all_dates)
fed_funds_rate_daily = fed_funds_rate.reindex(all_dates).ffill()

# Merge BTC + SP500
merged_data = btc_close_volume.merge(sp500_close_volume, how='left', left_index=True, right_index=True)

# Interpola no tempo (preenche os buracos no meio)
cols_to_interpolate = ['SP500_Close', 'SP500_Volume']
merged_data[cols_to_interpolate] = merged_data[cols_to_interpolate].interpolate(method='time')

# Garantir que a PRIMEIRA e a ÚLTIMA linha sejam preenchidas se ficaram NaN
merged_data[cols_to_interpolate] = merged_data[cols_to_interpolate].ffill().bfill()

merged_data

# Garante datetime no índice e remove timezone
fed_funds_rate.index = pd.to_datetime(fed_funds_rate.index).tz_localize(None)
# Reindexar o FED para ter as mesmas datas do merged_data (BTC + SP500)
fed_alinhado = fed_funds_rate.reindex(merged_data.index)

# Interpolar os valores nulos do FED
fed_alinhado = fed_alinhado.interpolate(method='time')

# Preencher possíveis NaNs na primeira ou última linha
fed_alinhado = fed_alinhado.ffill().bfill()

print(merged_data.isnull().sum())
print(merged_data.head())

# 1. Achatar as colunas para formato simples
merged_data.columns = ['_'.join(col).strip() for col in merged_data.columns.values]

# 2. Agora o merge vai funcionar!
merged_data = merged_data.merge(
    fed_funds_rate_daily,
    how='left',
    left_index=True,
    right_index=True
)

merged_data.head(100)

# ========== 2. Escalamento ==========
numerical_cols = [
    'BTC_Close_BTC-USD',
    'SP500_Close_^GSPC',
    'FedFundsRate',
    'BTC_Volume_BTC-USD',
    'SP500_Volume_^GSPC'
]

scaler_X = StandardScaler()
scaler_y = StandardScaler()

merged_scaled = merged_data.copy()
merged_scaled[numerical_cols] = scaler_X.fit_transform(merged_data[numerical_cols])
target_scaled = scaler_y.fit_transform(merged_data[['BTC_Close_BTC-USD']])

# ========== 3. Criar janelas ==========
def create_sequences(data, target, lookback=60):
    X, y = [], []
    for i in range(lookback, len(data)):
        X.append(data[i - lookback:i])
        y.append(target[i])
    return np.array(X), np.array(y)

X, y = create_sequences(merged_scaled[numerical_cols].values, target_scaled)

# ========== 4. Split ==========
train_size = int(len(X) * 0.8)
X_train, X_test = X[:train_size], X[train_size:]
y_train, y_test = y[:train_size], y[train_size:]

print("✅ Dados de treino:", X_train.shape, y_train.shape)

# ========== 5. Criar modelo ==========
model = Sequential([
    LSTM(64, input_shape=(X.shape[1], X.shape[2]), return_sequences=False),
    Dense(32, activation='relu'),
    Dense(1)
])
model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mae'])

print("🚀 Treinando modelo...")
model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=3, batch_size=32, verbose=2)

# ========== 6. Salvar ==========
model_dir = os.path.join("api_btc", "modelos")
os.makedirs(model_dir, exist_ok=True)

model_path = os.path.join(model_dir, "modelo_lstm.h5")
scaler_path = os.path.join(model_dir, "scaler_y.pkl")

model.save(model_path)
joblib.dump(scaler_y, scaler_path)

print(f"💾 Modelo salvo com sucesso em: {os.path.abspath(model_path)}")
print(f"💾 Scaler salvo com sucesso em: {os.path.abspath(scaler_path)}")
