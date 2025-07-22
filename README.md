# Dashboard Arkmeds

![CI](https://github.com/<OWNER>/<REPO>/actions/workflows/ci.yml/badge.svg)
![CD](https://github.com/<OWNER>/<REPO>/actions/workflows/cd.yml/badge.svg)

## Visão Geral
Projeto para centralizar indicadores da plataforma Arkmeds utilizando Streamlit multipage.

## Pré-requisitos
- Python 3.12+
- [Poetry](https://python-poetry.org/docs/#installation)

## Rodando o App
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

## KPIs de Técnicos

```python
from app.services.tech_metrics import compute_metrics
from app.arkmeds_client.auth import ArkmedsAuth
from app.arkmeds_client.client import ArkmedsClient
from datetime import date

auth = ArkmedsAuth.from_secrets()
client = ArkmedsClient(auth)
metrics = await compute_metrics(client, dt_ini=date(2025, 1, 1), dt_fim=date(2025, 1, 31))
print(metrics)
```

## Filtros Globais

Componente reutilizável para seleção de datas e opções na sidebar. O estado é
preservado em `st.session_state["filters"]` e um contador `filtros_version`
permite detectar mudanças.

![Filtros](docs/filtros.gif)

## Página Inicial

Visão consolidada dos principais indicadores do mês.

![Home](docs/home_page.png)

## Página de Ordens de Serviço

Screenshot demonstrando os indicadores e a tabela filtrada.

![Ordens de Serviço](docs/os_page.png)

## Página de Equipamentos

Visão geral do parque de equipamentos e métricas de manutenção.

![Equipamentos](docs/equip_page.png)

## Página de Técnicos

Ranking de desempenho por responsável, com indicadores de pendências,
concluídas, SLA médio e tempo de fechamento.

![Técnicos](docs/tech_page.png)

## Docker Multi-Arch

Para gerar a imagem para arm64 e amd64 utilize:
```bash
docker buildx build --platform linux/amd64,linux/arm64 -t rafael/arkmeds-dashboard:latest .
```

