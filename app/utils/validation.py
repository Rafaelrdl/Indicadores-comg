"""Data validation utilities for robust data handling."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union, Tuple, Type
import pandas as pd
import numpy as np
from datetime import datetime, date
from pydantic import BaseModel, ValidationError
import logging

from ..core.exceptions import DataValidationError, ConfigurationError
from ..core.constants import OSType, OSStatus, EquipmentStatus

logger = logging.getLogger(__name__)


class DataValidator:
    """Comprehensive data validation utilities."""
    
    @staticmethod
    def validate_dataframe(
        df: pd.DataFrame,
        required_columns: List[str],
        name: str = "DataFrame"
    ) -> pd.DataFrame:
        """
        Validate DataFrame structure and required columns.
        
        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            name: Name for error messages
        
        Returns:
            Validated DataFrame
        
        Raises:
            DataValidationError: If validation fails
        """
        if df is None:
            raise DataValidationError(f"{name} is None")
        
        if df.empty:
            logger.warning(f"{name} is empty")
            return df
        
        # Check required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise DataValidationError(
                f"{name} missing required columns: {missing_columns}"
            )
        
        logger.info(f"{name} validation passed: {len(df)} rows, {len(df.columns)} columns")
        return df
    
    @staticmethod
    def validate_date_column(
        df: pd.DataFrame,
        column: str,
        date_format: Optional[str] = None,
        allow_null: bool = True
    ) -> pd.DataFrame:
        """
        Validate and convert date column.
        
        Args:
            df: DataFrame containing the date column
            column: Name of the date column
            date_format: Expected date format (None for auto-detection)
            allow_null: Whether to allow null values
        
        Returns:
            DataFrame with validated date column
        
        Raises:
            DataValidationError: If date validation fails
        """
        if column not in df.columns:
            raise DataValidationError(f"Date column '{column}' not found")
        
        try:
            # Convert to datetime
            if date_format:
                df[column] = pd.to_datetime(df[column], format=date_format, errors='coerce')
            else:
                df[column] = pd.to_datetime(df[column], errors='coerce')
            
            # Check for null values
            null_count = df[column].isnull().sum()
            if null_count > 0:
                if not allow_null:
                    raise DataValidationError(
                        f"Date column '{column}' contains {null_count} null values"
                    )
                else:
                    logger.warning(f"Date column '{column}' has {null_count} null values")
            
            return df
        
        except Exception as e:
            raise DataValidationError(f"Failed to validate date column '{column}': {str(e)}")
    
    @staticmethod
    def validate_numeric_column(
        df: pd.DataFrame,
        column: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        allow_null: bool = True
    ) -> pd.DataFrame:
        """
        Validate numeric column values.
        
        Args:
            df: DataFrame containing the numeric column
            column: Name of the numeric column
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            allow_null: Whether to allow null values
        
        Returns:
            DataFrame with validated numeric column
        
        Raises:
            DataValidationError: If validation fails
        """
        if column not in df.columns:
            raise DataValidationError(f"Numeric column '{column}' not found")
        
        # Convert to numeric
        df[column] = pd.to_numeric(df[column], errors='coerce')
        
        # Check for null values
        null_count = df[column].isnull().sum()
        if null_count > 0 and not allow_null:
            raise DataValidationError(
                f"Numeric column '{column}' contains {null_count} null values"
            )
        
        # Check value ranges
        valid_values = df[column].dropna()
        
        if min_value is not None:
            below_min = (valid_values < min_value).sum()
            if below_min > 0:
                raise DataValidationError(
                    f"Column '{column}' has {below_min} values below minimum {min_value}"
                )
        
        if max_value is not None:
            above_max = (valid_values > max_value).sum()
            if above_max > 0:
                raise DataValidationError(
                    f"Column '{column}' has {above_max} values above maximum {max_value}"
                )
        
        return df
    
    @staticmethod
    def validate_categorical_column(
        df: pd.DataFrame,
        column: str,
        allowed_values: Optional[List[Any]] = None,
        case_sensitive: bool = True
    ) -> pd.DataFrame:
        """
        Validate categorical column values.
        
        Args:
            df: DataFrame containing the categorical column
            column: Name of the categorical column
            allowed_values: List of allowed values (None for no restriction)
            case_sensitive: Whether validation should be case sensitive
        
        Returns:
            DataFrame with validated categorical column
        
        Raises:
            DataValidationError: If validation fails
        """
        if column not in df.columns:
            raise DataValidationError(f"Categorical column '{column}' not found")
        
        if allowed_values is not None:
            # Normalize for comparison if case insensitive
            if not case_sensitive:
                df[column] = df[column].astype(str).str.lower()
                allowed_values = [str(val).lower() for val in allowed_values]
            
            # Check for invalid values
            valid_mask = df[column].isin(allowed_values)
            invalid_count = (~valid_mask).sum()
            
            if invalid_count > 0:
                invalid_values = df[~valid_mask][column].unique()
                raise DataValidationError(
                    f"Column '{column}' contains {invalid_count} invalid values: {invalid_values}"
                )
        
        return df
    
    @staticmethod
    def validate_pydantic_model(
        data: Dict[str, Any],
        model_class: Type[BaseModel]
    ) -> BaseModel:
        """
        Validate data against Pydantic model.
        
        Args:
            data: Data to validate
            model_class: Pydantic model class
        
        Returns:
            Validated model instance
        
        Raises:
            DataValidationError: If validation fails
        """
        try:
            return model_class(**data)
        except ValidationError as e:
            raise DataValidationError(f"Pydantic validation failed: {str(e)}")


class DataCleaner:
    """Data cleaning and preprocessing utilities."""
    
    @staticmethod
    def clean_string_column(
        df: pd.DataFrame,
        column: str,
        strip_whitespace: bool = True,
        remove_empty: bool = True,
        normalize_case: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Clean string column values.
        
        Args:
            df: DataFrame to clean
            column: Column name to clean
            strip_whitespace: Whether to strip leading/trailing whitespace
            remove_empty: Whether to replace empty strings with NaN
            normalize_case: Case normalization ('upper', 'lower', 'title')
        
        Returns:
            DataFrame with cleaned string column
        """
        if column not in df.columns:
            return df
        
        # Convert to string
        df[column] = df[column].astype(str)
        
        # Strip whitespace
        if strip_whitespace:
            df[column] = df[column].str.strip()
        
        # Remove empty strings
        if remove_empty:
            df[column] = df[column].replace('', np.nan)
        
        # Normalize case
        if normalize_case == 'upper':
            df[column] = df[column].str.upper()
        elif normalize_case == 'lower':
            df[column] = df[column].str.lower()
        elif normalize_case == 'title':
            df[column] = df[column].str.title()
        
        return df
    
    @staticmethod
    def remove_duplicates(
        df: pd.DataFrame,
        subset: Optional[List[str]] = None,
        keep: str = 'first'
    ) -> pd.DataFrame:
        """
        Remove duplicate rows from DataFrame.
        
        Args:
            df: DataFrame to clean
            subset: Columns to consider for identifying duplicates
            keep: Which duplicates to keep ('first', 'last', False)
        
        Returns:
            DataFrame with duplicates removed
        """
        initial_count = len(df)
        df_clean = df.drop_duplicates(subset=subset, keep=keep)
        removed_count = initial_count - len(df_clean)
        
        if removed_count > 0:
            logger.info(f"Removed {removed_count} duplicate rows")
        
        return df_clean
    
    @staticmethod
    def handle_outliers(
        df: pd.DataFrame,
        column: str,
        method: str = 'iqr',
        threshold: float = 1.5
    ) -> pd.DataFrame:
        """
        Handle outliers in numeric column.
        
        Args:
            df: DataFrame to process
            column: Numeric column name
            method: Outlier detection method ('iqr', 'zscore')
            threshold: Threshold for outlier detection
        
        Returns:
            DataFrame with outliers handled
        """
        if column not in df.columns or df[column].dtype not in ['int64', 'float64']:
            return df
        
        if method == 'iqr':
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            
            outlier_mask = (df[column] < lower_bound) | (df[column] > upper_bound)
        
        elif method == 'zscore':
            mean = df[column].mean()
            std = df[column].std()
            z_scores = np.abs((df[column] - mean) / std)
            outlier_mask = z_scores > threshold
        
        else:
            logger.warning(f"Unknown outlier method: {method}")
            return df
        
        outlier_count = outlier_mask.sum()
        if outlier_count > 0:
            logger.info(f"Found {outlier_count} outliers in column '{column}'")
            # Replace outliers with NaN (could also cap them)
            df.loc[outlier_mask, column] = np.nan
        
        return df


class DataTransformer:
    """Data transformation utilities."""
    
    @staticmethod
    def parse_arkmeds_datetime(
        datetime_str: str
    ) -> Optional[datetime]:
        """
        Parse Arkmeds datetime format (DD/MM/YY - HH:MM).
        
        Args:
            datetime_str: Datetime string from Arkmeds API
        
        Returns:
            Parsed datetime object or None if parsing fails
        """
        if not datetime_str or pd.isna(datetime_str):
            return None
        
        try:
            # Handle different formats from Arkmeds
            formats = [
                "%d/%m/%y - %H:%M",
                "%d/%m/%Y - %H:%M",
                "%d/%m/%y %H:%M",
                "%d/%m/%Y %H:%M",
                "%d/%m/%Y",
                "%d/%m/%y"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(str(datetime_str), fmt)
                except ValueError:
                    continue
            
            # If all formats fail, try pandas
            return pd.to_datetime(datetime_str, errors='coerce')
        
        except Exception as e:
            logger.warning(f"Failed to parse datetime '{datetime_str}': {str(e)}")
            return None
    
    @staticmethod
    def normalize_os_type(
        tipo_id: Any
    ) -> Optional[OSType]:
        """
        Normalize OS type ID to OSType enum.
        
        Args:
            tipo_id: Type ID from API
        
        Returns:
            OSType enum value or None
        """
        try:
            tipo_int = int(tipo_id)
            
            # Map known type IDs
            type_mapping = {
                1: OSType.CORRETIVA,
                2: OSType.PREVENTIVA,
                3: OSType.PREDITIVA,
                # Add more mappings as discovered
            }
            
            return type_mapping.get(tipo_int)
        
        except (ValueError, TypeError):
            logger.warning(f"Could not normalize OS type: {tipo_id}")
            return None
    
    @staticmethod
    def calculate_duration_hours(
        start_datetime: datetime,
        end_datetime: datetime
    ) -> Optional[float]:
        """
        Calculate duration in hours between two datetimes.
        
        Args:
            start_datetime: Start datetime
            end_datetime: End datetime
        
        Returns:
            Duration in hours or None if calculation fails
        """
        try:
            if not start_datetime or not end_datetime:
                return None
            
            duration = end_datetime - start_datetime
            return duration.total_seconds() / 3600
        
        except Exception as e:
            logger.warning(f"Failed to calculate duration: {str(e)}")
            return None
    
    @staticmethod
    def aggregate_by_period(
        df: pd.DataFrame,
        date_column: str,
        value_columns: List[str],
        period: str = 'M',
        agg_functions: Dict[str, str] = None
    ) -> pd.DataFrame:
        """
        Aggregate data by time period.
        
        Args:
            df: DataFrame to aggregate
            date_column: Date column for grouping
            value_columns: Columns to aggregate
            period: Aggregation period ('D', 'W', 'M', 'Q', 'Y')
            agg_functions: Custom aggregation functions per column
        
        Returns:
            Aggregated DataFrame
        """
        if df.empty or date_column not in df.columns:
            return pd.DataFrame()
        
        # Default aggregation functions
        if agg_functions is None:
            agg_functions = {col: 'mean' for col in value_columns}
        
        try:
            # Set date as index for resampling
            df_copy = df.copy()
            df_copy[date_column] = pd.to_datetime(df_copy[date_column])
            df_copy = df_copy.set_index(date_column)
            
            # Resample and aggregate
            aggregated = df_copy[value_columns].resample(period).agg(agg_functions)
            
            # Reset index
            aggregated = aggregated.reset_index()
            
            return aggregated
        
        except Exception as e:
            logger.error(f"Failed to aggregate data by period: {str(e)}")
            return pd.DataFrame()


class SchemaValidator:
    """Schema validation for API responses and data structures."""
    
    @staticmethod
    def validate_os_response(data: Dict[str, Any]) -> bool:
        """
        Validate OS (Ordem de Serviço) response structure.
        
        Args:
            data: API response data
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['id', 'tipo', 'estado', 'data_abertura']
        
        return all(field in data for field in required_fields)
    
    @staticmethod
    def validate_equipment_response(data: Dict[str, Any]) -> bool:
        """
        Validate equipment response structure.
        
        Args:
            data: API response data
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['id', 'nome', 'status']
        
        return all(field in data for field in required_fields)
    
    @staticmethod
    def validate_user_response(data: Dict[str, Any]) -> bool:
        """
        Validate user response structure.
        
        Args:
            data: API response data
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['id', 'nome']
        
        return all(field in data for field in required_fields)
