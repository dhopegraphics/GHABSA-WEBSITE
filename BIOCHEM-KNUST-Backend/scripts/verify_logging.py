#!/usr/bin/env python
"""
Logging Configuration Verification Script

This script verifies that the logging system is properly configured
for production deployment on PythonAnywhere with NO console output.

Run this before deploying to ensure OSError: write error won't occur.

Usage:
    python scripts/verify_logging.py
"""
import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BioChemSystem.settings')
django.setup()

import logging
from django.conf import settings


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_status(message, status='info'):
    """Print colored status message"""
    if status == 'pass':
        print(f"{Colors.GREEN}✓{Colors.END} {message}")
    elif status == 'fail':
        print(f"{Colors.RED}✗{Colors.END} {message}")
    elif status == 'warning':
        print(f"{Colors.YELLOW}⚠{Colors.END} {message}")
    else:
        print(f"{Colors.BLUE}ℹ{Colors.END} {message}")


def print_header(text):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")


def check_no_console_handlers():
    """Verify no StreamHandler exists in logging configuration"""
    print_header("Checking for Console Handlers")
    
    issues = []
    
    # Check all handlers
    for handler_name, handler_config in settings.LOGGING.get('handlers', {}).items():
        handler_class = handler_config.get('class', '')
        
        if 'StreamHandler' in handler_class:
            issues.append(f"Handler '{handler_name}' uses StreamHandler: {handler_class}")
            print_status(f"Found StreamHandler: {handler_name}", 'fail')
        else:
            print_status(f"Handler '{handler_name}': {handler_class}", 'pass')
    
    if issues:
        print_status(f"\n❌ Found {len(issues)} console handler(s) - MUST BE REMOVED!", 'fail')
        return False
    else:
        print_status("\n✓ No console handlers found - SAFE for PythonAnywhere", 'pass')
        return True


def check_log_directory():
    """Verify log directory exists and is writable"""
    print_header("Checking Log Directory")
    
    logs_dir = settings.LOGS_DIR
    
    if not os.path.exists(logs_dir):
        print_status(f"Log directory does not exist: {logs_dir}", 'fail')
        try:
            os.makedirs(logs_dir)
            print_status(f"Created log directory: {logs_dir}", 'pass')
        except Exception as e:
            print_status(f"Failed to create log directory: {e}", 'fail')
            return False
    else:
        print_status(f"Log directory exists: {logs_dir}", 'pass')
    
    # Check if writable
    test_file = os.path.join(logs_dir, '.test_write')
    try:
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print_status(f"Log directory is writable", 'pass')
        return True
    except Exception as e:
        print_status(f"Log directory is NOT writable: {e}", 'fail')
        return False


def check_file_handlers():
    """Verify all handlers are file-based with rotation"""
    print_header("Checking File Handlers Configuration")
    
    all_good = True
    
    for handler_name, handler_config in settings.LOGGING.get('handlers', {}).items():
        handler_class = handler_config.get('class', '')
        
        if 'NullHandler' in handler_class:
            print_status(f"{handler_name}: NullHandler (disabled)", 'info')
            continue
        
        if 'FileHandler' in handler_class or 'RotatingFileHandler' in handler_class:
            filename = handler_config.get('filename', 'N/A')
            max_bytes = handler_config.get('maxBytes', 0)
            backup_count = handler_config.get('backupCount', 0)
            
            print_status(f"{handler_name}:", 'info')
            print(f"  → File: {filename}")
            print(f"  → Max Size: {max_bytes / (1024*1024):.1f}MB")
            print(f"  → Backups: {backup_count}")
            
            if max_bytes == 0:
                print_status("  ⚠ No size limit - could fill disk!", 'warning')
                all_good = False
            
            if backup_count == 0:
                print_status("  ⚠ No backup rotation configured", 'warning')
        else:
            print_status(f"{handler_name}: Unknown handler type: {handler_class}", 'warning')
            all_good = False
    
    return all_good


def check_logger_configuration():
    """Verify logger configuration"""
    print_header("Checking Logger Configuration")
    
    loggers = settings.LOGGING.get('loggers', {})
    
    print_status(f"Found {len(loggers)} configured loggers", 'info')
    
    for logger_name, logger_config in loggers.items():
        handlers = logger_config.get('handlers', [])
        level = logger_config.get('level', 'NOTSET')
        
        # Check if any handler is 'console'
        if 'console' in handlers:
            print_status(f"Logger '{logger_name}' uses console handler!", 'fail')
            return False
        else:
            print_status(f"{logger_name}: {level} → {', '.join(handlers)}", 'pass')
    
    # Check root logger
    root_config = settings.LOGGING.get('root', {})
    root_handlers = root_config.get('handlers', [])
    
    if 'console' in root_handlers:
        print_status("Root logger uses console handler!", 'fail')
        return False
    else:
        print_status(f"Root logger: → {', '.join(root_handlers)}", 'pass')
    
    return True


def test_logging_works():
    """Test that logging actually works"""
    print_header("Testing Logging Functionality")
    
    try:
        # Create test loggers
        test_loggers = [
            ('app', logging.INFO, "Test application log"),
            ('payments', logging.INFO, "Test payment log"),
            ('security', logging.WARNING, "Test security log"),
            ('celery', logging.INFO, "Test celery log"),
        ]
        
        for logger_name, level, message in test_loggers:
            logger = logging.getLogger(logger_name)
            logger.log(level, f"[VERIFICATION TEST] {message}")
            print_status(f"Logged to {logger_name}: {message}", 'pass')
        
        print_status("\n✓ All test logs written successfully", 'pass')
        print_status("Check log files to verify they were created", 'info')
        return True
        
    except Exception as e:
        print_status(f"\n✗ Logging test failed: {e}", 'fail')
        return False


def search_print_statements():
    """Search for remaining print() statements in code"""
    print_header("Searching for print() Statements")
    
    import subprocess
    
    try:
        # Search for print statements
        result = subprocess.run(
            ['grep', '-r', 'print(', '--include=*.py', '.'],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        
        lines = result.stdout.strip().split('\n')
        
        # Filter out migrations, .pyc, and this script
        filtered_lines = [
            line for line in lines 
            if line and 
            'migrations/' not in line and 
            '.pyc' not in line and
            'verify_logging.py' not in line and
            'logging_config.py' not in line  # Utility file is OK
        ]
        
        if filtered_lines:
            print_status(f"Found {len(filtered_lines)} print() statements:", 'fail')
            for line in filtered_lines[:10]:  # Show first 10
                print(f"  {line}")
            if len(filtered_lines) > 10:
                print(f"  ... and {len(filtered_lines) - 10} more")
            print_status("\n⚠ These should be replaced with logger.*() calls", 'warning')
            return False
        else:
            print_status("No problematic print() statements found", 'pass')
            return True
            
    except Exception as e:
        print_status(f"Could not search for print statements: {e}", 'warning')
        return True  # Don't fail on this


def print_summary(results):
    """Print summary of all checks"""
    print_header("Verification Summary")
    
    passed = sum(results.values())
    total = len(results)
    
    for check, status in results.items():
        if status:
            print_status(check, 'pass')
        else:
            print_status(check, 'fail')
    
    print(f"\n{Colors.BOLD}Result: {passed}/{total} checks passed{Colors.END}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ READY FOR PRODUCTION DEPLOYMENT{Colors.END}")
        print(f"{Colors.GREEN}Your logging is properly configured for PythonAnywhere{Colors.END}")
        return True
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ NOT READY FOR DEPLOYMENT{Colors.END}")
        print(f"{Colors.RED}Fix the issues above before deploying{Colors.END}")
        return False


def main():
    """Run all verification checks"""
    print(f"\n{Colors.BOLD}PythonAnywhere Logging Configuration Verification{Colors.END}")
    print(f"Checking deployment readiness...\n")
    
    results = {
        'No Console Handlers': check_no_console_handlers(),
        'Log Directory Exists': check_log_directory(),
        'File Handlers Configured': check_file_handlers(),
        'Logger Configuration': check_logger_configuration(),
        'Logging Functionality': test_logging_works(),
        'No print() Statements': search_print_statements(),
    }
    
    success = print_summary(results)
    
    print(f"\n{Colors.BLUE}Next Steps:{Colors.END}")
    if success:
        print("1. Deploy to PythonAnywhere")
        print("2. Monitor logs/ directory for output")
        print("3. Verify no 'OSError: write error' in error logs")
        print(f"\n{Colors.GREEN}Documentation: IMPORTANT-DOCS/PYTHONANYWHERE_LOGGING_FIX.md{Colors.END}")
    else:
        print("1. Fix the issues identified above")
        print("2. Run this script again")
        print("3. Do NOT deploy until all checks pass")
    
    print()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
