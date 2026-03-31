"""
AirOne Professional v4.0 - Error Handler Module
Comprehensive error handling and recovery system
"""

import sys
import os
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import functools
import json

# Configure logging
logger = logging.getLogger(__name__)


class ErrorRecoveryStrategy:
    """Error recovery strategies"""
    IGNORE = "ignore"
    RETRY = "retry"
    FALLBACK = "fallback"
    ABORT = "abort"
    LOG_ONLY = "log_only"


class ErrorHandler:
    """Comprehensive error handling system"""
    
    def __init__(self, log_file: str = "logs/error.log", max_retries: int = 3):
        self.log_file = log_file
        self.max_retries = max_retries
        self.error_count = 0
        self.error_history = []
        self.recovery_strategies = {}
        
        # Create logs directory
        Path('logs').mkdir(exist_ok=True)
        
        # Setup error logging
        self._setup_error_logging()
    
    def _setup_error_logging(self):
        """Setup dedicated error logging"""
        self.error_logger = logging.getLogger('AirOneErrorHandler')
        self.error_logger.setLevel(logging.ERROR)
        
        # File handler
        try:
            fh = logging.FileHandler(self.log_file, encoding='utf-8')
            fh.setLevel(logging.ERROR)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            fh.setFormatter(formatter)
            self.error_logger.addHandler(fh)
        except Exception as e:
            print(f"Warning: Could not setup error log file: {e}")
    
    def register_strategy(self, error_type: type, strategy: ErrorRecoveryStrategy,
                         fallback_func: Optional[Callable] = None):
        """Register recovery strategy for specific error type"""
        self.recovery_strategies[error_type] = {
            'strategy': strategy,
            'fallback': fallback_func
        }
    
    def handle_error(self, error: Exception, context: str = "",
                    retry_count: int = 0) -> bool:
        """
        Handle an error with appropriate strategy
        
        Returns: True if should retry, False if should continue
        """
        self.error_count += 1
        timestamp = datetime.now().isoformat()
        
        # Log error
        error_info = {
            'timestamp': timestamp,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'retry_count': retry_count,
            'traceback': traceback.format_exc()
        }
        
        self.error_history.append(error_info)
        self.error_logger.error(
            f"Error in {context}: {type(error).__name__} - {str(error)}\n"
            f"Traceback:\n{traceback.format_exc()}"
        )
        
        # Check for registered strategy
        for error_type, strategy_info in self.recovery_strategies.items():
            if isinstance(error, error_type):
                return self._apply_strategy(strategy_info, error, retry_count)
        
        # Default strategy: log and continue
        print(f"\n[ERROR] {context}")
        print(f"  Type: {type(error).__name__}")
        print(f"  Message: {str(error)}")
        print(f"  Check logs/error.log for details\n")
        
        return False  # Don't retry by default
    
    def _apply_strategy(self, strategy_info: dict, error: Exception,
                       retry_count: int) -> bool:
        """Apply recovery strategy"""
        strategy = strategy_info['strategy']
        fallback = strategy_info.get('fallback')
        
        if strategy == ErrorRecoveryStrategy.IGNORE:
            return False
        
        elif strategy == ErrorRecoveryStrategy.RETRY:
            if retry_count < self.max_retries:
                print(f"[RETRY] Attempting retry {retry_count + 1}/{self.max_retries}")
                return True
            return False
        
        elif strategy == ErrorRecoveryStrategy.FALLBACK:
            if fallback:
                try:
                    fallback()
                    print(f"[FALLBACK] Using fallback function")
                except Exception as e:
                    print(f"[FALLBACK] Fallback failed: {e}")
            return False
        
        elif strategy == ErrorRecoveryStrategy.ABORT:
            print(f"[ABORT] Critical error - aborting operation")
            raise error
        
        elif strategy == ErrorRecoveryStrategy.LOG_ONLY:
            return False
        
        return False
    
    def get_error_report(self) -> Dict[str, Any]:
        """Generate error report"""
        return {
            'total_errors': self.error_count,
            'recent_errors': self.error_history[-10:],  # Last 10 errors
            'error_types': list(set(
                e['error_type'] for e in self.error_history
            )),
            'generated_at': datetime.now().isoformat()
        }
    
    def clear_error_history(self):
        """Clear error history"""
        self.error_history = []
        self.error_count = 0


def handle_exceptions(default_return=None, retry_count=0, log_context=""):
    """
    Decorator for handling exceptions in functions
    
    Usage:
        @handle_exceptions(default_return={}, log_context="my_function")
        def my_function():
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = ErrorHandler()
            current_retry = 0
            
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    context = log_context or func.__name__
                    should_retry = error_handler.handle_error(
                        e, context, current_retry
                    )
                    
                    if should_retry and current_retry < retry_count:
                        current_retry += 1
                        continue
                    
                    if default_return is not None:
                        return default_return
                    raise
        return wrapper
    return decorator


def safe_import(module_name: str, alternative: Optional[Any] = None):
    """
    Safely import a module with fallback
    
    Usage:
        pandas = safe_import('pandas', alternative=None)
        if pandas is None:
            print("Pandas not available")
    """
    try:
        return __import__(module_name)
    except ImportError as e:
        logger.warning(f"Module '{module_name}' not available: {e}")
        return alternative


def graceful_exit(message: str = "Exiting...", exit_code: int = 0):
    """
    Exit gracefully with message
    
    Usage:
        graceful_exit("Operation completed", 0)
    """
    print(f"\n[INFO] {message}")
    sys.exit(exit_code)


def validate_not_none(value: Any, param_name: str):
    """
    Validate that a value is not None
    
    Usage:
        validate_not_none(data, "input_data")
    """
    if value is None:
        raise ValueError(f"Parameter '{param_name}' cannot be None")
    return value


def validate_type(value: Any, expected_type: type, param_name: str):
    """
    Validate that a value is of expected type
    
    Usage:
        validate_type(count, int, "count")
    """
    if not isinstance(value, expected_type):
        raise TypeError(
            f"Parameter '{param_name}' must be {expected_type.__name__}, "
            f"got {type(value).__name__}"
        )
    return value


# Global error handler instance
global_error_handler = ErrorHandler()


def report_error(error: Exception, context: str = ""):
    """Quick error reporting using global handler"""
    return global_error_handler.handle_error(error, context)


def get_error_report():
    """Get global error report"""
    return global_error_handler.get_error_report()
