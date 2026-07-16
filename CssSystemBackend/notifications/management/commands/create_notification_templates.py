"""
Management command to create default notification templates and triggers
"""
from django.core.management.base import BaseCommand
from notifications.models import PushNotificationTemplate, NotificationTrigger


class Command(BaseCommand):
    help = 'Create default notification templates and triggers'

    def handle(self, *args, **options):
        self.stdout.write('Creating default notification templates...')
        
        templates_created = 0
        triggers_created = 0
        
        # Class Schedule Templates
        templates = [
            {
                'name': 'class_reminder_1hour',
                'title': '⏰ Class Starting Soon!',
                'body': '{course_name} ({course_code}) starts in 1 hour at {start_time} in {room}',
                'data': {
                    'screen': 'ClassSchedule',
                    'scheduleId': '{schedule_id}',
                    'type': 'class_reminder'
                },
                'priority': 'high',
                'category': 'class_reminder',
            },
            {
                'name': 'class_reminder_24hours',
                'title': '📅 Class Tomorrow',
                'body': 'Reminder: {course_name} ({course_code}) tomorrow at {start_time} in {room}',
                'data': {
                    'screen': 'ClassSchedule',
                    'scheduleId': '{schedule_id}',
                    'type': 'class_reminder'
                },
                'priority': 'default',
                'category': 'class_reminder',
            },
            
            # Exam Schedule Templates
            {
                'name': 'exam_reminder_1hour',
                'title': '🚨 Exam Starting Soon!',
                'body': '{course_name} exam in 1 hour at {exam_time}. Location: {college}, {room}',
                'data': {
                    'screen': 'ExamSchedule',
                    'examId': '{exam_id}',
                    'type': 'exam_reminder'
                },
                'priority': 'high',
                'category': 'exam_reminder',
                'sound': 'alarm',
            },
            {
                'name': 'exam_reminder_24hours',
                'title': '📝 Exam Tomorrow',
                'body': '{course_name} exam on {exam_date} at {exam_time}. Location: {college}, {room}',
                'data': {
                    'screen': 'ExamSchedule',
                    'examId': '{exam_id}',
                    'type': 'exam_reminder'
                },
                'priority': 'high',
                'category': 'exam_reminder',
            },
            
            # General Templates
            {
                'name': 'general_announcement',
                'title': '📢 Announcement',
                'body': '{message}',
                'data': {
                    'type': 'announcement'
                },
                'priority': 'default',
                'category': 'announcement',
            },
            {
                'name': 'deadline_reminder',
                'title': '⚠️ Deadline Approaching',
                'body': '{title} is due in {time_remaining}',
                'data': {
                    'screen': 'Planner',
                    'itemId': '{item_id}',
                    'type': 'deadline'
                },
                'priority': 'high',
                'category': 'deadline',
            },
        ]
        
        for template_data in templates:
            template, created = PushNotificationTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults=template_data
            )
            if created:
                templates_created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created template: {template.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'- Template already exists: {template.name}')
                )
        
        self.stdout.write('\nCreating default notification triggers...')
        
        # Create triggers for class schedules
        class_1hour_template = PushNotificationTemplate.objects.get(name='class_reminder_1hour')
        class_24hour_template = PushNotificationTemplate.objects.get(name='class_reminder_24hours')
        
        triggers_data = [
            {
                'name': 'Class Reminder - 1 Hour Before',
                'trigger_type': 'class_schedule',
                'template': class_1hour_template,
                'offset_value': 1,
                'offset_unit': 'hours',
            },
            {
                'name': 'Class Reminder - 24 Hours Before',
                'trigger_type': 'class_schedule',
                'template': class_24hour_template,
                'offset_value': 24,
                'offset_unit': 'hours',
            },
        ]
        
        # Create triggers for exam schedules
        exam_1hour_template = PushNotificationTemplate.objects.get(name='exam_reminder_1hour')
        exam_24hour_template = PushNotificationTemplate.objects.get(name='exam_reminder_24hours')
        
        triggers_data.extend([
            {
                'name': 'Exam Reminder - 1 Hour Before',
                'trigger_type': 'exam_schedule',
                'template': exam_1hour_template,
                'offset_value': 1,
                'offset_unit': 'hours',
            },
            {
                'name': 'Exam Reminder - 24 Hours Before',
                'trigger_type': 'exam_schedule',
                'template': exam_24hour_template,
                'offset_value': 24,
                'offset_unit': 'hours',
            },
        ])
        
        for trigger_data in triggers_data:
            trigger, created = NotificationTrigger.objects.get_or_create(
                name=trigger_data['name'],
                defaults=trigger_data
            )
            if created:
                triggers_created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created trigger: {trigger.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'- Trigger already exists: {trigger.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully created {templates_created} templates and {triggers_created} triggers'
            )
        )
