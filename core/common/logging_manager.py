"""
Centralized Logging Manager for Genie Application

This module provides comprehensive logging functionality for the desktop application,
with platform-specific log file locations and proper log rotation.
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional
import platform
import traceback

class LoggingManager:
    """Centralized logging manager for the Genie application."""
    
    def __init__(self, app_name: str = "GenieApp"):
        self.app_name = app_name
        self.logger = None
        self.log_dir = None
        self.log_file = None
        self._setup_logging()
    
    def _get_log_directory(self) -> Path:
        """Get platform-specific log directory."""
        system = platform.system()
        
        if system == "Windows":
            # Windows: %APPDATA%\GenieApp\logs
            base_dir = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
            log_dir = base_dir / self.app_name / 'logs'
        elif system == "Darwin":  # macOS
            # macOS: ~/Library/GenieApp/logs
            log_dir = Path.home() / 'Library' / self.app_name / 'logs'
        else:  # Linux and others
            # Linux: ~/.local/share/GenieApp/logs
            base_dir = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local' / 'share'))
            log_dir = base_dir / self.app_name / 'logs'
        
        # Create directory if it doesn't exist
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir
    
    def _setup_logging(self):
        """Set up comprehensive logging configuration."""
        # Get log directory
        self.log_dir = self._get_log_directory()
        self.log_file = self.log_dir / f"{self.app_name}.log"
        
        # Create logger
        self.logger = logging.getLogger(self.app_name)
        self.logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # File handler with rotation (10MB max, keep 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler (for development)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)
        
        # Log startup information
        self._log_startup_info()
    
    def _log_startup_info(self):
        """Log application startup information."""
        self.logger.info("=" * 50)
        self.logger.info(f"Starting {self.app_name}")
        self.logger.info(f"Platform: {platform.system()} {platform.release()}")
        self.logger.info(f"Python: {sys.version}")
        self.logger.info(f"Log file: {self.log_file}")
        self.logger.info(f"Working directory: {os.getcwd()}")
        self.logger.info("=" * 50)
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """Get a logger instance."""
        if name:
            return logging.getLogger(f"{self.app_name}.{name}")
        return self.logger
    
    def log_user_action(self, action: str, details: str = ""):
        """Log user actions for analytics and debugging."""
        message = f"USER_ACTION: {action}"
        if details:
            message += f" - {details}"
        self.logger.info(message)
    
    def log_error(self, error: Exception, context: str = ""):
        """Log errors with context information."""
        message = f"ERROR: {str(error)}"
        if context:
            message = f"{context} - {message}"
        self.logger.error(message, exc_info=True)
    
    def log_streamlit_error(self, error: Exception, context: str = "", traceback_str: str = None):
        """Log Streamlit-specific errors with enhanced context."""
        message = f"STREAMLIT_ERROR: {str(error)}"
        if context:
            message = f"{context} - {message}"
        
        # Log the error
        self.logger.error(message, exc_info=True)
        
        # Also log the traceback if provided
        if traceback_str:
            self.logger.error(f"Full traceback:\n{traceback_str}")
        
        # Log current Streamlit session state if available
        try:
            import streamlit as st
            if hasattr(st, 'session_state') and st.session_state:
                session_info = {k: str(v)[:100] for k, v in st.session_state.items()}
                self.logger.error(f"Streamlit session state: {session_info}")
        except Exception:
            pass
    
    def log_performance(self, operation: str, duration: float, details: str = ""):
        """Log performance metrics."""
        message = f"PERFORMANCE: {operation} took {duration:.2f}s"
        if details:
            message += f" - {details}"
        self.logger.info(message)
    
    def log_api_call(self, service: str, endpoint: str, status: str, duration: float = None):
        """Log API calls for monitoring."""
        message = f"API_CALL: {service} {endpoint} - {status}"
        if duration:
            message += f" ({duration:.2f}s)"
        self.logger.info(message)
    
    def log_file_operation(self, operation: str, file_path: str, status: str):
        """Log file operations."""
        message = f"FILE_OP: {operation} {file_path} - {status}"
        self.logger.info(message)
    
    def get_log_file_path(self) -> str:
        """Get the current log file path."""
        return str(self.log_file)
    
    def get_log_directory(self) -> str:
        """Get the log directory path."""
        return str(self.log_dir)
    
    def get_recent_logs(self, lines: int = 100) -> list:
        """Get recent log entries."""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception as e:
            self.logger.error(f"Failed to read log file: {e}")
            return []
    
    def clear_old_logs(self, days: int = 30):
        """Clear log files older than specified days."""
        try:
            cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            for log_file in self.log_dir.glob("*.log*"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    self.logger.info(f"Deleted old log file: {log_file}")
        except Exception as e:
            self.logger.error(f"Failed to clear old logs: {e}")
    
    def set_log_level(self, level: str):
        """Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)."""
        numeric_level = getattr(logging, level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f'Invalid log level: {level}')
        
        self.logger.setLevel(numeric_level)
        for handler in self.logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                handler.setLevel(numeric_level)
        
        self.logger.info(f"Log level set to {level}")


# Global logging manager instance
_logging_manager = None

def get_logging_manager() -> LoggingManager:
    """Get the global logging manager instance."""
    global _logging_manager
    if _logging_manager is None:
        _logging_manager = LoggingManager()
    return _logging_manager

def reset_logging_manager():
    """Reset the global logging manager instance to pick up configuration changes."""
    global _logging_manager
    _logging_manager = None

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Convenience function to get a logger."""
    return get_logging_manager().get_logger(name)

def log_user_action(action: str, details: str = ""):
    """Convenience function to log user actions."""
    get_logging_manager().log_user_action(action, details)

def log_error(error: Exception, context: str = ""):
    """Convenience function to log errors."""
    get_logging_manager().log_error(error, context)

def log_streamlit_error(error: Exception, context: str = "", traceback_str: str = None):
    """Convenience function to log Streamlit errors."""
    get_logging_manager().log_streamlit_error(error, context, traceback_str)

def log_performance(operation: str, duration: float, details: str = ""):
    """Convenience function to log performance."""
    get_logging_manager().log_performance(operation, duration, details)

def log_api_call(service: str, endpoint: str, status: str, duration: float = None):
    """Convenience function to log API calls."""
    get_logging_manager().log_api_call(service, endpoint, status, duration)

def log_file_operation(operation: str, file_path: str, status: str):
    """Convenience function to log file operations."""
    get_logging_manager().log_file_operation(operation, file_path, status)


# Context manager for performance logging
class PerformanceLogger:
    """Context manager for automatic performance logging."""
    
    def __init__(self, operation: str, details: str = ""):
        self.operation = operation
        self.details = details
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            log_performance(self.operation, duration, self.details)


# Decorator for automatic function logging
def log_function_call(func):
    """Decorator to automatically log function calls."""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.info(f"Calling {func.__name__}")
        
        start_time = datetime.now()
        try:
            result = func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Completed {func.__name__} in {duration:.2f}s")
            return result
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error in {func.__name__} after {duration:.2f}s: {e}")
            raise
    
    return wrapper


def setup_global_exception_handler():
    """Set up global exception handler to catch all uncaught exceptions."""
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Allow keyboard interrupt to work normally
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Log the uncaught exception
        logger = get_logger("global_exception_handler")
        logger.error(
            f"Uncaught exception: {exc_type.__name__}: {exc_value}",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        
        # Also log using the streamlit error function
        try:
            tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            log_streamlit_error(
                exc_value, 
                f"Uncaught {exc_type.__name__}", 
                tb_str
            )
        except Exception:
            pass
    
    # Set the global exception handler
    sys.excepthook = handle_exception


def streamlit_error_handler(func):
    """Decorator to catch and log Streamlit function errors."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            tb_str = traceback.format_exc()
            log_streamlit_error(e, f"Error in {func.__name__}", tb_str)
            
            # Re-raise the exception so Streamlit can handle it
            raise
    
    return wrapper