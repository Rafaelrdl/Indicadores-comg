# Copilot Instructions for AI Agents

> **Repository:** [https://github.com/Rafaelrdl/Indicadores-comg](https://github.com/Rafaelrdl/Indicadores-comg)
>
> **Stack:** Python 3.12 · Streamlit ≥ 1.47 · Poetry · HTTPX · Pydantic v2 · Plotly · Ruff · Pytest

---

## 1  Project Overview

`Indicadores‑comg` is a **multi‑page Streamlit dashboard** that aggregates maintenance and biomedical engineering KPIs from the **Arkmeds** SaaS platform.

**Architecture Philosophy**: The codebase follows a **layered architecture** with clear separation of concerns:
- **Core Layer**: Configuration, constants, exceptions, and logging
- **Data Layer**: Models, repositories, caching, and validation  
- **Service Layer**: Business logic and KPI calculations
- **UI Layer**: Reusable components, layouts, and page-specific logic
- **Integration Layer**: External API clients and authentication

High‑level pipeline:

1. **Auth** → JWT login or token refresh ([ArkmedsAuth])
2. **Data ingest** → async HTTPX client ([ArkmedsClient]) fetches paginated JSON
3. **Validation** → Data validation and transformation utilities ensure data quality
4. **Caching** → Intelligent caching system with filter-aware invalidation
5. **Domain layer** → metric services compute MTTR/MTBF, backlog, SLA etc.
6. **UI** → reusable components render KPIs, charts & tables; global filters live in the sidebar

---

## 2  Enhanced Directory Structure

```
app/
├─ main.py                    # Streamlit entry‑point
│
├─ core/                      # ✨ Core infrastructure
│  ├─ config.py              # Centralized configuration (Pydantic BaseSettings)
│  ├─ constants.py           # Application constants and enums
│  ├─ exceptions.py          # Custom exception hierarchy
│  └─ logging.py             # Structured logging configuration
│
├─ data/                      # ✨ Data layer
│  ├─ models/                # Pydantic data models
│  ├─ repositories/          # Data access patterns
│  └─ cache/
│     └─ smart_cache.py      # Intelligent caching system
│
├─ arkmeds_client/           # API integration layer
│  ├─ auth.py               # ArkmedsAuth (JWT login, cache)
│  ├─ client.py             # ArkmedsClient (async CRUD helpers)
│  └─ models.py             # Pydantic schemas (OS, Equipment, User…)
│
├─ services/                 # Business logic / KPI calculators
│  ├─ os_metrics.py         # Correctives / backlog / SLA
│  ├─ equip_metrics.py      # MTTR / MTBF / park status
│  └─ tech_metrics.py       # Technicians performance
│
├─ ui/                       # ✨ Enhanced UI layer
│  ├─ __init__.py           # set_page_config + inject filters
│  ├─ filters.py            # Sidebar widget & session_state
│  ├─ css.py                # Custom styles
│  ├─ utils.py              # UI utilities (run_async_safe, etc.)
│  ├─ components/           # ✨ Reusable UI components
│  │  ├─ metrics.py         # Metric cards, KPI displays
│  │  ├─ charts.py          # Plotly chart components
│  │  └─ tables.py          # Advanced data tables
│  └─ layouts/              # ✨ Layout components
│     └─ __init__.py        # Page layouts, sections, grids
│
├─ utils/                    # ✨ Utility modules  
│  ├─ validation.py         # Data validation utilities
│  └─ data_processing.py    # Data transformation utilities
│
├─ pages/                    # Streamlit multipage (auto‑discovered)
│  ├─ 1_Ordem de serviço.py # OS analysis page
│  ├─ 2_Equipamentos.py     # Equipment metrics page
│  └─ 3_Tecnico.py          # Technician performance page
│
├─ config/                   # Legacy constants (to be migrated)
│  └─ os_types.py           # ID maps: TIPO_CORRETIVA etc.
└─ tests/                    # Pytest suites
```

---

## 3  Core Architecture Components

### 3.1  Configuration System (`app/core/config.py`)

Uses **Pydantic BaseSettings** for centralized configuration with environment variable support:

```python
from app.core.config import get_settings

settings = get_settings()  # Auto-loads from env vars or Streamlit secrets
api_base_url = settings.api.base_url
cache_ttl = settings.cache.default_ttl
```

**Key Features:**
- Environment variable binding with validation
- Streamlit secrets integration
- Typed configuration with autocomplete
- Separation of concerns (API, Cache, UI, Performance settings)

### 3.2  Constants and Enums (`app/core/constants.py`)

Type-safe constants and enums for application-wide use:

```python
from app.core.constants import OSType, OSStatus, COLORS, CACHE_TTL

# Type-safe enums
if os_data.tipo == OSType.CORRETIVA:
    priority = "high"

# Consistent colors
chart_colors = [COLORS['primary'], COLORS['secondary']]
```

### 3.3  Enhanced Exception Handling (`app/core/exceptions.py`)

Custom exception hierarchy with context and error codes:

```python
from app.core.exceptions import APIError, DataValidationError

try:
    data = await client.fetch_os()
except APIError as e:
    st.error(f"API Error: {e.message}")
    logger.error(f"API call failed: {e}", extra=e.context)
```

### 3.4  Smart Caching System (`app/data/cache/smart_cache.py`)

Advanced caching with filter awareness and intelligent invalidation:

```python
from app.data.cache.smart_cache import smart_cache, cache_with_filters

@cache_with_filters(ttl=3600)
async def fetch_os_data(filters: FilterState) -> pd.DataFrame:
    # Cache key automatically includes filter values
    return await client.get_chamados(**filters.to_api_params())
```

**Features:**
- Filter-aware cache keys
- Automatic TTL management
- Memory usage monitoring
- Custom invalidation strategies

---

## 4  UI Component System

### 4.1  Reusable Metric Components (`app/ui/components/metrics.py`)

Type-safe metric display components:

```python
from app.ui.components.metrics import MetricsDisplay, Metric, KPICard

# Simple metrics
metrics = [
    Metric(label="MTTR", value="2.5h", delta="-0.3h", icon="⏱️"),
    Metric(label="MTBF", value="120h", delta="+5h", icon="🔧")
]
MetricsDisplay.render_metric_cards(metrics, columns=3)

# KPI dashboard
kpis = [
    KPICard(title="Manutenção Corretiva", metrics=corrective_metrics),
    KPICard(title="Manutenção Preventiva", metrics=preventive_metrics)
]
MetricsDisplay.render_kpi_dashboard(kpis)
```

### 4.2  Chart Components (`app/ui/components/charts.py`)

Plotly-based chart components with consistent theming:

```python
from app.ui.components.charts import TimeSeriesCharts, DistributionCharts

# Time series with automatic styling
TimeSeriesCharts.render_line_chart(
    data=trend_data,
    x_col="data",
    y_col="mttr",
    title="Evolução do MTTR",
    color_col="tipo_equipamento"
)

# Distribution analysis
DistributionCharts.render_bar_chart(
    data=summary_data,
    x_col="categoria",
    y_col="quantidade",
    title="Distribuição por Categoria"
)
```

### 4.3  Advanced Data Tables (`app/ui/components/tables.py`)

Feature-rich tables with filtering, pagination, and export:

```python
from app.ui.components.tables import DataTable

# Chainable table configuration
table = (DataTable(data=os_data, title="Ordens de Serviço")
    .add_filters(
        filterable_columns=["estado", "tipo"],
        searchable_columns=["numero", "descricao"]
    )
    .add_date_filter("data_abertura")
    .format_columns({
        "tempo_resolucao": "duration",
        "custo": "currency"
    })
    .add_pagination(page_size=25)
    .render()
)
```

### 4.4  Layout System (`app/ui/layouts/`)

Consistent page layouts and responsive grids:

```python
from app.ui.layouts import PageLayout, SectionLayout, GridLayout

# Page structure
layout = PageLayout(
    title="Análise de Equipamentos",
    description="Métricas de MTTR, MTBF e disponibilidade",
    icon="🔧"
)

layout.render_header()

with layout.main_content():
    with SectionLayout.metric_section("KPIs Principais", columns=4) as cols:
        for i, metric in enumerate(key_metrics):
            with cols[i]:
                st.metric(**metric)
    
    with SectionLayout.chart_section("Tendências"):
        render_trend_charts()
```

---

## 5  Data Processing Pipeline

### 5.1  Validation Utilities (`app/utils/validation.py`)

Comprehensive data validation with custom validators:

```python
from app.utils.validation import DataValidator, DataCleaner

# DataFrame validation
validated_df = DataValidator.validate_dataframe(
    df=raw_data,
    required_columns=["id", "data_abertura", "estado"],
    name="Chamados"
)

# Date column validation
validated_df = DataValidator.validate_date_column(
    df=validated_df,
    column="data_abertura",
    allow_null=False
)

# Data cleaning
cleaned_df = DataCleaner.clean_string_column(
    df=validated_df,
    column="descricao",
    strip_whitespace=True,
    normalize_case="title"
)
```

### 5.2  Data Processing (`app/utils/data_processing.py`)

Advanced analytics and transformations:

```python
from app.utils.data_processing import MetricsCalculator, DataProcessor

# MTTR calculation
mttr = MetricsCalculator.calculate_mttr(
    incidents=resolved_incidents,
    start_col="data_abertura",
    end_col="data_fechamento",
    group_by="tipo_equipamento"
)

# Trend analysis
trend_metrics = MetricsCalculator.calculate_trend_analysis(
    data=monthly_data,
    date_col="mes",
    value_col="mttr_medio",
    periods=12
)
```

---

## 6  Development Guidelines

### 6.1  Coding Standards

- **Type hints**: Use complete type annotations with `from __future__ import annotations`
- **Docstrings**: Google-style docstrings for all public functions
- **Error handling**: Use custom exceptions with context
- **Logging**: Structured logging with appropriate levels
- **Testing**: Unit tests with pytest and mocking for external dependencies

### 6.2  Performance Best Practices

- **Async Operations**: Use `run_async_safe()` for all async operations in Streamlit
- **Caching**: Leverage smart caching for expensive operations
- **Data Processing**: Process data in chunks for large datasets
- **Memory Management**: Monitor DataFrame memory usage and optimize dtypes

### 6.3  UI Best Practices

- **Component Reuse**: Use UI components instead of raw Streamlit widgets
- **Responsive Design**: Use GridLayout for responsive designs
- **Loading States**: Always show loading indicators for async operations
- **Error Handling**: Graceful degradation with user-friendly error messages

### 6.4  API Integration

- **Authentication**: Use ArkmedsAuth for JWT token management
- **Rate Limiting**: Respect API rate limits with exponential backoff
- **Error Handling**: Handle network errors gracefully
- **Data Validation**: Validate all API responses using SchemaValidator

---

## 7  Testing Strategy

### 7.1  Unit Tests (`tests/unit/`)

- Test core components in isolation
- Mock external dependencies (API, database)
- Focus on business logic and edge cases

### 7.2  Integration Tests (`tests/integration/`)

- Test component interactions
- Use test data for API responses
- Validate end-to-end workflows

### 7.3  UI Tests (`tests/ui/`)

- Test Streamlit page rendering
- Validate component behavior
- Check responsive layouts

---

## 8  Common Patterns

### 8.1  Adding a New Metric

1. Define calculation logic in appropriate service module
2. Add validation for required data columns
3. Create caching decorator if expensive
4. Add UI components for display
5. Write unit tests for calculation logic

### 8.2  Creating a New Page

1. Create page file in `app/pages/`
2. Use PageLayout for consistent structure
3. Import and use UI components
4. Add caching for data fetching
5. Handle errors gracefully

### 8.3  Adding New API Endpoints

1. Add method to ArkmedsClient
2. Define Pydantic models for response
3. Add validation in SchemaValidator
4. Create service layer function
5. Add caching if appropriate

---

## 9  Migration Notes

### 9.1  From Legacy to New Architecture

- Gradually migrate pages to use new UI components
- Replace direct API calls with service layer functions
- Move constants from `config/` to `core/constants.py`
- Update caching to use smart_cache decorators

### 9.2  Breaking Changes

- `st.cache_data` replaced with `smart_cache`
- Direct API calls should use service layer
- Configuration now centralized in `core/config.py`
- UI components require specific import patterns

---

This architecture provides a robust, maintainable, and scalable foundation for the Indicadores-comg dashboard application.
