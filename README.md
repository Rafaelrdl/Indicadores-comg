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
from arkmeds_client.models import OS

auth = ArkmedsAuth.from_secrets()
client = ArkmedsClient(auth)
os = await client.list_os(data_criacao__gte="2025-06-01")
```

```python
raw = await client.list_os()[0]
os_obj: OS = OS.model_validate(raw)
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

## KPIs de OS

```python
from app.services.os_metrics import compute_metrics
from app.arkmeds_client.auth import ArkmedsAuth
from app.arkmeds_client.client import ArkmedsClient
from datetime import date

auth = ArkmedsAuth.from_secrets()
client = ArkmedsClient(auth)
metrics = await compute_metrics(client, dt_ini=date(2025, 1, 1), dt_fim=date(2025, 1, 31))
print(metrics)
```

## KPIs de Equipamentos

```python
from app.services.equip_metrics import compute_metrics
from app.arkmeds_client.auth import ArkmedsAuth
from app.arkmeds_client.client import ArkmedsClient
from datetime import date

auth = ArkmedsAuth.from_secrets()
client = ArkmedsClient(auth)
metrics = await compute_metrics(client, dt_ini=date(2025, 1, 1), dt_fim=date(2025, 1, 31))
print(metrics)
```
