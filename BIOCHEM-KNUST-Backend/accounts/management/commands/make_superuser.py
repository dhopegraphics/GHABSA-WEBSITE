from django.core.management.base import BaseCommand
from accounts.models import CustomUser


class Command(BaseCommand):
    help = 'Promote a user to superuser status by phone number'

    def add_arguments(self, parser):
        parser.add_argument('phone', type=str, help='Phone number of the user to promote')

    def handle(self, *args, **options):
        phone = options['phone']
        
        try:
            user = CustomUser.objects.get(phone=phone)
            
            # Make the user a superuser
            user.is_superuser = True
            user.is_staff = True
            user.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Successfully promoted {phone} to superuser!')
            )
            self.stdout.write(f'   - is_superuser: {user.is_superuser}')
            self.stdout.write(f'   - is_staff: {user.is_staff}')
            
        except CustomUser.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ User with phone {phone} does not exist')
            )
