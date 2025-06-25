import numpy as np
import pandas as pd
import joblib
from keras.models import load_model
from sklearn.preprocessing import StandardScaler
import yfinance as yf
from fredapi import Fred
import os

def prever_btc():
    # Caminhos
    model_path = os.path.join("api_btc", "modelos", "modelo_lstm.h5")
    scaler_path = os.path.join("api_btc", "modelos", "scaler_y.pkl")

    # Carregar modelo e scaler
    model = load_model(model_path)
    scaler_y = joblib.load(scaler_path)

    # ===================== 1. Repetir ETL dos últimos dados =====================
    btc = yf.download('BTC-USD', start='2015-01-01', end='2024-01-01')
    sp500 = yf.download('^GSPC', start='2015-01-01', end='2024-01-01')
    fred = Fred(api_key='f2aeb0f0a807498a62d1b0d4311a431c')
    fed = fred.get_series('FEDFUNDS', start='2015-01-01', end='2024-01-01')

    btc_close_volume = btc[['Close', 'Volume']].rename(columns={'Close': 'BTC_Close', 'Volume': 'BTC_Volume'})
    sp500_close_volume = sp500[['Close', 'Volume']].rename(columns={'Close': 'SP500_Close', 'Volume': 'SP500_Volume'})
    fed = pd.DataFrame(fed, columns=['FedFundsRate'])

    all_dates = pd.date_range(start=btc.index.min(), end=btc.index.max(), freq='D')
    btc_close_volume = btc_close_volume.reindex(all_dates)
    sp500_close_volume = sp500_close_volume.reindex(all_dates)
    fed = fed.reindex(all_dates).interpolate().ffill().bfill()

    # Primeiro merge
    merged_data = btc_close_volume.merge(sp500_close_volume, left_index=True, right_index=True)

    # Corrigir MultiIndex para colunas simples antes do merge com fed
    merged_data.columns = [
        'BTC_Close_BTC-USD',
        'BTC_Volume_BTC-USD',
        'SP500_Close_^GSPC',
        'SP500_Volume_^GSPC'
    ]

    # Merge com a taxa de juros
    merged_data = merged_data.merge(fed, left_index=True, right_index=True)
    merged_data = merged_data.ffill().bfill()

    numerical_cols = merged_data.columns.tolist()

    # Normalizar com scaler novo (apenas para X, y usamos o scaler salvo)
    scaler_X = StandardScaler()
    merged_scaled = merged_data.copy()
    merged_scaled[numerical_cols] = scaler_X.fit_transform(merged_data[numerical_cols])

    # Selecionar última janela para previsão
    ultima_janela = merged_scaled[numerical_cols].values[-60:]
    entrada = np.expand_dims(ultima_janela, axis=0)

    # Prever e reverter escala
    pred_scaled = model.predict(entrada)
    pred_original = scaler_y.inverse_transform(pred_scaled)[0][0]

    print(f"📈 Previsão de fechamento do BTC (próximo dia): ${pred_original:,.2f}")
    return pred_original

if __name__ == "__main__":
    prever_btc()

def prever_btc_dias_a_frente(dias=1):
    import numpy as np
    import pandas as pd
    import joblib
    from keras.models import load_model
    from sklearn.preprocessing import StandardScaler
    import yfinance as yf
    from fredapi import Fred
    import os

    # Caminhos
    model_path = os.path.join("api_btc", "modelos", "modelo_lstm.h5")
    scaler_path = os.path.join("api_btc", "modelos", "scaler_y.pkl")

    # Carregar modelo e scaler
    model = load_model(model_path)
    scaler_y = joblib.load(scaler_path)

    # ===================== ETL dos dados históricos =====================
    btc = yf.download('BTC-USD', start='2015-01-01', end='2024-01-01')
    sp500 = yf.download('^GSPC', start='2015-01-01', end='2024-01-01')
    fred = Fred(api_key='f2aeb0f0a807498a62d1b0d4311a431c')
    fed = fred.get_series('FEDFUNDS', start='2015-01-01', end='2024-01-01')

    btc_close_volume = btc[['Close', 'Volume']].rename(columns={'Close': 'BTC_Close', 'Volume': 'BTC_Volume'})
    sp500_close_volume = sp500[['Close', 'Volume']].rename(columns={'Close': 'SP500_Close', 'Volume': 'SP500_Volume'})
    fed = pd.DataFrame(fed, columns=['FedFundsRate'])

    all_dates = pd.date_range(start=btc.index.min(), end=btc.index.max(), freq='D')
    btc_close_volume = btc_close_volume.reindex(all_dates)
    sp500_close_volume = sp500_close_volume.reindex(all_dates)
    fed = fed.reindex(all_dates).interpolate().ffill().bfill()

    # Primeiro merge
    merged_data = btc_close_volume.merge(sp500_close_volume, left_index=True, right_index=True)
    merged_data.columns = [
        'BTC_Close_BTC-USD',
        'BTC_Volume_BTC-USD',
        'SP500_Close_^GSPC',
        'SP500_Volume_^GSPC'
    ]
    merged_data = merged_data.merge(fed, left_index=True, right_index=True)
    merged_data = merged_data.ffill().bfill()

    numerical_cols = merged_data.columns.tolist()

    # Escalar os dados de entrada
    scaler_X = StandardScaler()
    merged_scaled = merged_data.copy()
    merged_scaled[numerical_cols] = scaler_X.fit_transform(merged_data[numerical_cols])

    # Pegar última janela de 60 dias
    entrada = merged_scaled[numerical_cols].values[-60:]
    previsoes = []

    for _ in range(dias):
        entrada_expandida = np.expand_dims(entrada, axis=0)
        pred_scaled = model.predict(entrada_expandida)
        pred = scaler_y.inverse_transform(pred_scaled)[0][0]
        previsoes.append(pred)

        nova_linha = entrada[-1].copy()
        nova_linha[0] = pred_scaled[0][0]  # Atualiza coluna do BTC_Close com previsão
        entrada = np.vstack([entrada[1:], nova_linha])  # Remove o primeiro dia, adiciona o novo

    return [float(p) for p in previsoes]  # garante lista de floats
