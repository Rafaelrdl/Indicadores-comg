"""Reusable chart components using Plotly."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ...core.constants import COLORS


class ChartConfig:
    """Configuration for chart styling and behavior."""

    DEFAULT_HEIGHT = 400
    DEFAULT_WIDTH = None

    THEME = {
        'background_color': 'rgba(0,0,0,0)',
        'grid_color': 'rgba(128,128,128,0.2)',
        'text_color': '#262730',
        'font_family': 'Arial, sans-serif'
    }


class TimeSeriesCharts:
    """Components for time series visualizations."""

    @staticmethod
    def render_line_chart(
        data: pd.DataFrame,
        x_col: str,
        y_col: str,
        title: str,
        color_col: str | None = None,
        height: int = ChartConfig.DEFAULT_HEIGHT
    ) -> None:
        """
        Render a line chart for time series data.
        
        Args:
            data: DataFrame with time series data
            x_col: Column name for x-axis (usually date/time)
            y_col: Column name for y-axis
            title: Chart title
            color_col: Optional column for color grouping
            height: Chart height in pixels
        """
        if data.empty:
            st.warning(f"Nenhum dado disponível para {title}")
            return

        fig = px.line(
            data,
            x=x_col,
            y=y_col,
            color=color_col,
            title=title,
            height=height,
            color_discrete_sequence=list(COLORS.values())
        )

        fig.update_layout(
            plot_bgcolor=ChartConfig.THEME['background_color'],
            paper_bgcolor=ChartConfig.THEME['background_color'],
            font_family=ChartConfig.THEME['font_family'],
            font_color=ChartConfig.THEME['text_color']
        )

        fig.update_xaxes(gridcolor=ChartConfig.THEME['grid_color'])
        fig.update_yaxes(gridcolor=ChartConfig.THEME['grid_color'])

        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def render_area_chart(
        data: pd.DataFrame,
        x_col: str,
        y_col: str,
        title: str,
        fill_color: str = COLORS['primary']
    ) -> None:
        """
        Render an area chart for cumulative data.
        
        Args:
            data: DataFrame with time series data
            x_col: Column name for x-axis
            y_col: Column name for y-axis
            title: Chart title
            fill_color: Fill color for the area
        """
        if data.empty:
            st.warning(f"Nenhum dado disponível para {title}")
            return

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=data[x_col],
            y=data[y_col],
            fill='tonexty',
            mode='lines',
            name=y_col,
            line_color=fill_color,
            fillcolor=f"rgba{tuple(list(px.colors.hex_to_rgb(fill_color)) + [0.3])}"
        ))

        fig.update_layout(
            title=title,
            plot_bgcolor=ChartConfig.THEME['background_color'],
            paper_bgcolor=ChartConfig.THEME['background_color'],
            height=ChartConfig.DEFAULT_HEIGHT
        )

        st.plotly_chart(fig, use_container_width=True)


class DistributionCharts:
    """Components for distribution and categorical visualizations."""

    @staticmethod
    def render_bar_chart(
        data: pd.DataFrame,
        x_col: str,
        y_col: str,
        title: str,
        orientation: str = 'v',
        color_col: str | None = None
    ) -> None:
        """
        Render a bar chart.
        
        Args:
            data: DataFrame with categorical data
            x_col: Column name for x-axis
            y_col: Column name for y-axis
            title: Chart title
            orientation: 'v' for vertical, 'h' for horizontal
            color_col: Optional column for color grouping
        """
        if data.empty:
            st.warning(f"Nenhum dado disponível para {title}")
            return

        fig = px.bar(
            data,
            x=x_col if orientation == 'v' else y_col,
            y=y_col if orientation == 'v' else x_col,
            color=color_col,
            title=title,
            orientation=orientation,
            height=ChartConfig.DEFAULT_HEIGHT,
            color_discrete_sequence=list(COLORS.values())
        )

        fig.update_layout(
            plot_bgcolor=ChartConfig.THEME['background_color'],
            paper_bgcolor=ChartConfig.THEME['background_color']
        )

        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def render_pie_chart(
        data: pd.DataFrame,
        values_col: str,
        names_col: str,
        title: str,
        hole_size: float = 0.0
    ) -> None:
        """
        Render a pie or donut chart.
        
        Args:
            data: DataFrame with categorical data
            values_col: Column name for slice values
            names_col: Column name for slice labels
            title: Chart title
            hole_size: Size of center hole (0.0 for pie, >0 for donut)
        """
        if data.empty:
            st.warning(f"Nenhum dado disponível para {title}")
            return

        fig = px.pie(
            data,
            values=values_col,
            names=names_col,
            title=title,
            hole=hole_size,
            height=ChartConfig.DEFAULT_HEIGHT,
            color_discrete_sequence=list(COLORS.values())
        )

        fig.update_layout(
            plot_bgcolor=ChartConfig.THEME['background_color'],
            paper_bgcolor=ChartConfig.THEME['background_color']
        )

        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def render_histogram(
        data: pd.DataFrame,
        column: str,
        title: str,
        bins: int = 20,
        color: str = COLORS['primary']
    ) -> None:
        """
        Render a histogram for numeric data distribution.
        
        Args:
            data: DataFrame with numeric data
            column: Column name for histogram
            title: Chart title
            bins: Number of bins
            color: Bar color
        """
        if data.empty or column not in data.columns:
            st.warning(f"Nenhum dado disponível para {title}")
            return

        fig = px.histogram(
            data,
            x=column,
            title=title,
            nbins=bins,
            height=ChartConfig.DEFAULT_HEIGHT,
            color_discrete_sequence=[color]
        )

        fig.update_layout(
            plot_bgcolor=ChartConfig.THEME['background_color'],
            paper_bgcolor=ChartConfig.THEME['background_color']
        )

        st.plotly_chart(fig, use_container_width=True)


class KPICharts:
    """Specialized charts for KPI visualization."""

    @staticmethod
    def render_gauge_chart(
        value: float,
        title: str,
        min_val: float = 0,
        max_val: float = 100,
        target: float | None = None,
        thresholds: dict[str, float] | None = None
    ) -> None:
        """
        Render a gauge chart for KPI visualization.
        
        Args:
            value: Current value
            title: Chart title
            min_val: Minimum value for scale
            max_val: Maximum value for scale
            target: Optional target value
            thresholds: Optional thresholds for color zones
        """
        # Default thresholds
        if thresholds is None:
            thresholds = {
                'red': max_val * 0.3,
                'yellow': max_val * 0.7,
                'green': max_val
            }

        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = value,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': title},
            delta = {'reference': target} if target else None,
            gauge = {
                'axis': {'range': [None, max_val]},
                'bar': {'color': COLORS['primary']},
                'steps': [
                    {'range': [min_val, thresholds['red']], 'color': COLORS['danger']},
                    {'range': [thresholds['red'], thresholds['yellow']], 'color': COLORS['warning']},
                    {'range': [thresholds['yellow'], max_val], 'color': COLORS['success']}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': target or max_val * 0.9
                }
            }
        ))

        fig.update_layout(
            height=300,
            plot_bgcolor=ChartConfig.THEME['background_color'],
            paper_bgcolor=ChartConfig.THEME['background_color']
        )

        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def render_trend_indicators(
        current_values: dict[str, float],
        previous_values: dict[str, float],
        title: str = "Indicadores de Tendência"
    ) -> None:
        """
        Render trend indicators comparing current vs previous periods.
        
        Args:
            current_values: Current period values
            previous_values: Previous period values
            title: Chart title
        """
        st.subheader(title)

        cols = st.columns(len(current_values))

        for i, (metric, current_val) in enumerate(current_values.items()):
            with cols[i]:
                previous_val = previous_values.get(metric, 0)

                # Calculate trend
                if previous_val != 0:
                    trend = ((current_val - previous_val) / previous_val) * 100
                    trend_icon = "📈" if trend > 0 else "📉" if trend < 0 else "➡️"
                    trend_color = "green" if trend > 0 else "red" if trend < 0 else "gray"
                else:
                    trend = 0
                    trend_icon = "➡️"
                    trend_color = "gray"

                st.metric(
                    label=f"{trend_icon} {metric}",
                    value=f"{current_val:.1f}",
                    delta=f"{trend:+.1f}%"
                )


class ComparisonCharts:
    """Charts for comparative analysis."""

    @staticmethod
    def render_comparison_bar(
        data: dict[str, list[float]],
        categories: list[str],
        title: str,
        y_title: str = "Valores"
    ) -> None:
        """
        Render grouped bar chart for comparison.
        
        Args:
            data: Dictionary with series names as keys and values as lists
            categories: Category labels for x-axis
            title: Chart title
            y_title: Y-axis title
        """
        fig = go.Figure()

        colors = list(COLORS.values())

        for i, (series_name, values) in enumerate(data.items()):
            fig.add_trace(go.Bar(
                name=series_name,
                x=categories,
                y=values,
                marker_color=colors[i % len(colors)]
            ))

        fig.update_layout(
            title=title,
            xaxis_title="Categorias",
            yaxis_title=y_title,
            barmode='group',
            height=ChartConfig.DEFAULT_HEIGHT,
            plot_bgcolor=ChartConfig.THEME['background_color'],
            paper_bgcolor=ChartConfig.THEME['background_color']
        )

        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def render_before_after_chart(
        before_data: pd.DataFrame,
        after_data: pd.DataFrame,
        metric_col: str,
        category_col: str,
        title: str = "Comparação Antes vs Depois"
    ) -> None:
        """
        Render before/after comparison chart.
        
        Args:
            before_data: DataFrame with before data
            after_data: DataFrame with after data
            metric_col: Column name for metric values
            category_col: Column name for categories
            title: Chart title
        """
        # Combine data for comparison
        before_summary = before_data.groupby(category_col)[metric_col].mean().reset_index()
        after_summary = after_data.groupby(category_col)[metric_col].mean().reset_index()

        before_summary['Period'] = 'Antes'
        after_summary['Period'] = 'Depois'

        combined_data = pd.concat([before_summary, after_summary], ignore_index=True)

        fig = px.bar(
            combined_data,
            x=category_col,
            y=metric_col,
            color='Period',
            title=title,
            barmode='group',
            height=ChartConfig.DEFAULT_HEIGHT,
            color_discrete_sequence=[COLORS['secondary'], COLORS['primary']]
        )

        fig.update_layout(
            plot_bgcolor=ChartConfig.THEME['background_color'],
            paper_bgcolor=ChartConfig.THEME['background_color']
        )

        st.plotly_chart(fig, use_container_width=True)
