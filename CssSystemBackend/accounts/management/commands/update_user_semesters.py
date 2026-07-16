from django.core.management.base import BaseCommand
from accounts.models import CustomUser


class Command(BaseCommand):
    help = 'Update current_semester for all users based on current date'

    def handle(self, *args, **options):
        users = CustomUser.objects.all()
        updated_count = 0
        
        self.stdout.write(self.style.WARNING(f'Found {users.count()} users to update...'))
        
        for user in users:
            # Calculate and save semester
            old_semester = user.current_semester
            user.current_semester = user.calculate_current_semester()
            user.save()
            
            if old_semester != user.current_semester:
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated {user.first_name} {user.last_name}: '
                        f'Semester {old_semester} -> {user.current_semester}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully updated {updated_count} users!'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'All {users.count()} users now have current_semester set.'
            )
        )
