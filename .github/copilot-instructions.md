# Copilot Instructions for AI Agents

## Visão Geral do Projeto
- Este é um dashboard multipágina em Streamlit para consolidar indicadores da plataforma Arkmeds.
- O código está organizado em torno de serviços de métricas, clientes de API, componentes de UI e páginas Streamlit.
- O fluxo principal: autenticação → coleta de dados via API Arkmeds → cálculo de métricas → exibição em páginas Streamlit.

## Estrutura e Componentes-Chave
- `app/` — código principal do dashboard.
  - `main.py`: ponto de entrada, inicializa UI e configurações.
  - `arkmeds_client/`: autenticação, cliente HTTP e modelos de dados (Pydantic) para integração com a API Arkmeds.
  - `services/`: lógica de cálculo de métricas (KPIs) para OS, equipamentos e técnicos. Cada serviço é assíncrono e usa cache.
  - `ui/`: componentes de UI (filtros, CSS, helpers) e inicialização de páginas.
  - `pages/`: cada arquivo representa uma página do Streamlit (ex: `2_os.py`, `3_equip.py`).
  - `config/`: constantes e mapeamentos de tipos/áreas usados nos serviços.
- `tests/` — testes unitários para serviços, filtros e modelos. Use `make test` ou `poetry run pytest`.

## Fluxos de Desenvolvimento
- **Instalação:**
  - Linux/macOS: `make install && make run`
  - Windows: `./make.bat install` e `./make.bat run PORT=8501` ou `./make.ps1 -Target install`
- **Execução:**
  - `make run` ou scripts em `scripts/` para rodar localmente.
  - Docker: `make docker` (build) e `make compose` (compose up)
- **Testes e Lint:**
  - `make lint` (ruff), `make format` (ruff format), `make test` (pytest)
- **CI/CD:**
  - Workflows GitHub Actions em `.github/workflows/` para CI (lint, test, coverage) e CD (build/push Docker).

## Convenções Específicas
- Páginas em `app/pages/` devem ser nomeadas com prefixo numérico ASCII (ex: `1_home.py`).
- Filtros de data, tipo, estado e responsável são persistidos em `st.session_state['filters']`.
- Serviços de métricas usam cache (`@st.cache_data`) e são assíncronos.
- Modelos de dados (OS, Equipment, User) usam Pydantic e validadores customizados para datas.
- Integração com a API Arkmeds é feita via `ArkmedsClient` e métodos como `list_os`, `list_equipment`.
- Variáveis sensíveis/configurações em `.env` e `.streamlit/secrets.toml`.

## Exemplos de Padrões
- Para adicionar um novo KPI, crie um serviço em `app/services/`, defina um modelo Pydantic e exponha via página Streamlit.
- Para novos filtros, edite `app/ui/filters.py` e garanta persistência em `st.session_state`.
- Para integração com novas rotas da API, adicione métodos em `arkmeds_client/client.py`.

## Referências Rápidas
- Build local: `make install && make run`
- Testes: `make test` ou `poetry run pytest`
- Lint/format: `make lint` / `make format`
- Docker: `make docker` / `make compose`
- Configuração de secrets: `.streamlit/secrets.toml` e `.env`

Consulte `README.md` para detalhes de uso e exemplos de comandos.
