"""Advanced data table components with filtering and pagination."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union, Callable
import pandas as pd
import streamlit as st
from datetime import datetime, date


class TableConfig:
    """Configuration for table display and behavior."""
    
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    DATE_FORMAT = "%d/%m/%Y"
    DATETIME_FORMAT = "%d/%m/%Y %H:%M"
    
    COLUMN_TYPES = {
        'currency': lambda x: f"R$ {x:,.2f}" if pd.notnull(x) else "-",
        'percentage': lambda x: f"{x:.1f}%" if pd.notnull(x) else "-",
        'duration': lambda x: f"{x:.1f}h" if pd.notnull(x) else "-",
        'date': lambda x: x.strftime(TableConfig.DATE_FORMAT) if pd.notnull(x) else "-",
        'datetime': lambda x: x.strftime(TableConfig.DATETIME_FORMAT) if pd.notnull(x) else "-"
    }


class DataTable:
    """Advanced data table with filtering, sorting and pagination."""
    
    def __init__(
        self,
        data: pd.DataFrame,
        title: str = "Tabela de Dados",
        key_prefix: str = "table"
    ):
        """
        Initialize data table component.
        
        Args:
            data: DataFrame to display
            title: Table title
            key_prefix: Unique prefix for widget keys
        """
        self.data = data.copy() if not data.empty else pd.DataFrame()
        self.title = title
        self.key_prefix = key_prefix
        self.filtered_data = self.data.copy()
    
    def add_filters(
        self,
        filterable_columns: Optional[List[str]] = None,
        searchable_columns: Optional[List[str]] = None
    ) -> "DataTable":
        """
        Add filtering capabilities to the table.
        
        Args:
            filterable_columns: Columns that can be filtered with selectbox
            searchable_columns: Columns that can be searched with text input
        
        Returns:
            Self for method chaining
        """
        if self.data.empty:
            return self
        
        with st.expander("🔍 Filtros", expanded=False):
            # Text search
            if searchable_columns:
                search_term = st.text_input(
                    "Buscar",
                    key=f"{self.key_prefix}_search",
                    placeholder="Digite para buscar..."
                )
                
                if search_term:
                    search_mask = pd.Series([False] * len(self.filtered_data))
                    for col in searchable_columns:
                        if col in self.filtered_data.columns:
                            search_mask |= self.filtered_data[col].astype(str).str.contains(
                                search_term, case=False, na=False
                            )
                    self.filtered_data = self.filtered_data[search_mask]
            
            # Column filters
            if filterable_columns:
                filter_cols = st.columns(min(len(filterable_columns), 3))
                
                for i, col in enumerate(filterable_columns):
                    if col in self.filtered_data.columns:
                        with filter_cols[i % 3]:
                            unique_values = sorted(self.filtered_data[col].dropna().unique())
                            
                            if len(unique_values) > 0:
                                selected_values = st.multiselect(
                                    f"Filtrar {col}",
                                    options=unique_values,
                                    key=f"{self.key_prefix}_filter_{col}"
                                )
                                
                                if selected_values:
                                    self.filtered_data = self.filtered_data[
                                        self.filtered_data[col].isin(selected_values)
                                    ]
        
        return self
    
    def add_date_filter(
        self,
        date_column: str,
        default_range: Optional[tuple] = None
    ) -> "DataTable":
        """
        Add date range filter.
        
        Args:
            date_column: Column name containing dates
            default_range: Default date range (start, end)
        
        Returns:
            Self for method chaining
        """
        if self.data.empty or date_column not in self.data.columns:
            return self
        
        # Convert to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(self.filtered_data[date_column]):
            self.filtered_data[date_column] = pd.to_datetime(
                self.filtered_data[date_column], errors='coerce'
            )
        
        # Get date range
        min_date = self.filtered_data[date_column].min().date()
        max_date = self.filtered_data[date_column].max().date()
        
        if default_range:
            start_date, end_date = default_range
        else:
            start_date, end_date = min_date, max_date
        
        with st.container():
            col1, col2 = st.columns(2)
            
            with col1:
                start_filter = st.date_input(
                    "Data Início",
                    value=start_date,
                    min_value=min_date,
                    max_value=max_date,
                    key=f"{self.key_prefix}_date_start"
                )
            
            with col2:
                end_filter = st.date_input(
                    "Data Fim",
                    value=end_date,
                    min_value=min_date,
                    max_value=max_date,
                    key=f"{self.key_prefix}_date_end"
                )
            
            # Apply date filter
            if start_filter and end_filter:
                mask = (
                    (self.filtered_data[date_column].dt.date >= start_filter) &
                    (self.filtered_data[date_column].dt.date <= end_filter)
                )
                self.filtered_data = self.filtered_data[mask]
        
        return self
    
    def format_columns(
        self,
        column_formats: Dict[str, Union[str, Callable]]
    ) -> "DataTable":
        """
        Apply formatting to specific columns.
        
        Args:
            column_formats: Dictionary mapping column names to format types or functions
        
        Returns:
            Self for method chaining
        """
        for col, format_type in column_formats.items():
            if col in self.filtered_data.columns:
                if isinstance(format_type, str) and format_type in TableConfig.COLUMN_TYPES:
                    # Use predefined formatter
                    formatter = TableConfig.COLUMN_TYPES[format_type]
                    self.filtered_data[col] = self.filtered_data[col].apply(formatter)
                elif callable(format_type):
                    # Use custom formatter
                    self.filtered_data[col] = self.filtered_data[col].apply(format_type)
        
        return self
    
    def add_pagination(
        self,
        page_size: Optional[int] = None
    ) -> "DataTable":
        """
        Add pagination to the table.
        
        Args:
            page_size: Number of rows per page
        
        Returns:
            Self for method chaining
        """
        if self.filtered_data.empty:
            return self
        
        page_size = page_size or TableConfig.DEFAULT_PAGE_SIZE
        total_rows = len(self.filtered_data)
        total_pages = (total_rows - 1) // page_size + 1
        
        if total_pages > 1:
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                page = st.selectbox(
                    "Página",
                    range(1, total_pages + 1),
                    key=f"{self.key_prefix}_page",
                    format_func=lambda x: f"Página {x} de {total_pages}"
                )
            
            # Apply pagination
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, total_rows)
            self.filtered_data = self.filtered_data.iloc[start_idx:end_idx]
            
            # Show pagination info
            st.caption(f"Mostrando {start_idx + 1}-{end_idx} de {total_rows} registros")
        
        return self
    
    def render(
        self,
        column_config: Optional[Dict[str, Any]] = None,
        hide_index: bool = True,
        use_container_width: bool = True
    ) -> None:
        """
        Render the final table.
        
        Args:
            column_config: Streamlit column configuration
            hide_index: Whether to hide the DataFrame index
            use_container_width: Whether to use full container width
        """
        st.subheader(self.title)
        
        if self.filtered_data.empty:
            st.info("Nenhum dado disponível com os filtros aplicados.")
            return
        
        # Display summary
        st.caption(f"Total de registros: {len(self.filtered_data)}")
        
        # Render table
        st.dataframe(
            self.filtered_data,
            column_config=column_config,
            hide_index=hide_index,
            use_container_width=use_container_width
        )


class SummaryTable:
    """Component for displaying summary statistics tables."""
    
    @staticmethod
    def render_group_summary(
        data: pd.DataFrame,
        group_by: str,
        metrics: Dict[str, str],
        title: str = "Resumo por Grupo"
    ) -> None:
        """
        Render summary table grouped by a column.
        
        Args:
            data: DataFrame to summarize
            group_by: Column to group by
            metrics: Dictionary mapping metric names to aggregation functions
            title: Table title
        """
        if data.empty or group_by not in data.columns:
            st.warning(f"Não é possível gerar {title}")
            return
        
        st.subheader(title)
        
        # Calculate summary
        summary_data = []
        for group_value in data[group_by].unique():
            group_data = data[data[group_by] == group_value]
            row = {group_by: group_value}
            
            for metric_name, agg_func in metrics.items():
                try:
                    if agg_func == 'count':
                        row[metric_name] = len(group_data)
                    elif agg_func == 'mean':
                        numeric_cols = group_data.select_dtypes(include=['number'])
                        if not numeric_cols.empty:
                            row[metric_name] = numeric_cols.iloc[:, 0].mean()
                    elif agg_func == 'sum':
                        numeric_cols = group_data.select_dtypes(include=['number'])
                        if not numeric_cols.empty:
                            row[metric_name] = numeric_cols.iloc[:, 0].sum()
                    else:
                        row[metric_name] = None
                except:
                    row[metric_name] = None
            
            summary_data.append(row)
        
        summary_df = pd.DataFrame(summary_data)
        
        if not summary_df.empty:
            st.dataframe(summary_df, use_container_width=True)
        else:
            st.info("Nenhum dado de resumo disponível")
    
    @staticmethod
    def render_comparison_table(
        data1: pd.DataFrame,
        data2: pd.DataFrame,
        metrics: List[str],
        labels: tuple = ("Período 1", "Período 2"),
        title: str = "Tabela de Comparação"
    ) -> None:
        """
        Render comparison table between two datasets.
        
        Args:
            data1: First dataset
            data2: Second dataset
            metrics: List of metrics to compare
            labels: Labels for the two periods
            title: Table title
        """
        st.subheader(title)
        
        comparison_data = []
        
        for metric in metrics:
            row = {"Métrica": metric}
            
            # Calculate values for each dataset
            for i, (data, label) in enumerate([(data1, labels[0]), (data2, labels[1])]):
                if not data.empty and metric in data.columns:
                    if data[metric].dtype in ['int64', 'float64']:
                        value = data[metric].mean()
                        row[label] = f"{value:.2f}"
                    else:
                        row[label] = str(data[metric].iloc[0]) if len(data) > 0 else "-"
                else:
                    row[label] = "-"
            
            # Calculate difference if both values are numeric
            try:
                val1 = float(row[labels[0]]) if row[labels[0]] != "-" else 0
                val2 = float(row[labels[1]]) if row[labels[1]] != "-" else 0
                diff = val2 - val1
                diff_pct = (diff / val1 * 100) if val1 != 0 else 0
                row["Diferença"] = f"{diff:+.2f} ({diff_pct:+.1f}%)"
            except:
                row["Diferença"] = "-"
            
            comparison_data.append(row)
        
        comparison_df = pd.DataFrame(comparison_data)
        
        if not comparison_df.empty:
            st.dataframe(comparison_df, use_container_width=True)
        else:
            st.info("Nenhum dado de comparação disponível")


class ExportTable:
    """Component for table export functionality."""
    
    @staticmethod
    def add_export_buttons(
        data: pd.DataFrame,
        filename_prefix: str = "dados",
        formats: List[str] = ["csv", "excel"]
    ) -> None:
        """
        Add export buttons for downloading table data.
        
        Args:
            data: DataFrame to export
            filename_prefix: Prefix for downloaded filename
            formats: List of export formats ('csv', 'excel', 'json')
        """
        if data.empty:
            return
        
        st.subheader("📥 Exportar Dados")
        
        cols = st.columns(len(formats))
        
        for i, format_type in enumerate(formats):
            with cols[i]:
                if format_type == "csv":
                    csv_data = data.to_csv(index=False)
                    st.download_button(
                        label="📄 Baixar CSV",
                        data=csv_data,
                        file_name=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv"
                    )
                
                elif format_type == "excel":
                    # Note: This requires openpyxl to be installed
                    try:
                        excel_buffer = io.BytesIO()
                        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                            data.to_excel(writer, index=False, sheet_name='Dados')
                        excel_data = excel_buffer.getvalue()
                        
                        st.download_button(
                            label="📊 Baixar Excel",
                            data=excel_data,
                            file_name=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    except ImportError:
                        st.error("openpyxl não está instalado para exportação Excel")
                
                elif format_type == "json":
                    json_data = data.to_json(orient='records', indent=2)
                    st.download_button(
                        label="🔗 Baixar JSON",
                        data=json_data,
                        file_name=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json"
                    )
