# Indicadores COMG

Projeto para cálculo e visualização de indicadores de manutenção.

## Pré-requisitos

- Python 3.11 ou superior

## Instalação

```bash
pip install -r requirements.txt
```

## Execução da aplicação

1. Defina as variáveis de ambiente da API Arkmeds (pode ser em um arquivo `.env`
   ou em `.streamlit/secrets.toml`):

   ```bash
   ARKMEDS_EMAIL=<seu-email>
   ARKMEDS_PASSWORD=<sua-senha>
   BASE_URL=https://api-os.arkmeds.com
   ```

   Para apontar para ambientes de staging ou produção, altere o valor de
   `BASE_URL` conforme necessário.

2. Execute:

   ```bash
   pip install -r requirements.txt
   streamlit run presentation/streamlit_app.py
   ```

## Testes e qualidade de código

```bash
ruff check .
ruff format .
pytest -q
```
