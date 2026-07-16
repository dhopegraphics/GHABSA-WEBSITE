#!/usr/bin/env python
"""
Master automation script for PythonAnywhere scheduled tasks
This script can run multiple notification tasks based on command-line arguments

Usage:
    python run_automation.py process    # Process scheduled notifications (run every 5-10 min)
    python run_automation.py generate   # Generate class and exam notifications (run daily)
    python run_automation.py all        # Run all automation tasks
"""
import os
import sys
import django
import logging
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BioChemSystem.settings')
django.setup()

from django.conf import settings
from django.core.management import call_command
from django.utils import timezone
from utils.logging_config import get_logger

# Get logger for automation tasks
logger = get_logger('automation', 'automation')


def process_scheduled_notifications():
    """Process and send pending scheduled notifications"""
    logger.info("="*60)
    logger.info(f"Processing Scheduled Notifications - {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)
    
    try:
        call_command('process_scheduled_notifications')
        logger.info("Scheduled notifications processed successfully")
        return True
    except Exception as e:
        logger.exception(f"Error processing scheduled notifications: {e}")
        return False


def generate_notifications():
    """Generate class and exam notifications"""
    logger.info("="*60)
    logger.info(f"Generating Notifications - {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)
    
    success = True
    
    # Generate class notifications
    logger.info("Generating class schedule notifications...")
    try:
        call_command('generate_class_notifications')
        logger.info("Class notifications generated successfully")
    except Exception as e:
        logger.exception(f"Error generating class notifications: {e}")
        success = False
    
    # Generate exam notifications
    logger.info("Generating exam schedule notifications...")
    try:
        call_command('generate_exam_notifications')
        logger.info("Exam notifications generated successfully")
    except Exception as e:
        logger.exception(f"Error generating exam notifications: {e}")
        success = False
    
    return success


def cleanup_old_notifications():
    """Clean up old sent/failed notifications (older than 30 days)"""
    logger.info("="*60)
    logger.info(f"Cleaning Up Old Notifications - {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)
    
    try:
        from notifications.models import PushNotification
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=30)
        
        deleted = PushNotification.objects.filter(
            status__in=['sent', 'failed', 'cancelled'],
            created_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"Cleaned up {deleted[0]} old notification(s)")
        return True
    except Exception as e:
        logger.exception(f"Error cleaning up notifications: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        logger.error("No command provided")
        logger.info("Usage: python run_automation.py [process|generate|cleanup|all]")
        logger.info("Commands:")
        logger.info("  process  - Process scheduled notifications (run every 5-10 minutes)")
        logger.info("  generate - Generate class and exam notifications (run daily)")
        logger.info("  cleanup  - Clean up old notifications (run weekly)")
        logger.info("  all      - Run all automation tasks")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    logger.info("#"*60)
    logger.info(f"{settings.BRAND_SITE_LABEL} Notification Automation System")
    logger.info(f"Started: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("#"*60)
    
    success = True
    
    if command == 'process':
        success = process_scheduled_notifications()
    
    elif command == 'generate':
        success = generate_notifications()
    
    elif command == 'cleanup':
        success = cleanup_old_notifications()
    
    elif command == 'all':
        logger.info("Running all automation tasks...")
        success = (
            generate_notifications() and
            process_scheduled_notifications() and
            cleanup_old_notifications()
        )
    
    else:
        logger.error(f"Unknown command: {command}")
        logger.info("Valid commands: process, generate, cleanup, all")
        sys.exit(1)
    
    logger.info("#"*60)
    if success:
        logger.info("Automation completed successfully")
    else:
        logger.warning("Automation completed with errors")
    logger.info(f"Finished: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("#"*60)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

