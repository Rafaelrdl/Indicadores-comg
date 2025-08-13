"""Layout components for consistent page structure."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Union

import streamlit as st

from ...core.constants import COLORS


class PageLayout:
    """Main page layout component with consistent structure."""

    def __init__(
        self,
        title: str,
        description: str | None = None,
        icon: str | None = None,
        layout: str = "wide"
    ):
        """
        Initialize page layout.
        
        Args:
            title: Page title
            description: Optional page description
            icon: Optional icon for the title
            layout: Streamlit layout mode ('wide' or 'centered')
        """
        self.title = title
        self.description = description
        self.icon = icon
        self.layout = layout

    def render_header(self) -> None:
        """Render page header with title and description."""
        # Title with optional icon
        if self.icon:
            st.title(f"{self.icon} {self.title}")
        else:
            st.title(self.title)

        # Description if provided
        if self.description:
            st.markdown(f"*{self.description}*")

        st.divider()

    @contextmanager
    def main_content(self):
        """Context manager for main content area."""
        st.container()
        yield

    @contextmanager
    def sidebar_content(self):
        """Context manager for sidebar content."""
        with st.sidebar:
            yield

    def render_footer(self, additional_info: str | None = None) -> None:
        """
        Render page footer.
        
        Args:
            additional_info: Optional additional information to display
        """
        st.divider()

        footer_cols = st.columns([2, 1])

        with footer_cols[0]:
            if additional_info:
                st.caption(additional_info)

        with footer_cols[1]:
            st.caption("Indicadores COMG © 2024")


class SectionLayout:
    """Component for creating consistent page sections."""

    @staticmethod
    @contextmanager
    def section(
        title: str,
        description: str | None = None,
        expanded: bool = True,
        border: bool = False
    ):
        """
        Create a collapsible section.
        
        Args:
            title: Section title
            description: Optional section description
            expanded: Whether section is expanded by default
            border: Whether to add border around section
        """
        with st.expander(title, expanded=expanded):
            if description:
                st.markdown(f"*{description}*")
                st.markdown("---")

            if border:
                with st.container():
                    yield
            else:
                yield

    @staticmethod
    @contextmanager
    def metric_section(title: str, columns: int = 3):
        """
        Create a section optimized for metrics display.
        
        Args:
            title: Section title
            columns: Number of metric columns
        """
        st.subheader(title)
        cols = st.columns(columns)
        yield cols
        st.markdown("---")

    @staticmethod
    @contextmanager
    def chart_section(title: str, full_width: bool = True):
        """
        Create a section optimized for charts.
        
        Args:
            title: Section title
            full_width: Whether to use full width
        """
        st.subheader(title)

        if full_width:
            with st.container():
                yield
        else:
            col1, col2, col3 = st.columns([1, 4, 1])
            with col2:
                yield

        st.markdown("---")

    @staticmethod
    @contextmanager
    def data_section(title: str, show_summary: bool = True):
        """
        Create a section optimized for data tables.
        
        Args:
            title: Section title
            show_summary: Whether to show data summary
        """
        st.subheader(title)

        container = st.container()
        yield container

        if show_summary:
            st.markdown("---")


class GridLayout:
    """Component for creating responsive grid layouts."""

    @staticmethod
    def two_column_layout(
        left_content: Callable,
        right_content: Callable,
        ratio: list[int] = [1, 1]
    ) -> None:
        """
        Create a two-column layout.
        
        Args:
            left_content: Function to render left column content
            right_content: Function to render right column content
            ratio: Column width ratio
        """
        col1, col2 = st.columns(ratio)

        with col1:
            left_content()

        with col2:
            right_content()

    @staticmethod
    def three_column_layout(
        left_content: Callable,
        center_content: Callable,
        right_content: Callable,
        ratio: list[int] = [1, 1, 1]
    ) -> None:
        """
        Create a three-column layout.
        
        Args:
            left_content: Function to render left column content
            center_content: Function to render center column content
            right_content: Function to render right column content
            ratio: Column width ratio
        """
        col1, col2, col3 = st.columns(ratio)

        with col1:
            left_content()

        with col2:
            center_content()

        with col3:
            right_content()

    @staticmethod
    def responsive_grid(
        content_functions: list[Callable],
        max_columns: int = 3,
        equal_width: bool = True
    ) -> None:
        """
        Create a responsive grid that adapts to content.
        
        Args:
            content_functions: List of functions to render content
            max_columns: Maximum number of columns
            equal_width: Whether columns should have equal width
        """
        num_items = len(content_functions)
        num_columns = min(num_items, max_columns)

        if equal_width:
            cols = st.columns(num_columns)
        else:
            cols = st.columns([1] * num_columns)

        for i, content_func in enumerate(content_functions):
            col_idx = i % num_columns
            with cols[col_idx]:
                content_func()


class CardLayout:
    """Component for creating card-based layouts."""

    @staticmethod
    @contextmanager
    def card(
        title: str | None = None,
        subtitle: str | None = None,
        background_color: str = "rgba(255, 255, 255, 0.05)",
        border_radius: str = "10px",
        padding: str = "20px"
    ):
        """
        Create a card container with styling.
        
        Args:
            title: Optional card title
            subtitle: Optional card subtitle
            background_color: Background color
            border_radius: Border radius
            padding: Internal padding
        """
        # Apply custom styling
        card_style = f"""
        <div style="
            background-color: {background_color};
            border-radius: {border_radius};
            padding: {padding};
            margin: 10px 0;
            border: 1px solid rgba(255, 255, 255, 0.1);
        ">
        """

        st.markdown(card_style, unsafe_allow_html=True)

        if title:
            st.subheader(title)

        if subtitle:
            st.caption(subtitle)

        yield

        st.markdown("</div>", unsafe_allow_html=True)

    @staticmethod
    def metric_card(
        title: str,
        value: int | float | str,
        delta: int | float | str | None = None,
        delta_color: str | None = None,
        icon: str | None = None,
        color: str = COLORS['primary']
    ) -> None:
        """
        Create a styled metric card.
        
        Args:
            title: Metric title
            value: Metric value
            delta: Optional delta value
            delta_color: Delta color ('normal', 'inverse', or 'off')
            icon: Optional icon
            color: Card accent color
        """
        with CardLayout.card():
            if icon:
                st.markdown(f"### {icon} {title}")
            else:
                st.markdown(f"### {title}")

            st.metric(
                label="",
                value=value,
                delta=delta,
                delta_color=delta_color
            )

    @staticmethod
    def info_card(
        title: str,
        content: str,
        icon: str | None = None,
        type: str = "info"
    ) -> None:
        """
        Create an information card.
        
        Args:
            title: Card title
            content: Card content
            icon: Optional icon
            type: Card type ('info', 'success', 'warning', 'error')
        """
        title_with_icon = f"{icon} {title}" if icon else title

        if type == "success":
            st.success(f"**{title_with_icon}**\n\n{content}")
        elif type == "warning":
            st.warning(f"**{title_with_icon}**\n\n{content}")
        elif type == "error":
            st.error(f"**{title_with_icon}**\n\n{content}")
        else:
            st.info(f"**{title_with_icon}**\n\n{content}")


class ModalLayout:
    """Component for modal-like dialogs."""

    @staticmethod
    @contextmanager
    def modal(
        title: str,
        key: str,
        max_width: str = "700px"
    ):
        """
        Create a modal dialog using Streamlit's dialog decorator.
        
        Args:
            title: Modal title
            key: Unique key for the modal
            max_width: Maximum width of the modal
        """
        # Note: This is a placeholder for future modal functionality
        # Streamlit doesn't have native modals, so we use expanders
        with st.expander(f"🔍 {title}", expanded=False):
            yield

    @staticmethod
    def confirmation_dialog(
        message: str,
        confirm_label: str = "Confirmar",
        cancel_label: str = "Cancelar",
        key: str = "confirm"
    ) -> bool | None:
        """
        Create a confirmation dialog.
        
        Args:
            message: Confirmation message
            confirm_label: Confirm button label
            cancel_label: Cancel button label
            key: Unique key for the dialog
        
        Returns:
            True if confirmed, False if cancelled, None if no action
        """
        st.warning(message)

        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button(confirm_label, key=f"{key}_confirm", type="primary"):
                return True

        with col2:
            if st.button(cancel_label, key=f"{key}_cancel"):
                return False

        return None


class ProgressLayout:
    """Component for progress indicators and loading states."""

    @staticmethod
    @contextmanager
    def loading_spinner(message: str = "Carregando..."):
        """
        Show loading spinner during operation.
        
        Args:
            message: Loading message
        """
        with st.spinner(message):
            yield

    @staticmethod
    def progress_bar(
        current: int,
        total: int,
        message: str = "Processando..."
    ) -> None:
        """
        Show progress bar.
        
        Args:
            current: Current progress value
            total: Total value
            message: Progress message
        """
        progress_percent = current / total if total > 0 else 0
        st.progress(progress_percent, text=f"{message} ({current}/{total})")

    @staticmethod
    @contextmanager
    def step_progress(steps: list[str], current_step: int = 0):
        """
        Show step-by-step progress.
        
        Args:
            steps: List of step descriptions
            current_step: Current step index (0-based)
        """
        st.subheader("Progresso")

        for i, step in enumerate(steps):
            if i < current_step:
                st.success(f"✅ {step}")
            elif i == current_step:
                st.info(f"🔄 {step}")
            else:
                st.write(f"⏳ {step}")

        st.divider()
        yield
