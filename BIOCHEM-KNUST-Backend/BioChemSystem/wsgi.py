"""
WSGI config for BioChemSystem project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import sys
import logging

# =============================================================================
# CRITICAL: Silence all console output BEFORE Django loads
# This prevents OSError: write error on PythonAnywhere
# =============================================================================

# Redirect stdout/stderr to devnull for third-party libraries
# that ignore logging configuration
class NullWriter:
    """Null writer that silently discards all output"""
    def write(self, text):
        pass
    def flush(self):
        pass
    def isatty(self):
        return False

# Store original streams (in case needed for debugging)
_original_stdout = sys.stdout
_original_stderr = sys.stderr

# ALWAYS redirect in WSGI context (PythonAnywhere)
# The wsgi.py is only loaded in production, not during local development
# Local development uses manage.py runserver which doesn't load wsgi.py
sys.stdout = NullWriter()
sys.stderr = NullWriter()

# Silence ALL potentially noisy libraries BEFORE they're imported
_noisy_loggers = [
    'httpx', 'httpcore', 'urllib3', 'urllib3.connectionpool',
    'requests', 'chardet', 'charset_normalizer', 'PIL',
    'cloudinary', 'exponent_server_sdk', 'pywebpush',
    'h2', 'hpack', 'asyncio', 'concurrent', 'multipart',
    'parso', 'jedi', 'watchdog', 'fsevents',
]
for logger_name in _noisy_loggers:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)
    logging.getLogger(logger_name).handlers = []
    logging.getLogger(logger_name).propagate = False

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BioChemSystem.settings')

# Initialize Django
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

