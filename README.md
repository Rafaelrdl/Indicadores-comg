# Indicadores COMG

Projeto para cálculo e visualização de indicadores de manutenção.

## Pré-requisitos

- Python 3.11 ou superior

## Instalação

```bash
pip install -r requirements.txt
```

## Execução da aplicação

1. Coloque o arquivo `ordens_servico.xls` em uma pasta `data/` na raiz do projeto. O formato esperado pode ser visto em `tests/fixtures/sample_orders.xls`.
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
