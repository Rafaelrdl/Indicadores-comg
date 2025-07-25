"""Core data models for UI components."""

from typing import Any, Optional, List, Dict, Union
from pydantic import BaseModel, field_validator


class Metric(BaseModel):
    """Model for individual metric display."""
    label: str
    value: str
    delta: Optional[str] = None
    delta_color: Optional[str] = "normal"
    icon: Optional[str] = None
    help_text: Optional[str] = None
    
    @field_validator('value', mode='before')
    @classmethod
    def convert_value_to_string(cls, v):
        """Convert numeric values to string."""
        if isinstance(v, (int, float)):
            return str(v)
        return v


class KPICard(BaseModel):
    """Model for KPI card with multiple metrics."""
    title: str
    metrics: List[Metric]
    description: Optional[str] = None
    color: Optional[str] = None


class ChartConfig(BaseModel):
    """Configuration for chart components."""
    chart_type: str
    title: Optional[str] = None
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    color_column: Optional[str] = None
    height: Optional[int] = 400
    show_legend: bool = True


class TableConfig(BaseModel):
    """Configuration for data table components."""
    columns: List[Dict[str, Any]]
    filters: Optional[List[Dict[str, Any]]] = None
    searchable_columns: Optional[List[str]] = None
    sortable: bool = True
    pagination: bool = False
    page_size: int = 10
