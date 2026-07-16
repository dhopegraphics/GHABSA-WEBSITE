"""
Logging utilities for production deployment on PythonAnywhere.

This module provides helper functions for consistent, file-based logging
across the application. NO console output to prevent OSError: write error.

Usage:
    from utils.logging_config import get_logger
    
    logger = get_logger(__name__)
    logger.info("This goes to file only")
    logger.error("Error message with context", extra={'user_id': 123})
    
    # For exceptions with stack trace
    try:
        risky_operation()
    except Exception as e:
        logger.exception("Operation failed")  # Includes full traceback
"""

import logging
from typing import Optional, Dict, Any


def get_logger(name: str, category: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance for the given module.
    
    Args:
        name: Usually __name__ of the calling module
        category: Optional category for specialized logging
                 Options: 'payment', 'sms', 'security', 'automation', 
                         'celery', 'api', 'scraper'
    
    Returns:
        logging.Logger: Configured logger instance
    
    Example:
        logger = get_logger(__name__)
        logger.info("Processing started")
        
        # For specialized logging
        payment_logger = get_logger(__name__, 'payment')
        payment_logger.info("Payment processed", extra={'amount': 100})
    """
    if category:
        # Map to specialized loggers defined in settings.py
        logger = logging.getLogger(category)
    else:
        logger = logging.getLogger(name)
    
    return logger


def log_function_call(logger: logging.Logger, func_name: str, **kwargs):
    """
    Log a function call with parameters.
    
    Args:
        logger: Logger instance
        func_name: Name of the function being called
        **kwargs: Parameters to log
    
    Example:
        logger = get_logger(__name__)
        log_function_call(logger, 'process_payment', 
                         user_id=123, amount=50.00, currency='USD')
    """
    params = ', '.join(f'{k}={v}' for k, v in kwargs.items())
    logger.debug(f"Function call: {func_name}({params})")


def log_api_request(logger: logging.Logger, method: str, path: str, 
                    user_id: Optional[int] = None, status_code: Optional[int] = None,
                    duration_ms: Optional[float] = None):
    """
    Log an API request with standardized format.
    
    Args:
        logger: Logger instance
        method: HTTP method (GET, POST, etc.)
        path: Request path
        user_id: Optional user ID
        status_code: Response status code
        duration_ms: Request duration in milliseconds
    
    Example:
        logger = get_logger(__name__, 'api')
        log_api_request(logger, 'POST', '/api/products/', 
                       user_id=123, status_code=200, duration_ms=45.2)
    """
    extra_info = []
    if user_id:
        extra_info.append(f"user={user_id}")
    if status_code:
        extra_info.append(f"status={status_code}")
    if duration_ms:
        extra_info.append(f"duration={duration_ms:.2f}ms")
    
    extra_str = f" [{', '.join(extra_info)}]" if extra_info else ""
    logger.info(f"{method} {path}{extra_str}")


def log_payment_event(logger: logging.Logger, event_type: str, 
                     reference: str, amount: float, currency: str = 'GHS',
                     user_id: Optional[int] = None, status: Optional[str] = None,
                     **extra):
    """
    Log payment-related events with standardized format.
    
    Args:
        logger: Logger instance
        event_type: Type of event (initialized, verified, completed, failed)
        reference: Payment reference
        amount: Payment amount
        currency: Currency code
        user_id: Optional user ID
        status: Payment status
        **extra: Additional context to log
    
    Example:
        logger = get_logger(__name__, 'payment')
        log_payment_event(logger, 'completed', 'PAY-123456', 
                         amount=100.00, user_id=45, status='success',
                         gateway='paystack')
    """
    msg = (f"Payment {event_type}: ref={reference}, "
           f"amount={amount} {currency}")
    
    if user_id:
        msg += f", user_id={user_id}"
    if status:
        msg += f", status={status}"
    
    if extra:
        extra_str = ', '.join(f'{k}={v}' for k, v in extra.items())
        msg += f", {extra_str}"
    
    logger.info(msg)


def log_scraper_event(logger: logging.Logger, action: str, 
                     source: str, records: Optional[int] = None,
                     success: bool = True, **extra):
    """
    Log web scraping events.
    
    Args:
        logger: Logger instance
        action: Action performed (fetched, parsed, saved, failed)
        source: Data source URL or identifier
        records: Number of records processed
        success: Whether operation succeeded
        **extra: Additional context
    
    Example:
        logger = get_logger(__name__, 'scraper')
        log_scraper_event(logger, 'fetched', 'KNUST Admissions', 
                         records=150, success=True)
    """
    level = logging.INFO if success else logging.ERROR
    msg = f"Scraper {action}: source={source}"
    
    if records is not None:
        msg += f", records={records}"
    
    if extra:
        extra_str = ', '.join(f'{k}={v}' for k, v in extra.items())
        msg += f", {extra_str}"
    
    logger.log(level, msg)


def log_security_event(logger: logging.Logger, event: str, 
                       user_id: Optional[int] = None,
                       ip_address: Optional[str] = None,
                       device_id: Optional[str] = None,
                       severity: str = 'info', **extra):
    """
    Log security-related events.
    
    Args:
        logger: Logger instance
        event: Security event description
        user_id: Optional user ID
        ip_address: Request IP address
        device_id: Device fingerprint/ID
        severity: Event severity (info, warning, error, critical)
        **extra: Additional context
    
    Example:
        logger = get_logger(__name__, 'security')
        log_security_event(logger, 'Failed login attempt', 
                          user_id=123, ip_address='192.168.1.1',
                          severity='warning', attempts=3)
    """
    level_map = {
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }
    level = level_map.get(severity.lower(), logging.INFO)
    
    msg = f"Security: {event}"
    
    if user_id:
        msg += f", user_id={user_id}"
    if ip_address:
        msg += f", ip={ip_address}"
    if device_id:
        msg += f", device={device_id}"
    
    if extra:
        extra_str = ', '.join(f'{k}={v}' for k, v in extra.items())
        msg += f", {extra_str}"
    
    logger.log(level, msg)


def log_celery_task(logger: logging.Logger, task_name: str, 
                   status: str, duration: Optional[float] = None,
                   **extra):
    """
    Log Celery task execution.
    
    Args:
        logger: Logger instance
        task_name: Name of the Celery task
        status: Task status (started, completed, failed, retrying)
        duration: Execution duration in seconds
        **extra: Additional context
    
    Example:
        logger = get_logger(__name__, 'celery')
        log_celery_task(logger, 'send_notifications', 'completed', 
                       duration=2.5, notifications_sent=50)
    """
    msg = f"Celery task {task_name}: {status}"
    
    if duration is not None:
        msg += f", duration={duration:.2f}s"
    
    if extra:
        extra_str = ', '.join(f'{k}={v}' for k, v in extra.items())
        msg += f", {extra_str}"
    
    level = logging.ERROR if status == 'failed' else logging.INFO
    logger.log(level, msg)


class ContextLogger:
    """
    Context manager for logging operation start/end with timing.
    
    Example:
        logger = get_logger(__name__)
        with ContextLogger(logger, 'database_query', user_id=123):
            # Your code here
            execute_query()
        # Automatically logs start, end, and duration
    """
    
    def __init__(self, logger: logging.Logger, operation: str, **context):
        self.logger = logger
        self.operation = operation
        self.context = context
        self.start_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        context_str = ', '.join(f'{k}={v}' for k, v in self.context.items())
        msg = f"Starting {self.operation}"
        if context_str:
            msg += f" [{context_str}]"
        self.logger.debug(msg)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        duration = time.time() - self.start_time
        
        if exc_type:
            self.logger.error(
                f"{self.operation} failed after {duration:.2f}s: {exc_val}",
                exc_info=(exc_type, exc_val, exc_tb)
            )
        else:
            self.logger.info(
                f"{self.operation} completed in {duration:.2f}s"
            )


def configure_file_only_logging():
    """
    Ensure all logging goes to files only, no console output.
    This should be called early in application startup.
    
    Call this in manage.py or wsgi.py to ensure production safety.
    """
    # Get all handlers and remove StreamHandlers
    root_logger = logging.getLogger()
    
    for handler in root_logger.handlers[:]:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            root_logger.removeHandler(handler)
    
    # Do the same for Django logger
    django_logger = logging.getLogger('django')
    for handler in django_logger.handlers[:]:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            django_logger.removeHandler(handler)
    
    # Silence noisy third-party libraries that might log to console
    silence_third_party_loggers()


def silence_third_party_loggers():
    """
    Configure third-party libraries to use file logging only.
    Prevents httpx, urllib3, and other libraries from writing to console.
    """
    # List of noisy third-party loggers
    noisy_loggers = [
        'httpx',           # HTTP client library
        'httpcore',        # HTTP core library  
        'urllib3',         # Used by requests
        'requests',        # HTTP library
        'selenium',        # Browser automation
        'boto3',           # AWS SDK
        'botocore',        # AWS core
        'paramiko',        # SSH library
    ]
    
    for logger_name in noisy_loggers:
        logger = logging.getLogger(logger_name)
        # Remove all stream handlers
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                logger.removeHandler(handler)
        
        # Prevent propagation to root logger (which might have stream handlers)
        logger.propagate = False
        
        # Set to WARNING level to reduce noise
        logger.setLevel(logging.WARNING)


# Convenience function for quick info logging
def log_info(message: str, category: Optional[str] = None, **extra):
    """Quick info log without creating logger explicitly."""
    logger = get_logger('app', category)
    if extra:
        logger.info(message, extra=extra)
    else:
        logger.info(message)


# Convenience function for quick error logging
def log_error(message: str, category: Optional[str] = None, exc_info: bool = False, **extra):
    """Quick error log without creating logger explicitly."""
    logger = get_logger('app', category)
    if extra:
        logger.error(message, exc_info=exc_info, extra=extra)
    else:
        logger.error(message, exc_info=exc_info)
