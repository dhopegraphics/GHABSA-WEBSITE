"""
Scheduled tasks for the accounts app.

These tasks can be run automatically using:
1. Django-Celery Beat (if installed)
2. Cron jobs
3. Manually via management commands

Recommended Schedule:
- deactivate_graduated_students_task: Run twice a year
  - January 1st (beginning of year)
  - December 1st (end of year)
"""

import logging
from django.utils import timezone
from accounts.models import CustomUser

logger = logging.getLogger(__name__)


def deactivate_graduated_students_task(include_staff=False, dry_run=False):
    """
    Task to deactivate students who have completed their program.
    
    This task identifies students who have graduated (based on their graduation_year)
    and sets their is_active status to False.
    
    Args:
        include_staff: If True, also deactivate staff members who have graduated
        dry_run: If True, only log what would be done without making changes
    
    Returns:
        dict: Summary of the operation with keys:
            - success: bool
            - deactivated_count: int
            - effective_year: int
            - message: str
    """
    now = timezone.now()
    current_year = now.year
    current_month = now.month
    
    # After November 30th, use next year as effective year
    adjustment = 1 if (current_month == 12 or (current_month == 11 and now.day > 30)) else 0
    effective_year = current_year + adjustment
    
    # Find users who have graduated but are still active
    queryset = CustomUser.objects.filter(
        graduation_year__lt=effective_year,
        is_active=True,
    )
    
    if not include_staff:
        queryset = queryset.filter(is_staff=False)
    
    count = queryset.count()
    
    if count == 0:
        message = 'No graduated students found that need to be deactivated.'
        logger.info(f'[Scheduled Task] {message}')
        return {
            'success': True,
            'deactivated_count': 0,
            'effective_year': effective_year,
            'message': message,
        }
    
    if dry_run:
        message = f'[DRY RUN] Would deactivate {count} graduated students.'
        logger.info(f'[Scheduled Task] {message}')
        return {
            'success': True,
            'deactivated_count': 0,
            'effective_year': effective_year,
            'message': message,
            'dry_run': True,
        }
    
    # Perform the deactivation
    try:
        updated_count = queryset.update(is_active=False)
        message = f'Successfully deactivated {updated_count} graduated students.'
        logger.info(
            f'[Scheduled Task] {message} '
            f'Effective year: {effective_year}, Include staff: {include_staff}'
        )
        return {
            'success': True,
            'deactivated_count': updated_count,
            'effective_year': effective_year,
            'message': message,
        }
    except Exception as e:
        message = f'Error deactivating graduated students: {e}'
        logger.error(f'[Scheduled Task] {message}')
        return {
            'success': False,
            'deactivated_count': 0,
            'effective_year': effective_year,
            'message': message,
            'error': str(e),
        }


# Celery task wrapper (if Celery is installed)
try:
    from celery import shared_task
    
    @shared_task(name='accounts.deactivate_graduated_students')
    def celery_deactivate_graduated_students(include_staff=False):
        """
        Celery task to deactivate graduated students.
        
        Schedule this task in celery beat to run:
        - At the beginning of each year (January 1st)
        - At the end of each year (December 1st)
        
        Example celery beat schedule (in settings.py):
        
        CELERY_BEAT_SCHEDULE = {
            'deactivate-graduated-students-january': {
                'task': 'accounts.deactivate_graduated_students',
                'schedule': crontab(month_of_year=1, day_of_month=1, hour=0, minute=0),
            },
            'deactivate-graduated-students-december': {
                'task': 'accounts.deactivate_graduated_students',
                'schedule': crontab(month_of_year=12, day_of_month=1, hour=0, minute=0),
            },
        }
        """
        return deactivate_graduated_students_task(include_staff=include_staff)
    
except ImportError:
    # Celery is not installed, skip the task decorator
    pass
