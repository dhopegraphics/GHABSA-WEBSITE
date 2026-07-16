"""
Quick Test Script for Push Notifications

This script provides helper commands to test push notifications
Run in Django shell: python manage.py shell < test_push_notifications.py
Or import functions: from scripts.test_push_notifications import *
"""

from notifications.models import PushNotificationDevice
from core.models import NotifyUser
from accounts.models import CustomUser
from notifications.services import PushNotificationService


def show_all_devices():
    """Display all registered push notification devices"""
    print("\n" + "="*80)
    print("REGISTERED PUSH NOTIFICATION DEVICES")
    print("="*80)
    
    devices = PushNotificationDevice.objects.all().order_by('-created_at')
    
    if not devices:
        print("❌ No devices registered yet")
        print("\nTo register a device:")
        print("  - Web: Open browser, login, grant notification permission")
        print("  - Mobile: Open Expo app, login, grant notification permission")
        return
    
    print(f"\nTotal Devices: {devices.count()}")
    print(f"Active: {devices.filter(is_active=True).count()}")
    print(f"Web: {devices.filter(platform='web').count()}")
    print(f"Mobile (Expo): {devices.filter(platform='expo').count()}")
    
    print("\n" + "-"*80)
    for device in devices:
        status = "✅ ACTIVE" if device.is_active else "❌ INACTIVE"
        print(f"{status} | {device.user.username} | {device.platform.upper()} | {device.device_name}")
        print(f"         Last Used: {device.last_used.strftime('%Y-%m-%d %H:%M') if device.last_used else 'Never'}")
        print(f"         Created: {device.created_at.strftime('%Y-%m-%d %H:%M')}")
        print("-"*80)
    
    print()


def test_single_device(username):
    """
    Send a test notification to a specific user's first active device
    
    Args:
        username (str): Username of the recipient
        
    Example:
        test_single_device('admin')
    """
    print(f"\n🔔 Testing notification for user: {username}")
    print("="*80)
    
    try:
        user = CustomUser.objects.get(username=username)
    except CustomUser.DoesNotExist:
        print(f"❌ User '{username}' not found")
        print("\nAvailable users:")
        for u in CustomUser.objects.all()[:10]:
            print(f"  - {u.username}")
        return
    
    # Check for active devices
    devices = PushNotificationDevice.objects.filter(user=user, is_active=True)
    
    if not devices.exists():
        print(f"❌ No active devices found for {username}")
        print("\nUser needs to:")
        print("  1. Open the app (web or mobile)")
        print("  2. Login")
        print("  3. Grant notification permission")
        return
    
    print(f"✅ Found {devices.count()} active device(s) for {username}")
    for device in devices:
        print(f"   - {device.platform}: {device.device_name}")
    
    # Send test notification
    print("\n📤 Sending test notification...")
    
    result = PushNotificationService.send_to_user(
        user=user,
        title="Test Notification",
        body=f"This is a test notification for {username}. If you see this, push notifications are working! 🎉",
        data={
            "type": "test",
            "screen": "Home",
            "test_id": "quick_test_1"
        }
    )
    
    print("\n" + "="*80)
    if result.get('success'):
        print(f"✅ SUCCESS: Notification sent to {result.get('devices_notified', 0)} device(s)")
        print("\n✨ Check your device for the notification!")
    else:
        print(f"❌ FAILED: {result.get('message')}")
        print("\nTroubleshooting:")
        print("  1. Check device is active in admin")
        print("  2. Check backend logs: tail -f logs/django.log")
        print("  3. Verify notification permission granted")
    print("="*80 + "\n")


def test_notifyuser_model(username, channel='push'):
    """
    Test the NotifyUser model (production workflow)
    
    Args:
        username (str): Username of the recipient
        channel (str): 'sms', 'push', or 'both'
        
    Example:
        test_notifyuser_model('admin', channel='push')
        test_notifyuser_model('admin', channel='both')
    """
    print(f"\n📝 Testing NotifyUser Model")
    print(f"User: {username} | Channel: {channel}")
    print("="*80)
    
    try:
        user = CustomUser.objects.get(username=username)
    except CustomUser.DoesNotExist:
        print(f"❌ User '{username}' not found")
        return
    
    # Check for devices if channel involves push
    if channel in ['push', 'both']:
        devices = PushNotificationDevice.objects.filter(user=user, is_active=True)
        if not devices.exists():
            print(f"⚠️  WARNING: No active devices found for {username}")
            print("   Push notification will not be sent")
            print()
    
    # Create NotifyUser record
    notification = NotifyUser.objects.create(
        recipient=user,
        title="NotifyUser Test",
        message=f"Testing NotifyUser model with channel='{channel}'. This tests the production notification workflow.",
        channel=channel,
        push_data={
            "type": "test",
            "screen": "Academics",
            "test_source": "notifyuser_model"
        },
        action="send"  # This triggers sending on save
    )
    
    print("\n📊 Notification Status:")
    print("-"*80)
    print(f"ID: {notification.id}")
    print(f"Recipient: {notification.recipient.username}")
    print(f"Channel: {notification.channel}")
    print(f"Action: {notification.action}")
    print(f"Sent: {notification.sent}")
    print()
    
    if channel in ['sms', 'both']:
        print(f"SMS Sent: {'✅' if notification.sms_sent else '❌'}")
        if notification.sms_error:
            print(f"SMS Error: {notification.sms_error}")
    
    if channel in ['push', 'both']:
        print(f"Push Sent: {'✅' if notification.push_sent else '❌'}")
        if notification.push_error:
            print(f"Push Error: {notification.push_error}")
    
    print("-"*80)
    
    if notification.sent:
        print("\n✅ SUCCESS: Notification sent successfully!")
        print("Check your device for the notification")
    else:
        print("\n❌ FAILED: Notification was not sent")
        print("Check errors above for details")
    
    print()


def test_bulk_notification(usernames, channel='push'):
    """
    Send test notification to multiple users
    
    Args:
        usernames (list): List of usernames
        channel (str): 'sms', 'push', or 'both'
        
    Example:
        test_bulk_notification(['admin', 'student1', 'student2'], channel='push')
    """
    print(f"\n📢 Testing Bulk Notification")
    print(f"Users: {', '.join(usernames)} | Channel: {channel}")
    print("="*80)
    
    success_count = 0
    failed_count = 0
    
    for username in usernames:
        try:
            user = CustomUser.objects.get(username=username)
            
            notification = NotifyUser.objects.create(
                recipient=user,
                title="Bulk Test Notification",
                message=f"Testing bulk notification to {username}",
                channel=channel,
                push_data={"type": "bulk_test"},
                action="send"
            )
            
            if notification.sent:
                success_count += 1
                print(f"✅ {username}: Sent")
            else:
                failed_count += 1
                print(f"❌ {username}: Failed")
                
        except CustomUser.DoesNotExist:
            failed_count += 1
            print(f"❌ {username}: User not found")
    
    print("="*80)
    print(f"\n📊 Results: {success_count} success, {failed_count} failed")
    print()


def show_recent_notifications(limit=10):
    """Display recent NotifyUser records"""
    print(f"\n📜 Recent Notifications (Last {limit})")
    print("="*80)
    
    notifications = NotifyUser.objects.all().order_by('-created_at')[:limit]
    
    if not notifications:
        print("❌ No notifications found")
        return
    
    for notif in notifications:
        status = "✅" if notif.sent else "❌"
        print(f"{status} | {notif.recipient.username} | {notif.channel} | {notif.action}")
        print(f"    Title: {notif.title or 'N/A'}")
        print(f"    SMS: {'✅' if notif.sms_sent else '❌'} | Push: {'✅' if notif.push_sent else '❌'}")
        print(f"    Created: {notif.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print("-"*80)
    
    print()


def cleanup_inactive_devices():
    """Mark inactive devices (for testing cleanup)"""
    print("\n🧹 Device Cleanup")
    print("="*80)
    
    from django.utils import timezone
    from datetime import timedelta
    
    # Devices not used in 30 days
    cutoff = timezone.now() - timedelta(days=30)
    old_devices = PushNotificationDevice.objects.filter(
        is_active=True,
        last_used__lt=cutoff
    )
    
    count = old_devices.count()
    
    if count == 0:
        print("✅ No inactive devices to clean up")
        return
    
    print(f"Found {count} devices not used in 30+ days:")
    for device in old_devices:
        print(f"  - {device.user.username}: {device.platform} ({device.device_name})")
    
    response = input(f"\nMark these {count} devices as inactive? (yes/no): ")
    
    if response.lower() == 'yes':
        old_devices.update(is_active=False)
        print(f"✅ Marked {count} devices as inactive")
    else:
        print("❌ Cancelled")
    
    print()


# Quick access functions
def test_admin():
    """Quick test for admin user"""
    test_single_device('admin')


def test_me(username):
    """Quick test for yourself"""
    test_single_device(username)


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🔔 PUSH NOTIFICATION TEST HELPER")
    print("="*80)
    print("\nAvailable Commands:")
    print("  show_all_devices()                           - List all registered devices")
    print("  test_single_device('username')               - Send test to one user")
    print("  test_notifyuser_model('username', 'push')    - Test NotifyUser model")
    print("  test_bulk_notification(['user1', 'user2'])   - Test bulk send")
    print("  show_recent_notifications()                  - Show recent notifications")
    print("  cleanup_inactive_devices()                   - Clean up old devices")
    print("  test_admin()                                 - Quick test for admin user")
    print("\nExample Usage:")
    print("  python manage.py shell")
    print("  >>> from scripts.test_push_notifications import *")
    print("  >>> show_all_devices()")
    print("  >>> test_single_device('admin')")
    print("="*80 + "\n")
    
    # Auto-run on direct execution
    show_all_devices()
