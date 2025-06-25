# 📊 Previsão de Preço do Bitcoin com LSTM — RNC-BTC

Este projeto utiliza **Redes Neurais Recorrentes (LSTM)** para prever o preço do **Bitcoin (BTC)** em relação ao dólar (USD), com uma interface amigável em Django + Plotly. Ideal para estudos de **Deep Learning aplicado a séries temporais financeiras**.

---

## 🚀 Visão Geral

- 🔁 **Modelo LSTM**: treinado para prever os próximos dias com base em dados históricos de BTC.
- 🌐 **Backend Django**: APIs REST com DRF.
- 📈 **Frontend com Plotly.js**: exibe previsões e valores reais.
- 💾 **Persistência**: banco de dados com previsões salvas automaticamente.
- 📅 **Consulta por data**: prevê apenas se o valor ainda não estiver no banco.
- 🧠 **Autopreenchimento**: preenche previsões futuras automaticamente com base no último valor conhecido.

---

## 📦 Estrutura do Projeto

RNC-BTC/
│
├── api_btc/ # App principal Django
│ ├── modelos/ # Modelos de ML (LSTM)
│ ├── migrations/ # Migrações do banco
│ ├── templates/ # HTML com Plotly.js
│ ├── views.py # Lógica de exibição e API
│ └── models.py # Modelo PrevisaoBTC
│
├── RN_BTC/ # Configuração Django
├── static/ # Estáticos (se aplicável)
├── db.sqlite3 # Banco de dados (ignorado no git)
├── requirements.txt # Dependências
├── .gitignore # Arquivos a ignorar
└── manage.py

yaml
Copy
Edit

---

## 🔬 Sobre o Modelo LSTM

Utiliza a arquitetura LSTM da biblioteca Keras/TensorFlow para capturar padrões temporais do preço do Bitcoin.

### 📌 Dados usados:
- Fonte: [Yahoo Finance](https://finance.yahoo.com)
- Paridade: `BTC-USD`
- Colunas utilizadas: `Close`, normalizadas

### 🛠️ Pré-processamento:
- Normalização com `MinMaxScaler`
- Criação de janelas de entrada (`X`) e saída (`y`)
- Split entre treino/teste
- Treinamento por `n` épocas

---

## 💡 Funcionalidade Principal

### ✅ Consulta por data (GET)
`/api/previsoes/buscar_por_data/?data=YYYY-MM-DD`

- Se já existe: retorna do banco.
- Se não existe:
  - Verifica última data conhecida
  - Gera novas previsões LSTM até alcançar a data pedida
  - Salva tudo no banco
- Retorna: JSON com data, preço previsto, modelo, paridade e (se houver) **preço real** do BTC.

---

## 🖼️ Interface Web

A interface permite:
- Selecionar a data desejada
- Exibir:
  - 📅 Data
  - 💰 Preço previsto
  - 📉 Valor real (se já disponível)
- 📊 Plot com `Plotly.js` (preço previsto vs real)
- 🧾 Tabela detalhada com os valores

---

## ▶️ Como Executar Localmente

### 1. Clone o repositório

```bash
git clone https://github.com/seu_usuario/RNC-BTC.git
cd RNC-BTC

2. Crie o ambiente virtual
bash
Copy
Edit
python -m venv RN_BTC
source RN_BTC/Scripts/activate  # Windows
# ou
source RN_BTC/bin/activate      # Linux/macOS

3. Instale as dependências
bash
Copy
Edit
pip install -r requirements.txt

4. Aplique as migrações
bash
Copy
Edit
python manage.py migrate

5. Rode o servidor
bash
Copy
Edit
python manage.py runserver

Abra em: http://127.0.0.1:8000

Categoria	Ferramenta
Backend	Django, Django REST
Deep Learning	TensorFlow, Keras
API Financeira	Yahoo Finance (yfinance)
Frontend	Plotly.js + HTML5
Banco de dados	SQLite
