"""Reusable metric display components."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from ...data.models import KPICard, Metric


class MetricsDisplay:
    """Component for displaying metrics in various layouts."""

    @staticmethod
    def render_metric_cards(metrics: list[Metric], columns: int = 3) -> None:
        """
        Render metrics as cards in a grid layout.
        
        Args:
            metrics: List of metrics to display
            columns: Number of columns in the grid
        """
        if not metrics:
            st.info("Nenhuma métrica disponível.")
            return

        cols = st.columns(columns)

        for i, metric in enumerate(metrics):
            col_idx = i % columns
            with cols[col_idx]:
                # Add icon if provided
                label = f"{metric.icon} {metric.label}" if metric.icon else metric.label

                st.metric(
                    label=label,
                    value=metric.value,
                    delta=metric.delta,
                    delta_color=metric.delta_color,
                    help=metric.help_text
                )

    @staticmethod
    def render_kpi_dashboard(kpis: list[KPICard]) -> None:
        """
        Render KPI dashboard with grouped metrics.
        
        Args:
            kpis: List of KPI cards to display
        """
        for kpi in kpis:
            st.subheader(kpi.title)

            # Use equal column widths for all metrics
            cols = st.columns(len(kpi.metrics))

            for i, metric in enumerate(kpi.metrics):
                with cols[i]:
                    label = f"{metric.icon} {metric.label}" if metric.icon else metric.label
                    st.metric(
                        label=label,
                        value=metric.value,
                        delta=metric.delta,
                        delta_color=metric.delta_color,
                        help=metric.help_text
                    )

            st.divider()

    @staticmethod
    def render_summary_metrics(
        title: str,
        metrics_data: dict[str, Any],
        layout: str = "horizontal"
    ) -> None:
        """
        Render summary metrics with customizable layout.
        
        Args:
            title: Section title
            metrics_data: Dictionary with metric names as keys and values
            layout: Layout type ('horizontal' or 'vertical')
        """
        st.header(title)

        if layout == "horizontal":
            cols = st.columns(len(metrics_data))
            for i, (label, value) in enumerate(metrics_data.items()):
                with cols[i]:
                    st.metric(label=label, value=value)
        else:
            for label, value in metrics_data.items():
                st.metric(label=label, value=value)

    @staticmethod
    def render_comparison_metrics(
        current_metrics: dict[str, Any],
        previous_metrics: dict[str, Any],
        title: str = "Comparação com Período Anterior"
    ) -> None:
        """
        Render metrics with comparison to previous period.
        
        Args:
            current_metrics: Current period metrics
            previous_metrics: Previous period metrics for comparison
            title: Section title
        """
        st.header(title)

        cols = st.columns(len(current_metrics))

        for i, (label, current_value) in enumerate(current_metrics.items()):
            with cols[i]:
                previous_value = previous_metrics.get(label, 0)

                # Calculate delta
                if isinstance(current_value, (int, float)) and isinstance(previous_value, (int, float)):
                    delta = current_value - previous_value
                    delta_percent = (delta / previous_value * 100) if previous_value != 0 else 0
                    delta_display = f"{delta:+.1f} ({delta_percent:+.1f}%)"
                else:
                    delta_display = None

                st.metric(
                    label=label,
                    value=current_value,
                    delta=delta_display
                )


class ProgressIndicators:
    """Component for progress and status indicators."""

    @staticmethod
    def render_progress_bar(
        label: str,
        value: float,
        max_value: float = 100.0,
        format_string: str = "%.1f",
        color: str | None = None
    ) -> None:
        """
        Render a progress bar with label.
        
        Args:
            label: Progress bar label
            value: Current value
            max_value: Maximum value (default 100)
            format_string: Format for displaying value
            color: Custom color (not supported in Streamlit)
        """
        progress_percent = min(value / max_value, 1.0) if max_value > 0 else 0

        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(label)
            st.progress(progress_percent)
        with col2:
            st.metric("", f"{format_string % value}/{format_string % max_value}")

    @staticmethod
    def render_status_indicators(
        statuses: dict[str, str],
        colors: dict[str, str] | None = None
    ) -> None:
        """
        Render status indicators with colored badges.
        
        Args:
            statuses: Dictionary with status names and values
            colors: Optional color mapping for statuses
        """
        cols = st.columns(len(statuses))

        for i, (label, status) in enumerate(statuses.items()):
            with cols[i]:
                # Use colors if provided
                if colors and status in colors:
                    color = colors[status]
                    st.markdown(
                        f"**{label}**: <span style='color: {color}'>{status}</span>",
                        unsafe_allow_html=True
                    )
                else:
                    st.write(f"**{label}**: {status}")


class DataCards:
    """Component for data cards and info boxes."""

    @staticmethod
    def render_info_card(
        title: str,
        content: str,
        icon: str | None = None,
        color: str = "info"
    ) -> None:
        """
        Render an information card.
        
        Args:
            title: Card title
            content: Card content
            icon: Optional icon
            color: Card color theme
        """
        title_with_icon = f"{icon} {title}" if icon else title

        if color == "success":
            st.success(f"**{title_with_icon}**\n\n{content}")
        elif color == "warning":
            st.warning(f"**{title_with_icon}**\n\n{content}")
        elif color == "error":
            st.error(f"**{title_with_icon}**\n\n{content}")
        else:
            st.info(f"**{title_with_icon}**\n\n{content}")

    @staticmethod
    def render_data_summary_card(
        data: pd.DataFrame,
        title: str = "Resumo dos Dados"
    ) -> None:
        """
        Render a data summary card showing key statistics.
        
        Args:
            data: DataFrame to summarize
            title: Card title
        """
        if data.empty:
            st.warning(f"**{title}**: Nenhum dado disponível")
            return

        with st.container():
            st.subheader(title)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total de Registros", len(data))

            with col2:
                st.metric("Colunas", len(data.columns))

            with col3:
                # Calculate completeness
                completeness = (1 - data.isnull().sum().sum() / (len(data) * len(data.columns))) * 100
                st.metric("Completude", f"{completeness:.1f}%")
