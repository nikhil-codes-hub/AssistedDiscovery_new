"""
Error Tracking Utility for Debugging Specific Issues

This module provides utilities to track and log specific errors that occur in the application,
particularly useful for debugging issues that show up in the UI but not in regular logs.
"""

import streamlit as st
import traceback
import inspect
from functools import wraps
from typing import Any, Callable
from .logging_manager import get_logger, log_streamlit_error


class ErrorTracker:
    """Track and log specific types of errors."""
    
    def __init__(self):
        self.logger = get_logger("error_tracker")
        self.error_count = 0
    
    def log_none_type_error(self, context: str, variable_name: str = None, line_number: int = None):
        """Log NoneType unpacking errors with detailed context."""
        self.error_count += 1
        
        # Get caller information
        frame = inspect.currentframe().f_back
        caller_info = inspect.getframeinfo(frame)
        
        error_details = {
            "error_type": "NoneType_Unpacking",
            "context": context,
            "file": caller_info.filename,
            "line": caller_info.lineno,
            "function": caller_info.function,
            "variable": variable_name,
            "error_count": self.error_count
        }
        
        self.logger.error(f"NoneType unpacking error in {context}: {error_details}")
        
        # Also log to Streamlit error handler
        try:
            error_msg = f"TypeError: cannot unpack non-iterable NoneType object in {context}"
            log_streamlit_error(
                TypeError(error_msg),
                f"NoneType unpacking error #{self.error_count}",
                f"Context: {context}\nFile: {caller_info.filename}:{caller_info.lineno}\nFunction: {caller_info.function}"
            )
        except Exception:
            pass
    
    def log_variable_state(self, variables: dict, context: str):
        """Log the state of variables for debugging."""
        self.logger.info(f"Variable state in {context}:")
        for var_name, var_value in variables.items():
            var_type = type(var_value).__name__
            var_repr = repr(var_value)[:100] if var_value is not None else "None"
            self.logger.info(f"  {var_name}: {var_type} = {var_repr}")


# Global error tracker instance
_error_tracker = ErrorTracker()


def track_none_type_errors(func: Callable) -> Callable:
    """Decorator to track NoneType unpacking errors in functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except TypeError as e:
            if "cannot unpack non-iterable NoneType object" in str(e):
                _error_tracker.log_none_type_error(
                    context=f"{func.__module__}.{func.__name__}",
                    variable_name="unknown"
                )
            raise
        except Exception as e:
            # Log other exceptions too
            _error_tracker.logger.error(f"Error in {func.__name__}: {e}")
            raise
    
    return wrapper


def safe_unpack(value: Any, expected_length: int, context: str = "unknown", default_value: Any = None):
    """Safely unpack values with detailed error logging."""
    if value is None:
        _error_tracker.log_none_type_error(
            context=f"safe_unpack in {context}",
            variable_name="value"
        )
        
        # Return default values
        if default_value is not None:
            return default_value
        return [None] * expected_length
    
    try:
        # Try to unpack the value
        if hasattr(value, '__len__') and len(value) == expected_length:
            return value
        elif hasattr(value, '__iter__'):
            # Convert to list and pad/truncate as needed
            value_list = list(value)
            if len(value_list) < expected_length:
                value_list.extend([None] * (expected_length - len(value_list)))
            return value_list[:expected_length]
        else:
            _error_tracker.log_variable_state(
                {"value": value, "expected_length": expected_length},
                f"safe_unpack in {context}"
            )
            return [value] + [None] * (expected_length - 1)
    
    except Exception as e:
        _error_tracker.log_none_type_error(
            context=f"safe_unpack exception in {context}",
            variable_name="value"
        )
        log_streamlit_error(e, f"safe_unpack failed in {context}")
        return [None] * expected_length


def debug_streamlit_state(context: str = "unknown"):
    """Debug Streamlit session state for troubleshooting."""
    try:
        if hasattr(st, 'session_state'):
            state_info = {}
            for key, value in st.session_state.items():
                state_info[key] = {
                    "type": type(value).__name__,
                    "value": str(value)[:100] if value is not None else "None",
                    "is_none": value is None
                }
            
            _error_tracker.log_variable_state(state_info, f"streamlit_state_{context}")
        else:
            _error_tracker.logger.info(f"No session state available in {context}")
    except Exception as e:
        _error_tracker.logger.error(f"Failed to debug Streamlit state in {context}: {e}")


def log_function_call_with_args(func: Callable) -> Callable:
    """Decorator to log function calls with their arguments."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Log function call
        _error_tracker.logger.info(f"Calling {func.__name__} with args: {args[:3]}... kwargs: {list(kwargs.keys())}")
        
        # Log argument types and None values
        for i, arg in enumerate(args[:5]):  # Log first 5 args
            if arg is None:
                _error_tracker.logger.warning(f"Argument {i} is None in {func.__name__}")
        
        for key, value in kwargs.items():
            if value is None:
                _error_tracker.logger.warning(f"Keyword argument '{key}' is None in {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            
            # Log result if it's None
            if result is None:
                _error_tracker.logger.warning(f"Function {func.__name__} returned None")
            
            return result
        except Exception as e:
            _error_tracker.logger.error(f"Exception in {func.__name__}: {e}")
            raise
    
    return wrapper


# Convenience functions
def log_none_type_error(context: str, variable_name: str = None):
    """Log a NoneType unpacking error."""
    _error_tracker.log_none_type_error(context, variable_name)


def log_variable_state(variables: dict, context: str):
    """Log variable states for debugging."""
    _error_tracker.log_variable_state(variables, context)


def get_error_count() -> int:
    """Get the current error count."""
    return _error_tracker.error_count