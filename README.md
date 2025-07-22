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

## Autenticação
Utilize o `ArkmedsAuth` para obter um JWT de forma transparente.

```python
from arkmeds_client.auth import ArkmedsAuth

auth = ArkmedsAuth.from_secrets()
token = await auth.get_token()
```

## Uso do ArkmedsClient

```python
from arkmeds_client.auth import ArkmedsAuth
from arkmeds_client.client import ArkmedsClient

auth = ArkmedsAuth.from_secrets()
client = ArkmedsClient(auth)
os = await client.list_os(data_criacao__gte="2025-06-01")
```

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
