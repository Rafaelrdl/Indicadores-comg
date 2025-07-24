# AGENTS.md — Contributor & AI Agent Guide for **Indicadores‑comg**

> **Repository**: <https://github.com/Rafaelrdl/Indicadores-comg>  
> **Primary Tech**: Python 3.12 • Streamlit • Requests • Pandas • Ruff • Pytest  
> **Scope**: Simple KPI dashboard that queries the Arkmeds REST API and presents metrics.

---

## 1  Project Mission

A lightweight Streamlit app that logs into Arkmeds, retrieves basic maintenance data (OS, Equipamentos, Técnicos) and displays a handful of KPIs (Corretivas, Preventivas, MTTR, MTBF, SLA, Backlog). **No complex async, no micro‑services** — just clear code that anyone can clone and run in minutes.

---

## 2  Repo Map (single‑layer)

```
app/
├─ main.py            # ⭢ streamlit run app/main.py
├─ arkmeds_client.py  # small sync wrapper around requests
├─ metrics.py         # pure‑python KPI calculators (sync, cached)
├─ pages/             # Streamlit multipage files
│  ├─ 1_home.py       # Landing KPIs
│  ├─ 2_os.py         # Ordens de Serviço
│  ├─ 3_equip.py      # Equipamentos
│  └─ 4_tech.py       # Técnicos
└─ ui/filters.py      # sidebar date/type filters

requirements.txt      # single dependency list
README.md             # quick‑start & screenshots
AGENTS.md             # you are here 😉
```

### Why so flat?
* Fewer imports ⇒ fewer “ModuleNotFoundError”.
* Easier onboarding for new contributors (and AI agents).

---

## 3  Dev Environment Quick‑start

|            | Linux / macOS                           | Windows PowerShell                        |
|------------|-----------------------------------------|-------------------------------------------|
| **Setup**  | `python -m venv .venv && source .venv/bin/activate` | `python -m venv .venv ; .\.venv\Scripts\Activate.ps1` |
| **Install**| `pip install -r requirements.txt`        | same                                      |
| **Run**    | `streamlit run app/main.py`             | `streamlit run app/main.py`               |
| **Secrets**| copy `.streamlit/secrets.example.toml` → `.streamlit/secrets.toml` and fill `email, password, base_url=https://…` |

> **Note**: `base_url` **must** include `https://` or requests will raise `UnsupportedProtocol`.

### Docker (optional)
```bash
docker build -t indicadores:dev . && docker run -p 8501:8501 indicadores:dev
```
_(only needed for production deploy)_

---

## 4  Coding Guidelines

| Topic                     | Rule |
|---------------------------|------|
| **Imports**               | All project imports are *absolute* from `app` root (e.g. `from metrics import get_os_metrics`). |
| **Async**                 | ✘ Not used. All functions are synchronous. |
| **Caching**               | Use `@st.cache_data(ttl=600)` on *pure* functions that return dict/df. |
| **Style**                 | Ruff default (`ruff format` before commit). |
| **Typing**                | Add `-> dict` / `-> pd.DataFrame` hints. |
| **Commit message**        | `[area] short description`, e.g. `[ui] add SLA gauge`. |
| **Branch naming**         | `feat/…`, `fix/…`, `chore/…`. |
| **PR**                    | Fill template: _What_, _Why_, _How to test_. |

---

## 5  Testing & Validation

1. **Lint**: `ruff check .`  
2. **Unit tests**: `pytest -q` (small fixtures under `tests/`).  
3. **Manual**: `streamlit run app/main.py` and click through all pages.

CI (GitHub Actions) runs steps 1‑2 automatically.

---

## 6  Adding Functionality

| Task | Where | Checklist |
|------|-------|-----------|
| **New KPI** | `metrics.py` | 1) fetch raw list via `arkmeds_client.*` 2) compute aggregate 3) return in KPI dict 4) render in page. |
| **New API call** | `arkmeds_client.py` | Add simple `requests.get/post`; handle pagination if needed. |
| **New filter** | `ui/filters.py` | Add `st.selectbox/datepicker`; write to `st.session_state["filters"]`. |
| **New page** | `app/pages/5_newpage.py` | `st.set_page_config(page_title="…", page_icon="📊")`. |

---

## 7  AI Agent Expectations

1. **Search context first** → skim only relevant files before editing.  
2. **Modify minimal set** → one feature/fix per PR.  
3. **Keep path flat** → no new nested packages unless justified.  
4. **No async / threading** unless approved in issue.  
5. **Run tests** → ensure `ruff` & `pytest` green before proposing merge.  
6. **Document** changes in the PR body + update this `AGENTS.md` if process shifts.

---

## 8  Documentation Links

| Component          | Docs |
|--------------------|------|
| Arkmeds Swagger    | <https://app.swaggerhub.com/apis-docs/Arkmeds/Arkmeds-APIs/1.0.0> |
| Streamlit          | <https://docs.streamlit.io/> |
| Requests           | <https://requests.readthedocs.io/> |
| Ruff               | <https://github.com/astral-sh/ruff> |
| GitHub Actions     | <https://docs.github.com/actions> |

---

Happy coding ― and keep it **simple & synchronous**! ☕
