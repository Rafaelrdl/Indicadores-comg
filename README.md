# Indicadores COMG

Projeto para cálculo e visualização de indicadores de manutenção.

## Pré-requisitos

- Python 3.11 ou superior

## Instalação

Clone o repositório e execute:

```bash
bash setup.sh
```

Este script instalará as dependências listadas em ``requirements.txt``.

## Execução da aplicação

1. Coloque o arquivo `ordens_servico.xlsx` em uma pasta `data/` na raiz do projeto. O formato esperado pode ser visto em `tests/fixtures/sample_orders.xlsx`.
2. Inicie a interface Streamlit:

```bash
PYTHONPATH=$(pwd) streamlit run presentation/streamlit_app.py
```

## Testes e qualidade de código

```bash
ruff check .
ruff format .
pytest -q
```

