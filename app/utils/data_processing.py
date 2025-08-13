"""Data transformation and processing utilities."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd


logger = logging.getLogger(__name__)


class DataProcessor:
    """Advanced data processing and transformation utilities."""

    @staticmethod
    def merge_datasets(
        datasets: list[pd.DataFrame],
        join_keys: list[str],
        how: str = 'inner',
        suffixes: list[str] | None = None
    ) -> pd.DataFrame:
        """
        Merge multiple datasets on common keys.
        
        Args:
            datasets: List of DataFrames to merge
            join_keys: Column names to join on
            how: Type of join ('inner', 'outer', 'left', 'right')
            suffixes: Suffixes for overlapping columns
        
        Returns:
            Merged DataFrame
        """
        if not datasets:
            return pd.DataFrame()

        if len(datasets) == 1:
            return datasets[0]

        try:
            # Start with first dataset
            result = datasets[0]

            for i, df in enumerate(datasets[1:], 1):
                suffix = suffixes[i] if suffixes and i < len(suffixes) else f"_{i}"

                result = result.merge(
                    df,
                    on=join_keys,
                    how=how,  # type: ignore
                    suffixes=('', suffix)
                )

            logger.info(f"Merged {len(datasets)} datasets into {len(result)} rows")
            return result

        except Exception as e:
            logger.error(f"Failed to merge datasets: {e!s}")
            return pd.DataFrame()

    @staticmethod
    def pivot_long_to_wide(
        df: pd.DataFrame,
        id_columns: list[str],
        value_column: str,
        category_column: str,
        agg_func: str = 'mean'
    ) -> pd.DataFrame:
        """
        Pivot data from long to wide format.
        
        Args:
            df: DataFrame in long format
            id_columns: Columns that identify unique records
            value_column: Column containing values to pivot
            category_column: Column containing categories for new columns
            agg_func: Aggregation function for duplicate values
        
        Returns:
            DataFrame in wide format
        """
        try:
            pivoted = df.pivot_table(
                index=id_columns,
                columns=category_column,
                values=value_column,
                aggfunc=agg_func,
                fill_value=0
            )

            # Flatten column names
            pivoted.columns.name = None
            pivoted = pivoted.reset_index()

            logger.info(f"Pivoted data from {len(df)} to {len(pivoted)} rows")
            return pivoted

        except Exception as e:
            logger.error(f"Failed to pivot data: {e!s}")
            return df

    @staticmethod
    def calculate_rolling_metrics(
        df: pd.DataFrame,
        date_column: str,
        value_columns: list[str],
        window_size: int,
        metrics: list[str] = ['mean', 'std', 'min', 'max']
    ) -> pd.DataFrame:
        """
        Calculate rolling window metrics.
        
        Args:
            df: DataFrame with time series data
            date_column: Date column for sorting
            value_columns: Columns to calculate metrics for
            window_size: Size of rolling window
            metrics: List of metrics to calculate
        
        Returns:
            DataFrame with rolling metrics
        """
        if df.empty or date_column not in df.columns:
            return df

        try:
            # Sort by date
            df_sorted = df.sort_values(date_column).copy()

            for col in value_columns:
                if col in df_sorted.columns:
                    for metric in metrics:
                        if metric == 'mean':
                            df_sorted[f'{col}_rolling_mean'] = df_sorted[col].rolling(window_size).mean()
                        elif metric == 'std':
                            df_sorted[f'{col}_rolling_std'] = df_sorted[col].rolling(window_size).std()
                        elif metric == 'min':
                            df_sorted[f'{col}_rolling_min'] = df_sorted[col].rolling(window_size).min()
                        elif metric == 'max':
                            df_sorted[f'{col}_rolling_max'] = df_sorted[col].rolling(window_size).max()

            return df_sorted

        except Exception as e:
            logger.error(f"Failed to calculate rolling metrics: {e!s}")
            return df

    @staticmethod
    def detect_anomalies(
        df: pd.DataFrame,
        value_column: str,
        method: str = 'zscore',
        threshold: float = 3.0
    ) -> pd.DataFrame:
        """
        Detect anomalies in numeric data.
        
        Args:
            df: DataFrame with data
            value_column: Column to analyze for anomalies
            method: Detection method ('zscore', 'iqr', 'isolation')
            threshold: Threshold for anomaly detection
        
        Returns:
            DataFrame with anomaly indicators
        """
        if df.empty or value_column not in df.columns:
            return df

        df_result = df.copy()

        try:
            if method == 'zscore':
                mean = df[value_column].mean()
                std = df[value_column].std()
                z_scores = np.abs((df[value_column] - mean) / std)
                df_result['is_anomaly'] = z_scores > threshold
                df_result['anomaly_score'] = z_scores

            elif method == 'iqr':
                Q1 = df[value_column].quantile(0.25)
                Q3 = df[value_column].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR

                df_result['is_anomaly'] = (
                    (df[value_column] < lower_bound) |
                    (df[value_column] > upper_bound)
                )
                df_result['anomaly_score'] = np.maximum(
                    (lower_bound - df[value_column]) / IQR,
                    (df[value_column] - upper_bound) / IQR
                )
                df_result['anomaly_score'] = np.maximum(df_result['anomaly_score'], 0)

            anomaly_count = df_result['is_anomaly'].sum()
            logger.info(f"Detected {anomaly_count} anomalies using {method} method")

            return df_result

        except Exception as e:
            logger.error(f"Failed to detect anomalies: {e!s}")
            return df


class MetricsCalculator:
    """Calculate KPI and business metrics."""

    @staticmethod
    def calculate_mttr(
        incidents: pd.DataFrame,
        start_col: str,
        end_col: str,
        group_by: str | None = None
    ) -> float | pd.DataFrame:
        """
        Calculate Mean Time To Repair (MTTR).
        
        Args:
            incidents: DataFrame with incident data
            start_col: Column with incident start time
            end_col: Column with incident end time
            group_by: Optional column to group by
        
        Returns:
            MTTR value or DataFrame with grouped MTTR
        """
        if incidents.empty:
            return 0.0 if group_by is None else pd.DataFrame()

        try:
            # Calculate resolution time in hours
            incidents = incidents.copy()
            incidents['resolution_time'] = (
                pd.to_datetime(incidents[end_col]) -
                pd.to_datetime(incidents[start_col])
            ).dt.total_seconds() / 3600

            # Filter out negative or null resolution times
            valid_incidents = incidents[
                (incidents['resolution_time'] > 0) &
                (incidents['resolution_time'].notna())
            ]

            if group_by:
                mttr_by_group = valid_incidents.groupby(group_by)['resolution_time'].mean()
                return mttr_by_group.reset_index(name='mttr')
            else:
                return valid_incidents['resolution_time'].mean()

        except Exception as e:
            logger.error(f"Failed to calculate MTTR: {e!s}")
            return 0.0 if group_by is None else pd.DataFrame()

    @staticmethod
    def calculate_mtbf(
        incidents: pd.DataFrame,
        equipment_uptime: pd.DataFrame,
        equipment_col: str = 'equipamento_id',
        time_col: str = 'data_abertura'
    ) -> pd.DataFrame:
        """
        Calculate Mean Time Between Failures (MTBF).
        
        Args:
            incidents: DataFrame with incident data
            equipment_uptime: DataFrame with equipment uptime data
            equipment_col: Column identifying equipment
            time_col: Column with time data
        
        Returns:
            DataFrame with MTBF by equipment
        """
        if incidents.empty or equipment_uptime.empty:
            return pd.DataFrame()

        try:
            # Count failures per equipment
            failure_counts = incidents.groupby(equipment_col).size().reset_index(name='failure_count')

            # Merge with uptime data
            mtbf_data = equipment_uptime.merge(failure_counts, on=equipment_col, how='left')
            mtbf_data['failure_count'] = mtbf_data['failure_count'].fillna(0)

            # Calculate MTBF (uptime hours / number of failures)
            mtbf_data['mtbf'] = np.where(
                mtbf_data['failure_count'] > 0,
                mtbf_data['uptime_hours'] / mtbf_data['failure_count'],
                mtbf_data['uptime_hours']  # No failures = total uptime
            )

            return mtbf_data[[equipment_col, 'mtbf', 'failure_count', 'uptime_hours']]

        except Exception as e:
            logger.error(f"Failed to calculate MTBF: {e!s}")
            return pd.DataFrame()

    @staticmethod
    def calculate_sla_compliance(
        tickets: pd.DataFrame,
        sla_hours: dict[str, float],
        priority_col: str = 'prioridade',
        resolution_time_col: str = 'tempo_resolucao'
    ) -> pd.DataFrame:
        """
        Calculate SLA compliance metrics.
        
        Args:
            tickets: DataFrame with ticket data
            sla_hours: Dictionary mapping priorities to SLA hours
            priority_col: Column with ticket priority
            resolution_time_col: Column with resolution time in hours
        
        Returns:
            DataFrame with SLA compliance by priority
        """
        if tickets.empty:
            return pd.DataFrame()

        try:
            tickets = tickets.copy()

            # Map SLA targets
            tickets['sla_target'] = tickets[priority_col].map(sla_hours)

            # Calculate compliance
            tickets['sla_met'] = tickets[resolution_time_col] <= tickets['sla_target']

            # Group by priority and calculate metrics
            sla_metrics = tickets.groupby(priority_col).agg({
                'sla_met': ['count', 'sum', 'mean'],
                resolution_time_col: ['mean', 'median']
            }).round(2)

            # Flatten column names
            sla_metrics.columns = [
                'total_tickets', 'tickets_met_sla', 'compliance_rate',
                'avg_resolution_time', 'median_resolution_time'
            ]

            sla_metrics['compliance_percentage'] = sla_metrics['compliance_rate'] * 100

            return sla_metrics.reset_index()

        except Exception as e:
            logger.error(f"Failed to calculate SLA compliance: {e!s}")
            return pd.DataFrame()

    @staticmethod
    def calculate_trend_analysis(
        data: pd.DataFrame,
        date_col: str,
        value_col: str,
        periods: int = 12
    ) -> dict[str, Any]:
        """
        Calculate trend analysis metrics.
        
        Args:
            data: DataFrame with time series data
            date_col: Date column
            value_col: Value column to analyze
            periods: Number of periods for trend calculation
        
        Returns:
            Dictionary with trend metrics
        """
        if data.empty or len(data) < 2:
            return {}

        try:
            # Sort by date and take last N periods
            data_sorted = data.sort_values(date_col).tail(periods)

            # Calculate basic statistics
            current_value = data_sorted[value_col].iloc[-1]
            previous_value = data_sorted[value_col].iloc[-2] if len(data_sorted) > 1 else current_value

            # Calculate trend
            change = current_value - previous_value
            percent_change = (change / previous_value * 100) if previous_value != 0 else 0

            # Calculate moving averages
            if len(data_sorted) >= 3:
                ma_3 = data_sorted[value_col].tail(3).mean()
            else:
                ma_3 = current_value

            if len(data_sorted) >= 7:
                ma_7 = data_sorted[value_col].tail(7).mean()
            else:
                ma_7 = current_value

            # Determine trend direction
            if len(data_sorted) >= 3:
                recent_values = data_sorted[value_col].tail(3).values
                if all(recent_values[i] <= recent_values[i+1] for i in range(len(recent_values)-1)):
                    trend_direction = "crescente"
                elif all(recent_values[i] >= recent_values[i+1] for i in range(len(recent_values)-1)):
                    trend_direction = "decrescente"
                else:
                    trend_direction = "estável"
            else:
                trend_direction = "estável"

            return {
                'current_value': current_value,
                'previous_value': previous_value,
                'change': change,
                'percent_change': percent_change,
                'ma_3': ma_3,
                'ma_7': ma_7,
                'trend_direction': trend_direction,
                'volatility': data_sorted[value_col].std(),
                'min_value': data_sorted[value_col].min(),
                'max_value': data_sorted[value_col].max()
            }

        except Exception as e:
            logger.error(f"Failed to calculate trend analysis: {e!s}")
            return {}


class DataAggregator:
    """Utilities for data aggregation and summarization."""

    @staticmethod
    def create_summary_stats(
        df: pd.DataFrame,
        numeric_columns: list[str] | None = None,
        categorical_columns: list[str] | None = None
    ) -> dict[str, pd.DataFrame]:
        """
        Create comprehensive summary statistics.
        
        Args:
            df: DataFrame to summarize
            numeric_columns: List of numeric columns to analyze
            categorical_columns: List of categorical columns to analyze
        
        Returns:
            Dictionary with different summary DataFrames
        """
        summaries = {}

        if df.empty:
            return summaries

        try:
            # Numeric summary
            if numeric_columns:
                numeric_cols = [col for col in numeric_columns if col in df.columns]
                if numeric_cols:
                    summaries['numeric'] = df[numeric_cols].describe()

            # Categorical summary
            if categorical_columns:
                categorical_cols = [col for col in categorical_columns if col in df.columns]
                if categorical_cols:
                    cat_summary = []
                    for col in categorical_cols:
                        value_counts = df[col].value_counts()
                        cat_summary.append({
                            'column': col,
                            'unique_values': df[col].nunique(),
                            'most_common': value_counts.index[0] if len(value_counts) > 0 else None,
                            'most_common_count': value_counts.iloc[0] if len(value_counts) > 0 else 0,
                            'null_count': df[col].isnull().sum()
                        })
                    summaries['categorical'] = pd.DataFrame(cat_summary)

            # Missing data summary
            missing_data = df.isnull().sum()
            missing_pct = (missing_data / len(df)) * 100
            summaries['missing'] = pd.DataFrame({
                'missing_count': missing_data,
                'missing_percentage': missing_pct
            }).round(2)

            return summaries

        except Exception as e:
            logger.error(f"Failed to create summary stats: {e!s}")
            return {}

    @staticmethod
    def aggregate_by_time_period(
        df: pd.DataFrame,
        date_col: str,
        value_cols: list[str],
        freq: str = 'D',
        agg_functions: dict[str, str | list[str]] | None = None
    ) -> pd.DataFrame:
        """
        Aggregate data by time periods with flexible aggregation functions.
        
        Args:
            df: DataFrame to aggregate
            date_col: Date column for grouping
            value_cols: Columns to aggregate
            freq: Frequency for aggregation ('D', 'W', 'M', 'Q', 'Y')
            agg_functions: Custom aggregation functions per column
        
        Returns:
            Aggregated DataFrame
        """
        if df.empty or date_col not in df.columns:
            return pd.DataFrame()

        try:
            # Default aggregation functions
            if agg_functions is None:
                agg_functions = dict.fromkeys(value_cols, 'mean')

            # Convert date column
            df_copy = df.copy()
            df_copy[date_col] = pd.to_datetime(df_copy[date_col])

            # Set date as index
            df_copy = df_copy.set_index(date_col)

            # Resample and aggregate
            aggregated = df_copy[value_cols].resample(freq).agg(agg_functions)  # type: ignore

            # Reset index
            aggregated = aggregated.reset_index()

            return aggregated

        except Exception as e:
            logger.error(f"Failed to aggregate by time period: {e!s}")
            return pd.DataFrame()

    @staticmethod
    def create_cross_tabulation(
        df: pd.DataFrame,
        row_col: str,
        col_col: str,
        value_col: str | None = None,
        agg_func: str = 'count'
    ) -> pd.DataFrame:
        """
        Create cross-tabulation (contingency table).
        
        Args:
            df: DataFrame with data
            row_col: Column for rows
            col_col: Column for columns
            value_col: Optional value column to aggregate
            agg_func: Aggregation function
        
        Returns:
            Cross-tabulation DataFrame
        """
        if df.empty:
            return pd.DataFrame()

        try:
            if value_col and value_col in df.columns:
                crosstab = pd.pivot_table(
                    df,
                    index=row_col,
                    columns=col_col,
                    values=value_col,
                    aggfunc=agg_func,  # type: ignore
                    fill_value=0
                )
            else:
                crosstab = pd.crosstab(df[row_col], df[col_col])

            return crosstab

        except Exception as e:
            logger.error(f"Failed to create cross-tabulation: {e!s}")
            return pd.DataFrame()
