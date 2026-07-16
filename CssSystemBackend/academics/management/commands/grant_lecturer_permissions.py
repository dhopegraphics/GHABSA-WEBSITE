from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from accounts.models import CustomUser
from academics.models import Lecturer


class Command(BaseCommand):
    help = 'Grant all superusers permissions to manage Lecturers'

    def handle(self, *args, **options):
        # Get Lecturer content type
        content_type = ContentType.objects.get_for_model(Lecturer)
        
        # Get all permissions for Lecturer model
        permissions = Permission.objects.filter(content_type=content_type)
        
        self.stdout.write(f"Found {permissions.count()} permissions for Lecturer model:")
        for perm in permissions:
            self.stdout.write(f"  - {perm.codename}: {perm.name}")
        
        # Grant permissions to all superusers
        superusers = CustomUser.objects.filter(is_superuser=True)
        
        for user in superusers:
            for perm in permissions:
                user.user_permissions.add(perm)
            
            self.stdout.write(
                self.style.SUCCESS(f"✅ Granted Lecturer permissions to: {user}")
            )
        
        self.stdout.write(
            self.style.SUCCESS(f"\n✅ Successfully granted permissions to {superusers.count()} superuser(s)")
        )
