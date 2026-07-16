"""
Send Recent Updates Push Notifications
Management command to send push notifications for recent updates

Usage:
    python manage.py send_recent_updates_notifications --type=task_due
    python manage.py send_recent_updates_notifications --type=event_upcoming
    python manage.py send_recent_updates_notifications --type=payment_reminder
    python manage.py send_recent_updates_notifications --all

Schedule this command to run periodically (e.g., via cron or PythonAnywhere scheduled tasks):
    - task_due: Run daily at 8 AM
    - event_upcoming: Run daily at 7 AM
    - payment_reminder: Run every 3 days
"""
from django.core.management.base import BaseCommand, CommandError
from notifications.recent_updates_repository import RecentUpdatesRepository
from notifications.services import NotificationService


class Command(BaseCommand):
    help = 'Send push notifications for recent updates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['task_due', 'event_upcoming', 'helpdesk_response', 'payment_reminder'],
            help='Type of notification to send',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Send all types of notifications',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending',
        )

    def handle(self, *args, **options):
        notification_type = options.get('type')
        send_all = options.get('all')
        dry_run = options.get('dry_run')

        if not notification_type and not send_all:
            raise CommandError('Must specify either --type or --all')

        if send_all:
            types_to_send = ['task_due', 'event_upcoming', 'payment_reminder']
        else:
            types_to_send = [notification_type]

        total_sent = 0
        total_failed = 0

        for notif_type in types_to_send:
            self.stdout.write(
                self.style.WARNING(f'\n📬 Processing {notif_type} notifications...')
            )

            try:
                # Get users who need notifications
                users_to_notify = RecentUpdatesRepository.get_users_needing_notifications(
                    notif_type
                )

                self.stdout.write(
                    f'Found {len(users_to_notify)} user(s) to notify'
                )

                if dry_run:
                    self.stdout.write(
                        self.style.WARNING('🔍 DRY RUN - No notifications will be sent')
                    )

                # Send notifications
                for user, notification_data in users_to_notify:
                    try:
                        if dry_run:
                            self.stdout.write(
                                f'  Would send to {user.first_name} {user.last_name}: '
                                f'{notification_data["title"]}'
                            )
                        else:
                            # Send push notification
                            NotificationService.send_push_notification(
                                user=user,
                                title=notification_data['title'],
                                body=notification_data['body'],
                                data=notification_data.get('data', {}),
                                sound='default',
                                category=notif_type,
                            )
                            
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✅ Sent to {user.first_name} {user.last_name}'
                                )
                            )
                            total_sent += 1

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'  ❌ Failed for {user.first_name} {user.last_name}: {str(e)}'
                            )
                        )
                        total_failed += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error processing {notif_type}: {str(e)}')
                )
                total_failed += 1

        # Summary
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(
            self.style.SUCCESS(f'✅ Successfully sent: {total_sent}')
        )
        if total_failed > 0:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed: {total_failed}')
            )
        self.stdout.write('=' * 50 + '\n')

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '🔍 This was a dry run. Use without --dry-run to actually send notifications.'
                )
            )
