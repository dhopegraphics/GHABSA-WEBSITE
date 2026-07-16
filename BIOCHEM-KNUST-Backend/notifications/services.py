"""
Push Notification Service
Handles sending push notifications via Expo Push Notifications, FCM, or Web Push
"""
import requests
from django.conf import settings
from django.utils import timezone
from typing import List, Dict, Any
import logging
import json

logger = logging.getLogger(__name__)


class PushNotificationService:
    """Service for sending push notifications"""
    
    EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
    
    @staticmethod
    def send_push_notification(
        device_tokens: List[str] = None,
        title: str = None,
        body: str = None,
        data: Dict[str, Any] = None,
        sound: str = 'default',
        priority: str = 'default',
        badge: int = 1,
        category: str = None,
        user = None,  # Accept user parameter for convenience
    ) -> Dict[str, Any]:
        """
        Send push notification to multiple devices using Expo Push Notifications
        Can accept either device_tokens list OR user object
        
        Args:
            device_tokens: List of Expo push tokens (if user not provided)
            user: CustomUser instance (alternative to device_tokens)
            title: Notification title
            body: Notification body
            data: Additional data payload
            sound: Notification sound
            priority: Priority level (default, normal, high)
            badge: Badge count for iOS
            category: Notification category
        
        Returns:
            Dict with success status and results
        """
        # If user is provided, get their device tokens
        if user and not device_tokens:
            from notifications.models import PushNotificationDevice
            devices = PushNotificationDevice.objects.filter(
                user=user,
                is_active=True
            )
            device_tokens = list(devices.values_list('device_token', flat=True))
            
            if not device_tokens:
                logger.warning(f"No active devices found for user {user.phone if hasattr(user, 'phone') else user.username}")
                return {'success': False, 'error': 'No active devices found for user'}
        
        if not device_tokens:
            return {'success': False, 'error': 'No device tokens provided'}
        
        # Filter valid Expo tokens
        valid_tokens = [
            token for token in device_tokens
            if token.startswith('ExponentPushToken[') or token.startswith('ExpoPushToken[')
        ]
        
        if not valid_tokens:
            return {'success': False, 'error': 'No valid Expo tokens provided'}
        
        messages = []
        for token in valid_tokens:
            message = {
                'to': token,
                'title': title,
                'body': body,
                'sound': sound,
                'priority': priority,
                'badge': badge,
            }
            
            if data:
                message['data'] = data
            
            if category:
                message['categoryId'] = category
            
            messages.append(message)
        
        try:
            response = requests.post(
                PushNotificationService.EXPO_PUSH_URL,
                json=messages,
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                },
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            return {
                'success': True,
                'data': result.get('data', []),
                'errors': result.get('errors', [])
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending push notification: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def send_to_user(user, title: str, body: str, **kwargs) -> Dict[str, Any]:
        """
        Send push notification to all active devices of a user (mobile and web)
        
        Args:
            user: CustomUser instance
            title: Notification title
            body: Notification body
            **kwargs: Additional notification parameters
        
        Returns:
            Dict with success status and results including per-device status
        """
        from notifications.models import PushNotificationDevice, NotificationPreference
        
        # Check user preferences
        try:
            preferences = user.notification_preferences
            if not preferences.push_enabled:
                logger.info(f"Push notifications disabled for user {user.username}")
                return {'success': False, 'error': 'Push notifications disabled by user'}
            
            if preferences.is_in_quiet_hours():
                logger.info(f"User {user.username} is in quiet hours")
                return {'success': False, 'error': 'User is in quiet hours'}
        except NotificationPreference.DoesNotExist:
            # Create default preferences if not exist
            NotificationPreference.objects.create(user=user)
        
        # Get all active devices for this user (supports multiple devices)
        devices = PushNotificationDevice.objects.filter(
            user=user,
            is_active=True
        )
        
        device_count = devices.count()
        if device_count == 0:
            logger.warning(f"No active devices found for user {user.username}")
            return {'success': False, 'error': 'No active devices found'}
        
        logger.info(f"Sending notification to {device_count} device(s) for user {user.username}")
        
        # Separate mobile and web devices
        mobile_devices = devices.filter(platform__in=['ios', 'android'])
        web_devices = devices.filter(platform='web')
        
        results = {
            'success': True,
            'mobile': {'sent': 0, 'failed': 0},
            'web': {'sent': 0, 'failed': 0},
            'total_devices': device_count
        }
        
        # Send to mobile devices (Expo/FCM)
        if mobile_devices.exists():
            device_tokens = list(mobile_devices.values_list('device_token', flat=True))
            mobile_result = PushNotificationService.send_push_notification(
                device_tokens=device_tokens,
                title=title,
                body=body,
                **kwargs
            )
            if mobile_result.get('success'):
                results['mobile']['sent'] = len(device_tokens)
                logger.info(f"Sent to {len(device_tokens)} mobile device(s)")
            else:
                results['mobile']['failed'] = len(device_tokens)
        
        # Send to web devices (Web Push)
        if web_devices.exists():
            web_result = WebPushService.send_to_user_web_devices(user, title, body, **kwargs)
            results['web']['sent'] = web_result.get('success', 0)
            results['web']['failed'] = web_result.get('failed', 0)
            if web_result.get('errors'):
                results['message'] = '; '.join(web_result.get('errors'))
            logger.info(f"Sent to {web_result.get('success', 0)} web device(s), {web_result.get('failed', 0)} failed")
        
        # Overall success if any device received the notification
        results['success'] = (results['mobile']['sent'] + results['web']['sent']) > 0
        results['devices_notified'] = results['mobile']['sent'] + results['web']['sent']
        
        if not results['success'] and not results.get('message'):
            results['message'] = 'No active devices found or all sends failed'
        
        return results
    
    @staticmethod
    def send_to_users(users, title: str, body: str, **kwargs) -> Dict[str, Any]:
        """
        Send push notification to multiple users
        
        Args:
            users: QuerySet or list of CustomUser instances
            title: Notification title
            body: Notification body
            **kwargs: Additional notification parameters
        
        Returns:
            Dict with success status and summary
        """
        results = {
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        for user in users:
            result = PushNotificationService.send_to_user(user, title, body, **kwargs)
            if result.get('success'):
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'user': user.username,
                    'error': result.get('error')
                })
        
        return results


class WebPushService:
    """Service for sending Web Push notifications to browsers"""
    
    @staticmethod
    def send_web_push(
        subscription_info: Dict[str, Any],
        title: str,
        body: str,
        data: Dict[str, Any] = None,
        icon: str = None,
        badge: str = None,
        tag: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send Web Push notification to a single browser subscription
        
        Args:
            subscription_info: Web Push subscription object (endpoint, keys)
            title: Notification title
            body: Notification body
            data: Additional data payload
            icon: Notification icon URL
            badge: Badge icon URL
            tag: Notification tag for grouping
        
        Returns:
            Dict with success status and results
        """
        try:
            from pywebpush import webpush, WebPushException
            import json
            import tempfile
            import os
            
            # Get VAPID configuration
            vapid_private_key_b64 = getattr(settings, 'WEBPUSH_SETTINGS', {}).get('VAPID_PRIVATE_KEY')
            vapid_email = getattr(settings, 'WEBPUSH_SETTINGS', {}).get('VAPID_ADMIN_EMAIL')
            
            if not vapid_private_key_b64 or not vapid_email:
                logger.error("VAPID keys not configured in settings")
                return {
                    'success': False,
                    'error': 'Web Push not configured on server'
                }
            
            # Convert DER base64 to PEM format and write to temp file
            # pywebpush expects a PEM file path or PEM string
            try:
                import base64
                from cryptography.hazmat.primitives.serialization import load_der_private_key, Encoding, PrivateFormat, NoEncryption
                from cryptography.hazmat.backends import default_backend
                
                # Decode base64 DER
                padding = '=' * (4 - len(vapid_private_key_b64) % 4) if len(vapid_private_key_b64) % 4 else ''
                private_key_der = base64.urlsafe_b64decode(vapid_private_key_b64 + padding)
                
                # Load key and convert to PEM
                private_key_obj = load_der_private_key(private_key_der, password=None, backend=default_backend())
                vapid_private_key_pem = private_key_obj.private_bytes(
                    encoding=Encoding.PEM,
                    format=PrivateFormat.PKCS8,
                    encryption_algorithm=NoEncryption()
                ).decode('utf-8')
                
                # Write PEM to temporary file
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem') as temp_pem:
                    temp_pem.write(vapid_private_key_pem)
                    vapid_key_path = temp_pem.name
                
                logger.info(f"Created temporary PEM file: {vapid_key_path}")
                
            except Exception as key_error:
                logger.error(f"Failed to convert VAPID key: {str(key_error)}", exc_info=True)
                return {
                    'success': False,
                    'error': f'Invalid VAPID key format: {str(key_error)}'
                }
            
            # Prepare notification payload
            payload = {
                'title': title,
                'body': body,
                'icon': icon or '/static/icons/notification-icon.png',
                'badge': badge or '/static/icons/badge-icon.png',
                'tag': tag or 'default',
                'data': data or {},
            }
            
            # Send the notification using the temp PEM file
            try:
                response = webpush(
                    subscription_info=subscription_info,
                    data=json.dumps(payload),
                    vapid_private_key=vapid_key_path,  # Use temp file path
                    vapid_claims={
                        "sub": f"mailto:{vapid_email}"
                    }
                )
                
                logger.info(f"Web Push sent successfully: {response.status_code}")
                return {
                    'success': True,
                    'status_code': response.status_code
                }
            finally:
                # Clean up temp file
                try:
                    os.unlink(vapid_key_path)
                except:
                    pass
            
        except WebPushException as e:
            logger.error(f"Web Push error: {str(e)}")
            # If subscription is expired/invalid, mark for deletion
            if e.response and e.response.status_code in [404, 410]:
                return {
                    'success': False,
                    'error': 'Subscription expired or invalid',
                    'expired': True
                }
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error sending Web Push: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def send_to_user_web_devices(user, title: str, body: str, **kwargs) -> Dict[str, Any]:
        """
        Send Web Push notifications to all user's web devices
        
        Args:
            user: CustomUser instance
            title: Notification title
            body: Notification body
            **kwargs: Additional notification parameters
        
        Returns:
            Dict with success status and results
        """
        from notifications.models import PushNotificationDevice
        
        # Get all active web devices for this user
        web_devices = PushNotificationDevice.objects.filter(
            user=user,
            is_active=True,
            platform='web'
        )
        
        device_count = web_devices.count()
        if device_count == 0:
            return {
                'success': False,
                'error': 'No active web devices found'
            }
        
        results = {
            'total': device_count,
            'success': 0,
            'failed': 0,
            'expired': [],
            'errors': []  # Collect actual error messages
        }
        
        for device in web_devices:
            if not device.web_subscription:
                error_msg = f"Web device {device.id} missing subscription data"
                logger.warning(error_msg)
                results['failed'] += 1
                results['errors'].append(error_msg)
                continue
            
            result = WebPushService.send_web_push(
                subscription_info=device.web_subscription,
                title=title,
                body=body,
                **kwargs
            )
            
            if result.get('success'):
                results['success'] += 1
                logger.info(f"Successfully sent web push to device {device.id}")
            else:
                results['failed'] += 1
                error_msg = result.get('error', 'Unknown error')
                results['errors'].append(f"Device {device.id}: {error_msg}")
                logger.error(f"Failed to send web push to device {device.id}: {error_msg}")
                # If subscription expired, mark device as inactive
                if result.get('expired'):
                    device.is_active = False
                    device.save()
                    results['expired'].append(str(device.id))
                    logger.info(f"Marked expired web device {device.id} as inactive")
        
        return results


class BulkNotificationService:
    """Service for sending bulk personalized notifications"""
    
    @staticmethod
    def send_exam_notifications_to_users(users, exam_schedule):
        """
        Send personalized exam schedule notifications to multiple users
        
        Args:
            users: QuerySet or list of CustomUser instances
            exam_schedule: ExaminationSchedule instance
        
        Returns:
            Dict with success/failure summary
        """
        from notifications.models import PushNotification
        
        results = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        for user in users:
            results['total'] += 1
            
            # Create personalized data for this user
            personalized_data = {
                'type': 'exam_notification',
                'exam_id': str(exam_schedule.id),
                'course_name': exam_schedule.course.course_name,
                'course_code': exam_schedule.course.course_code,
                'exam_date': exam_schedule.time.strftime('%Y-%m-%d'),
                'exam_time': exam_schedule.time.strftime('%I:%M %p'),
                'college': exam_schedule.college,
                'room': exam_schedule.room or 'TBA',
                'user_index': user.index_number if hasattr(user, 'index_number') else 'N/A',
            }
            
            # Create personalized title and body
            title = f"Exam Alert: {exam_schedule.course.course_code}"
            body = (
                f"Your {exam_schedule.course.course_name} exam is scheduled for "
                f"{exam_schedule.time.strftime('%B %d, %Y at %I:%M %p')}. \n"
                f"Location: {exam_schedule.college} - {exam_schedule.room or 'TBA'}. \n"
                f"Index Range: {exam_schedule.index_number_start} - {exam_schedule.index_number_end}"
            )
            
            # Send notification
            result = PushNotificationService.send_to_user(
                user=user,
                title=title,
                body=body,
                data=personalized_data,
                priority='high',
                category='exam'
            )
            
            # Create notification record
            notification = PushNotification.objects.create(
                user=user,
                title=title,
                body=body,
                data=personalized_data,
                status='sent' if result.get('success') else 'failed',
                sent_at=timezone.now() if result.get('success') else None,
                error_message=result.get('error', '') if not result.get('success') else None,
                priority='high',
                trigger_type='exam_schedule',
                trigger_id=str(exam_schedule.id),
            )
            
            if result.get('success'):
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'user': user.username,
                    'error': result.get('error', 'Unknown error')
                })
        
        return results
    
    @staticmethod
    def send_class_notifications_to_users(users, class_schedule):
        """
        Send personalized class schedule notifications to multiple users
        
        Args:
            users: QuerySet or list of CustomUser instances
            class_schedule: ClassSchedule instance
        
        Returns:
            Dict with success/failure summary
        """
        from notifications.models import PushNotification
        
        results = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        for user in users:
            results['total'] += 1
            
            # Create personalized data
            personalized_data = {
                'type': 'class_notification',
                'class_id': str(class_schedule.id),
                'course_name': class_schedule.course.course_name,
                'course_code': class_schedule.course.course_code,
                'day': class_schedule.get_day_of_week_display(),
                'start_time': class_schedule.start_time.strftime('%I:%M %p'),
                'end_time': class_schedule.end_time.strftime('%I:%M %p'),
                'room': class_schedule.room or 'TBA',
                'program': class_schedule.get_program_display(),
                'year': class_schedule.year,
                'group': class_schedule.get_group_display(),
            }
            
            title = f"Class Update: {class_schedule.course.course_code}"
            body = (
                f"{class_schedule.course.course_name} - {class_schedule.get_day_of_week_display()} "
                f"{class_schedule.start_time.strftime('%I:%M %p')} - {class_schedule.end_time.strftime('%I:%M %p')}. \n"
                f"Room: {class_schedule.room or 'TBA'}. \n"
                f"Program: Year {class_schedule.year} {class_schedule.get_program_display()} {class_schedule.get_group_display()}"
            )
            
            result = PushNotificationService.send_to_user(
                user=user,
                title=title,
                body=body,
                data=personalized_data,
                priority='normal',
                category='class'
            )
            
            # Create notification record
            notification = PushNotification.objects.create(
                user=user,
                title=title,
                body=body,
                data=personalized_data,
                status='sent' if result.get('success') else 'failed',
                sent_at=timezone.now() if result.get('success') else None,
                error_message=result.get('error', '') if not result.get('success') else None,
                priority='normal',
                trigger_type='class_schedule',
                trigger_id=str(class_schedule.id),
            )
            
            if result.get('success'):
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'user': user.username,
                    'error': result.get('error', 'Unknown error')
                })
        
        return results
    
    @staticmethod
    def send_custom_bulk_notification(users, title: str, body: str, data: Dict = None, priority: str = 'normal'):
        """
        Send custom notification to multiple users with optional personalized data
        
        Args:
            users: QuerySet or list of CustomUser instances
            title: Notification title (can include {username} placeholder)
            body: Notification body (can include {username}, {email} placeholders)
            data: Additional data to include
            priority: Notification priority
        
        Returns:
            Dict with success/failure summary
        """
        from notifications.models import PushNotification
        
        results = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        for user in users:
            results['total'] += 1
            
            # Personalize title and body with user data
            personalized_title = title.format(
                username=user.username,
                email=user.email,
                first_name=getattr(user, 'first_name', ''),
                last_name=getattr(user, 'last_name', ''),
            )
            
            personalized_body = body.format(
                username=user.username,
                email=user.email,
                first_name=getattr(user, 'first_name', ''),
                last_name=getattr(user, 'last_name', ''),
                index_number=getattr(user, 'index_number', 'N/A'),
            )
            
            # Merge user-specific data
            personalized_data = data.copy() if data else {}
            personalized_data.update({
                'user_id': str(user.id),
                'username': user.username,
            })
            
            result = PushNotificationService.send_to_user(
                user=user,
                title=personalized_title,
                body=personalized_body,
                data=personalized_data,
                priority=priority,
            )
            
            # Create notification record
            notification = PushNotification.objects.create(
                user=user,
                title=personalized_title,
                body=personalized_body,
                data=personalized_data,
                status='sent' if result.get('success') else 'failed',
                sent_at=timezone.now() if result.get('success') else None,
                error_message=result.get('error', '') if not result.get('success') else None,
                priority=priority,
                trigger_type='manual_bulk',
            )
            
            if result.get('success'):
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'user': user.username,
                    'error': result.get('error', 'Unknown error')
                })
        
        return results


class NotificationScheduler:
    """Handle scheduled notifications"""
    
    @staticmethod
    def schedule_notification(
        user,
        title: str,
        body: str,
        scheduled_at,
        template=None,
        trigger_type=None,
        trigger_id=None,
        **kwargs
    ):
        """
        Schedule a notification to be sent later
        
        Args:
            user: CustomUser instance
            title: Notification title
            body: Notification body
            scheduled_at: DateTime when to send
            template: PushNotificationTemplate instance (optional)
            trigger_type: Type of trigger that created this
            trigger_id: ID of the triggering object
            **kwargs: Additional notification parameters
        
        Returns:
            PushNotification instance
        """
        from notifications.models import PushNotification
        
        notification = PushNotification.objects.create(
            user=user,
            template=template,
            title=title,
            body=body,
            data=kwargs.get('data', {}),
            sound=kwargs.get('sound', 'default'),
            priority=kwargs.get('priority', 'default'),
            badge=kwargs.get('badge', 1),
            category=kwargs.get('category', None),
            status='scheduled',
            scheduled_at=scheduled_at,
            trigger_type=trigger_type,
            trigger_id=trigger_id,
        )
        
        return notification
    
    @staticmethod
    def process_pending_notifications():
        """
        Process and send all pending scheduled notifications
        Should be called by Celery task periodically
        """
        from notifications.models import PushNotification
        
        now = timezone.now()
        
        # Get all scheduled notifications that are due
        pending_notifications = PushNotification.objects.filter(
            status='scheduled',
            scheduled_at__lte=now
        ).select_related('user')
        
        results = {
            'processed': 0,
            'sent': 0,
            'failed': 0
        }
        
        for notification in pending_notifications:
            results['processed'] += 1
            
            try:
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
                    results['sent'] += 1
                else:
                    notification.status = 'failed'
                    notification.error_message = result.get('error', 'Unknown error')
                    results['failed'] += 1
                
                notification.save()
                
            except Exception as e:
                logger.error(f"Error processing notification {notification.id}: {str(e)}")
                notification.status = 'failed'
                notification.error_message = str(e)
                notification.save()
                results['failed'] += 1
        
        return results


# Alias for backward compatibility and convenience
NotificationService = PushNotificationService
