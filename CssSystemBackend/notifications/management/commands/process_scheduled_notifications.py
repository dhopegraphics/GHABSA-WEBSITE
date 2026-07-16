"""
Management command to process scheduled notifications
This command should be run periodically (every 5-10 minutes) via cron/scheduled task

Usage:
    python manage.py process_scheduled_notifications
    python manage.py process_scheduled_notifications --dry-run
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from notifications.models import PushNotification
from notifications.services import PushNotificationService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process and send all pending scheduled notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()
        
        # Get pending scheduled notifications that are due
        pending_notifications = PushNotification.objects.filter(
            status='scheduled',
            scheduled_at__lte=now
        ).select_related('user').order_by('scheduled_at')
        
        count = pending_notifications.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS(
                f"✅ No pending scheduled notifications to process at {now.strftime('%Y-%m-%d %H:%M:%S')}"
            ))
            return
        
        self.stdout.write(self.style.WARNING(
            f"Found {count} scheduled notification(s) to process"
        ))
        
        if dry_run:
            self.stdout.write(self.style.NOTICE("\n🔍 DRY RUN - No notifications will be sent\n"))
            for notif in pending_notifications:
                self.stdout.write(
                    f"  - [{notif.scheduled_at}] {notif.user.username}: {notif.title} - {notif.body[:50]}..."
                )
            return
        
        # Process notifications
        sent_count = 0
        failed_count = 0
        
        for notification in pending_notifications:
            try:
                self.stdout.write(
                    f"📤 Sending to {notification.user.username}: {notification.title}"
                )
                
                result = PushNotificationService.send_to_user(
                    user=notification.user,
                    title=notification.title,
                    body=notification.body,
                    data=notification.data,
                    sound=notification.sound,
                    priority=notification.priority,
                    badge=notification.badge,
                    category=notification.category,
                )
                
                if result.get('success'):
                    notification.status = 'sent'
                    notification.sent_at = now
                    notification.save()
                    sent_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"  ✅ Sent successfully"
                    ))
                else:
                    notification.status = 'failed'
                    notification.error_message = result.get('error', 'Unknown error')
                    notification.save()
                    failed_count += 1
                    self.stdout.write(self.style.ERROR(
                        f"  ❌ Failed: {result.get('error', 'Unknown error')}"
                    ))
                    
            except Exception as e:
                notification.status = 'failed'
                notification.error_message = str(e)
                notification.save()
                failed_count += 1
                self.stdout.write(self.style.ERROR(
                    f"  ❌ Exception: {str(e)}"
                ))
        
        # Summary
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS(
            f"📊 Processing Summary:"
        ))
        self.stdout.write(f"  Total processed: {count}")
        self.stdout.write(self.style.SUCCESS(f"  ✅ Sent: {sent_count}"))
        self.stdout.write(self.style.ERROR(f"  ❌ Failed: {failed_count}"))
        self.stdout.write("="*60)
        
        logger.info(
            f"Processed {count} scheduled notifications: "
            f"{sent_count} sent, {failed_count} failed"
        )
