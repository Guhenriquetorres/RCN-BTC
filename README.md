# 📈 RCN-BTC

## 🔍 Descrição do Projeto
Este projeto tem como objetivo realizar a validação de modelos de **Redes Neurais Recorrentes (RNN, LSTM e GRU)** aplicados à previsão de séries temporais no mercado de **Bitcoin (BTC)**.

Através deste estudo, buscamos entender a eficácia desses modelos na previsão de preços, considerando a alta volatilidade e comportamento não-linear do mercado cripto.

---

## 🎯 Objetivos
- 📊 **Por que:** O mercado de criptomoedas é altamente volátil e sensível a padrões não lineares. Avaliar modelos robustos pode fornecer previsões mais precisas.
- 🎯 **Para que:** Construir modelos preditivos que possam apoiar traders, investidores e pesquisadores na tomada de decisão.
- 🛠️ **Como:** Utilizando redes neurais recorrentes (RNN), LSTM e GRU treinadas com dados históricos de preço do Bitcoin.
- 📏 **Métrica de Sucesso:** 
  - Erro Quadrático Médio (RMSE)
  - Erro Absoluto Médio (MAE)
  - Comparação entre modelos tradicionais (ARIMA, Prophet) e modelos de Deep Learning.

---

## 📂 Dataset
- Fonte dos dados: [Yahoo Finance](https://finance.yahoo.com/) ou [Binance API](https://binance-docs.github.io/apidocs/spot/en/).
- Dados: Preço diário do Bitcoin (Open, High, Low, Close, Volume) dos últimos anos.

---

## 🧠 Tecnologias e Ferramentas
- **Backend:**
  - Python
  - Django (API REST)
- **Machine Learning / Deep Learning:**
  - TensorFlow
  - Keras
  - Scikit-Learn
- **Análise e Manipulação de Dados:**
  - Pandas
  - NumPy
- **Visualização:**
  - Matplotlib
  - Plotly
  - Seaborn
- **Banco de Dados:**
  - SQLite ou PostgreSQL
- **Documentação e Versionamento:**
  - Git & GitHub

---

## 🚫 Atenção
> ❌ **Streamlit está PROIBIDO neste projeto.**
Se utilizar, haverá perda de **5 pontos na média**.

---

## 🏗️ Estrutura do Projeto
```plaintext
RCN-BTC/
├── backend/          # API em Django
│   ├── models/       # Modelos e banco de dados
│   ├── serializers/  # Serialização de dados
│   └── urls.py       # Rotas da API
├── notebooks/        # Análises, EDA e modelos de ML
├── data/             # Dados brutos e processados
├── frontend/         # Interface (HTML/CSS/JS ou React)
├── README.md         # Documentação do projeto
└── requirements.txt  # Dependências
