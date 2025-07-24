# Copilot Instructions for AI Agents

> **Repository:** [https://github.com/Rafaelrdl/Indicadores-comg](https://github.com/Rafaelrdl/Indicadores-comg)
>
> **Stack:** Python 3.12 · Streamlit ≥ 1.30 · Poetry · HTTPX · Pydantic v2 · Ruff · Pytest

---

## 1  Project Overview

`Indicadores‑comg` is a **multi‑page Streamlit dashboard** that aggregates maintenance and biomedical engineering KPIs from the **Arkmeds** SaaS platform.

High‑level pipeline:

1. **Auth** → JWT login or token refresh ([ArkmedsAuth]).
2. **Data ingest** → async HTTPX client ([ArkmedsClient]) fetches paginated JSON.
3. **Domain layer** → metric services compute MTTR/MTBF, backlog, SLA etc. and cache results.
4. **UI** → pages under `app/pages/` render KPIs, charts & tables; global filters live in the sidebar.

---

## 2  Directory Map

app/
├─ main.py # Streamlit entry‑point
│
├─ arkmeds_client/ # API integration layer
│ ├─ auth.py # ArkmedsAuth (JWT login, cache)
│ ├─ client.py # ArkmedsClient (async CRUD helpers)
│ └─ models.py # Pydantic schemas (OS, Equipment, User…)
│
├─ services/ # Business logic / KPI calculators
│ ├─ os_metrics.py # Correctives / backlog / SLA
│ ├─ equip_metrics.py # MTTR / MTBF / park status
│ └─ tech_metrics.py # Technicians performance
│
├─ ui/ # Reusable UI pieces
│ ├─ init.py # set_page_config + inject filters
│ ├─ filters.py # Sidebar widget & session_state
│ └─ css.py # (Optional) custom styles
│
├─ pages/ # Streamlit multipage (auto‑discovered)
│ ├─ 1_home.py # Executive overview
│ ├─ 2_os.py # Ordens de Serviço
│ ├─ 3_equip.py # Equipamentos
│ └─ 4_tech.py # Técnicos
│
├─ config/ # Constants & mapping tables
│ └─ os_types.py # ID maps: TIPO_CORRETIVA etc.
└─ tests/ # Pytest suites

yaml
Copiar
Editar

---

## 3  Development Workflow

| Task             | Linux/macOS                              | Windows PowerShell                  |
| ---------------- | ---------------------------------------- | ----------------------------------- |
| **Install deps** | `make install`                           | `./make.ps1 -Target install`        |
| **Run app**      | `make run`                               | `./make.ps1 -Target run -Port 8501` |
| **Lint**         | `make lint`                              | idem                                |
| **Tests**        | `make test`                              | idem                                |
| **Docker**       | `make docker` → build`make compose` → up | n/a                                 |

> **Editable install** – `make install` runs `pip install -e .` so `app` is importable everywhere.

### Secrets & Env

- `.streamlit/secrets.toml` → `[arkmeds] email, password, base_url="https://…", token`.  
  **‼️ base_url must include `https://`**.
- `.env` for extra flags (`STREAMLIT_SERVER_HEADLESS=1`, etc.).

---

## 4  Conventions & Patterns

- **File names** in `app/pages/` start with an ASCII prefix (`1_`, `2_`, …) for menu order.
- Use `st.session_state["filters"]` to persist **date‑range, tipo, estado, responsável**.
- Metric services are **async** and wrapped with `@st.cache_data(ttl=900)`.
- All Arkmeds endpoints live under `v3`; trailing slashes **omitted** (`/auth/login`, not `/auth/login/`).
- Dates from API come as `"DD/MM/YY - HH:MM"`; validators parse to `datetime`.

---

## 5  Typical Extension Recipes

### Add a New KPI

1. Create a service in `app/services/` returning a Pydantic model.
2. Cache the function.
3. Render in a page → `st.metric`, plotly chart, or table.

### Add a Sidebar Filter

1. Edit `ui/filters.py` → add widget + write to `session_state`.
2. Pass new filter down to service layer (`compute_metrics`).

### New API Route

1. Add async method in `arkmeds_client/client.py`.
2. Update relevant service to consume it.
3. Cover with tests in `tests/`.

---

## 6  Quick Reference Commands

```bash
# Setup & run (Linux/macOS)
make install && make run

# Windows PowerShell
./make.ps1 -Target install
./make.ps1 -Target run -Port 8501

# Lint / format / test
make lint    # Ruff static analysis
make format  # Ruff formatter
make test    # Pytest suite

# Docker
make docker   # Build image
make compose  # docker‑compose up -d
For full details consult README.md and the inline docstrings.

7  Key Documentation Links
Component	Official Docs
Arkmeds API	https://app.swaggerhub.com/apis-docs/Arkmeds/Arkmeds-APIs/1.0.0
Streamlit	https://docs.streamlit.io/
Poetry	https://python-poetry.org/docs/
Pydantic v2	https://docs.pydantic.dev/latest/
HTTPX	https://www.python-httpx.org/
Ruff	https://github.com/astral-sh/ruff
GitHub Actions	https://docs.github.com/actions