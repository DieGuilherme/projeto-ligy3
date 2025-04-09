# Faturamento Ligy - App Streamlit

Aplicação para processamento de faturamento com geração de faturas PDF por cliente.

## 🚀 Como rodar no Streamlit Cloud

1. Crie um repositório com esta estrutura
2. No painel do Streamlit Community Cloud:
   - Escolha este repositório
   - Defina o arquivo principal: `app/_PRO_faturas_v2_final.py`
3. Pronto!

## 🧾 Estrutura

```
.
├── app/
│   ├── _PRO_faturas_v2.py
│   ├── _PRO_faturas_v2_final.py
│   └── _gerador_de_faturas.py
├── assets/
│   ├── Montserrat-Regular.ttf
│   ├── Montserrat-Bold.ttf
│   └── Fatura_Ligy_bco.pdf
├── .streamlit/
│   └── config.toml
├── requirements.txt
└── README.md
```

## 🛠️ Como rodar localmente

```bash
pip install -r requirements.txt
streamlit run app/_PRO_faturas_v2_final.py
```
