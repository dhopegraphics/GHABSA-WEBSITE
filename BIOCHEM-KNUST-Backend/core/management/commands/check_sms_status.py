"""
Management command to check SMS delivery status from MNotify.

Usage:
    python manage.py check_sms_status
    python manage.py check_sms_status --campaign-id ABC123
    python manage.py check_sms_status --phone 0597959032
"""

from django.core.management.base import BaseCommand
from core.models import NotifyUser
import httpx
from django.conf import settings


class Command(BaseCommand):
    help = "Check SMS delivery status from MNotify dashboard"

    def add_arguments(self, parser):
        parser.add_argument(
            '--campaign-id',
            type=str,
            help='Check status of specific campaign ID'
        )
        parser.add_argument(
            '--phone',
            type=str,
            help='Check status for specific phone number'
        )
        parser.add_argument(
            '--recent',
            type=int,
            default=10,
            help='Check N most recent SMS (default: 10)'
        )

    def handle(self, *args, **options):
        campaign_id = options.get('campaign_id')
        phone = options.get('phone')
        recent = options['recent']
        
        if campaign_id:
            self._check_campaign(campaign_id)
        elif phone:
            self._check_phone(phone)
        else:
            self._check_recent(recent)
    
    def _check_campaign(self, campaign_id):
        """Check status of specific campaign"""
        self.stdout.write(f"\n🔍 Checking campaign: {campaign_id}\n")
        
        # Find in database
        notifications = NotifyUser.objects.filter(sms_campaign_id=campaign_id)
        
        if notifications.exists():
            for notif in notifications:
                self.stdout.write(f"📱 Recipient: {notif.recipient.phone}")
                self.stdout.write(f"📅 Sent at: {notif.last_updated}")
                self.stdout.write(f"✅ SMS Sent: {notif.sms_sent}")
                if notif.sms_error:
                    self.stdout.write(self.style.ERROR(f"❌ Error: {notif.sms_error}"))
        else:
            self.stdout.write(self.style.WARNING(f"⚠️  Campaign {campaign_id} not found in database"))
        
        # Check MNotify API for campaign status
        self._check_mnotify_status(campaign_id)
    
    def _check_phone(self, phone):
        """Check recent SMS to specific phone"""
        self.stdout.write(f"\n🔍 Checking SMS to: {phone}\n")
        
        notifications = NotifyUser.objects.filter(
            recipient__phone__contains=phone,
            channel__in=['sms', 'both']
        ).order_by('-created_at')[:5]
        
        if not notifications.exists():
            self.stdout.write(self.style.WARNING(f"⚠️  No SMS found for {phone}"))
            return
        
        for notif in notifications:
            self._display_notification(notif)
    
    def _check_recent(self, count):
        """Check recent SMS"""
        self.stdout.write(f"\n📊 Checking {count} most recent SMS\n")
        self.stdout.write("=" * 70 + "\n")
        
        notifications = NotifyUser.objects.filter(
            channel__in=['sms', 'both']
        ).order_by('-created_at')[:count]
        
        if not notifications.exists():
            self.stdout.write(self.style.WARNING("⚠️  No SMS notifications found"))
            return
        
        for i, notif in enumerate(notifications, 1):
            self.stdout.write(f"\n#{i}:")
            self._display_notification(notif)
    
    def _display_notification(self, notif):
        """Display notification details"""
        self.stdout.write(f"  📱 To: {notif.recipient.phone}")
        self.stdout.write(f"  📅 Created: {notif.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write(f"  📝 Message: {notif.message[:50]}...")
        
        if notif.sms_sent:
            self.stdout.write(self.style.SUCCESS(f"  ✅ Status: SENT"))
            self.stdout.write(f"  🔖 Campaign: {notif.sms_campaign_id}")
            
            # Check MNotify status
            if notif.sms_campaign_id:
                self._check_mnotify_status(notif.sms_campaign_id, indent=4)
        else:
            self.stdout.write(self.style.ERROR(f"  ❌ Status: FAILED"))
            if notif.sms_error:
                self.stdout.write(f"  💬 Error: {notif.sms_error[:60]}")
        
        self.stdout.write(f"  🔄 Retries: {notif.retry_count}")
    
    def _check_mnotify_status(self, campaign_id, indent=0):
        """Check campaign status from MNotify API"""
        try:
            # MNotify campaign status endpoint
            url = f"https://api.mnotify.com/api/campaign/{campaign_id}?key={settings.SMS_API_KEY}"
            
            with httpx.Client(timeout=15.0) as client:
                response = client.get(url)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    prefix = " " * indent
                    
                    if result.get('status') == 'success':
                        data = result.get('data', {})
                        
                        self.stdout.write(f"{prefix}🌐 MNotify Status:")
                        self.stdout.write(f"{prefix}   Type: {data.get('type', 'N/A')}")
                        self.stdout.write(f"{prefix}   Total Sent: {data.get('total_sent', 'N/A')}")
                        self.stdout.write(f"{prefix}   Delivered: {data.get('delivered', 'N/A')}")
                        self.stdout.write(f"{prefix}   Failed: {data.get('failed', 'N/A')}")
                        self.stdout.write(f"{prefix}   Pending: {data.get('pending', 'N/A')}")
                        
                        # Show delivery status
                        status = data.get('status', 'UNKNOWN')
                        if status == 'DELIVERED':
                            self.stdout.write(self.style.SUCCESS(f"{prefix}   ✅ Delivery: {status}"))
                        elif status == 'SUBMITTED':
                            self.stdout.write(self.style.WARNING(f"{prefix}   ⏳ Delivery: {status} (processing by network)"))
                        elif status == 'FAILED':
                            self.stdout.write(self.style.ERROR(f"{prefix}   ❌ Delivery: {status}"))
                        else:
                            self.stdout.write(f"{prefix}   📍 Delivery: {status}")
                    else:
                        self.stdout.write(self.style.WARNING(
                            f"{prefix}⚠️  MNotify: {result.get('message', 'Could not get status')}"
                        ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f"{prefix}⚠️  MNotify API returned status {response.status_code}"
                    ))
                    
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f"{' ' * indent}⚠️  Could not check MNotify status: {str(e)}"
            ))
