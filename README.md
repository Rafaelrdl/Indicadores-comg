# Dashboard Arkmeds

## Visão Geral
Projeto para centralizar indicadores da plataforma Arkmeds utilizando Streamlit multipage.

## Pré-requisitos
- Python 3.12+
- [Poetry](https://python-poetry.org/docs/#installation)

## Como Rodar Localmente
```bash
poetry install
poetry run streamlit run app/main.py
```

## Estrutura de Pastas
```
app/
├── arkmeds_client/
├── services/
├── ui/
└── main.py
```

## Configuração de secrets
Copie `secrets.toml.example` para `.streamlit/secrets.toml` e preencha os campos necessários.
