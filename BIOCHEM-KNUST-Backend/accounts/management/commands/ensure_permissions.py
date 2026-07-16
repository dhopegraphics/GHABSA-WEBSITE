"""
Management command to ensure the custom permission exists.
Run this on PythonAnywhere after deployment.

Usage:
    python manage.py ensure_permissions
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from accounts.models import CustomUser


class Command(BaseCommand):
    help = 'Ensures custom permissions exist in the database'

    def handle(self, *args, **options):
        self.stdout.write('=' * 70)
        self.stdout.write(self.style.SUCCESS('ENSURING CUSTOM PERMISSIONS'))
        self.stdout.write('=' * 70)
        self.stdout.write('')

        # Get content type for CustomUser
        content_type = ContentType.objects.get_for_model(CustomUser)
        
        # Define the custom permission
        permission_data = {
            'codename': 'view_sensitive_student_data',
            'name': 'Can view sensitive student information (emails, student ID, index number)',
            'content_type': content_type,
        }
        
        # Check if permission exists
        permission, created = Permission.objects.get_or_create(
            codename=permission_data['codename'],
            content_type=permission_data['content_type'],
            defaults={'name': permission_data['name']}
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created permission: {permission.codename}'))
        else:
            self.stdout.write(self.style.WARNING(f'✓ Permission already exists: {permission.codename}'))
        
        self.stdout.write('')
        self.stdout.write(f'  Codename: {permission.codename}')
        self.stdout.write(f'  Name: {permission.name}')
        self.stdout.write(f'  Content Type: {permission.content_type}')
        self.stdout.write('')
        self.stdout.write('=' * 70)
        self.stdout.write(self.style.SUCCESS('✅ Permission check completed!'))
        self.stdout.write('=' * 70)
        self.stdout.write('')
        self.stdout.write('To grant this permission to a user:')
        self.stdout.write('1. Django Admin: Users → Edit User → User permissions → Add permission')
        self.stdout.write('2. Python Shell: user.user_permissions.add(permission)')
        self.stdout.write('')
