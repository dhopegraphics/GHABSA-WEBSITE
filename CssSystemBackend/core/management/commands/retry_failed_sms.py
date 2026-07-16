"""
Management command to retry failed SMS notifications.

Usage:
    python manage.py retry_failed_sms
    python manage.py retry_failed_sms --max-retries 5
    python manage.py retry_failed_sms --dry-run
"""

from django.core.management.base import BaseCommand
from core.models import NotifyUser
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = "Retry sending failed SMS notifications"

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-retries',
            type=int,
            default=3,
            help='Maximum number of retry attempts (default: 3)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be retried without actually sending'
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Only retry failures from last N hours (default: 24)'
        )

    def handle(self, *args, **options):
        max_retries = options['max_retries']
        dry_run = options['dry_run']
        hours = options['hours']
        
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Find failed SMS notifications
        failed_notifications = NotifyUser.objects.filter(
            action='sent',
            sms_sent=False,
            channel__in=['sms', 'both'],
            retry_count__lt=max_retries,
            last_updated__gte=cutoff_time
        ).order_by('created_at')
        
        count = failed_notifications.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS(
                f"✅ No failed SMS notifications to retry (checked last {hours} hours)"
            ))
            return
        
        self.stdout.write(self.style.WARNING(
            f"Found {count} failed SMS notification(s) from last {hours} hours"
        ))
        
        if dry_run:
            self.stdout.write(self.style.NOTICE("\n🔍 DRY RUN - No messages will be sent\n"))
            for notif in failed_notifications:
                self.stdout.write(
                    f"  - ID {notif.id}: {notif.recipient.phone} "
                    f"(Retries: {notif.retry_count}, Error: {notif.sms_error[:50] if notif.sms_error else 'Unknown'})"
                )
            return
        
        # Retry sending
        success_count = 0
        failed_count = 0
        
        for notif in failed_notifications:
            self.stdout.write(
                f"\n📤 Retrying SMS #{notif.id} to {notif.recipient.phone} "
                f"(Attempt {notif.retry_count + 1}/{max_retries})..."
            )
            
            try:
                # Set action back to 'send' to trigger re-sending
                notif.action = 'send'
                notif.save()
                
                if notif.sms_sent:
                    success_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"  ✅ Success! Campaign ID: {notif.sms_campaign_id}"
                    ))
                else:
                    failed_count += 1
                    self.stdout.write(self.style.ERROR(
                        f"  ❌ Failed: {notif.sms_error[:100]}"
                    ))
            except Exception as e:
                failed_count += 1
                self.stdout.write(self.style.ERROR(
                    f"  ❌ Exception: {str(e)}"
                ))
        
        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(
            f"✅ Retry Summary: {success_count} succeeded, {failed_count} failed"
        ))
        
        if failed_count > 0:
            remaining = NotifyUser.objects.filter(
                action='sent',
                sms_sent=False,
                channel__in=['sms', 'both'],
                retry_count__lt=max_retries
            ).count()
            
            if remaining > 0:
                self.stdout.write(self.style.WARNING(
                    f"⚠️  {remaining} notification(s) still need retry (run command again)"
                ))
