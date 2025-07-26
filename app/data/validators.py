"""Data validators for the application."""

from typing import Any, Dict, List, Optional, Union, Type
import pandas as pd
import streamlit as st
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def validate_input_data(data: Any, expected_type: Type, error_message: str) -> None:
    """Validate input data type and raise ValidationError if invalid.
    
    Args:
        data: Data to validate
        expected_type: Expected data type
        error_message: Error message to show if validation fails
        
    Raises:
        ValidationError: If data doesn't match expected type
    """
    from app.core.exceptions import ValidationError
    
    if not isinstance(data, expected_type):
        logger.error(f"Validation failed: {error_message}. Got {type(data)}, expected {expected_type}")
        raise ValidationError(error_message)


class DataValidator:
    """Validator for data integrity and quality."""
    
    @staticmethod
    def validate_list(data: Any, required_fields: Optional[List[str]] = None) -> List[Dict]:
        """Validate a list of data objects."""
        if not isinstance(data, list):
            logger.warning(f"Expected list, got {type(data)}")
            return []
        
        if not data:
            logger.info("Empty data list")
            return []
        
        if required_fields:
            valid_items = []
            for item in data:
                if isinstance(item, dict):
                    if all(field in item for field in required_fields):
                        valid_items.append(item)
                    else:
                        logger.warning(f"Item missing required fields: {required_fields}")
                else:
                    logger.warning(f"Expected dict, got {type(item)}")
            return valid_items
        
        return data
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame, required_columns: List[str], name: str = "DataFrame") -> pd.DataFrame:
        """Validate DataFrame has required columns."""
        if df is None or df.empty:
            logger.warning(f"{name} is empty or None")
            return pd.DataFrame()
        
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            logger.warning(f"{name} missing columns: {missing_cols}")
        
        return df
    
    @staticmethod
    def validate_date_column(df: pd.DataFrame, column: str, allow_null: bool = True) -> pd.DataFrame:
        """Validate and convert date column."""
        if column not in df.columns:
            logger.warning(f"Date column '{column}' not found")
            return df
        
        try:
            df[column] = pd.to_datetime(df[column], errors='coerce')
            if not allow_null:
                df = df.dropna(subset=[column])
        except Exception as e:
            logger.error(f"Error converting {column} to datetime: {e}")
        
        return df


class DataCleaner:
    """Data cleaning utilities."""
    
    @staticmethod
    def clean_string_column(df: pd.DataFrame, column: str, strip_whitespace: bool = True, 
                           normalize_case: Optional[str] = None) -> pd.DataFrame:
        """Clean string column."""
        if column not in df.columns:
            return df
        
        try:
            if strip_whitespace:
                df[column] = df[column].astype(str).str.strip()
            
            if normalize_case == "upper":
                df[column] = df[column].str.upper()
            elif normalize_case == "lower":
                df[column] = df[column].str.lower()
            elif normalize_case == "title":
                df[column] = df[column].str.title()
        except Exception as e:
            logger.error(f"Error cleaning column {column}: {e}")
        
        return df
    
    @staticmethod
    def remove_duplicates(df: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
        """Remove duplicate rows."""
        try:
            return df.drop_duplicates(subset=subset)
        except Exception as e:
            logger.error(f"Error removing duplicates: {e}")
            return df


class SchemaValidator:
    """Schema validation for API responses."""
    
    @staticmethod
    def validate_response(data: Any, expected_type: type = dict) -> bool:
        """Validate API response structure."""
        return isinstance(data, expected_type)
    
    @staticmethod
    def validate_required_fields(data: Dict, required_fields: List[str]) -> bool:
        """Validate required fields are present."""
        return all(field in data for field in required_fields)


# Aliases for backward compatibility
DataTransformer = DataCleaner
