import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from accounts.models import CustomUser
from admissions.models import EligibilityCheck
from phonenumber_field.phonenumber import PhoneNumber
import re


class Command(BaseCommand):
    help = 'Export first year students contacts to CSV file for Google Contacts import'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='first_year_contacts.csv',
            help='CSV filename (default: first_year_contacts.csv)'
        )
        parser.add_argument(
            '--year',
            type=int,
            default=2029,
            help='Graduation year to filter (default: 2029 for current first years)'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default=None,
            help='Output directory (default: project root)'
        )

    def handle(self, *args, **options):
        filename = options['file']
        graduation_year = options['year']
        output_dir = options['output_dir'] or settings.BASE_DIR
        
        # Create full file path
        file_path = os.path.join(output_dir, filename)
        
        self.stdout.write(f"Exporting contacts for graduation year: {graduation_year}")
        self.stdout.write(f"Output file: {file_path}")
        
        # Dictionary to store unique contacts (using phone as key to avoid duplicates)
        contacts = {}
        
        # Process CustomUser records
        self.stdout.write("Processing CustomUser records...")
        custom_users = CustomUser.objects.filter(graduation_year=graduation_year)
        
        for user in custom_users:
            phone_str = self.format_phone(user.phone)
            if phone_str:
                # Build full name
                full_name = self.build_full_name(user.first_name, user.middle_name, user.last_name)
                program = user.program or 'Unknown'
                
                # Create contact entry
                contact_name = f"{full_name} {program}{str(graduation_year)[-2:]}"
                
                contacts[phone_str] = {
                    'name': contact_name,
                    'phone': phone_str,
                    'source': 'CustomUser'
                }
        
        self.stdout.write(f"Found {len(contacts)} contacts from CustomUser")
        
        # Process EligibilityCheck records (all are considered first years)
        self.stdout.write("Processing EligibilityCheck records...")
        eligibility_checks = EligibilityCheck.objects.all()
        
        new_contacts_count = 0
        for check in eligibility_checks:
            # Clean and format phone number
            phone_str = self.clean_phone_string(check.phone)
            if phone_str:
                # Only add if not already exists (avoid duplicates)
                if phone_str not in contacts:
                    # Use full_name from EligibilityCheck
                    full_name = check.full_name.strip()
                    program = check.preferred_program or 'Unknown'
                    
                    # Create contact entry
                    contact_name = f"{full_name} {program}{str(graduation_year)[-2:]}"
                    
                    contacts[phone_str] = {
                        'name': contact_name,
                        'phone': phone_str,
                        'source': 'EligibilityCheck'
                    }
                    new_contacts_count += 1
        
        self.stdout.write(f"Added {new_contacts_count} new contacts from EligibilityCheck")
        self.stdout.write(f"Total unique contacts: {len(contacts)}")
        
        # Write to CSV
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header for Google Contacts
                writer.writerow(['Name', 'Phone 1 - Value'])
                
                # Sort contacts by name for better organization
                sorted_contacts = sorted(contacts.values(), key=lambda x: x['name'])
                
                for contact in sorted_contacts:
                    writer.writerow([contact['name'], contact['phone']])
            
            self.stdout.write(
                self.style.SUCCESS(f"Successfully exported {len(contacts)} contacts to {file_path}")
            )
            
            # Print summary
            self.stdout.write("\n--- SUMMARY ---")
            self.stdout.write(f"Total contacts exported: {len(contacts)}")
            self.stdout.write(f"Graduation year: {graduation_year}")
            self.stdout.write(f"Output file: {file_path}")
            
            # Show sample entries
            self.stdout.write("\n--- SAMPLE ENTRIES ---")
            sample_contacts = list(contacts.values())[:5]
            for contact in sample_contacts:
                self.stdout.write(f"{contact['name']}, {contact['phone']} (from {contact['source']})")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error writing to CSV file: {str(e)}")
            )

    def build_full_name(self, first_name, middle_name, last_name):
        """Build full name from name components"""
        name_parts = [first_name]
        if middle_name:
            name_parts.append(middle_name)
        name_parts.append(last_name)
        return ' '.join(part.strip() for part in name_parts if part)

    def format_phone(self, phone_field):
        """Format phone number from PhoneNumberField"""
        if not phone_field:
            return None
            
        try:
            # Convert PhoneNumber to string
            if isinstance(phone_field, PhoneNumber):
                phone_str = str(phone_field)
                # Remove any spaces or dashes and ensure it starts with +
                phone_clean = re.sub(r'[^\d+]', '', phone_str)
                if phone_clean and (phone_clean.startswith('+233') or phone_clean.startswith('233')):
                    if not phone_clean.startswith('+'):
                        phone_clean = '+' + phone_clean
                    return phone_clean
            return None
        except Exception:
            return None

    def clean_phone_string(self, phone_string):
        """Clean and format phone string from EligibilityCheck"""
        if not phone_string:
            return None
            
        # Remove all non-digit characters except +
        phone_clean = re.sub(r'[^\d+]', '', str(phone_string))
        
        # Handle different phone formats
        if phone_clean.startswith('+233'):
            return phone_clean
        elif phone_clean.startswith('233'):
            return '+' + phone_clean
        elif phone_clean.startswith('0') and len(phone_clean) == 10:
            # Convert 0XXXXXXXXX to +233XXXXXXXXX
            return '+233' + phone_clean[1:]
        elif len(phone_clean) == 9:
            # Assume it's missing the leading 0, add +233
            return '+233' + phone_clean
        
        # If it doesn't match expected formats, return None
        return None