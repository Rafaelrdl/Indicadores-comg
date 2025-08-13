"""Core data models for UI components."""

from typing import Any

from pydantic import BaseModel, field_validator


class Metric(BaseModel):
    """Model for individual metric display."""

    label: str
    value: str
    delta: str | None = None
    delta_color: str | None = "normal"
    icon: str | None = None
    help_text: str | None = None

    @field_validator("value", mode="before")
    @classmethod
    def convert_value_to_string(cls, v):
        """Convert numeric values to string."""
        if isinstance(v, (int, float)):
            return str(v)
        return v


class KPICard(BaseModel):
    """Model for KPI card with multiple metrics."""

    title: str
    metrics: list[Metric]
    description: str | None = None
    color: str | None = None


class ChartConfig(BaseModel):
    """Configuration for chart components."""

    chart_type: str
    title: str | None = None
    x_column: str | None = None
    y_column: str | None = None
    color_column: str | None = None
    height: int | None = 400
    show_legend: bool = True


class TableConfig(BaseModel):
    """Configuration for data table components."""

    columns: list[dict[str, Any]]
    filters: list[dict[str, Any]] | None = None
    searchable_columns: list[str] | None = None
    sortable: bool = True
    pagination: bool = False
    page_size: int = 10
