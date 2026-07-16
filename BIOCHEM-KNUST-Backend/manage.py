#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BioChemSystem.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # Configure logging to use files only (no console output)
    # This prevents OSError: write error on PythonAnywhere
    try:
        from utils.logging_config import configure_file_only_logging
        configure_file_only_logging()
    except ImportError:
        # If utils.logging_config doesn't exist yet, continue
        pass
    
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
