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
1. Copie o arquivo de exemplo:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```
2. Preencha as variáveis com suas credenciais reais.
3. Opcionalmente deixe `token` vazio para que o login seja feito automaticamente.

## Contribuindo
1. Instale os hooks do pre-commit dentro do ambiente do Poetry:
   ```bash
   poetry shell
   pre-commit install
   ```
2. Para atualizar as versões dos hooks:
   ```bash
   pre-commit autoupdate
   ```
