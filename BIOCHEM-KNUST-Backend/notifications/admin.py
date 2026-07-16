from django.contrib import admin
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import path
from django.utils import timezone
from notifications.models import (
    PushNotificationDevice,
    PushNotificationTemplate,
    PushNotification,
    NotificationTrigger,
    NotificationPreference,
)
from notifications.services import BulkNotificationService


@admin.register(PushNotificationDevice)
class PushNotificationDeviceAdmin(admin.ModelAdmin):
    list_display = ['user', 'platform', 'device_name', 'is_active', 'last_used', 'created_at', 'device_count']
    list_filter = ['platform', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__personal_email', 'user__student_email', 'device_token', 'device_name']
    readonly_fields = ['created_at', 'last_used', 'device_token_preview']
    actions = ['send_test_notification']
    
    def device_count(self, obj):
        """Show total devices for this user"""
        count = PushNotificationDevice.objects.filter(user=obj.user, is_active=True).count()
        return f"{count} device(s)"
    device_count.short_description = "User's Total Devices"
    
    def device_token_preview(self, obj):
        """Show abbreviated token for security"""
        token = obj.device_token
        if len(token) > 40:
            return f"{token[:20]}...{token[-20:]}"
        return token
    device_token_preview.short_description = "Device Token (Preview)"
    
    @admin.action(description="Send test push notification")
    def send_test_notification(self, request, queryset):
        """Send a test notification to selected devices"""
        from notifications.services import PushNotificationService
        import logging
        
        logger = logging.getLogger(__name__)
        success_count = 0
        failed_count = 0
        
        for device in queryset:
            try:
                if not device.is_active:
                    messages.warning(request, f"Device {device.device_name} for {device.user.username} is inactive - skipped")
                    continue
                
                # Send test notification
                result = PushNotificationService.send_to_user(
                    user=device.user,
                    title="Test Notification",
                    body=f"This is a test notification sent from admin to {device.platform} device: {device.device_name}",
                    data={
                        "type": "test",
                        "timestamp": str(timezone.now()),
                        "device_id": str(device.id),
                        "platform": device.platform
                    }
                )
                
                if result.get('success'):
                    success_count += 1
                    logger.info(f"Test notification sent to {device.user.username} on {device.platform}")
                else:
                    failed_count += 1
                    messages.warning(request, f"Failed to send to {device.user.username}: {result.get('message')}")
                    logger.error(f"Failed to send test notification to {device.user.username}: {result.get('message')}")
                    
            except Exception as e:
                failed_count += 1
                messages.error(request, f"Error sending to {device.user.username}: {str(e)}")
                logger.error(f"Exception sending test notification to {device.user.username}: {str(e)}", exc_info=True)
        
        # Summary message
        if success_count > 0:
            messages.success(request, f"Successfully sent test notifications to {success_count} device(s)")
        if failed_count > 0:
            messages.warning(request, f"Failed to send to {failed_count} device(s)")
        if success_count == 0 and failed_count == 0:
            messages.info(request, "No active devices selected")


@admin.register(PushNotificationTemplate)
class PushNotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'title', 'priority', 'is_active', 'created_at']
    list_filter = ['priority', 'is_active', 'created_at']
    search_fields = ['name', 'title', 'body']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PushNotification)
class PushNotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'status', 'scheduled_at', 'sent_at', 'created_at']
    list_filter = ['status', 'priority', 'trigger_type', 'created_at']
    search_fields = ['user__username', 'title', 'body']
    readonly_fields = ['created_at', 'updated_at', 'sent_at']
    date_hierarchy = 'created_at'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('send-bulk/', self.admin_site.admin_view(self.send_bulk_view), name='notifications-send-bulk'),
            path('send-all-exams/', self.admin_site.admin_view(self.send_all_exams), name='notifications-send-all-exams'),
            path('send-today-classes/', self.admin_site.admin_view(self.send_today_classes), name='notifications-send-today-classes'),
            path('send-all-pending/', self.admin_site.admin_view(self.send_all_pending), name='notifications-send-all-pending'),
        ]
        return custom_urls + urls
    
    def send_all_exams(self, request):
        """Send notifications for all upcoming exams in the next 24 hours"""
        from accounts.models import CustomUser
        from timetable_system.models import ExaminationSchedule
        from django.utils import timezone
        from datetime import timedelta
        
        if request.method == 'POST':
            try:
                # Get all exams in the next 24 hours
                now = timezone.now()
                tomorrow = now + timedelta(hours=24)
                upcoming_exams = ExaminationSchedule.objects.filter(
                    time__gte=now,
                    time__lte=tomorrow
                ).order_by('time')
                
                total_success = 0
                total_failed = 0
                total_skipped = 0
                exam_count = 0
                
                for exam in upcoming_exams:
                    # Get users for this exam by index number range
                    users = CustomUser.objects.filter(
                        is_active=True,
                        index_number__gte=exam.index_number_start,
                        index_number__lte=exam.index_number_end
                    )
                    
                    if users.exists():
                        results = BulkNotificationService.send_exam_notifications_to_users(users, exam)
                        total_success += results['success']
                        total_failed += results['failed']
                        total_skipped += results['skipped']
                        exam_count += 1
                
                messages.success(
                    request,
                    f"✅ Processed {exam_count} exams: Sent to {total_success} users, {total_failed} failed, {total_skipped} skipped"
                )
            except Exception as e:
                messages.error(request, f'Error sending exam notifications: {str(e)}')
            
            return redirect('admin:notifications_pushnotification_changelist')
        
        return redirect('admin:notifications-send-bulk')
    
    def send_today_classes(self, request):
        """Send notifications for all classes scheduled today"""
        from accounts.models import CustomUser
        from timetable_system.models import ClassSchedule
        from django.utils import timezone
        from datetime import datetime
        
        if request.method == 'POST':
            try:
                # Get today's day of week (1=Monday, 7=Sunday)
                today = timezone.now()
                day_of_week = today.isoweekday()
                current_year = datetime.now().year
                
                # Get all classes scheduled for today
                today_classes = ClassSchedule.objects.filter(
                    day_of_week=day_of_week
                )
                
                total_success = 0
                total_failed = 0
                class_count = 0
                
                for class_schedule in today_classes:
                    # Calculate graduation_year from class schedule year
                    diff = 4 - class_schedule.year
                    target_graduation_year = current_year + diff
                    
                    # Get users for this class
                    users = CustomUser.objects.filter(
                        is_active=True,
                        program=class_schedule.program,
                        graduation_year=target_graduation_year,
                    )
                    
                    # Only filter by group if the program requires groups (e.g., CS)
                    from timetable_system.models import ClassSchedule
                    if ClassSchedule.program_requires_group(class_schedule.program) and class_schedule.group:
                        users = users.filter(group=class_schedule.group)
                    
                    if users.exists():
                        results = BulkNotificationService.send_class_notifications_to_users(users, class_schedule)
                        total_success += results['success']
                        total_failed += results['failed']
                        class_count += 1
                
                messages.success(
                    request,
                    f"✅ Processed {class_count} classes: Sent to {total_success} users, {total_failed} failed"
                )
            except Exception as e:
                messages.error(request, f'Error sending class notifications: {str(e)}')
            
            return redirect('admin:notifications_pushnotification_changelist')
        
        return redirect('admin:notifications-send-bulk')
    
    def send_all_pending(self, request):
        """Send all pending notifications (exams + classes)"""
        from accounts.models import CustomUser
        from timetable_system.models import ExaminationSchedule, ClassSchedule
        from django.utils import timezone
        from datetime import timedelta, datetime
        
        if request.method == 'POST':
            try:
                now = timezone.now()
                tomorrow = now + timedelta(hours=24)
                current_year = datetime.now().year
                day_of_week = now.isoweekday()
                
                total_success = 0
                total_failed = 0
                total_skipped = 0
                
                # Send exam notifications
                upcoming_exams = ExaminationSchedule.objects.filter(
                    time__gte=now,
                    time__lte=tomorrow
                )
                
                exam_count = 0
                for exam in upcoming_exams:
                    users = CustomUser.objects.filter(
                        is_active=True,
                        index_number__gte=exam.index_number_start,
                        index_number__lte=exam.index_number_end
                    )
                    
                    if users.exists():
                        results = BulkNotificationService.send_exam_notifications_to_users(users, exam)
                        total_success += results['success']
                        total_failed += results['failed']
                        total_skipped += results['skipped']
                        exam_count += 1
                
                # Send class notifications
                today_classes = ClassSchedule.objects.filter(day_of_week=day_of_week)
                
                class_count = 0
                for class_schedule in today_classes:
                    diff = 4 - class_schedule.year
                    target_graduation_year = current_year + diff
                    
                    users = CustomUser.objects.filter(
                        is_active=True,
                        program=class_schedule.program,
                        graduation_year=target_graduation_year,
                    )
                    
                    # Only filter by group if the program requires groups (e.g., CS)
                    if ClassSchedule.program_requires_group(class_schedule.program) and class_schedule.group:
                        users = users.filter(group=class_schedule.group)
                    
                    if users.exists():
                        results = BulkNotificationService.send_class_notifications_to_users(users, class_schedule)
                        total_success += results['success']
                        total_failed += results['failed']
                        class_count += 1
                
                messages.success(
                    request,
                    f"✅ Sent all pending notifications: {exam_count} exams + {class_count} classes = {total_success} successful, {total_failed} failed, {total_skipped} skipped"
                )
            except Exception as e:
                messages.error(request, f'Error sending pending notifications: {str(e)}')
            
            return redirect('admin:notifications_pushnotification_changelist')
        
        return redirect('admin:notifications-send-bulk')
    
    def send_bulk_view(self, request):
        """Handle bulk notification sending"""
        from accounts.models import CustomUser
        from timetable_system.models import ExaminationSchedule, ClassSchedule
        
        if request.method == 'POST':
            from datetime import datetime
            notification_type = request.POST.get('notification_type')
            user_filter = request.POST.get('user_filter')
            current_year = datetime.now().year
            
            # Get users based on filter
            # Using formula from CustomUser.year: year = 4 - diff, where diff = graduation_year - current_year
            # Therefore: diff = 4 - year, and: graduation_year = current_year + diff
            if user_filter == 'all':
                users = CustomUser.objects.filter(is_active=True)
            elif user_filter == 'year_1':
                # Year 1: diff = 4 - 1 = 3, graduation_year = current_year + 3
                users = CustomUser.objects.filter(is_active=True, graduation_year=current_year + 3)
            elif user_filter == 'year_2':
                # Year 2: diff = 4 - 2 = 2, graduation_year = current_year + 2
                users = CustomUser.objects.filter(is_active=True, graduation_year=current_year + 2)
            elif user_filter == 'year_3':
                # Year 3: diff = 4 - 3 = 1, graduation_year = current_year + 1
                users = CustomUser.objects.filter(is_active=True, graduation_year=current_year + 1)
            elif user_filter == 'year_4':
                # Year 4: diff = 4 - 4 = 0, graduation_year = current_year
                users = CustomUser.objects.filter(is_active=True, graduation_year=current_year)
            elif user_filter == 'cs_program':
                users = CustomUser.objects.filter(is_active=True, program='CS')
            elif user_filter == 'it_program':
                users = CustomUser.objects.filter(is_active=True, program='IT')
            else:
                users = CustomUser.objects.filter(is_active=True)
            
            # Handle different notification types
            if notification_type == 'exam_schedule':
                exam_id = request.POST.get('exam_schedule_id')
                try:
                    exam = ExaminationSchedule.objects.get(id=exam_id)
                    # Filter users by index number range
                    users = users.filter(
                        index_number__gte=exam.index_number_start,
                        index_number__lte=exam.index_number_end
                    )
                    results = BulkNotificationService.send_exam_notifications_to_users(users, exam)
                    messages.success(
                        request,
                        f"Sent to {results['success']} users, {results['failed']} failed, {results['skipped']} skipped"
                    )
                except ExaminationSchedule.DoesNotExist:
                    messages.error(request, 'Exam schedule not found')
            
            elif notification_type == 'class_schedule':
                class_id = request.POST.get('class_schedule_id')
                try:
                    from datetime import datetime
                    class_schedule = ClassSchedule.objects.get(id=class_id)
                    
                    # Calculate graduation_year from class schedule year
                    # Using the same formula as CustomUser.year property:
                    # year = 4 - diff, where diff = graduation_year - current_year
                    # Therefore: diff = 4 - year
                    # And: graduation_year = current_year + diff
                    current_year = datetime.now().year
                    diff = 4 - class_schedule.year
                    target_graduation_year = current_year + diff
                    
                    # Filter users by program, graduation_year, and group
                    users = users.filter(
                        program=class_schedule.program,
                        graduation_year=target_graduation_year,
                    )
                    
                    # Only filter by group if the program requires groups (e.g., CS)
                    from timetable_system.models import ClassSchedule
                    if ClassSchedule.program_requires_group(class_schedule.program) and class_schedule.group:
                        users = users.filter(group=class_schedule.group)
                    
                    results = BulkNotificationService.send_class_notifications_to_users(users, class_schedule)
                    messages.success(
                        request,
                        f"Sent to {results['success']} users (Year {class_schedule.year}, graduates {target_graduation_year}), {results['failed']} failed"
                    )
                except ClassSchedule.DoesNotExist:
                    messages.error(request, 'Class schedule not found')
                except Exception as e:
                    messages.error(request, f'Error sending notifications: {str(e)}')
            
            elif notification_type == 'custom':
                title = request.POST.get('title')
                body = request.POST.get('body')
                priority = request.POST.get('priority', 'normal')
                
                results = BulkNotificationService.send_custom_bulk_notification(
                    users=users,
                    title=title,
                    body=body,
                    priority=priority
                )
                messages.success(
                    request,
                    f"Sent to {results['success']} users, {results['failed']} failed"
                )
            
            return redirect('admin:notifications_pushnotification_changelist')
        
        # GET request - show form with statistics
        from timetable_system.models import ExaminationSchedule, ClassSchedule
        from django.utils import timezone
        from datetime import timedelta, datetime
        from django.db.models import Q
        
        # Calculate statistics
        now = timezone.now()
        tomorrow = now + timedelta(hours=24)
        current_year = datetime.now().year
        day_of_week = now.isoweekday()
        
        # Upcoming exams in next 24 hours
        upcoming_exams = ExaminationSchedule.objects.filter(
            time__gte=now,
            time__lte=tomorrow
        )
        upcoming_exams_count = upcoming_exams.count()
        
        # Calculate potential recipients for upcoming exams
        exam_recipients = 0
        for exam in upcoming_exams:
            exam_recipients += CustomUser.objects.filter(
                is_active=True,
                index_number__gte=exam.index_number_start,
                index_number__lte=exam.index_number_end
            ).count()
        
        # Classes scheduled for today
        today_classes = ClassSchedule.objects.filter(day_of_week=day_of_week)
        classes_today_count = today_classes.count()
        
        # Calculate potential recipients for today's classes
        class_recipients = 0
        for class_schedule in today_classes:
            diff = 4 - class_schedule.year
            target_graduation_year = current_year + diff
            
            class_users = CustomUser.objects.filter(
                is_active=True,
                program=class_schedule.program,
                graduation_year=target_graduation_year,
            )
            
            if class_schedule.group:
                class_users = class_users.filter(group=class_schedule.group)
            
            class_recipients += class_users.count()
        
        # Active users (with at least one notification channel enabled)
        active_users_count = CustomUser.objects.filter(
            is_active=True
        ).filter(
            Q(notification_preferences__push_enabled=True) |
            Q(notification_preferences__sms_enabled=True) |
            Q(notification_preferences__email_enabled=True)
        ).distinct().count()
        
        # Registered devices
        registered_devices_count = PushNotificationDevice.objects.filter(
            is_active=True
        ).count()
        
        stats = {
            'upcoming_exams': upcoming_exams_count,
            'classes_today': classes_today_count,
            'active_users': active_users_count,
            'registered_devices': registered_devices_count,
            'exam_recipients': exam_recipients,
            'class_recipients': class_recipients,
            'total_pending': exam_recipients + class_recipients,
        }
        
        context = {
            'title': 'Send Bulk Notifications',
            'exam_schedules': ExaminationSchedule.objects.all().order_by('-time')[:50],
            'class_schedules': ClassSchedule.objects.all().order_by('-created_at')[:50],
            'stats': stats,
        }
        return render(request, 'admin/notifications/send_bulk_form.html', context)


@admin.register(NotificationTrigger)
class NotificationTriggerAdmin(admin.ModelAdmin):
    list_display = ['name', 'trigger_type', 'template', 'offset_value', 'offset_unit', 'is_active']
    list_filter = ['trigger_type', 'offset_unit', 'is_active']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'push_enabled', 'sms_enabled', 'email_enabled', 'quiet_hours_enabled']
    list_filter = ['push_enabled', 'sms_enabled', 'email_enabled', 'quiet_hours_enabled']
    search_fields = ['user__username', 'user__personal_email', 'user__student_email']
    readonly_fields = ['created_at', 'updated_at']
