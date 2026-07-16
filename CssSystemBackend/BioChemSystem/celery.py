"""
Celery configuration for BioChemSystem project - DISABLED FOR PYTHONANYWHERE

⚠️ IMPORTANT: Celery is NOT supported on PythonAnywhere free/hacker accounts.

Use Django Management Commands with PythonAnywhere Scheduled Tasks instead:

SETUP ON PYTHONANYWHERE:
========================
1. Go to "Tasks" tab in dashboard
2. Add these scheduled tasks:

   a) Every hour (or more frequently on paid accounts):
      Command: cd /home/yourusername/CssSystemBackend && python manage.py retry_pending_transactions
      
   b) Daily at 3:00 AM:
      Command: cd /home/yourusername/CssSystemBackend && python manage.py cleanup_abandoned_transactions

AVAILABLE COMMANDS:
===================
- python manage.py retry_pending_transactions [--max-age-hours 24] [--min-age-minutes 5] [--dry-run]
- python manage.py cleanup_abandoned_transactions [--hours 48] [--dry-run]

These commands provide the same functionality as the disabled Celery tasks below.
"""

# The code below is DISABLED but kept for reference
# Uncomment only if deploying to a platform that supports Celery (e.g., Heroku, AWS, Azure)

# import os
# import logging
# from celery import Celery
# from celery.signals import setup_logging
# from celery.schedules import crontab

# # Set the default Django settings module for the 'celery' program.
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BioChemSystem.settings')

# app = Celery('BioChemSystem')

# # Using a string here means the worker doesn't have to serialize
# # the configuration object to child processes.
# # - namespace='CELERY' means all celery-related configuration keys
# #   should have a `CELERY_` prefix.
# app.config_from_object('django.conf:settings', namespace='CELERY')

# # Load task modules from all registered Django apps.
# app.autodiscover_tasks()

# # Celery Beat Schedule - Periodic Tasks
# app.conf.beat_schedule = {
#     'check-pending-transactions-every-5-minutes': {
#         'task': 'payments.tasks.check_and_retry_pending_transactions',
#         'schedule': 300.0,  # Every 5 minutes (in seconds)
#         'options': {
#             'expires': 240.0,  # Task expires after 4 minutes
#         }
#     },
#     'cleanup-abandoned-transactions-daily': {
#         'task': 'payments.tasks.cleanup_abandoned_transactions',
#         'schedule': crontab(hour=3, minute=0),  # Every day at 3:00 AM
#         'options': {
#             'expires': 3600.0,  # Task expires after 1 hour
#         }
#     },
# }


# @setup_logging.connect
# def config_celery_logging(**kwargs):
#     """
#     Configure Celery to use Django's logging configuration.
#     This ensures all Celery logs go to files, not console.
#     """
#     from django.conf import settings
#     from logging.config import dictConfig
    
#     # Use Django's logging configuration
#     dictConfig(settings.LOGGING)


# @app.task(bind=True, ignore_result=True)
# def debug_task(self):
#     """Debug task for testing Celery setup"""
#     logger = logging.getLogger('celery')
#     logger.info(f'Debug task executed: {self.request!r}')

